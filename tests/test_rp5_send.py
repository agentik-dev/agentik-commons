"""Packet rp5-send: the last check of the exact bytes, the account, the search, the screen that is
the bytes, the typed word on the terminal device, the one door to a writing `gh` call and the
browser's links. Each test runs in a temp HOME with a PATH of a stub folder, /usr/bin and /bin: a
stub `gh` records its argv and stdin and answers from fixture files, and a stub `ps` prints a tree
with no `claude` in it. The typed word goes through `pty.fork`. Nothing here reaches the network,
runs the real `gh` or reads the real home; logins and repos are made up."""
import ast
import fcntl
import hashlib
import io
import json
import os
import pty
import re
import select
import signal
import struct
import subprocess
import sys
import tempfile
import termios
import time
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "plugins" / "suite" / "lib"
PACKAGE = LIB / "agentik_suite"
SEND = PACKAGE / "send.py"
SYSTEM = "/usr/bin:/bin"
REPO = "example-owner/faketool"
LOGIN = "octo-example"
FP = "0123456789ab"
PUBLIC = {"tools": {"faketool": REPO}}

sys.path.insert(0, str(LIB))
from agentik_suite import catalogue, term  # noqa: E402
try:
    from agentik_suite import send  # noqa: E402
except ImportError:
    send = None

MESSAGES = catalogue.load()
HEAD, END = MESSAGES.get("issue.screen.head", "\0head"), MESSAGES.get("issue.screen.end", "\0end")
MORE, ASK = MESSAGES.get("issue.screen.more", "\0more"), MESSAGES.get("issue.send.ask", "\0ask")
WITHIN = MESSAGES.get("issue.screen.within", "\0within")
PAUSE = getattr(send, "QUIET", 0) + 0.5  # a person reads the question before answering it
EARLY = [2, "err.issue.send.early"]
SMALL = [2, "err.issue.send.small"]

GH = r'''#!/usr/bin/python3 -I
import json, os, sys
d = %r
args = sys.argv[1:]
data = sys.stdin.buffer.read().decode("utf-8") if args[:2] == ["issue", "create"] else ""
with open(os.path.join(d, "calls.jsonl"), "a") as fh:
    fh.write(json.dumps({"argv": args, "stdin": data,
                         "vars": sorted(k for k in os.environ if k.endswith("_TOKEN"))}) + "\n")
key = "_".join(args[:2])
if os.path.exists(os.path.join(d, key + ".out")):
    with open(os.path.join(d, key + ".out")) as fh:
        sys.stdout.write(fh.read())
code = 0
if os.path.exists(os.path.join(d, key + ".exit")):
    with open(os.path.join(d, key + ".exit")) as fh:
        code = int(fh.read())
sys.exit(code)
'''
PS = '#!/bin/sh\necho "    1     0 /sbin/launchd"\necho "$PPID     1 /usr/bin/python3"\n'
PS_ABOVE = ('#!/bin/sh\necho "    1     0 /sbin/launchd"\necho "$PPID  4242 /usr/bin/python3"\n'
            'echo " 4242     1 /opt/made-up/bin/claude"\n')
URL = "https://github.com/%s/issues/7" % REPO


def draft(happened="the check said no", tool="faketool", pad_to=None, lines=None):
    """A draft in the form's shape: the title, a blank line, labelled lines, the marker."""
    body = ["Ran: `faketool doctor`", "Happened: %s" % happened, "Expected: `it passes`",
            "Versions: `faketool 1.2.3`"]
    if lines:
        body = ["Out: `step %02d of the made-up run wrote a line of %s`" % (i, "x" * (i * 3 % 70))
                for i in range(lines - 3)]
    text = "\n".join(["%s doctor: the check failed" % tool, ""] + body
                     + ["agentik-issue/1 %s 1.2.3 %s" % (tool, FP)]) + "\n"
    if pad_to:
        short = pad_to - len(text.encode())
        text = text.replace("Out: `step 00 ", "Out: `step 00 " + "y" * short, 1)
    return text.encode("utf-8")


class FakeForm:
    """rp4's three functions, faked: each line a field; a `Happened` line's value is free."""
    LABEL = "Happened: "

    def __init__(self, raises=False, drift=False):
        self.raises, self.drift = raises, drift

    def parse(self, data, tools):
        if self.raises:
            raise ValueError("not the form")
        fields = []
        for n, text in enumerate(data.decode("utf-8").split("\n")[:-1], 1):
            if text.startswith(self.LABEL):
                fields.append(("happened", n, text[len(self.LABEL):]))
            else:
                fields.append(("fixed", n, text))
        return fields

    def build(self, fields):
        out = "".join((self.LABEL + v if k == "happened" else v) + "\n" for k, _, v in fields)
        return (out + ("drift\n" if self.drift else "")).encode("utf-8")

    def free(self, fields):
        return [f for f in fields if f[0] == "happened"]


def fake_scrub(hit):
    return types.SimpleNamespace(detect=lambda value, m: ["path"] if value == hit else [])


