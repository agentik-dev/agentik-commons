"""Row rp6-verb, the fix of review 1 and phase 2: `issue` after its first adversary.

F1, no cut before the scrub: a secret walked across each cut lands nowhere in part. F2, `reword`
prints and saves only scrubbed words. F3, `new` numbers past the placeholders the person typed.
F4 and F5, `discard` (and every word) acts on a real draft folder only, and no word of the verb
shows a traceback. F6, every word answers --json with one object. Phase 2, each refusal is sc4's
two lines, and no `next:` line files or carries --yes. Each test runs in rp6's temp HOME with its
stub `gh`, `ps` and tool; every value here is made up.
"""
import json
import os
import pty
import select
import shutil
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_rp6_issue import (EXPECTED, FAILING, LAUNCHER, PUBLIC, TOOL, URL, IssueHome)  # noqa: E402

from agentik_suite import form, gather  # noqa: E402

SECRET = "Qm4Rt8Yp2Wx6Kz0Lb3Nv7Hc5Jd9Fg1Sa"  # made up, 32 bytes, in MADE_UP_TOKEN
OLD_CAP = 16384  # the cut of gather's read the review measured, before layer 1
LOGIN = "brindlewort"  # a made-up login
ZW = LOGIN[:4] + "​" + LOGIN[4:]
DOCTOR = r'''#!/usr/bin/python3 -I
import json, os, sys
def read(n, default):
    try:
        with open(os.path.join(os.environ["HOME"], "detail-%%d.txt" %% n)) as fh:
            return fh.read()
    except OSError:
        return default
if sys.argv[1:] == ["doctor", "--json"]:
    print(json.dumps({"schema": "agentik.doctor/1", "ok": True, "checks": [
        {"name": "doctor", "status": "fail", "detail": read(1, %r), "remedy": None},
        {"name": "meter", "status": "warn", "detail": read(2, "slow"), "remedy": None}]}))
    sys.exit(1)
sys.exit(2)
''' % FAILING
EDITOR = '''#!/usr/bin/python3 -I
import sys
with open(sys.argv[1]) as fh:
    text = fh.read()
with open(sys.argv[1], "w") as fh:
    fh.write(text.replace("billing-api", "billing-svc"))
'''


def grams(secret):
    """Every run of four bytes of `secret`: a fragment of four bytes or more holds one."""
    return {secret[i:i + 4] for i in range(len(secret) - 3)}


def pad(n):
    """`n` bytes of plain words that end in a space."""
    return ("c " * n)[:n - 1] + " " if n > 0 else ""


def long_path(n):
    """A made-up path of `n` bytes that the scrub replaces whole."""
    segs, size = [], 0
    while size + 8 <= n - 9:
        segs.append("seg%04d" % len(segs))
        size += 8
    return ("/" + "/".join(segs) + "/" + "x" * n)[:n]


class FixHome(IssueHome):
    def setUp(self):
        IssueHome.setUp(self)
        self.stub("agentik-" + TOOL, DOCTOR)

    def meta(self):
        with open(os.path.join(self.draft_dir(), "draft.json")) as fh:
            return fh.read()

    def write(self, name, text):
        path = os.path.join(self.home, name)
        with open(path, "w") as fh:
            fh.write(text)
        return path

    def pty_word(self, *args, **more):
        """`issue ARGS` with stdin and stderr on a pty and stdout a pipe, run to its end:
        (exit, screen, stdout)."""
        r, w = os.pipe()
        pid, fd = pty.fork()
        if pid == 0:  # the child
            try:
                os.close(r)
                os.dup2(w, 1)
                os.chdir(self.work)
                os.execve(str(LAUNCHER), [str(LAUNCHER), "issue", *args], self.env(**more))
            finally:
                os._exit(127)
        os.close(w)
        screen, end = b"", time.time() + 60
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
        os.close(fd)
        _, status = os.waitpid(pid, 0)
        with os.fdopen(r, "rb") as fh:
            out = fh.read()
        return os.waitstatus_to_exitcode(status), screen.decode("utf-8", "replace"), out.decode()


