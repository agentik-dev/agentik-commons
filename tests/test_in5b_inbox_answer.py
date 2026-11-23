"""Row in5b-inbox-answer: `inbox answer <repo> N (--pick L | --say T) [--dry-run] [--yes]`.

On in4's home (`test_in4_inbox.InboxHome`): the made-up `agentik-ledger` gives the `questions` read
and here lists a verb `reply` in its describe. Its `reply` is a stub: it records its argv, its cwd
and whether fds 0 and 2 are terminals, prints one line on each stream, asks once on a terminal as
the writer does, exits with the code the test sets, and on a write sets that question's state to
`answered` in the world file. Every checkout is a temp folder's; the inbox helper walks each one
whole and reads its `git status` around every run (in4's acceptance 17).
"""
import io
import json
import os
import pty
import re
import select
import shlex
import subprocess
import time

import test_in4_inbox as in4
from test_agentik_suite import LIB

REPLY = r'''if args[:1] == ["reply"]:
    with open(os.path.join(here, "world.json")) as fh:
        world = json.load(fh)
    how = world.get("reply", {})
    got = None
    if "--yes" not in args and "--dry-run" not in args and os.isatty(0):
        sys.stderr.write("write it? [y/N] ")
        sys.stderr.flush()
        got = sys.stdin.readline().strip()
    with open(os.path.join(here, "reply-calls"), "a") as fh:
        fh.write(json.dumps({"argv": args, "cwd": os.getcwd(), "tty0": os.isatty(0), "tty2": os.isatty(2),
                             "got": got}) + "\n")
    print("the line after")
    sys.stderr.write("the writer's note\n")
    code = how.get("exit", 0)
    if code == 0 and "--dry-run" not in args and got in (None, "y"):
        for q in world["questions"][os.path.realpath(os.getcwd())]["questions"]:
            if q["n"] == int(args[1]):
                q["state"] = "answered"
        with open(os.path.join(here, "world.json"), "w") as fh:
            json.dump(world, fh)
    sys.exit(code)
'''
BLOCK2 = "## 2. Which way the gate opens\n\n- **North** (Recommended)\n- **South**\n\n**Your answer:**"
SAY = "the \"west\" gate, at $HOME's end, café über alles"


class AnswerHome(in4.InboxHome):
    verbs = [{"name": "reply", "summary": "the owner's answer", "top": False}]

    def setUp(self):
        in4.InboxHome.setUp(self)
        tool = in4.TOOL.replace('with open(os.path.join(here, "tools.json"))',
                                REPLY + 'with open(os.path.join(here, "tools.json"))', 1)
        with open(os.path.join(self.side, "ledger.py"), "w") as fh:
            fh.write(tool)
        self.ledger_stub(self.verbs)
        real = os.path.realpath(self.pear)
        self.world["questions"][real]["questions"].append(
            {"n": 2, "title": "Which way the gate opens", "line": 12, "state": "open", "why": None,
             "proposed": self.today.isoformat(), "recommended": "North", "text": BLOCK2})
        self.save()
        self.user("checkouts: [%s, %s]\n" % (self.pear, self.quince))

    def ledger_stub(self, verbs):
        answer = dict(in4.describe("ledger"), verbs=verbs)
        self.stub("agentik-ledger", in4.STUB % {
            "call": shlex.quote(json.dumps(["ledger", "describe", "--json"])),
            "calls": shlex.quote(os.path.join(self.side, "tool-calls")),
            "describe": shlex.quote(json.dumps(answer)),
            "pyc": shlex.quote(os.path.join(self.side, "pyc")),
            "tool": shlex.quote(os.path.join(self.side, "ledger.py")), "name": "ledger"})

    def user(self, text):
        path = os.path.join(self.home, ".config", "agentik", "suite", "config.yaml")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def replies(self):
        try:
            with open(os.path.join(self.side, "reply-calls")) as fh:
                return [json.loads(line) for line in fh]
        except FileNotFoundError:
            return []

    def answer(self, *args, cwd=None, **more):
        """`inbox answer ...` with stdin a pipe, stdout and stderr pipes, the checkouts walked."""
        before = (self.walk(), self.status(), self.snapshot())
        p = subprocess.run([self.L, "inbox", "answer"] + list(args), input="", capture_output=True,
                           text=True, env=self.env(TZ="UTC", **more), timeout=60, cwd=cwd or self.side)
        self.assertEqual((self.walk(), self.status(), self.snapshot()), before, args)
        self.assertFalse(os.path.exists(self.calls), args)
        return p.returncode, p.stdout, p.stderr

    def refused(self, code, err, *words):
        self.assertEqual(code, 2, err)
        self.assertRegex(err, r"\AFAIL  [^\n]*\nnext: [^\n]+\n\Z")
        for word in words:
            self.assertIn(word, err)
        self.assertEqual(self.replies(), [])


