"""Packet rp6-verb: `issue`, the verb that joins scrub, gather, form and send.

Each test runs in a temp HOME with a PATH of a stub folder, /usr/bin and /bin: the stub `claude`
of the suite's tests, a stub `gh` that records its argv and stdin and answers from a fixture, a
stub `ps` with no `claude` in it, and a stub tool whose doctor fails as design/22's example does.
The tool is read from public.json at run time. The typed word goes through `pty.fork`. Nothing
here reaches the network, runs the real `gh` or `claude`, or reads the real home.
"""
import fcntl
import json
import os
import pty
import re
import select
import shutil
import struct
import subprocess
import sys
import termios
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LAUNCHER, LIB, PLUGIN, ROOT, Home  # noqa: E402

sys.path.insert(0, str(LIB))
from agentik_suite import form, gather, scrub  # noqa: E402

PUBLIC = json.loads((LIB / "public.json").read_text())
NAMES = sorted(t for t in PUBLIC["tools"] if t != "suite")  # the fixture's {tool-N}, filled here
TOOL = NAMES[0]
REPO = PUBLIC["tools"][TOOL]
FIXTURE = ROOT / "tests" / "fixtures" / "rp6-example.md"
SKILL = PLUGIN / "skills" / "issue" / "SKILL.md"
URL = "https://github.com/%s/issues/41" % REPO
LOGIN = "sam-example"
EXPECTED = "doctor passes in a fresh clone of billing-api, before any session"
FAILING = "doctor: failing: resolved, meter"
OUTPUT = "no profile resolved for /Volumes/work/acme\n%s\n" % FAILING
GH = r'''#!/usr/bin/python3 -I
import json, os, sys
d = %r
args = sys.argv[1:]
data = sys.stdin.buffer.read().decode("utf-8") if args[:2] == ["issue", "create"] else ""
with open(os.path.join(d, "calls.jsonl"), "a") as fh:
    fh.write(json.dumps({"argv": args, "stdin": data}) + "\n")
key = "_".join(args[:2])
if os.path.exists(os.path.join(d, key + ".out")):
    with open(os.path.join(d, key + ".out")) as fh:
        sys.stdout.write(fh.read())
'''
PS = '#!/bin/sh\necho "    1     0 /sbin/launchd"\necho "$PPID     1 /usr/bin/python3"\n'
DOCTOR = r'''#!/usr/bin/python3 -I
import json, sys
if sys.argv[1:] == ["doctor", "--json"]:
    print(json.dumps({"schema": "agentik.doctor/1", "ok": True, "checks": [
        {"name": "doctor", "status": "fail", "detail": %r, "remedy": None}]}))
    sys.exit(1)
sys.exit(2)
''' % FAILING


def system_line():
    u = os.uname()
    release = re.match(r"[0-9.]*", u.release).group() or "unreadable"
    # The launcher runs the command under /usr/bin/python3 (its env names no AGENTIK_PYTHON), so
    # the draft's version is that interpreter's, not the one running these tests.
    python = subprocess.run(["/usr/bin/python3", "-I", "-c", "import sys; print('%d.%d.%d' % sys.version_info[:3])"],
                            capture_output=True, text=True, timeout=30).stdout.strip()
    return "%s %s %s, Python %s" % (u.sysname, release, u.machine, python)