class CutTest(FixHome):
    """F1 (S1): design/22 item 4, layer 1 runs before any cut."""

    def leaks(self, *texts):
        return sorted(g for g in grams(SECRET) for t in texts if g in t)

    def walk(self, make):
        """For each place of the secret across a cut, from one byte before it to one byte after:
        `make(n)` writes the inputs with `n` bytes of the secret before the cut and gives `new`'s
        extra words; no four bytes of it reach the draft, draft.json or either stream, and a draft
        that held some would be refused by send --dry-run."""
        for n in range(-1, len(SECRET) + 2):
            code, out, err = self.issue("new", TOOL, "--exit", "2", *make(n), MADE_UP_TOKEN=SECRET)
            self.assertEqual(code, 0, (n, err[-300:]))
            data, meta = self.draft().decode(), self.meta()
            if self.leaks(data):
                code, screen, _ = self.pty_send("--dry-run", MADE_UP_TOKEN=SECRET)
                self.assertNotEqual(code, 0, (n, "send --dry-run passed a fragment"))
            self.assertEqual(self.leaks(data, meta, out, err), [], n)
            self.issue("discard")

    def test_f1_a_secret_across_the_read_cap_and_the_bounds(self):
        def make(n):
            head = long_path(OLD_CAP - n - len(" is token ")) + " is token "
            self.write("err.txt", head + SECRET + " more\n" + pad(gather.LINE - n) + SECRET + " end\n"
                       + FAILING + "\n")
            self.write("detail-1.txt", head + SECRET + " failed")
            self.write("detail-2.txt", pad(gather.ROW_DETAIL - n) + SECRET + " slow")
            return ["--output", os.path.join(self.home, "err.txt"),
                    "--ran", pad(gather.RAN - n) + SECRET + " x",
                    "--expected", pad(gather.EXPECTED - n) + SECRET + " works"]
        self.walk(make)

    def test_f1_a_secret_across_the_tail_of_one_long_line(self):
        """A last line longer than the read's window: the pin kept its last OLD_CAP bytes."""
        def make(n):
            tail = " " + pad(OLD_CAP - (len(SECRET) - n) - 1)
            self.write("err.txt", pad(gather.TAIL + 4000) + SECRET + tail + "\n")
            return ["--output", os.path.join(self.home, "err.txt")]
        self.walk(make)

    def test_f1_a_secret_across_the_windows_edge(self):
        def make(n):
            after = gather.TAIL - 1 - (len(SECRET) - n)
            self.write("err.txt", pad(5000) + SECRET + " " + pad(after - 1) + "\n")
            return ["--output", os.path.join(self.home, "err.txt")]
        self.walk(make)

    def test_f1_no_free_value_is_cut_before_the_scrub(self):
        self.assertEqual(gather._free("a" * gather.READ_CAP), "a" * gather.READ_CAP)
        self.assertEqual(gather._free("a" * gather.READ_CAP + SECRET), gather.UNREADABLE)
        self.assertEqual(form._cut("suite", "x" * 60 + " <path-12> after"), "x" * 60)

    def test_f1_a_clean_draft_still_passes_the_last_check(self):
        code, out, err = self.new(MADE_UP_TOKEN=SECRET)
        self.assertEqual(code, 0, err)
        code, screen, _ = self.pty_send("--dry-run", MADE_UP_TOKEN=SECRET)
        self.assertEqual(code, 0, screen[-400:])


class RewordTest(FixHome):
    """F2 (S1): nothing of a render is printed or saved before the layer has scrubbed it."""

    def test_f2_the_words_a_render_adds_are_scrubbed(self):
        for said in ("%s, %s saw it" % (FAILING, LOGIN), "%s, seen by %s" % (FAILING, ZW)):
            for json_too in ((), ("--json",)):
                self.assertEqual(self.new(USER=LOGIN)[0], 0)
                path = self.write("render.txt", "Happened: %s\nExpected: %s\n" % (said, EXPECTED))
                code, out, err = self.issue(*json_too, "reword", path, USER=LOGIN)
                self.assertEqual(code, 0, err)
                meta = json.loads(self.meta())
                texts = (out, err, self.draft().decode(), json.dumps(meta, ensure_ascii=False))
                for text in texts:
                    for raw in (LOGIN, ZW, "​"):
                        self.assertNotIn(raw, text, (said, json_too))
                self.issue("discard")