class RunTest(AnswerHome):
    def test_1_the_answer_runs_the_writer(self):
        code, out, err = self.answer("pear-hq", "2", "--pick", "North", "--yes")
        self.assertEqual((code, out, err), (0, "the line after\n", "the writer's note\n"))
        calls = self.replies()
        self.assertEqual([(c["argv"], c["cwd"]) for c in calls],
                         [(["reply", "2", "--pick=North", "--yes"], os.path.realpath(self.pear))])

    def test_2_the_words_reach_it_byte_for_byte(self):
        self.answer("pear-hq", "2", "--say", SAY, "--dry-run")
        self.answer("pear-hq", "2", "--pick=North", "-y", "--dry-run")
        self.answer("pear-hq", "2", "--say=" + SAY, "--yes")
        self.assertEqual([c["argv"] for c in self.replies()],
                         [["reply", "2", "--say=" + SAY, "--dry-run"],
                          ["reply", "2", "--pick=North", "--dry-run", "--yes"],
                          ["reply", "2", "--say=" + SAY, "--yes"]])

    def test_3_its_exit_passes_through(self):
        for k in (1, 2):
            self.world["reply"] = {"exit": k}
            self.save()
            code, out, err = self.answer("pear-hq", "2", "--pick", "North", "--yes")
            self.assertEqual((code, err), (k, "the writer's note\n"))

    def on_pty(self, *args):
        master, slave = pty.openpty()
        p = subprocess.Popen([self.L, "inbox", "answer"] + list(args), stdin=slave, stdout=slave, stderr=slave,
                             env=self.env(TZ="UTC"), cwd=self.side, close_fds=True)
        os.close(slave)
        chunks, sent = [], False
        try:
            while True:
                if not sent and b"[y/N]" in b"".join(chunks):
                    time.sleep(0.2)
                    os.write(master, b"y\n")
                    sent = True
                ready, _, _ = select.select([master], [], [], 60)
                if not ready:
                    break
                try:
                    data = os.read(master, 65536)
                except OSError:
                    break
                if not data:
                    break
                chunks.append(data)
        finally:
            os.close(master)
        return p.wait(timeout=30), b"".join(chunks).decode("utf-8", "replace")

    def test_4_the_terminal(self):
        code, screen = self.on_pty("pear-hq", "2", "--pick", "North")
        self.assertEqual(code, 0, screen)
        self.assertEqual([(c["tty0"], c["tty2"], c["got"]) for c in self.replies()], [(True, True, "y")])
        code, out, err = self.answer("pear-hq", "2", "--pick", "North")
        self.assertEqual(code, 2)
        self.assertIn("--yes", err)
        self.assertEqual(len(self.replies()), 1)
        code, out, err = self.answer("pear-hq", "2", "--pick", "North", "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(self.replies()[-1]["argv"], ["reply", "2", "--pick=North", "--dry-run"])

    def test_8_the_inbox_afterwards(self):
        code, out, err = self.inbox()
        self.assertTrue(out.startswith("Waiting on you: 4,"), out)
        self.assertEqual(self.answer("pear-hq", "2", "--pick", "North", "--yes")[0], 0)
        code, out, err = self.inbox()
        self.assertTrue(out.startswith("Waiting on you: 3,"), out)
        self.assertRegex(out, r"question 2  Which way the gate opens\n +answered, not entered yet; its sitting enters it\n")
        code, out, err = self.inbox("--check")
        self.assertNotIn("question 2", out)


class RepoTest(AnswerHome):
    def test_5_the_repo(self):
        self.answer("./pear-hq", "2", "--pick", "North", "--yes", cwd=self.T)
        self.answer(self.quince, "2", "--pick", "North", "--yes")
        self.assertEqual([c["cwd"] for c in self.replies()],
                         [os.path.realpath(self.pear), os.path.realpath(self.quince)])
        os.remove(os.path.join(self.side, "reply-calls"))
        code, out, err = self.answer("plum-hq", "2", "--pick", "North", "--yes")
        self.refused(code, err, "plum-hq", "pear-hq, quince-hq", "next: %s inbox\n" % self.L)
        code, out, err = self.answer(os.path.join(self.pear, "README.md"), "2", "--pick", "North", "--yes")
        self.refused(code, err, "not a directory")
        other = self.checkout(os.path.join(self.T, "other", "pear-hq"))
        self.user("checkouts: [%s, %s]\n" % (self.pear, other))
        code, out, err = self.answer("pear-hq", "2", "--pick", "North", "--yes")
        self.refused(code, err, self.pear, other)
        code, out, err = self.inbox("2")
        self.assertIn("To answer from here, run %s inbox answer %s 2 --pick <label>.\n" % (self.L, self.pear), out)

    def test_9_the_opened_block_names_the_form(self):
        code, out, err = self.inbox("2")
        self.assertEqual(code, 0, err)
        self.assertIn("\nTo answer from here, run %s inbox answer pear-hq 2 --pick <label>.\n"
                      "To answer: type after" % self.L, out)


class WordsTest(AnswerHome):
    def test_6_the_words_refused_first(self):
        for args, word in ((("--pick", "North", "--yes"), "repo"), (("pear-hq", "--pick", "North"), "number"),
                           (("pear-hq", "0", "--pick", "North"), "0"), (("pear-hq", "02", "--pick", "North"), "02"),
                           (("pear-hq", "x", "--pick", "North"), "x"), (("pear-hq", "2", "--yes"), "--say"),
                           (("pear-hq", "2", "--pick", "North", "--say", "no"), "--say"),
                           (("pear-hq", "2", "--pick", "North", "--check"), "--check"),
                           (("pear-hq", "2", "3", "--pick", "North"), "3"), (("pear-hq", "2", "--pick"), "--pick")):
            code, out, err = self.answer(*args)
            self.refused(code, err, word, "next: %s help inbox\n" % self.L)
        code, out, err = self.answer("pear-hq", "2", "--pick", "North", "--json")
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)["error"]["remedy"], "%s help inbox" % self.L)
        self.assertEqual(self.replies(), [])
        for flag in ("--yes", "--dry-run", "--say", "--pick"):
            code, out, err = self.inbox(*([flag] if flag in ("--yes", "--dry-run") else [flag, "x"]))
            self.assertEqual((code, err), (2, "FAIL  %s is not a flag of inbox\nnext: %s help inbox\n" % (flag, self.L)))

    def test_6_setup_and_config_keep_their_switch(self):
        import sys
        sys.path.insert(0, str(LIB))
        from agentik_suite import cli
        opts, words, bad = cli.parse(["setup", "--pick", "x"])
        self.assertEqual((opts["pick"], words, bad), (True, ["setup", "x"], None))
        opts, words, bad = cli.parse(["config", "--pick"])
        self.assertEqual((opts["config_pick"], words, bad), (True, ["config"], None))
        opts, words, bad = cli.parse(["inbox", "answer", "a", "2", "--pick", "x"])
        self.assertEqual((opts["pick"], opts["pick_label"], words), (False, "x", ["inbox", "answer", "a", "2"]))
        self.assertFalse(cli.refused(["inbox", "answer", "a", "2", "--say", "x", "--dry-run"]))
        for line in (["inbox", "answer", "a"], ["inbox", "answer", "a", "2"], ["inbox", "answer", "a", "2", "--check"],
                     ["inbox", "--pick", "x"], ["inbox", "1", "--dry-run"]):
            self.assertTrue(cli.refused(line), line)
        cmd = cli.Command(["inbox", "answer", "a", "2", "--say", "x", "--dry-run"], self.env(),
                          io.StringIO(), io.StringIO())
        cmd.verb = "inbox"
        self.assertTrue(cmd.offer(["inbox", "answer", "a", "2", "--dry-run"]).endswith("help inbox"))
        self.assertTrue(cmd.offer(["inbox", "answer", "a", "2", "--say=x", "--dry-run"]).endswith("help inbox"))