class Base(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(send, "agentik_suite.send does not exist")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = os.path.realpath(tmp.name)
        self.stubs = os.path.join(self.home, "stubs")
        self.gh = os.path.join(self.home, "gh")
        os.mkdir(self.stubs)
        os.mkdir(self.gh)
        self.stub("gh", GH % self.gh)
        self.stub("ps", PS)
        self.fixture("auth_status.out", json.dumps({"hosts": {"github.com": [
            {"active": True, "host": "github.com", "login": LOGIN, "state": "success"}]}}))
        self.fixture("issue_list.out", "[]")
        self.fixture("issue_create.out", URL + "\n")

    def stub(self, name, body):
        path = os.path.join(self.stubs, name)
        with open(path, "w") as fh:
            fh.write(body)
        os.chmod(path, 0o755)

    def fixture(self, name, text):
        with open(os.path.join(self.gh, name), "w") as fh:
            fh.write(text)

    def env(self, **more):
        env = {"HOME": self.home, "PATH": "%s:%s" % (self.stubs, SYSTEM)}
        env.update(more)
        return env

    def calls(self, verb=None):
        path = os.path.join(self.gh, "calls.jsonl")
        if not os.path.exists(path):
            return []
        with open(path) as fh:
            found = [json.loads(line) for line in fh]
        return [c for c in found if verb is None or c["argv"][:2] == verb.split()]

    def drive(self, data, word, rows=24, cols=200, env=None, notes=(), after=None, ahead=None,
              blind=None, resize=None, file_repo=None, stdin=None):
        """approve, then _file when approved, in a child of pty.fork; this side reads the screen,
        presses Enter at each page's prompt and types `word` at the last, each after a person's
        pause; `word` may be [(pause, bytes)]. `ahead` is typed before any screen. `blind` is a
        writer that never reads the screen: [(seconds, bytes)] on its own clock, and the child
        starts `approve` only once its first line waits on the terminal, so the stream begins
        before the screen whatever the machine's load. `resize` is (rows, cols), set at the
        first question before it is answered. `stdin`, when given, is the child's fd 0, a pipe,
        while the terminal stays its device. (screen, result)."""
        env = env or self.env()
        out = os.path.join(self.home, "result.json")
        pid, fd = pty.fork()
        if pid == 0:
            try:
                fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
                if stdin is not None:
                    r, w = os.pipe()
                    os.write(w, stdin)
                    os.close(w)
                    os.dup2(r, 0)
                    os.close(r)
                if blind:  # the blind stream's first line waits before anything is drawn
                    select.select([0], [], [], 20)
                result = {}
                t = term.Term(env=env, out=io.StringIO(), err=io.StringIO())
                try:
                    approved = send.approve(data, REPO, LOGIN, list(notes), env, t)
                    result["approved"] = approved is not None
                    if approved is not None:
                        if after:
                            after(approved)
                        result["url"] = send._file(approved, file_repo or REPO, env)
                except send.Refusal as e:
                    result["refusal"] = [e.code, e.mid] + ([e.values] if e.values else [])
                except Exception as e:  # noqa: BLE001 - said back to the parent
                    result["error"] = "%s: %s" % (type(e).__name__, e)
                with open(out, "w") as fh:
                    json.dump(result, fh)
            finally:
                os._exit(0)
        words = word if isinstance(word, list) else [(PAUSE, word)]
        replies = {MORE.encode(): [(PAUSE, b"\n")], WITHIN.encode(): [(PAUSE, b"\n")],
                   ASK.encode(): words}
        buf, pos, deadline = b"", 0, time.monotonic() + 30
        began, sched, asked = time.monotonic(), list(blind or []), 0
        if ahead:
            os.write(fd, ahead)
        if blind:
            os.set_blocking(fd, False)
        try:
            while True:
                if time.monotonic() > deadline:
                    os.kill(pid, signal.SIGKILL)
                    self.fail("the child ran past 30 s; the screen: %r" % buf[-400:])
                while sched and time.monotonic() - began >= sched[0][0]:
                    try:
                        os.write(fd, sched.pop(0)[1])
                    except (BlockingIOError, OSError):
                        pass
                if select.select([fd], [], [], 0.005 if blind else 1)[0]:
                    try:
                        chunk = os.read(fd, 65536)
                    except BlockingIOError:
                        continue
                    except OSError:
                        break
                    if not chunk:
                        break
                    buf += chunk
                while not blind:
                    hits = sorted((buf.find(k, pos), k) for k in replies if buf.find(k, pos) >= 0)
                    if not hits:
                        break
                    pos = hits[0][0] + len(hits[0][1])
                    asked += 1
                    if resize and asked == 1:
                        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", resize[0],
                                                                         resize[1], 0, 0))
                    for pause, typed in replies[hits[0][1]]:
                        time.sleep(pause)
                        try:
                            os.write(fd, typed)
                        except OSError:  # the child refused and is gone
                            break
        finally:
            os.close(fd)
            os.waitpid(pid, 0)
        with open(out) as fh:
            return buf.decode("utf-8", "replace").replace("\r\n", "\n"), json.load(fh)

    def shown(self, screen):
        """The lines between the head and the end lines, less each page's prompt and the line
        break its Enter echoes, joined."""
        lines = screen.split("\n")
        start = lines.index(HEAD) + 1
        end = lines.index(END, start)
        kept, skip, join = [], False, False
        for line in lines[start:end]:
            if line in (MORE, WITHIN):
                skip, join = True, line == WITHIN
                continue
            if skip and line == "":
                skip = False
                continue
            skip = False
            if join:
                kept[-1] += line
            else:
                kept.append(line)
            join = False
        return "\n".join(kept) + "\n"

    def tops(self, screen, cols):
        """For each question, the screen rows written since the last answer through the
        question and the cursor's row under it, from the head line on; the blank row an Enter's
        echo leaves above a page is not the page's. A wide character counts two columns."""
        found, used = [], 0
        lines = screen.split("\n")
        for line in lines[lines.index(HEAD) if HEAD in lines else len(lines):]:
            used += max(1, -(-sum(2 if ord(c) > 0x2e80 else 1 for c in line) // cols))
            if line in (MORE, WITHIN, ASK):
                found.append(used + 1)
                used = -1
        return found

    def pages(self, screen, cols):
        """The rows each page writes before its prompt, the echo of the Enter that opened it
        left out; the last page, which ends at the word's question, as well."""
        found = []
        for n, part in enumerate(re.split("(?:%s|%s|%s)\n" % (
                re.escape(MORE), re.escape(WITHIN), re.escape(ASK)), screen)[:-1]):
            lines = part.split("\n")[(1 if n else 0):-1]
            found.append(sum(max(1, -(-len(line) // cols)) for line in lines))
        return found


class TypedWordTest(Base):
    def test_1_send_files_the_bytes_the_screen_showed(self):
        data = draft()
        path = os.path.join(self.home, "draft.md")
        with open(path, "wb") as fh:
            fh.write(data)
        with open(path, "rb") as fh:
            screen, result = self.drive(fh.read(), b"send\n")
        self.assertEqual(result, {"approved": True, "url": URL})
        created = self.calls("issue create")
        self.assertEqual(len(created), 1)
        argv = created[0]["argv"]
        self.assertEqual(argv[argv.index("-R") + 1], "github.com/" + REPO)
        self.assertEqual(argv[argv.index("-F") + 1], "-")
        joined = (argv[argv.index("-t") + 1] + "\n\n" + created[0]["stdin"]).encode("utf-8")
        self.assertEqual(joined, data)
        self.assertEqual(self.shown(screen).encode("utf-8"), data)
        self.assertEqual(created[0]["vars"], [])
        with open(path, "rb") as fh:
            self.assertEqual(fh.read(), joined)
        self.assertIn(MESSAGES["issue.screen.repo"].replace("{repo}", REPO), screen)
        self.assertIn(MESSAGES["issue.screen.login"].replace("{login}", LOGIN), screen)

    def test_2_any_other_answer_files_nothing(self):
        for word in (b"y\n", b"yes\n", b"SEND\n", b"\n", b"send \n", b"\x04", b"\x03"):
            with self.subTest(word=word):
                screen, result = self.drive(draft(), word)
                self.assertEqual(result, {"approved": False}, screen[-300:])
                self.assertEqual(self.calls("issue create"), [])

    def test_3_no_terminal_is_refused(self):
        path = os.path.join(self.home, "draft.md")
        with open(path, "wb") as fh:
            fh.write(draft())
        code = ("import json, sys; sys.path.insert(0, %r)\n"
                "from agentik_suite import send, term\n"
                "env = json.loads(sys.argv[2]); t = term.Term(env=env)\n"
                "try:\n"
                "    a = send.approve(open(sys.argv[1], 'rb').read(), %r, %r, [], env, t)\n"
                "    print(json.dumps({'approved': a is not None}))\n"
                "except send.Refusal as e:\n"
                "    print(json.dumps({'refusal': [e.code, e.mid]}))\n" % (str(LIB), REPO, LOGIN))
        p = subprocess.run([sys.executable, "-I", "-c", code, path, json.dumps(self.env())],
                           input=b"send\n", capture_output=True, timeout=60,
                           start_new_session=True, env=self.env())
        self.assertEqual(json.loads(p.stdout), {"refusal": [2, "err.issue.send.tty"]}, p.stderr)
        self.assertEqual(self.calls(), [])
        # a terminal, and `send` waiting on stdin: the word is read from the device alone
        _, result = self.drive(draft(), b"no\n", stdin=b"send\n" * 64)
        self.assertEqual(result, {"approved": False})
        self.assertEqual(self.calls("issue create"), [])

    def test_4_inside_claude_code_is_refused(self):
        _, result = self.drive(draft(), b"send\n", env=self.env(CLAUDECODE="1"))
        self.assertEqual(result, {"refusal": [2, "err.issue.send.inside"]})
        self.stub("ps", PS_ABOVE)
        _, result = self.drive(draft(), b"send\n")
        self.assertEqual(result, {"refusal": [2, "err.issue.send.parent"]})
        self.assertEqual(self.calls("issue create"), [])
        self.stub("ps", PS)
        screen, result = self.drive(draft(), b"send\n", env=self.env(CLAUDE_CODE_USE_BEDROCK="1"))
        self.assertEqual(result, {"approved": True, "url": URL})
        self.assertIn(ASK, screen)

    def test_7_a_tall_draft_is_paged_in_order(self):
        data = draft(lines=44, pad_to=4107)
        self.assertEqual((len(data), data.count(b"\n")), (4107, 44))
        screen, result = self.drive(data, b"no\n", rows=24, cols=80)
        self.assertEqual(result, {"approved": False})
        self.assertGreaterEqual(screen.count(MORE), 2)
        self.assertEqual(self.shown(screen).encode("utf-8"), data)
        for page in screen.split(MORE + "\n")[1:-1]:  # a page between two prompts fits
            rows = sum(max(1, -(-len(line) // 80)) for line in page.split("\n")[1:-1])
            self.assertLessEqual(rows, 22, page)
        screen, result = self.drive(data, b"no\n", rows=60, cols=200)
        self.assertEqual(screen.count(MORE), 0)
        self.assertEqual(self.shown(screen).encode("utf-8"), data)

    def test_r1_f3_a_line_taller_than_a_page_is_paged_by_its_rows(self):
        data = draft(happened=" ".join("w%03d" % n for n in range(500)))
        self.assertGreater(max(map(len, data.split(b"\n"))), 22 * 80)
        screen, result = self.drive(data, b"no\n", rows=24, cols=80)
        self.assertEqual(result, {"approved": False})
        self.assertTrue(all(0 < n <= 22 for n in self.pages(screen, 80)), self.pages(screen, 80))
        self.assertGreaterEqual(screen.count(WITHIN), 1)
        self.assertEqual(self.shown(screen).encode("utf-8"), data)
        wide = draft(happened="\u4e2d" * 1500)  # a wide character takes two columns
        screen, result = self.drive(wide, b"no\n", rows=24, cols=80)
        self.assertEqual(self.shown(screen).encode("utf-8"), wide)
        for part in re.split("(?:%s|%s)\n" % (re.escape(MORE), re.escape(WITHIN)), screen)[1:-1]:
            rows = sum(max(1, -(-sum(2 if ord(c) > 0x2e80 else 1 for c in line) // 80))
                       for line in part.split("\n")[1:-1])
            self.assertLessEqual(rows, 22)

    def test_8_the_approved_bytes_are_what_is_filed(self):
        data = draft()
        path = os.path.join(self.home, "draft.md")
        with open(path, "wb") as fh:
            fh.write(data)

        def rewrite(approved):
            with open(path, "wb") as fh:
                fh.write(draft(happened="something else"))
        _, result = self.drive(data, b"send\n", after=rewrite)
        self.assertEqual(result, {"approved": True, "url": URL})
        created = self.calls("issue create")
        self.assertEqual(created[0]["stdin"].encode("utf-8"), data.split(b"\n", 2)[2])

        def change(approved):
            approved.data = draft(happened="something else")
        _, result = self.drive(data, b"send\n", after=change)
        self.assertEqual(result, {"approved": True, "refusal": [2, "err.issue.send.changed"]})
        self.assertEqual(len(self.calls("issue create")), 1)

        def change_with_hash(approved):  # a rewrite that keeps the object agreeing with itself
            approved.data = draft(happened="something else")
            approved.sha256 = hashlib.sha256(approved.data).hexdigest()
        _, result = self.drive(data, b"send\n", after=change_with_hash)
        self.assertEqual(result, {"approved": True, "refusal": [2, "err.issue.send.changed"]})
        self.assertEqual(len(self.calls("issue create")), 1)

    def test_9_a_failed_search_is_one_line_on_the_screen(self):
        self.fixture("issue_list.exit", "1")
        state, found = send.search(self.env(), REPO, FP)
        self.assertEqual((state, found), ("failed", []))
        screen, result = self.drive(draft(), b"no\n", notes=send.notes(state, found))
        self.assertEqual(result, {"approved": False})
        self.assertEqual(screen.count(MESSAGES["issue.screen.failed"]), 1)
        self.assertLess(screen.index(END), screen.index(MESSAGES["issue.screen.failed"]))


class AccountTest(Base):
    def test_5_the_account_is_never_picked_silently(self):
        self.fixture("auth_status.out", json.dumps({"hosts": {"github.com": [
            {"active": True, "login": LOGIN, "state": "success"},
            {"active": False, "login": "other-example", "state": "success"}]}}))
        t = term.Term(env={}, out=io.StringIO(), err=io.StringIO())
        road = send.account(self.env(), None)
        self.assertEqual(road["road"], "refuse")
        self.assertIn("gh auth switch --user", t.text(road["why"], send="agentik issue send", **road["values"]))
        road = send.account(self.env(), "other-example")
        self.assertEqual(road["road"], "refuse")
        self.assertIn("gh auth switch --user other-example", t.text(road["why"], send="agentik issue send", **road["values"]))
        self.assertEqual(send.account(self.env(), LOGIN), {"road": "gh", "login": LOGIN})
        self.fixture("auth_status.out", json.dumps({"hosts": {"github.com": [
            {"active": True, "login": LOGIN, "state": "success"}]}}))
        self.assertEqual(send.account(self.env(), None), {"road": "gh", "login": LOGIN})
        before = len(self.calls())
        for name in ("GH_TOKEN", "GITHUB_TOKEN"):
            road = send.account(self.env(**{name: "made-up"}), None)
            self.assertEqual(road, {"road": "web", "why": "issue.send.web.token", "values": {"name": name}})
            self.assertEqual(len(t.text(road["why"], **road["values"]).splitlines()), 1)
        self.assertEqual(len(self.calls()), before)
        empty = os.path.join(self.home, "empty")
        os.mkdir(empty)
        self.assertEqual(send.account(self.env(PATH=empty), None)["why"], "issue.send.web.nogh")
        self.fixture("auth_status.out", json.dumps({"hosts": {}}))
        self.assertEqual(send.account(self.env(), None)["why"], "issue.send.web.noaccount")
        self.assertNotIn("token", json.dumps(self.calls()))


class CheckTest(Base):
    def test_6_check_names_a_line_and_a_kind_never_a_match(self):
        value = "/tmp/made-up-folder/run.log"
        data = draft(happened=value)
        got = send.check(data, None, PUBLIC, FakeForm(), fake_scrub(value))
        self.assertEqual(got, [(4, "path")])
        self.assertEqual(send.check(draft(), None, PUBLIC, FakeForm(), fake_scrub(value)), [])
        cases = {"form": send.check(data, None, PUBLIC, FakeForm(raises=True), fake_scrub(value)),
                 "drift": send.check(data, None, PUBLIC, FakeForm(drift=True), fake_scrub(value)),
                 "size": send.check(data, None, PUBLIC, FakeForm(), fake_scrub(value), ceiling=64),
                 "tool": send.check(draft(happened=value, tool="othertool"), None, PUBLIC,
                                    FakeForm(), fake_scrub(value))}
        self.assertEqual([k for _, k in cases["form"]], ["form"])
        self.assertEqual(cases["drift"], [(4, "path"), (8, "form")])
        self.assertIn("size", [k for _, k in cases["size"]])
        self.assertIn("tool", [k for _, k in cases["tool"]])
        for got in [send.check(data, None, PUBLIC, FakeForm(), fake_scrub(value))] + list(cases.values()):
            for line, kind in got:
                self.assertIsInstance(line, int)
                self.assertNotIn(value, kind)
                self.assertFalse(set(kind) - set("abcdefghijklmnopqrstuvwxyz_"), kind)
        self.assertEqual(send.repo_of(draft(), PUBLIC), REPO)
        self.assertIsNone(send.repo_of(draft(tool="othertool"), PUBLIC))


class SearchTest(Base):
    def test_9_the_search_reads_open_closed_and_failed(self):
        hit = {"number": 7, "title": "faketool doctor: the check failed", "url": URL}
        self.fixture("issue_list.out", json.dumps([dict(hit, state="OPEN")]))
        state, found = send.search(self.env(), REPO, FP)
        self.assertEqual((state, found[0]["url"]), ("open", URL))
        argv = self.calls("issue list")[0]["argv"]
        self.assertEqual(argv, ["issue", "list", "-R", "github.com/" + REPO, "-S", FP + " in:body",
                                "-s", "all", "--json", "number,title,state,url", "-L", "5"])
        self.fixture("issue_list.out", json.dumps([dict(hit, state="CLOSED")]))
        state, found = send.search(self.env(), REPO, FP)
        self.assertEqual((state, found[0]["url"]), ("closed", URL))
        self.assertEqual(send.notes(state, found), [("issue.screen.closed", {"url": URL})])
        self.fixture("issue_list.out", "[]")
        self.assertEqual(send.search(self.env(), REPO, FP), ("none", []))


class WebTest(Base):
    def test_10_the_links_and_nothing_opened(self):
        body = ("Happened: `%s`\n" % ("z" * 1000)).encode()
        search, new = send.web(b"faketool doctor: a title\n\n" + body, REPO, FP)
        self.assertEqual(search, "https://github.com/%s/issues?q=%s%%20in%%3Abody" % (REPO, FP))
        self.assertIn("title=faketool%20doctor%3A%20a%20title", new)
        self.assertIn("&body=Happened%3A%20%60zzz", new)
        self.assertLess(len(new.encode()), 6000)
        big = ("\u20ac" * 1365 + "\n").encode("utf-8")
        self.assertEqual(len(big), 4096)
        _, new = send.web(b"faketool doctor: a title\n\n" + big, REPO, FP)
        self.assertEqual(new, "https://github.com/%s/issues/new" % REPO)
        self.assertEqual(self.calls(), [])


def unseen_cases():
    """(name, characters, kind): each class of design/22 item 4(e), built at run time."""
    tags = "".join(chr(0xE0000 + ord(c)) for c in "made-up-host.example")
    return [("tags", tags, "format"), ("zero width space", chr(0x200B), "format"),
            ("zero width joiner", chr(0x200D), "format"), ("word joiner", chr(0x2060), "format"),
            ("right to left override", chr(0x202E), "format"), ("isolate", chr(0x2066), "format"),
            ("byte order mark", chr(0xFEFF), "format"), ("soft hyphen", chr(0xAD), "format"),
            ("line separator", chr(0x2028), "separator"),
            ("paragraph separator", chr(0x2029), "separator"),
            ("private use", chr(0xE000), "private"), ("private plane", chr(0xF0000), "private"),
            ("unassigned", chr(0x0378), "unassigned"), ("no-break space", chr(0xA0), "space"),
            ("ideographic space", chr(0x3000), "space"), ("escape", chr(0x1B), "control"),
            ("carriage return", chr(0x0D), "control"), ("variation selector", chr(0xFE0F), "blank"),
            ("hangul filler", chr(0x3164), "blank"), ("braille blank", chr(0x2800), "blank"),
            ("full-width letters", chr(0xFF4D) + chr(0xFF41), "nfkc")]


class UnseenTest(Base):
    """R1-F1: a character a terminal does not draw as itself is refused anywhere in the bytes:
    the title, a fixed line of the form and a free value, by `check` and by the screen."""

    def place(self, where, chars):
        data = draft()
        lines = data.decode("utf-8").split("\n")
        n = {"title": 1, "fixed": 6, "free": 4}[where]
        lines[n - 1] += chars
        return "\n".join(lines).encode("utf-8"), n

    def test_r1_f1_check_refuses_each_class_on_any_line(self):
        for name, chars, kind in unseen_cases():
            for where in ("title", "fixed", "free"):
                with self.subTest(name=name, where=where):
                    data, n = self.place(where, chars)
                    self.assertEqual(send.check(data, None, PUBLIC, FakeForm(), fake_scrub(None)),
                                     [(n, kind)])
                    with self.assertRaises(send.Refusal) as cm:
                        send._shown_lines(data)
                    self.assertEqual((cm.exception.code, cm.exception.mid, cm.exception.values),
                                     (1, "err.issue.send.line", {"line": n, "kind": kind}))
        self.assertEqual(send.check(draft(happened="caf\u00e9 \u20ac 12"), None, PUBLIC, FakeForm(),
                                    fake_scrub(None)), [])

    def test_r1_f1_send_refuses_and_files_nothing(self):
        for name, chars, kind in unseen_cases():
            if kind in ("control", "nfkc"):
                continue
            with self.subTest(name=name):
                data, n = self.place("free", chars)
                screen, result = self.drive(data, b"send\n")
                self.assertEqual(result, {"refusal": [1, "err.issue.send.line",
                                                      {"line": n, "kind": kind}]})
                self.assertNotIn(HEAD, screen)
        self.assertEqual(self.calls("issue create"), [])


class QuietTest(Base):
    """R1-F2 and R2-F1: the answer to a question is refused, exit 2, whenever the wait after the
    question is drawn drops any byte, so no stream that began before a question answers it; a
    line right after the word is a refusal too. A person who answers once the question shows,
    on quiet input, sends."""

    def trickle(self, every, secs=12.0):
        return [(i * every, b"send\n") for i in range(int(secs / every))]

    def test_r2_f1_a_blind_trickle_never_answers(self):
        for every in (0.35, 0.5, 1.0):
            for name, data in (("short", draft()), ("paged", draft(lines=44, pad_to=4107))):
                with self.subTest(every=every, draft=name):
                    screen, result = self.drive(data, b"", rows=24, cols=80,
                                                blind=self.trickle(every))
                    self.assertEqual(result, {"refusal": EARLY}, screen[-300:])
        self.assertEqual(self.calls("issue create"), [])

    def test_r2_f1_a_flood_that_stops_then_one_line_never_answers(self):
        flood = [(i * 0.005, b"send\n") for i in range(520)] + [(3.3, b"send\n")]
        _, result = self.drive(draft(), b"", blind=flood)
        self.assertEqual(result, {"refusal": EARLY})
        _, result = self.drive(draft(), b"", blind=[(i * 0.005, b"send\n") for i in range(720)])
        self.assertEqual(result, {"refusal": EARLY})
        self.assertEqual(self.calls("issue create"), [])

    def test_r2_f1_a_byte_in_the_wait_refuses_whatever_the_clock(self):
        """`_settle` on a pipe, no clock to race: a byte waiting when the question is drawn
        refuses; no byte is quiet; an end of input keeps the draft."""
        for pending in (b"send\n", b"\n", b"x"):
            with self.subTest(pending=pending):
                r, w = os.pipe()
                self.addCleanup(os.close, r)
                self.addCleanup(os.close, w)
                os.write(w, pending)
                with self.assertRaises(send.Refusal) as cm:
                    send._settle(r)
                self.assertEqual([cm.exception.code, cm.exception.mid], EARLY)
        r, w = os.pipe()
        self.addCleanup(os.close, r)
        self.assertTrue(send._settle(r))
        os.close(w)
        self.assertFalse(send._settle(r))
        text = MESSAGES.get("err.issue.send.early", "")
        self.assertEqual(len(text.splitlines()), 1)
        self.assertIn("again", text)

    def test_r1_f2_a_word_typed_ahead_is_refused(self):
        _, result = self.drive(draft(), [(0, b"send\n")])
        self.assertEqual(result, {"refusal": EARLY})
        _, result = self.drive(draft(), b"send\n", ahead=b"send\n")
        self.assertEqual(result, {"refusal": EARLY})
        self.assertEqual(self.calls("issue create"), [])

    def test_r2_f1_a_person_who_answers_once_it_shows_sends_once(self):
        _, result = self.drive(draft(), [(send.QUIET + 1.0, b"send\n")])
        self.assertEqual(result, {"approved": True, "url": URL})
        _, result = self.drive(draft(lines=44, pad_to=4107), [(send.QUIET + 1.0, b"send\n")],
                               rows=24, cols=80)
        self.assertEqual(result, {"approved": True, "url": URL})
        self.assertEqual(len(self.calls("issue create")), 2)

    def test_r1_f2_a_line_on_after_the_word_is_a_flood(self):
        _, result = self.drive(draft(), [(PAUSE, b"send\n"), (0.05, b"send\n")])
        self.assertEqual(result, {"refusal": [2, "err.issue.send.flood"]})
        self.assertEqual(self.calls("issue create"), [])


class SizeTest(Base):
    """R2-F2: a page counts its question's own rows and the cursor's against the screen, the
    size is read again at each page, and a terminal with no room for one row of the draft beside
    the question is refused, exit 2, before anything of the draft is drawn."""
    TALL = " ".join("w%03d" % n for n in range(100))

    def test_r2_f2_no_page_is_taller_than_a_narrow_screen(self):
        for name, data in (("tall", draft(happened=self.TALL)), ("short", draft())):
            with self.subTest(draft=name):
                screen, result = self.drive(data, b"no\n", rows=10, cols=20)
                self.assertEqual(result, {"approved": False}, screen[-300:])
                tops = self.tops(screen, 20)
                self.assertTrue(tops and max(tops) <= 10, tops)
                self.assertEqual(self.shown(screen).encode("utf-8"), data)

    def test_r2_f2_no_room_for_a_row_is_refused_before_it_draws(self):
        for rows, cols in ((1, 80), (2, 80), (12, 1), (12, 2)):
            with self.subTest(rows=rows, cols=cols):
                screen, result = self.drive(draft(), b"send\n", rows=rows, cols=cols)
                self.assertEqual(result, {"refusal": SMALL}, screen[-300:])
                self.assertNotIn(HEAD, screen)
        self.assertEqual(self.calls("issue create"), [])
        self.assertEqual(len(MESSAGES.get("err.issue.send.small", "").splitlines()), 1)

    def test_r2_f2_the_size_is_read_again_at_each_page(self):
        data = draft(happened=" ".join("w%03d" % n for n in range(300)))
        screen, result = self.drive(data, b"no\n", rows=24, cols=80, resize=(10, 80))
        self.assertEqual(result, {"approved": False}, screen[-300:])
        tops = self.tops(screen, 80)
        self.assertLessEqual(tops[0], 24)
        self.assertTrue(len(tops) > 2 and max(tops[1:]) <= 10, tops)
        self.assertEqual(self.shown(screen).encode("utf-8"), data)


class ApprovalTest(Base):
    """R1-F4: an approval is made by `approve` alone and is good once."""

    def test_r1_f4_an_approval_built_by_hand_files_nothing(self):
        data = draft()
        try:
            forged = send.Approved(data, REPO, LOGIN)
        except TypeError:  # the shape before this row's fix
            forged = send.Approved(data, REPO)
        with self.assertRaises(send.Refusal) as cm:
            send._file(forged, REPO, self.env())
        self.assertEqual((cm.exception.code, cm.exception.mid), (2, "err.issue.send.unapproved"))
        self.assertEqual(self.calls("issue create"), [])
        self.assertEqual(MESSAGES["err.issue.send.unapproved"],
                         "This issue has no approval left, since an approval is used once, so "
                         "nothing was sent. Run {send} again to see it.")

    def test_r1_f4_a_rewrite_that_keeps_the_hash_files_nothing(self):
        other = draft(happened="something no one saw")

        def rewrite(approved):
            approved.data, approved.sha256 = other, hashlib.sha256(other).hexdigest()
        _, result = self.drive(draft(), b"send\n", after=rewrite)
        self.assertEqual(result, {"approved": True, "refusal": [2, "err.issue.send.changed"]})
        self.assertEqual(self.calls("issue create"), [])

    def test_r1_f4_an_approval_pointed_at_another_repo_files_nothing(self):
        def retarget(approved):
            approved.repo = "example-owner/elsewhere"
        _, result = self.drive(draft(), b"send\n", after=retarget,
                               file_repo="example-owner/elsewhere")
        self.assertEqual(result, {"approved": True, "refusal": [2, "err.issue.send.changed"]})
        self.assertEqual(self.calls("issue create"), [])

    def test_r1_f4_an_approval_is_good_once(self):
        env = self.env()

        def first(approved):
            self.assertEqual(send._file(approved, REPO, env), URL)
        _, result = self.drive(draft(), b"send\n", env=env, after=first)
        self.assertEqual(result, {"approved": True, "refusal": [2, "err.issue.send.unapproved"]})
        self.assertEqual(len(self.calls("issue create")), 1)


class FileAccountTest(Base):
    """R1-F5: `_file` reads the active account again just before the create and files only as
    the login the screen showed; a token variable refuses, and the child's environment holds
    none."""

    def test_r1_f5_an_account_switched_after_the_screen_files_nothing(self):
        def switch(approved):
            self.fixture("auth_status.out", json.dumps({"hosts": {"github.com": [
                {"active": False, "login": LOGIN, "state": "success"},
                {"active": True, "login": "other-example", "state": "success"}]}}))
        _, result = self.drive(draft(), b"send\n", after=switch)
        self.assertEqual(result, {"approved": True,
                                  "refusal": [2, "err.issue.send.switched", {"login": LOGIN}]})

        def unread(approved):
            self.fixture("auth_status.out", "{}")
        _, result = self.drive(draft(), b"send\n", after=unread)
        self.assertEqual(result["refusal"][:2], [2, "err.issue.send.switched"])
        self.assertEqual(self.calls("issue create"), [])

    def test_r1_f5_a_token_variable_files_nothing(self):
        for name in ("GH_TOKEN", "GITHUB_TOKEN"):
            for value in ("made-up-" + "v" * 8, ""):
                with self.subTest(name=name, value=value):
                    _, result = self.drive(draft(), b"send\n", env=self.env(**{name: value}))
                    self.assertEqual(result, {"approved": True, "refusal": [
                        2, "err.issue.send.token", {"name": name}]})
                    road = send.account(self.env(**{name: value}), None)
                    self.assertEqual(road["road"], "web")
        self.assertEqual(self.calls("issue create"), [])

    def test_r1_f5_the_create_holds_no_token_variable(self):
        name = "GH_" + "ENTERPRISE_TOKEN"
        _, result = self.drive(draft(), b"send\n", env=self.env(**{name: "made-up"}))
        self.assertEqual(result, {"approved": True, "url": URL})
        created = self.calls("issue create")
        self.assertEqual([c["vars"] for c in created], [[]])
        self.assertEqual(self.calls("auth status")[-1]["vars"], [])


class DoorTest(unittest.TestCase):
    def test_11_one_create_in_the_package(self):
        counts = {}
        for path in sorted(PACKAGE.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                n = sum("issue create" in line for line in path.read_text().splitlines())
                if n:
                    counts[path.name] = n
        self.assertEqual(counts, {"send.py": 1})

    STARTERS = {"Popen", "run", "call", "check_call", "check_output", "getoutput",
                "getstatusoutput", "system", "popen", "startfile", "posix_spawn", "posix_spawnp",
                "create_subprocess_exec", "create_subprocess_shell", "_run"} | {
                    "exec" + t for t in ("l", "le", "lp", "lpe", "v", "ve", "vp", "vpe")} | {
                    "spawn" + t for t in ("l", "le", "lp", "lpe", "v", "ve", "vp", "vpe")}

    @staticmethod
    def words(node):
        """The words of an argv as written: string constants split, a list's items, a sum's
        sides, `"a b".split()`; `?` for anything else."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value.split()
        if isinstance(node, (ast.List, ast.Tuple)):
            return [w for item in node.elts for w in DoorTest.words(item)]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return DoorTest.words(node.left) + DoorTest.words(node.right)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "split" and not node.args):
            return DoorTest.words(node.func.value)
        return ["?"]

    def starts(self):
        """(module, function, callee, argv words) of each call in the package that starts a
        process, by the callee's name however it is reached."""
        found = []
        for path in sorted(PACKAGE.rglob("*.py")):
            tree = ast.parse(path.read_text())
            for func in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.Module))]:
                inner = [n for n in ast.walk(func) if isinstance(n, ast.FunctionDef) and n is not func]
                skip = {id(m) for f in inner for m in ast.walk(f)}
                for node in ast.walk(func):
                    if id(node) in skip or not isinstance(node, ast.Call):
                        continue
                    callee = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(
                        node.func, "id", "?")
                    if callee in self.STARTERS:
                        argv = self.words(node.args[0]) if node.args else ["?"]
                        found.append((path.name, getattr(func, "name", "<module>"), callee, argv))
        return found

    def test_11_one_writing_call_in_the_package(self):
        starts = [s for s in self.starts() if s[0] == "send.py"]
        self.assertEqual([(f, c) for _, f, c, _ in starts if c != "_run"], [("_run", "Popen")])
        runs = {(f, " ".join(argv[:3])) for _, f, c, argv in starts if c == "_run"}
        self.assertEqual(runs, {("accounts", "gh auth status"), ("search", "gh issue list"),
                                ("_claude_above", "ps -A -o"), ("_file", "gh issue create")})
        self.assertEqual(len([s for s in starts if s[2] == "_run"]), 4)
        for _, func, callee, argv in starts:  # each call of the door's runner reads as written
            if callee == "_run":
                self.assertNotIn("?", argv[:3], func)
        writing = [s for s in starts if "create" in s[3]]
        self.assertEqual([(m, f) for m, f, _, _ in writing], [("send.py", "_file")])
        for module, func, callee, argv in self.starts():  # the package's other starters
            if module != "send.py":
                self.assertNotIn("gh", argv, (module, func))
        for path in sorted(PACKAGE.rglob("*.py")):  # gh's name is spelled in send.py alone,
            if path.name == "send.py":  # and as a word scrub keeps (`scrub.PROGRAMS`), never run
                continue
            tree = ast.parse(path.read_text())
            kept = set()
            if path.name == "scrub.py":
                kept = self.kept_words(tree)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and (
                        id(node) not in kept):
                    self.assertNotIn("gh", re.findall(r"[\w-]+", node.value), path.name)

    def kept_words(self, tree):
        """The string elements of scrub's `PROGRAMS = (...)`, a list of words a scrub leaves as
        they are; held to never reach a process starter's arguments in that module."""
        kept = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and [getattr(t, "id", None) for t in node.targets] == [
                    "PROGRAMS"] and isinstance(node.value, ast.Tuple):
                kept |= {id(e) for e in node.value.elts if isinstance(e, ast.Constant)}
            if isinstance(node, ast.Call):
                callee = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(
                    node.func, "id", "?")
                if callee in self.STARTERS:
                    names = {n.id for a in node.args + [k.value for k in node.keywords]
                             for n in ast.walk(a) if isinstance(n, ast.Name)}
                    self.assertNotIn("PROGRAMS", names, "scrub.py starts a process with PROGRAMS")
        return kept

    def test_join_gh_is_a_word_scrub_keeps_and_starts_nothing(self):
        """The join with rp2's scrub: `gh` is in `scrub.PROGRAMS`, a word left as it is, and that
        list reaches no starter; a `gh` anywhere else in scrub.py is still refused by line 11."""
        tree = ast.parse((PACKAGE / "scrub.py").read_text())
        kept = self.kept_words(tree)
        words = [n.value for n in ast.walk(tree) if id(n) in kept]
        self.assertIn("gh", words)
        bad = ast.parse('PROGRAMS = ("gh",)\nsubprocess.run(list(PROGRAMS))\n')
        with self.assertRaises(AssertionError):
            self.kept_words(bad)
        loose = ast.parse('PROGRAMS = ("git",)\nCMD = "gh issue create"\n')
        kept = self.kept_words(loose)
        loose_gh = [n for n in ast.walk(loose) if isinstance(n, ast.Constant) and n.value ==
                    "gh issue create"]
        self.assertTrue(loose_gh and id(loose_gh[0]) not in kept)

    def test_r1_r6_imports_and_no_way_round(self):
        self.assertTrue(SEND.exists())
        source = SEND.read_text()
        mods = set(re.findall(r"^(?:import|from) ([\w.]+)", source, re.M))
        self.assertFalse(mods & {"pty", "termios", "urllib", "tty"}, mods)
        self.assertFalse(re.search(r"\b(scrub|form|gather)\b", " ".join(mods)), mods)
        for word in ("os.environ", "getenv", "--yes", "yes=", "AGENTIK_"):
            self.assertNotIn(word, source)
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        tools = [p["name"] for p in market["plugins"] if p["name"] != "suite"]
        pattern = re.compile(r"\b(?:%s)\b" % "|".join(map(re.escape, tools)), re.I)
        section = (PACKAGE / "messages.md").read_text().split("\n## Issue\n", 1)
        self.assertEqual(len(section), 2)
        for name, text in (("send.py", source), ("this file", Path(__file__).read_text()),
                           ("## Issue", section[1])):
            hit = pattern.search(text)
            self.assertIsNone(hit, "%s names %s" % (name, hit and hit.group(0)))

    def test_r8_every_id_is_in_the_last_section(self):
        source = SEND.read_text()
        used = set(re.findall(r'"((?:err\.)?issue\.[a-z_.]+)"', source))
        self.assertTrue(used)
        text = (PACKAGE / "messages.md").read_text()
        head, section = text.split("\n## Issue\n", 1)
        self.assertNotIn("\n## ", section)
        ids = {m.group(1) for m in map(catalogue.ITEM.match, section.splitlines()) if m}
        self.assertEqual(used - ids, set())
        self.assertFalse(re.search(r"`(?:err\.)?issue\.", head))
        self.assertTrue(all(i.startswith(("issue.", "err.issue.", "hint.issue."))  # rp6 joins the verb's
                            for i in ids), ids)


class JoinTest(unittest.TestCase):
    """Phase 2: the real scrub, gather and form, as landed, into `check`, `marker` and `repo_of`.
    The machine is made by hand; no process is started and no home is read."""

    @classmethod
    def setUpClass(cls):
        from agentik_suite import form, gather, scrub
        cls.form, cls.gather, cls.scrub = form, gather, scrub
        cls.public = json.loads((LIB / "public.json").read_text())
        cls.m = scrub.build(cls.public, home="/home/zqvuser", logins=("zqvlogin",),
                            hosts=("zqvhost",))

    def facts(self, tool, free, rows=1):
        return {
            "schema": "agentik.issue-facts/1", "tool": tool,
            "versions": [{"name": tool, "plugin": "1.2.3", "commit": None, "launcher": None}],
            "system": {"os": "Darwin", "release": "27.0.0", "arch": "arm64", "python": "3.9.6",
                       "claude": "2.1.3", "where": "at a terminal"},
            "checks": {"read": True, "rows": [{"tool": tool, "status": "fail", "name": free,
                                                "detail": free}] * rows,
                       "failed": rows, "warned": 0, "passed": 2},
            "plugins": {"named": [{"name": tool, "version": "1.2.3"}], "others": 0},
            "output": {"ran": free, "exit": 2, "lines": [free, free]},
            "words": {"expected": free}}

    def made(self, tool, free, bound=True):
        """The bytes a verb would make: scrub each free value, bound, draft, fit, build."""
        g, f = self.gather, self.form
        facts = g.map_free(self.facts(tool, free), lambda v: self.scrub.scrub(v, self.m)[0])
        fp = f.fingerprint(tool, "doctor fails")
        fields, went = f.fit(f.draft(g.bound(facts) if bound else facts, tool, "doctor fails",
                                     "doctor fails", fp))
        return f.build(fields), fp, went

    def check(self, data):
        return send.check(data, self.m, self.public, self.form, self.scrub)

    def test_join_every_public_tool_reads_back_to_its_repo(self):
        self.assertEqual(send.CEILING, self.form.CEILING)
        for tool, repo in sorted(self.public["tools"].items()):
            with self.subTest(tool=tool):
                data, fp, went = self.made(tool, "the doctor said no")
                self.assertEqual((went, self.check(data)), ([], []))
                self.assertEqual(send.marker(data)[:3], (tool, "1.2.3", fp))
                self.assertEqual(send.repo_of(data, self.public), repo)

    def test_join_detect_kinds_reach_the_line_message_as_named(self):
        tool = sorted(self.public["tools"])[0]
        named = set(self.scrub.KINDS) | {"control", "encoded"}
        self.assertTrue(all(send.KIND.match(k) for k in named), named)
        raw = self.form.build(self.form.draft(
            self.facts(tool, "token=ghp_" + "a" * 36), tool, "doctor fails", "doctor fails",
            self.form.fingerprint(tool, "doctor fails")))
        kinds = {k for _, k in self.check(raw)}
        self.assertIn("secret", kinds)
        self.assertLessEqual(kinds, named)

    def test_join_a_secret_bound_away_leaves_a_line_refused_as_secret(self):
        """rp2's phase 2: a bound that drops a whole <secret> can leave `Authorization: Bearer`
        bare, which reads as a secret again. The refusal fails safe and stays."""
        tool = sorted(self.public["tools"])[0]
        lead = " Authorization: Bearer "
        whole, _, _ = self.made(tool, lead.strip() + " " + "Z" * 24)
        self.assertEqual(self.check(whole), [])
        cut, _, _ = self.made(tool, "x" * (self.gather.RAN - len(lead) - 3) + lead + "Z" * 24)
        found = self.check(cut)
        self.assertTrue(found and {k for _, k in found} == {"secret"}, found)

    def test_join_a_form_still_over_its_ceiling_is_refused_by_size(self):
        tool = sorted(self.public["tools"])[0]
        f = self.form
        fields, went = f.fit(f.draft(self.facts(tool, "w" * 300, rows=20), tool, "doctor fails",
                                     "doctor fails", f.fingerprint(tool, "doctor fails")))
        self.assertEqual(went[-1][0], "over")
        data = f.build(fields)
        self.assertEqual(len(data), went[-1][1])
        self.assertIn("size", {k for _, k in self.check(data)})


if __name__ == "__main__":
    unittest.main()