class NumberingTest(FixHome):
    """F3: a placeholder the person typed and a replaced path never share a name."""

    def test_f3_new_numbers_past_the_given_values(self):
        code, out, err = self.issue("new", TOOL, "--ran", "agentik %s doctor" % TOOL, "--exit", "2",
                                    "--output", "err.txt", "--expected", "it reads <path-1> fine")
        self.assertEqual(code, 0, err)
        lines = self.draft().decode().split("\n")
        typed = [i for i, l in enumerate(lines, 1) if "it reads <path-1> fine" in l]
        replaced = [i for i, l in enumerate(lines, 1) if "no profile resolved for <path-2>" in l]
        self.assertEqual((len(typed), len(replaced)), (1, 1), lines)
        self.assertNotIn("<path-1>", lines[replaced[0] - 1])
        said = [l for l in out.splitlines() if l.startswith("replaced")]
        self.assertEqual(said, ["replaced 1 path on line %d" % replaced[0]], out)


class DiscardTest(FixHome):
    """F4, F5: discard removes one real draft folder of mode 0700 in a real drafts folder."""

    def outside(self):
        place = os.path.join(self.home, "elsewhere")
        os.makedirs(os.path.join(place, "20250101T000000Z-0001"))
        self.write(os.path.join("elsewhere", "20250101T000000Z-0001", "keep.txt"), "kept")
        return place

    def refused(self, args, name):
        code, out, err = self.issue(*args)
        self.assertEqual((code, out), (2, ""), (args, err))
        self.assertTrue(err.startswith("FAIL  "), err)
        self.assertNotIn("Traceback", err)
        self.assertNotIn(self.home, err)
        if name:
            self.assertIn(name, err)
        return err

    def test_f4_a_linked_drafts_folder_is_refused_by_every_word(self):
        place = self.outside()
        os.makedirs(os.path.dirname(self.drafts))
        os.symlink(place, self.drafts)
        render = self.write("render.txt", "Happened: x\nExpected: y\n")
        for args in (("discard",), ("show",), ("strike", "kept"), ("drop", "plugins"),
                     ("reword", render), ("send", "--dry-run"), ("new", TOOL)):
            err = self.refused(args, None)
            self.assertIn("drafts folder", err, args)
        self.assertEqual(os.listdir(place), ["20250101T000000Z-0001"])
        self.assertEqual(os.listdir(os.path.join(place, "20250101T000000Z-0001")), ["keep.txt"])

    def test_f5_an_entry_that_is_no_draft_folder_is_refused(self):
        self.assertEqual(self.new()[0], 0)
        real = self.draft_dir()
        place = self.outside()
        name = "29991231T235959Z-abcd"
        entry = os.path.join(self.drafts, name)
        for make in (lambda: os.symlink(place, entry), lambda: self.write(entry, "x"),
                     lambda: os.mkdir(entry, 0o755)):
            make()
            if os.path.isdir(entry) and not os.path.islink(entry):
                os.chmod(entry, 0o755)
            for args in (("discard",), ("--json", "discard")):
                code, out, err = self.issue(*args)
                self.assertEqual(code, 2, err)
                self.assertNotIn("Traceback", out + err)
                self.assertNotIn(self.home, out + err)
                self.assertIn(name, out + err)
            self.assertTrue(os.path.lexists(entry))
            (os.rmdir if os.path.isdir(entry) and not os.path.islink(entry) else os.unlink)(entry)
        self.assertEqual(os.listdir(os.path.join(place, "20250101T000000Z-0001")), ["keep.txt"])
        self.assertTrue(os.path.isdir(real))

    def test_f5_no_word_shows_a_traceback(self):
        """Every word over each wrong state of the drafts: an exit of the frame, no traceback, no
        absolute path on stderr."""
        render = self.write("render.txt", "Happened: %s\nExpected: %s\n" % (FAILING, EXPECTED))
        words = [(), ("--check",), ("show",), ("strike", "billing-api"), ("drop", "plugins"),
                 ("edit",), ("reword", render), ("send", "--dry-run"), ("discard",), ("new", TOOL),
                 ("--json", "show"), ("--json", "discard")]

        def draft_file(how):
            def make():
                path = os.path.join(self.draft_dir(), "issue.md")
                os.unlink(path)
                how(path)
            return make

        states = {
            "root a file": lambda: (shutil.rmtree(self.drafts), self.write(self.drafts, "x")),
            "root open": lambda: os.chmod(self.drafts, 0o755),
            "issue.md gone": draft_file(lambda p: None),
            "issue.md a link": draft_file(lambda p: os.symlink(os.path.join(self.home, "err.txt"), p)),
            "issue.md a folder": draft_file(lambda p: os.mkdir(p)),
            "issue.md not utf-8": draft_file(lambda p: open(p, "wb").write(b"\xff\xfe\x00 x\n\n")),
            "draft.json garbage": lambda: self.write(os.path.join(self.draft_dir(), "draft.json"), "{["),
            "draft unreadable": lambda: os.chmod(self.draft_dir(), 0o300),
        }
        for label, spoil in states.items():
            if os.path.lexists(self.drafts):
                for top, dirs, _ in os.walk(self.drafts):
                    for d in dirs:
                        os.chmod(os.path.join(top, d), 0o700)
                (shutil.rmtree if os.path.isdir(self.drafts) else os.unlink)(self.drafts)
            self.assertEqual(self.new()[0], 0)
            spoil()
            for args in words:
                code, out, err = self.issue(*args)
                self.assertIn(code, (0, 1, 2), (label, args, err))
                self.assertNotIn("Traceback", out + err, (label, args))
                self.assertNotIn(self.home, err, (label, args))
            if os.path.isdir(self.drafts):
                for top, dirs, _ in os.walk(self.drafts):
                    for d in dirs:
                        os.chmod(os.path.join(top, d), 0o700)