class WriterTest(AnswerHome):
    def test_7_no_writer(self):
        self.ledger_stub([])
        code, out, err = self.answer("pear-hq", "2", "--pick", "North", "--yes")
        self.refused(code, err, "agentik-ledger", "next: %s update\n" % self.L)
        os.remove(os.path.join(self.stubs, "agentik-ledger"))
        code, out, err = self.answer("pear-hq", "2", "--pick", "North", "--yes")
        self.assertEqual(code, 3, err)
        self.assertEqual(self.replies(), [])

    def test_7_no_tools_name_in_the_package(self):
        for top, dirs, files in os.walk(os.path.join(str(LIB), "agentik_suite")):
            for name in files:
                if name.endswith((".py", ".md")):
                    with open(os.path.join(top, name), encoding="utf-8") as fh:
                        text = fh.read()
                    self.assertIsNone(re.search(r"agentik-ledger|agentik-bench|pear-hq|agentik-decision[s]", text), name)


class ReviewOneTest(AnswerHome):
    """The fix of review 1: a --pick or --say with no value is still seen (F1, F2), a relative
    PATH entry finds the writer from the suite's own folder (F3), the value rides its flag (N1)."""

    def test_r1_a_flag_with_no_value_is_one_of_the_two(self):
        how = "FAIL  give the answer as --pick <label> or as --say <text>, one of the two\nnext: %s help inbox\n"
        for args in (("pear-hq", "2", "--pick", "--say", "x", "--yes"), ("pear-hq", "2", "--say", "x", "--pick", "--yes"),
                     ("pear-hq", "2", "--pick", "--yes"), ("pear-hq", "2", "--say", "--yes"),
                     ("pear-hq", "2", "--pick"), ("pear-hq", "2", "--say"),
                     ("pear-hq", "2", "--pick=North", "--say", "--yes")):
            self.assertEqual(self.answer(*args), (2, "", how % self.L), args)
        self.assertEqual(self.replies(), [])

    def test_r1_outside_answer_as_before_the_row(self):
        fail = "FAIL  %s is not a flag of inbox\nnext: %s help inbox\n"
        for args, flag in ((("--pick",), "--pick"), (("--say",), "--say"), (("1", "--pick"), "--pick"),
                           (("--check", "--pick"), "--pick"), (("--say", "--check"), "--say"),
                           ((self.pear, "--pick"), "--pick")):
            self.assertEqual(self.inbox(*args), (2, "", fail % (flag, self.L)), args)
        code, out, err = self.inbox("--pick", "--json")
        self.assertEqual((code, err), (2, ""))
        self.assertEqual(json.loads(out), {"schema": "agentik.inbox/1", "ok": False, "error": {
            "code": "unknown_flag", "message": "--pick is not a flag of inbox", "remedy": "%s help inbox" % self.L}})
        import sys
        sys.path.insert(0, str(LIB))
        from agentik_suite import cli
        opts, words, bad = cli.parse(["inbox", "--pick"])
        self.assertEqual((opts["pick"], opts["pick_label"], words, bad), (True, None, ["inbox"], None))
        opts, words, bad = cli.parse(["inbox", "--say"])
        self.assertEqual((opts["say"], words, bad), (None, ["inbox"], "--say"))
        opts, words, bad = cli.parse(["setup", "--pick"])
        self.assertEqual((opts["pick"], words, bad), (True, ["setup"], None))

    def test_r2_a_relative_path_entry_runs_the_writer_found(self):
        marker = os.path.join(self.side, "planted-ran")
        planted = os.path.join(self.pear, "agentik-ledger")
        with open(planted, "w") as fh:
            fh.write("#!/bin/sh\necho planted > %s\necho 'not the writer'\n" % shlex.quote(marker))
        os.chmod(planted, 0o755)
        rest = self.env()["PATH"].split(os.pathsep, 1)[1]
        for entry, cwd in ((".", self.stubs), ("", self.stubs), (os.path.relpath(self.stubs, self.T), self.T)):
            code, out, err = self.answer("pear-hq", "2", "--pick", "North", "--yes", cwd=cwd,
                                         PATH=entry + os.pathsep + rest)
            self.assertEqual((code, out, err), (0, "the line after\n", "the writer's note\n"), entry)
            self.assertEqual([(c["argv"], c["cwd"]) for c in self.replies()][-1:],
                             [(["reply", "2", "--pick=North", "--yes"], os.path.realpath(self.pear))], entry)
            self.assertFalse(os.path.exists(marker), entry)
        self.assertEqual(len(self.replies()), 3)

    def test_r3_the_value_rides_its_flag(self):
        for value in ("--say=-x", "--say=--ledger=/elsewhere/DECISIONS.md", "--pick=-x"):
            self.assertEqual(self.answer("pear-hq", "2", value, "--dry-run")[0], 0, value)
        self.assertEqual(self.answer("pear-hq", "2", "--say", "-x", "--dry-run")[0], 2)  # refused, as before
        self.assertEqual([c["argv"] for c in self.replies()],
                         [["reply", "2", "--say=-x", "--dry-run"],
                          ["reply", "2", "--say=--ledger=/elsewhere/DECISIONS.md", "--dry-run"],
                          ["reply", "2", "--pick=-x", "--dry-run"]])