class IssueHome(Home):
    def setUp(self):
        Home.setUp(self)
        self.ghdir = os.path.join(self.home, "gh")
        os.mkdir(self.ghdir)
        self.stub("gh", GH % self.ghdir)
        self.stub("ps", PS)
        self.stub("agentik-" + TOOL, DOCTOR)
        self.plugin_files(os.path.join(self.home, ".claude"), {TOOL: "2.0.0-alpha.101", "suite": "0.6.0"},
                          whole=False)
        self.gh_answer("auth_status", json.dumps({"hosts": {"github.com": [
            {"active": True, "host": "github.com", "login": LOGIN, "state": "success"}]}}))
        self.gh_answer("issue_list", "[]")
        self.gh_answer("issue_create", URL + "\n")
        self.work = os.path.join(self.home, "work")
        os.mkdir(self.work)
        with open(os.path.join(self.work, "err.txt"), "w") as fh:
            fh.write(OUTPUT)
        self.drafts = os.path.join(self.home, ".local", "state", "agentik-suite", "issues")

    def gh_answer(self, key, text):
        with open(os.path.join(self.ghdir, key + ".out"), "w") as fh:
            fh.write(text)

    def gh_calls(self, verb=None):
        try:
            with open(os.path.join(self.ghdir, "calls.jsonl")) as fh:
                calls = [json.loads(l) for l in fh]
        except FileNotFoundError:
            return []
        return [c for c in calls if verb is None or " ".join(c["argv"]).startswith(verb)]

    def issue(self, *args, cwd=None, stdin=None, **more):
        p = subprocess.run([str(LAUNCHER), "issue", *args], capture_output=True, text=True,
                           env=self.env(**more), timeout=90, cwd=cwd or self.work,
                           input=stdin, start_new_session=True)
        return p.returncode, p.stdout, p.stderr

    def new(self, *more, **env):
        return self.issue("new", TOOL, "--ran", "agentik %s doctor" % TOOL, "--exit", "2",
                          "--output", "err.txt", "--expected", EXPECTED, *more, **env)

    def draft_dir(self):
        names = sorted(os.listdir(self.drafts),
                       key=lambda n: (n[:16], os.lstat(os.path.join(self.drafts, n)).st_ctime_ns))
        return os.path.join(self.drafts, names[-1])

    def draft(self):
        with open(os.path.join(self.draft_dir(), "issue.md"), "rb") as fh:
            return fh.read()

    def put_draft(self, data):
        with open(os.path.join(self.draft_dir(), "issue.md"), "wb") as fh:
            fh.write(data)

    def reads_back(self, data):
        return form.build(form.parse(data, PUBLIC["tools"])) == data

    def pty_send(self, *args, word=b"send\n", **more):
        """`issue send` in a child of pty.fork, its stdout a pipe; the word typed once the question
        shows. (exit, screen, stdout)."""
        r, w = os.pipe()
        pid, fd = pty.fork()
        if pid == 0:  # the child
            try:
                os.close(r)
                os.dup2(w, 1)
                fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", 200, 200, 0, 0))
                os.chdir(self.work)
                os.execve(str(LAUNCHER), [str(LAUNCHER), "issue", "send", *args], self.env(**more))
            finally:
                os._exit(127)
        os.close(w)
        screen, typed, end = b"", False, time.time() + 60
        while time.time() < end:
            ready, _, _ = select.select([fd], [], [], 0.2)
            if ready:
                try:
                    data = os.read(fd, 65536)
                except OSError:
                    break
                if not data:
                    break
                screen += data
                continue
            if not typed and b"Type send" in screen:
                time.sleep(0.6)
                os.write(fd, word)
                typed = True
        os.close(fd)
        _, status = os.waitpid(pid, 0)
        with os.fdopen(r, "rb") as fh:
            out = fh.read()
        return os.waitstatus_to_exitcode(status), screen.decode("utf-8", "replace"), out.decode()


class ReadTest(IssueHome):
    def test_1_bare_issue_in_an_empty_home(self):
        before = self.snapshot()
        code, out, err = self.issue()
        self.assertEqual(code, 0, err)
        self.assertEqual(len(out.splitlines()), 1, out)
        self.assertIn("No draft", out)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.issue("--check")[0], 0)

    def test_12_help_json_and_a_tool_outside_the_table(self):
        code, out, err = self.run_cli("help")
        self.assertEqual(code, 0, err)
        self.assertIn("issue", out)
        code, out, err = self.issue("--help")
        self.assertEqual(code, 0, err)
        self.assertIn("usage:", out)
        self.assertEqual(self.issue("new", "nosuchtool")[0], 2)
        code, out, err = self.issue("strke")
        self.assertEqual(code, 2)
        self.assertIn("strike", err)  # the nearest word is named
        code, out, err = self.new("--json")
        self.assertEqual(code, 0, err)
        obj = json.loads(out)
        self.assertEqual(set(obj), {"schema", "ok", "id", "path", "tool", "repo", "size", "counts",
                                    "unsure", "went"})
        self.assertEqual((obj["schema"], obj["tool"], obj["repo"]), ("agentik.issue/1", TOOL, REPO))