class JsonTest(FixHome):
    """F6: every word answers --json with one agentik.issue/1 object on stdout, nothing else there,
    and no key holds an absolute path."""

    def one(self, out, keys):
        self.assertEqual(out.count("\n"), 1, out)
        obj = json.loads(out)
        self.assertEqual(set(obj), {"schema", "ok", "id"} | set(keys), obj)
        self.assertEqual((obj["schema"], obj["ok"]), ("agentik.issue/1", True))

        def walk(value):
            if isinstance(value, dict):
                return [v for item in value.values() for v in walk(item)]
            if isinstance(value, list):
                return [v for item in value for v in walk(item)]
            return [value] if isinstance(value, str) else []
        for value in walk(obj):
            self.assertFalse(value.startswith("/") or self.home in value, value)
        return obj

    def test_f6_each_word_answers_json(self):
        self.assertEqual(self.new()[0], 0)
        name = os.path.basename(self.draft_dir())
        code, out, err = self.issue("--json", "strike", "billing-api")
        obj = self.one(out, ("words", "places", "struck"))
        self.assertEqual((code, obj["id"], obj["struck"], obj["places"]), (0, name, ["<struck-1>"], 1))
        code, out, err = self.issue("--json", "drop", "plugins")
        self.assertEqual(self.one(out, ("dropped",))["dropped"], ["plugins"])
        code, out, err = self.issue("--json", "show")
        self.assertEqual(self.one(out, ("text",))["text"], self.draft().decode())
        render = self.write("render.txt", "Happened: %s, every time\nExpected: doctor should pass in a "
                            "fresh clone of <struck-1>, before any session\n" % FAILING)
        code, out, err = self.issue("--json", "reword", render)
        obj = self.one(out, ("reworded", "added"))
        self.assertEqual((code, obj["reworded"]), (0, True), err)
        self.assertIn("every", obj["added"])
        editor = os.path.join(self.stubs, "edit-stub")
        with open(editor, "w") as fh:
            fh.write(EDITOR)
        os.chmod(editor, 0o755)
        self.assertEqual(self.issue("--json", "discard")[0], 0)
        self.assertEqual(self.new()[0], 0)
        code, screen, out = self.pty_word("--json", "edit", EDITOR=editor)
        obj = self.one(out, ("size", "unsure"))
        self.assertEqual((code, obj["size"]), (0, len(self.draft())), screen)
        self.assertIn(b"billing-svc", self.draft())
        code, screen, out = self.pty_send("--json")
        obj = self.one(out, ("filed", "url", "recorded"))
        self.assertEqual((code, obj["filed"], obj["url"], obj["recorded"]), (0, True, URL, True), screen)
        name = os.path.basename(self.draft_dir())
        code, out, err = self.issue("--json", "discard", "--draft", name)
        self.assertEqual(self.one(out, ("discarded",))["id"], name)