class ReviewTwoTest(AnswerHome):
    """The fix of review 2: the writer's path is joined to the folder and never normalised, so the
    file run is the one the PATH search found, a `<link>/..` entry among them (F1)."""

    def setUp(self):
        AnswerHome.setUp(self)
        self.marker = os.path.join(self.side, "planted-ran")
        self.system = self.env()["PATH"].split(os.pathsep, 1)[1]

    def plant(self, folder):
        """An executable of the writer's name in `folder`, which writes the marker when run."""
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, "agentik-ledger")
        with open(path, "w") as fh:
            fh.write("#!/bin/sh\necho planted >> %s\necho 'not the writer'\n" % shlex.quote(self.marker))
        os.chmod(path, 0o755)

    def runs(self, entry, cwd, path=None):
        """The answer with PATH `entry` then the system's (or `path` whole), from `cwd`: the stub
        ran once, in the checkout, and no plant ran."""
        before = len(self.replies())
        path = entry + os.pathsep + self.system if path is None else path
        got = self.answer("pear-hq", "2", "--pick", "North", "--yes", cwd=cwd, PATH=path)
        self.assertEqual(got, (0, "the line after\n", "the writer's note\n"), path)
        self.assertEqual([(c["argv"], c["cwd"]) for c in self.replies()[before:]],
                         [(["reply", "2", "--pick=North", "--yes"], os.path.realpath(self.pear))], path)
        self.assertFalse(os.path.exists(self.marker), path)

    def link_entries(self):
        """`<checkout>/ln/..`, absolute and relative to the caller's folder, where ln points into
        the stubs' folder: the kernel reads ln/.. as the stubs' folder, the text folds it to the
        checkout."""
        os.makedirs(os.path.join(self.stubs, "sub"))
        link = os.path.join(self.pear, "ln")
        os.symlink(os.path.join(self.stubs, "sub"), link)
        return os.path.join(link, ".."), os.path.join(os.path.relpath(link, self.side), "..")

    def test_f1_a_link_and_dotdot_entry_runs_the_writer_found(self):
        entries = self.link_entries()
        self.plant(self.pear)  # where ln/.. folds to as text
        for entry in entries:
            self.runs(entry, self.side)
        self.assertEqual(len(self.replies()), 2)

    def test_f1_the_same_entry_with_no_plant(self):
        for entry in self.link_entries():
            self.runs(entry, self.side)
        self.assertEqual(len(self.replies()), 2)

    def test_f1_the_path_shapes_review_two_checked(self):
        self.plant(self.pear)
        sibling = os.path.join(self.home, ".config")
        for entry, cwd in ((".", self.stubs), ("", self.stubs),
                           (os.path.relpath(self.stubs, self.home), self.home),
                           (os.path.join("..", os.path.basename(self.stubs)), sibling),
                           (os.path.relpath(self.stubs, self.pear), self.pear)):
            self.runs(entry, cwd)
        # a trailing and a doubled empty entry, from the stubs' folder
        for path in (self.system + os.pathsep, self.system.replace(os.pathsep, os.pathsep * 2, 1)):
            self.runs(None, self.stubs, path)
        # a relative entry that finds a copy of the writer from the caller's folder, while the
        # checkout holds a plant under the same relative name
        copy = os.path.join(self.side, "bin", "agentik-ledger")
        os.makedirs(os.path.dirname(copy))
        with open(os.path.join(self.stubs, "agentik-ledger")) as src, open(copy, "w") as dst:
            dst.write(src.read())
        os.chmod(copy, 0o755)
        self.plant(os.path.join(self.pear, "bin"))
        self.runs("bin" + os.pathsep + self.stubs, self.side)
        # a symlinked entry, relative and absolute
        os.symlink(self.stubs, os.path.join(self.side, "stublink"))
        self.runs("stublink", self.side)
        self.runs(os.path.join(self.side, "stublink"), self.side)
        self.assertFalse(os.path.exists(self.marker))


if __name__ == "__main__":
    import unittest
    unittest.main()