class NewTest(IssueHome):
    def expected_bytes(self):
        text = FIXTURE.read_text().replace("{system}", system_line())
        for n, name in enumerate(NAMES):
            text = text.replace("{tool-%d}" % n, name)
        return text.encode()

    def test_2_the_designs_example(self):
        code, out, err = self.new()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.draft(), self.expected_bytes())
        lines = self.draft().decode().split("\n")
        n = [i for i, l in enumerate(lines, 1) if "<path-1>" in l][0]
        self.assertIn("line %d" % n, out + err)
        self.assertEqual(oct(os.stat(self.draft_dir()).st_mode & 0o777), "0o700")
        meta = json.loads(open(os.path.join(self.draft_dir(), "draft.json")).read())
        self.assertEqual(meta["repo"], REPO)
        code, out, err = self.issue("--check")
        self.assertEqual(code, 1)
        self.assertEqual(len(out.splitlines()), 1, out)
        code, out, err = self.issue()
        self.assertEqual(code, 0, err)
        self.assertIn("unsent", out)

    def test_3_piped_the_lines_are_the_files_bytes(self):
        code, out, err = self.new()
        self.assertEqual(code, 0, err)
        data = self.draft().decode()
        self.assertIn(data, out)
        self.assertNotIn("\x1b", out + err)

    def test_4_strike(self):
        self.new()
        before = self.draft()
        code, out, err = self.issue("strike", "billing-api")
        self.assertEqual(code, 0, err)
        self.assertIn("Struck 1 word in 1 place: <struck-1>.", out)
        after = self.draft()
        self.assertEqual(len(after), len(before) - 1)
        self.assertTrue(self.reads_back(after))
        for word in ("details", "1"):
            code, out, err = self.issue("strike", word)
            self.assertIn("0 places", out, word)
            self.assertEqual(self.draft(), after)

    def test_5_drop(self):
        self.new()
        code, out, err = self.issue("drop", "plugins", "output")
        self.assertEqual(code, 0, err)
        data = self.draft()
        self.assertNotIn(b"Plugins: ", data)
        self.assertNotIn(b"Last lines:", data)
        self.assertNotIn(b"**Ran:**", data)
        self.assertTrue(self.reads_back(data))
        self.assertEqual(self.issue("drop", "nothing")[0], 2)
        self.assertEqual(self.draft(), data)

    def test_10_reword(self):
        self.new()
        before = self.draft()
        path = os.path.join(self.home, "render.txt")
        with open(path, "w") as fh:
            fh.write("Happened: %s\nExpected: doctor passes in a fresh clone of Zorblat\n" % FAILING)
        code, out, err = self.issue("reword", path)
        self.assertEqual(code, 1)
        self.assertEqual(self.draft(), before)
        with open(path, "w") as fh:
            fh.write("Happened: %s, every time\nExpected: doctor should pass in a fresh clone of "
                     "billing-api, before any session\n" % FAILING)
        code, out, err = self.issue("reword", path)
        self.assertEqual(code, 0, err)
        fields = form.parse(self.draft(), PUBLIC["tools"])
        self.assertEqual(fields["happened"], "%s, every time" % FAILING)
        self.assertIn("should pass", fields["expected"])
        self.assertIn("should", out + err)
        self.assertIn("every", out + err)

    def test_11_a_marker_leaves_no_trace(self):
        mark = "zq" + "vmarkr"
        work = os.path.join(self.home, "proj-" + mark)
        os.mkdir(work)
        subprocess.run(["git", "init", "-q", work], check=True, env=self.env())
        with open(os.path.join(work, "err.txt"), "w") as fh:
            fh.write("reading /opt/%s/conf failed for %s\nvalue %s-%s seen\n%s\n"
                     % (mark, os.path.join(work, "x"), "tok", mark + "secretvalue", FAILING))
        code, out, err = self.issue("new", TOOL, "--ran", "agentik %s doctor" % TOOL, "--exit", "2",
                                    "--output", "err.txt", "--expected", "works in proj-" + mark,
                                    cwd=work, MADE_UP_TOKEN="tok-" + mark + "secretvalue")
        self.assertEqual(code, 0, err)
        for text in (out, err, self.draft().decode(),
                     open(os.path.join(self.draft_dir(), "draft.json")).read()):
            self.assertNotIn(mark, text)

    def test_a1_a_bound_value_is_checked_again(self):
        m = scrub.machine(self.env(), self.work, PUBLIC)
        token = "Zx9" * 12
        base = "Authorization: Bearer " + token
        at = scrub.scrub(base, m)[0].index("<")
        for flag, cap in (("--ran", gather.RAN), ("--expected", gather.EXPECTED),
                          ("--output", gather.LINE)):
            pad = ("ab " * cap)[:cap - at - 4]
            value = pad + base
            args = ["new", TOOL, "--exit", "2"]
            if flag == "--output":
                with open(os.path.join(self.work, "long.txt"), "w") as fh:
                    fh.write(value + "\n")
                args += ["--output", "long.txt"]
            else:
                args += [flag, value]
            code, out, err = self.issue(*args)
            self.assertEqual(code, 0, err)
            self.assertNotIn(token, self.draft().decode())
            code, out, err = self.issue("send", "--dry-run")
            self.assertEqual(code, 2, (flag, err))  # past the check: no terminal to show it on
            self.assertNotIn("fails the", err, flag)
            self.issue("discard")