class Phase2Test(FixHome):
    """Main's rules over the verb: a refusal is its cause, then `next:` and a line that only reads
    or the help of the verb; never a line that files, and never one with --yes."""

    def nexts(self, text):
        return [l[len("next: "):] for l in text.splitlines() if l.startswith("next: ")]

    def assert_safe(self, line, why):
        words = line.split()
        self.assertNotIn("send", words[words.index("issue") + 1:] if "issue" in words else words, why)
        self.assertFalse({"--yes", "-y"} & set(words), why)

    def refusal(self, args, cause, tail, exit_code=2, **env):
        code, out, err = self.issue(*args, **env)
        self.assertEqual((code, out), (exit_code, ""), (args, err))
        lines = err.splitlines()
        at = [i for i, l in enumerate(lines) if l.startswith("FAIL  ")]
        self.assertEqual(len(at), 1, (args, err))
        self.assertEqual(lines[at[0]:-1], ["FAIL  " + cause], (args, err))
        self.assertTrue(lines[-1].startswith("next: "), (args, err))
        nxt = lines[-1][len("next: "):]
        self.assertTrue(nxt.endswith(tail), (args, nxt))
        self.assert_safe(nxt, args)
        code, out, err = self.issue("--json", *args, **env)
        obj = json.loads(out)["error"]
        self.assertEqual((code, obj["message"]), (exit_code, cause), args)
        self.assertTrue(obj["remedy"].endswith(tail), (args, obj))
        return nxt

    def test_each_refusal_is_its_cause_then_a_line_that_files_nothing(self):
        self.refusal(("show",), "no draft waits", "help issue")
        self.assertEqual(self.new()[0], 0)
        for args, cause, tail in (
                (("snd",), "snd is not a word of issue; the nearest is send", "help issue"),
                (("shw",), "shw is not a word of issue; the nearest is show", "issue show"),
                (("zzz",), "zzz is not a word of issue", "help issue"),
                (("--check", "show"), "--check reads the drafts and takes no word", "issue --check"),
                (("show", "--draft", "nope"), "no draft is named nope", "issue"),
                (("new", "nosuchtool"), "nosuchtool is no tool an issue can name; one of "
                 + ", ".join(sorted(PUBLIC["tools"])), "help issue"),
                (("new", "--exit", "300"), "--exit takes the command's exit code, 0 to 255, not 300",
                 "help issue"),
                (("strike",), "strike takes the words to strike", "help issue"),
                (("drop", "nothing"), "nothing is no part of the draft; one of "
                 + ", ".join(form.SECTIONS), "help issue"),
                (("send", "--yes"), "send takes no --yes: an issue is filed only when you read it on "
                 "your terminal and type send there", "help issue"),
                (("send", "--dry-rn"), "--dry-rn is not a flag of issue", "help issue"),
                (("discard", "--dry-rn"), "--dry-rn is not a flag of issue", "help issue"),
                (("send",), "send needs a terminal to type in, and this process has none; send from "
                 "your own terminal", "help issue")):
            self.refusal(args, cause, tail)
        self.gh_answer("issue_list", json.dumps([{"number": 7, "title": "x", "state": "OPEN",
                                                   "url": URL[:-2] + "7"}]))
        self.refusal(("send",), "an open issue already holds this failure: %s; add to it there, or pass "
                     "--not-a-duplicate to file another" % (URL[:-2] + "7"), "help issue", exit_code=1)
        self.assertEqual(self.gh_calls("issue create"), [])

    def test_a_refusal_on_the_terminal_names_no_send_line(self):
        self.assertEqual(self.new()[0], 0)
        code, screen, out = self.pty_send(CLAUDECODE="1")
        self.assertEqual(code, 2, screen)
        self.assertIn("send files nothing from inside Claude Code", screen)
        for line in self.nexts(screen.replace("\r", "")):
            self.assert_safe(line, screen)
        self.assertEqual(self.gh_calls("issue create"), [])

    def test_a_filed_draft_names_the_list(self):
        self.assertEqual(self.new()[0], 0)
        self.assertEqual(self.pty_send()[0], 0)
        nxt = self.refusal(("send",), "this draft was already filed: %s" % URL, "issue", exit_code=1)
        self.assertFalse(nxt.endswith("help issue"), nxt)


if __name__ == "__main__":
    unittest.main()