class SendTest(IssueHome):
    def test_6_the_last_check_refuses(self):
        self.new()
        self.put_draft(b"Some prose, not the form at all.\n")
        code, out, err = self.issue("send", "--dry-run")
        self.assertEqual(code, 1)
        self.assertIn("form", err)
        self.new()
        data = self.draft().decode()
        raw = os.path.join(self.home, "secret-notes.txt")
        data = data.replace("no profile resolved for <path-1>", "no profile resolved for " + raw)
        self.put_draft(data.encode())
        code, out, err = self.issue("send", "--dry-run")
        self.assertEqual(code, 1)
        n = [i for i, l in enumerate(data.split("\n"), 1) if raw in l][0]
        self.assertIn("line %d" % n, err)
        self.assertIn("path", err)
        self.assertNotIn(self.home, out + err)
        self.assertNotIn("secret-notes", out + err)

    def test_7_send_typed_in_a_pty(self):
        self.new()
        data = self.draft()
        code, screen, out = self.pty_send()
        self.assertEqual(code, 0, screen)
        self.assertEqual(len(self.gh_calls("issue list")), 1)
        made = self.gh_calls("issue create")
        self.assertEqual(len(made), 1)
        argv = made[0]["argv"]
        title = argv[argv.index("-t") + 1]
        self.assertEqual((title + "\n\n" + made[0]["stdin"]).encode(), data)
        self.assertEqual(out, URL + "\n")
        sent = json.loads(open(os.path.join(self.draft_dir(), "sent.json")).read())
        self.assertEqual(sent["url"], URL)
        before = len(self.gh_calls())
        code, out, err = self.issue("send")
        self.assertEqual(code, 1)
        self.assertIn(URL, out + err)
        self.assertEqual(len(self.gh_calls()), before)

    def test_8_no_way_round_the_typed_word(self):
        self.new()
        code, out, err = self.issue("send", "--yes")
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())
        self.assertEqual(self.gh_calls(), [])
        self.assertEqual(self.issue("send", stdin="send\n")[0], 2)
        self.assertEqual(self.gh_calls("issue create"), [])
        code, screen, out = self.pty_send(CLAUDECODE="1")
        self.assertEqual(code, 2, screen)
        self.assertEqual(self.gh_calls("issue create"), [])
        self.gh_answer("issue_list", json.dumps([{"number": 7, "title": "x", "state": "OPEN",
                                                   "url": "https://github.com/%s/issues/7" % REPO}]))
        code, out, err = self.issue("send")
        self.assertEqual(code, 1)
        self.assertIn("/issues/7", err)
        self.assertIn("--not-a-duplicate", err)
        code, screen, out = self.pty_send("--not-a-duplicate", word=b"no\n")
        self.assertIn("Type send", screen)
        self.assertEqual(code, 1)
        self.assertEqual(self.gh_calls("issue create"), [])

    def test_9_a_linked_drafts_folder_is_refused(self):
        self.new()
        moved = os.path.join(self.home, "elsewhere")
        shutil.move(self.drafts, moved)
        os.symlink(moved, self.drafts)
        code, out, err = self.issue("send")
        self.assertEqual(code, 2, err)
        self.assertEqual(self.gh_calls(), [])

    def test_discard_and_show(self):
        self.new()
        data = self.draft()
        code, out, err = self.issue("show")
        self.assertEqual((code, out.encode()), (0, data))
        name = os.path.basename(self.draft_dir())
        code, out, err = self.issue("discard")
        self.assertEqual(code, 0, err)
        self.assertIn(name, out + err)
        self.assertEqual(os.listdir(self.drafts), [])


class FrozenTest(IssueHome):
    def test_13_the_frozen_tree_holds_the_scanner_and_the_table(self):
        prefix = os.path.join(self.home, "prefix")
        code, out, err = self.run_cli("install-cli", "--prefix", prefix, "--yes")
        self.assertEqual(code, 0, err)
        p = subprocess.run([os.path.join(prefix, "bin", "agentik-suite"), "issue"], capture_output=True,
                           text=True, env=self.env(), timeout=60, cwd=self.work)
        self.assertEqual(p.returncode, 0, p.stderr)


class SkillTest(unittest.TestCase):
    def test_14_the_skill_hands_the_send_line_to_the_user(self):
        text = SKILL.read_text()
        self.assertEqual(text.count("agentik issue send"), 1)
        fenced = re.findall(r"```.*?```", text, re.S)
        self.assertFalse(any("issue send" in f for f in fenced))
        line = [l for l in text.splitlines() if "agentik issue send" in l][0]
        self.assertIn("terminal", line)
        p = subprocess.run([str(ROOT / "scripts" / "plugin-description-bytes"), str(PLUGIN)],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)


if __name__ == "__main__":
    unittest.main()
