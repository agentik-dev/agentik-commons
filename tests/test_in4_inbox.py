"""Row in4-inbox: `inbox`, one list of what waits on the owner across every checkout.

Each run is the suite's launcher in a temp HOME (`Home`), TZ=UTC, its cwd a temp folder in no repo.
On the stub PATH two made-up tools, `agentik-ledger` (the reads `questions` and `backlog`) and
`agentik-bench` (`charter`), each a script that answers `describe --json`, prints for each read the
object built from the world file the test wrote, for the paths it is given, and records its argv.
Four made-up checkouts under a temp folder T: `pear-hq`, `quince-hq`, `fig-hq`, each a git repository
on `main` with one commit, and `plum-hq`, which is not made. Every fixture is dated from the clock at
the test's start. After every run each checkout is walked whole and its `git status` read again
(acceptance 17).
"""
import datetime
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import time
import unittest

import test_agentik_suite as base
from test_agentik_suite import LAUNCHER, LIB, SYSTEM

ANSI = re.compile(r"\x1b\[[0-9;]*m")
GIT_ENV = {"PATH": SYSTEM, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "TZ": "UTC",
           "GIT_OPTIONAL_LOCKS": "0"}
READS = {"ledger": [["questions", ["questions", "--json"]], ["backlog", ["backlog", "--json"]]],
         "bench": [["charter", ["charter", "show", "--json"]]]}
TOOL = r'''import json, os, sys, time
here = os.path.dirname(os.path.abspath(__file__))
name, args = sys.argv[1], sys.argv[2:]
with open(os.path.join(here, "tool-calls"), "a") as fh:
    fh.write(json.dumps([name] + args) + "\n")
with open(os.path.join(here, "tools.json")) as fh:
    reads = json.load(fh)[name]
if args == ["describe", "--json"]:
    print(json.dumps({"schema": "agentik.describe/1", "ok": True, "tool": name, "version": "1.0.0",
                      "summary": "A made-up tool.", "repo": "example/" + name, "plugin": name + "@agentik",
                      "needs": [], "verbs": [],
                      "reads": [{"kind": "status", "name": r, "argv": a} for r, a in reads]}))
    sys.exit(0)
with open(os.path.join(here, "world.json")) as fh:
    world = json.load(fh)
for read, argv in reads:
    if args[:len(argv)] != argv:
        continue
    given = args[len(argv):]
    how = world.get("how", {}).get(read, {})
    with open(os.path.join(here, read + ".pid"), "w") as fh:
        fh.write(str(os.getpid()))
    time.sleep(how.get("sleep", 0))
    if "exit" in how:
        sys.exit(how["exit"])
    if "print" in how:
        print(how["print"])
        sys.exit(0)
    entries = world.get(read, {})
    repos = [dict(entries[os.path.realpath(p)], repo=p) for p in given if os.path.realpath(p) in entries]
    left = [p for p in given if os.path.realpath(p) not in entries]
    if read == "backlog":
        print(json.dumps({"repos": repos, "skipped": left}))
    else:
        print(json.dumps({"schema": "agentik.%s/1" % read, "ok": True, "repos": repos,
                          "skipped": [{"repo": p, "why": "nothing to read"} for p in left]}))
    sys.exit(0)
sys.exit(2)
'''

NEXT_ACT = "Cut the first row, then name the repos in the README."
BLOCK = ("## 1. Which barn holds the hay\n\n**Where things stand.** The hay is in the yard and rain is due.\n\n"
         "**Your answer:**")
PEAR = """warn  pear-hq  3 wait
   question 1  Which barn holds the hay
               recommended: The red barn; asked today
   hand        Start the first run
               run: lampd run --first
   row 2       buys the lock for the second barn
               waits on it: The second barn's door
   sitting     2026-11-13-1, 3 h ago: Cut the first row, then name the repos in the README.
"""
SCREEN = "Waiting on you: 3, in 2 checkouts (from the command line).\n\n" + PEAR + \
    "\nok  quince-hq  nothing waits\n"
FIG = """warn  fig-hq  1 waits
   question 1  Paint the gate green
               answered, not entered yet; its sitting enters it
   hand        The fence wire is on order and the owner collects it
               no command is given; see history/sittings/2026-11-11-2.md:18
   sitting     2026-11-11-2, 2 d ago: Wait for the wire.
   decided     2 without asking, the newest on 2026-11-12
"""
CHECK = """pear-hq: question 1: Which barn holds the hay; recommended: The red barn
pear-hq: hand: Start the first run; run: lampd run --first
pear-hq: row 2: buys the lock for the second barn
fig-hq: hand: The fence wire is on order and the owner collects it; no command, see history/sittings/2026-11-11-2.md:18
plum-hq: not read: not a directory
"""
OPENED = """pear-hq  question 1, open, asked today

## 1. Which barn holds the hay

**Where things stand.** The hay is in the yard and rain is due.

**Your answer:**

To answer: type after "Your answer:" in the block at OPEN-QUESTIONS.md:5.
Or start claude in pear-hq and ask for its open questions.
"""
CHARTER_TWO = "note  not read  charter: agentik-bench charter show --json exited 2\n"
DOCTOR = "next: %s doctor shows which command is missing or behind its plugin.\n"
USER = "~/.config/agentik/suite/config.yaml"


def git(path, *args):
    return subprocess.run(["git", "-C", path] + list(args), check=True, capture_output=True, text=True,
                          env=GIT_ENV).stdout


class InboxHome(base.Home):
    def setUp(self):
        base.Home.setUp(self)
        side = self.temp()
        self.side = side
        self.T = os.path.join(side, "T")
        os.mkdir(self.T)
        self.now = time.time()
        self.today = datetime.datetime.fromtimestamp(self.now, datetime.timezone.utc).date()
        with open(os.path.join(side, "tool.py"), "w") as fh:
            fh.write(TOOL)
        with open(os.path.join(side, "tools.json"), "w") as fh:
            json.dump(READS, fh)
        for name in READS:
            self.stub("agentik-" + name, '#!/bin/sh\nPYTHONPYCACHEPREFIX="%s" exec /usr/bin/python3 -B "%s" %s "$@"\n'
                      % (os.path.join(side, "pyc"), os.path.join(side, "tool.py"), name))
        self.walked = [self.T]
        self.pear, self.quince, self.fig = (self.checkout(os.path.join(self.T, n))
                                            for n in ("pear-hq", "quince-hq", "fig-hq"))
        self.plum = os.path.join(self.T, "plum-hq")
        self.world = {"how": {}}
        for kind, path in (("pear", self.pear), ("quince", self.quince), ("fig", self.fig)):
            self.give(kind, path)
        self.save()
        self.L = str(LAUNCHER)

    def temp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return os.path.realpath(tmp.name)

    def checkout(self, path, changed=False):
        os.makedirs(path)
        with open(os.path.join(path, "README.md"), "w") as fh:
            fh.write("A made-up checkout.\n")
        git(path, "init", "-q", "-b", "main")
        git(path, "add", "README.md")
        git(path, "-c", "user.name=fixture", "-c", "user.email=", "commit", "-qm", "one")
        if os.path.basename(path) in ("pear-hq", "a1") or changed:
            with open(os.path.join(path, "README.md"), "a") as fh:
                fh.write("A line more.\n")
            with open(os.path.join(path, "notes.txt"), "w") as fh:
                fh.write("Not tracked.\n")
        return path

    def give(self, kind, path):
        """The three reads' entries for one made-up checkout, under its real path."""
        real = os.path.realpath(path)
        w = self.world
        for read in ("questions", "charter", "backlog"):
            w.setdefault(read, {})
        decided = {"count": 0, "newest": None}
        if kind == "pear":
            w["questions"][real] = {"file": "OPEN-QUESTIONS.md", "answered": 0, "decided": decided, "questions": [
                {"n": 1, "title": "Which barn holds the hay", "line": 5, "state": "open", "why": None,
                 "proposed": self.today.isoformat(), "recommended": "The red barn", "text": BLOCK}]}
            w["charter"][real] = {"file": os.path.join(path, "history", "sittings", "2026-11-13-1.md"),
                                  "name": "2026-11-13-1", "mtime": self.now - 3.5 * 3600, "closed": False,
                                  "next_act": NEXT_ACT,
                                  "waits": [{"line": 12, "what": "Start the first run",
                                             "command": "lampd run --first"}]}
            w["backlog"][real] = {"handoff": os.path.join(path, "HANDOFF.md"), "steps": [
                {"n": 1, "title": "The first barn", "line": 8, "level": "S3", "state": None},
                {"n": 2, "title": "The second barn's door", "line": 9, "level": "S3",
                 "state": {"word": "waiting", "on": "the owner", "text": "buys the lock for the second barn"}}]}
        elif kind == "quince":
            w["questions"][real] = {"file": "OPEN-QUESTIONS.md", "answered": 0, "decided": decided,
                                    "questions": []}
            w["backlog"][real] = {"handoff": os.path.join(path, "HANDOFF.md"), "steps": [
                {"n": 1, "title": "A quiet step", "line": 8, "level": "S4",
                 "state": {"word": "open", "on": None, "text": "nothing yet"}}]}
        elif kind == "fig":
            w["questions"][real] = {
                "file": os.path.join(path, "OPEN-QUESTIONS.md"), "answered": 1,
                "decided": {"count": 2, "newest": "2026-11-12"}, "questions": [
                    {"n": 1, "title": "Paint the gate green", "line": 7, "state": "answered",
                     "why": "typed above the answer line",
                     "proposed": (self.today - datetime.timedelta(days=3)).isoformat(),
                     "recommended": "Green", "text": "## 1. Paint the gate green\n\n**Your answer:** green"}]}
            w["charter"][real] = {"file": "history/sittings/2026-11-11-2.md", "name": "2026-11-11-2",
                                  "mtime": self.now - 2.2 * 86400, "closed": False,
                                  "next_act": "Wait for the wire.",
                                  "waits": [{"line": 18, "command": None,
                                             "what": "- The fence wire is on order and the owner collects it"}]}
            w["backlog"][real] = {"handoff": os.path.join(path, "HANDOFF.md"), "steps": []}
        else:  # a checkout with nothing in it
            w["questions"][real] = {"file": "OPEN-QUESTIONS.md", "answered": 0, "decided": decided,
                                    "questions": []}

    def save(self):
        with open(os.path.join(self.side, "world.json"), "w") as fh:
            json.dump(self.world, fh)

    def how(self, read, **how):
        self.world["how"][read] = how
        self.save()

    # ---- acceptance 17: nothing in a checkout moves ----------------------------------------

    def walk(self):
        found = {}
        for top in self.walked:
            for folder, dirs, files in os.walk(top):
                for path in [folder] + [os.path.join(folder, n) for n in files]:
                    st = os.lstat(path)
                    digest = None
                    if stat.S_ISREG(st.st_mode):
                        with open(path, "rb") as fh:
                            digest = hashlib.sha256(fh.read()).hexdigest()
                    found[path] = (st.st_mode, st.st_size, st.st_mtime_ns, digest)
        return found

    def status(self):
        return [git(p, "status", "--porcelain", "--branch")
                for p in (self.pear, getattr(self, "a1", None)) if p and os.path.isdir(os.path.join(p, ".git"))]

    def inbox(self, *args, cwd=None, path=None, **more):
        before = (self.walk(), self.status(), self.snapshot())
        env = self.env(TZ="UTC", **more)
        if path is not None:
            env["PATH"] = path
        p = subprocess.run([self.L, "inbox"] + list(args), capture_output=True, text=True, env=env,
                           timeout=60, cwd=cwd or self.side)
        self.assertEqual((self.walk(), self.status(), self.snapshot()), before, args)
        self.assertFalse(os.path.exists(self.calls), args)  # the stub claude: no call
        return p.returncode, p.stdout, p.stderr

    def calls_of(self):
        try:
            with open(os.path.join(self.side, "tool-calls")) as fh:
                found = [json.loads(line) for line in fh]
        except FileNotFoundError:
            return []
        return [c for c in found if c[1:] != ["describe", "--json"]]

    def hint_open(self, *paths):
        return "next: %s inbox 1 %s opens question 1 as it is written.\n" % (self.L, " ".join(paths))


class ListTest(InboxHome):
    def test_1_the_first_screen_piped(self):
        self.assertEqual(git(self.pear, "status", "--porcelain", "--branch"), "## main\n M README.md\n?? notes.txt\n")
        code, out, err = self.inbox(self.pear, self.quince)
        self.assertEqual((code, out), (0, SCREEN))
        self.assertEqual(err, self.hint_open(self.pear, self.quince))
        self.assertNotIn("\x1b", out + err)

    def test_2_the_same_on_a_terminal_of_80(self):
        code, text = self.run_pty("inbox", self.pear, self.quince, cols=80, TZ="UTC")
        self.assertEqual(code, 0)
        self.assertIn("\x1b[1m" + "pear-hq" + "\x1b[0m", text)  # the name bold
        lines = ANSI.sub("", text).replace("\r\n", "\n").splitlines()
        self.assertIn("!  pear-hq  3 wait", lines)
        self.assertIn("✓  quince-hq  nothing waits", lines)
        self.assertIn("   sitting     2026-11-13-1, 3 h ago: Cut the first row, then name the repos i…", lines)
        self.assertIn("               run: lampd run --first", lines)
        long = [l for l in lines if len(l) > 79 and not l.startswith("next: ")]
        self.assertEqual(long, [])

    def test_3_nothing_waits_and_a_checkout_that_is_no_folder(self):
        code, out, err = self.inbox(self.quince)
        self.assertEqual((code, out, err), (0, "Nothing waits on you in 1 checkout (from the command line).\n\n"
                                               "ok  quince-hq  nothing waits\n", ""))
        code, out, err = self.inbox(self.pear, self.plum)
        self.assertEqual((code, out), (0, "Waiting on you: at least 3, in 2 checkouts (from the command line).\n\n"
                                          + PEAR + "\nnote  plum-hq  not read: not a directory\n"))
        self.assertEqual(err, self.hint_open(self.pear, self.plum))
        self.assertFalse([c for c in self.calls_of() if self.plum in c], "a path that is no folder goes to no tool")

    def test_4_the_other_kinds_of_row(self):
        code, out, err = self.inbox(self.fig)
        self.assertEqual((code, out, err), (0, "Waiting on you: 1, in 1 checkout (from the command line).\n\n"
                                               + FIG, ""))
        self.world["charter"][self.fig]["waits"] = None
        self.save()
        code, out, err = self.inbox(self.fig)
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[:3], ["Nothing waits on you in 1 checkout (from the command line).", "",
                                                "ok  fig-hq  nothing waits"])
        self.assertIn("   sitting     2026-11-11-2, 2 d ago, with no Waits part: Wait for the wire.\n", out)

    def test_5_a_question_that_cannot_be_asked(self):
        q = self.world["questions"][self.pear]["questions"][0]
        q.update(state="unreadable", why="no base line, or more than one")
        self.save()
        code, out, err = self.inbox(self.pear)
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("Waiting on you: 2, in 1 checkout"), out)
        self.assertIn("warn  pear-hq  2 wait\n   question 1  Which barn holds the hay\n"
                      "               cannot be asked yet, since no base line, or more than one; its sitting mends it\n",
                      out)
        code, out, err = self.inbox("--check", self.pear)
        self.assertEqual(code, 1)
        self.assertNotIn("question", out)
        self.assertEqual(len(out.splitlines()), 2)

    def test_6_a_read_that_gave_no_answer(self):
        self.how("charter", exit=2)
        code, out, err = self.inbox(self.pear, self.quince)
        self.assertEqual((code, out), (0, "Waiting on you: at least 2, in 2 checkouts (from the command line).\n"
                                          + CHARTER_TWO + """
warn  pear-hq  2 wait
   question 1  Which barn holds the hay
               recommended: The red barn; asked today
   row 2       buys the lock for the second barn
               waits on it: The second barn's door

note  quince-hq  nothing readable waits
"""))
        self.assertEqual(err, DOCTOR % self.L)
        self.how("charter", print=json.dumps({"schema": "agentik.charter/2", "ok": True}))
        code, out, err = self.inbox(self.pear, self.quince)
        self.assertIn("note  not read  charter: agentik-bench charter show --json answers in a shape this "
                      "version does not know\n", out)
        self.assertTrue(out.startswith("Waiting on you: at least 2,"), out)
        self.assertEqual((code, err), (0, DOCTOR % self.L))
        self.how("charter", sleep=10)
        start = time.monotonic()
        code, out, err = self.inbox(self.pear, self.quince)
        self.assertLess(time.monotonic() - start, 6.0)
        self.assertIn("note  not read  charter: agentik-bench charter show --json gave no answer in 5 s\n", out)
        self.assertTrue(out.startswith("Waiting on you: at least 2,"), out)
        self.assertEqual((code, err), (0, DOCTOR % self.L))
        with open(os.path.join(self.side, "charter.pid")) as fh:
            pid = int(fh.read())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)
        os.unlink(os.path.join(self.stubs, "agentik-bench"))
        code, out, err = self.inbox(self.pear, self.quince)
        self.assertIn("note  not read  charter: no command on PATH gives that read\n", out)
        self.assertTrue(out.startswith("Waiting on you: at least 2,"), out)
        self.assertEqual((code, err), (0, DOCTOR % self.L))

    def test_7_a_backlog_answer_of_another_shape(self):
        for step in self.world["backlog"][self.pear]["steps"]:
            del step["state"]
        self.world["backlog"][self.fig]["steps"] = [
            {"n": 3, "title": "The gate's hinge", "line": 9, "level": "S3",
             "state": {"word": "waiting", "on": "the owner", "text": "oils the hinge"}}]
        self.save()
        code, out, err = self.inbox(self.pear, self.fig)
        self.assertEqual(code, 0)
        shape = "agentik-ledger backlog --json answers in a shape this version does not know"
        self.assertTrue(out.startswith("Waiting on you: at least 4, in 2 checkouts (from the command line).\n"
                                       "note  not read  backlog in pear-hq: %s\n\n" % shape), out)
        self.assertIn("   row 3       oils the hinge\n               waits on it: The gate's hinge\n", out)
        self.assertNotIn("row 2", out)
        for step in self.world["backlog"][self.fig]["steps"]:
            del step["state"]
        self.save()
        code, out, err = self.inbox(self.pear, self.fig)
        rows = [l for l in out.splitlines() if l.startswith("note  not read")]
        self.assertEqual(rows, ["note  not read  backlog: %s" % shape])

    def test_8_no_tool_gives_a_read(self):
        for name in READS:
            os.unlink(os.path.join(self.stubs, "agentik-" + name))
        code, out, err = self.inbox(self.pear)
        self.assertEqual((code, out, err), (3, "", "FAIL  no command on PATH gives a read the inbox needs\n"
                                                   "next: %s setup\n" % self.L))


class CheckTest(InboxHome):
    def test_9_check(self):
        code, out, err = self.inbox("--check", self.pear, self.fig, self.plum)
        self.assertEqual((code, out, err), (1, CHECK, ""))
        self.assertEqual(self.inbox("--check", self.quince), (0, "", ""))
        self.how("charter", exit=2)
        code, out, err = self.inbox("--check", self.pear)
        self.assertEqual((code, err), (1, ""))
        self.assertEqual(out.splitlines()[0], "not read: charter: agentik-bench charter show --json exited 2")

    def test_10_json(self):
        code, out, err = self.inbox("--json", self.pear, self.plum)
        self.assertEqual((code, err), (0, ""))
        obj = json.loads(out)
        self.assertEqual((obj["schema"], obj["ok"], obj["count"], obj["complete"], obj["covers"]["rule"]),
                         ("agentik.inbox/1", True, 3, False, "args"))
        self.assertEqual(obj["covers"]["checkouts"], [self.pear, self.plum])
        pear, plum = obj["checkouts"]
        self.assertEqual((pear["name"], pear["read"], plum["name"], plum["read"]), ("pear-hq", True, "plum-hq", False))
        self.assertEqual(pear["questions"][0]["n"], 1)
        self.assertTrue(pear["questions"][0]["waits"])
        self.assertEqual(pear["hands"], [{"what": "Start the first run", "command": "lampd run --first",
                                          "file": "history/sittings/2026-11-13-1.md", "line": 12}])
        self.assertEqual([r["n"] for r in pear["rows"]], [2])
        self.assertEqual(pear["sitting"]["charter"], "2026-11-13-1")
        self.assertEqual(pear["sitting"]["next_act"], NEXT_ACT)
        self.assertEqual(sorted((r["name"], r["state"], r["repo"]) for r in obj["reads"]),
                         [("backlog", "ok", self.pear), ("charter", "ok", None), ("questions", "ok", None)])
        code, out, err = self.inbox("--json", "--check", self.pear, self.plum)
        obj = json.loads(out)
        # R11 names a line for each checkout not read, so plum-hq's is the fourth
        self.assertEqual((code, obj["check"], len(obj["lines"])), (1, True, 4))
        self.assertEqual(obj["lines"][-1], "plum-hq: not read: not a directory")

    def test_11_a_question_by_its_number(self):
        code, out, err = self.inbox("1", self.pear)
        self.assertEqual((code, out, err), (0, OPENED, ""))
        self.assertEqual(out.split("\n\n")[1:4], BLOCK.split("\n\n"))
        code, out, err = self.inbox("7", self.pear)
        self.assertEqual((code, out, err), (2, "", "FAIL  no checkout read here holds a question 7\n"
                                                   "next: %s inbox %s\n" % (self.L, self.pear)))
        code, out, err = self.inbox("--check", "1")
        self.assertEqual((code, out, err), (2, "", "FAIL  --check and a question's number are two answers\n"
                                                   "next: %s inbox --check\n" % self.L))
        code, out, err = self.inbox("1", self.pear, self.fig)
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith(OPENED + "\n" + "fig-hq  question 1, answered, asked 3 d ago\n\n## 1. Paint"), out)
        code, out, err = self.inbox("--json", "1", self.pear)
        opened = json.loads(out)["opened"]
        self.assertEqual([(o["name"], o["n"], o["state"], o["text"]) for o in opened],
                         [("pear-hq", 1, "open", BLOCK)])

    def test_r2_a_noun_of_digits_with_a_slash_is_a_path(self):
        os.mkdir(os.path.join(self.side, "7"))
        self.give("plain", os.path.join(self.side, "7"))
        self.save()
        code, out, err = self.inbox("./7")
        self.assertEqual((code, out, err), (0, "Nothing waits on you in 1 checkout (from the command line).\n\n"
                                               "ok  7  nothing waits\n", ""))
        self.assertEqual(self.inbox("07")[0], 0)  # a leading zero: a path, here no folder


class CoversTest(InboxHome):
    def user(self, text):
        path = os.path.join(self.home, ".config", "agentik", "suite", "config.yaml")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def test_12_the_user_files_list(self):
        home_quince = self.checkout(os.path.join(self.home, "quince-hq"))
        self.give("quince", home_quince)
        self.save()
        self.user("checkouts: [%s, ~/quince-hq, rel/x]\n" % self.pear)
        code, out, err = self.inbox()
        self.assertEqual(code, 0, err)
        self.assertEqual(out, SCREEN.replace("(from the command line)", "(from your checkouts list)"))
        notes = [l for l in err.splitlines() if "rel/x" in l]
        self.assertEqual(notes, ["note  rel/x in %s is not read: a checkout is an absolute path, "
                                 "or one under ~/." % USER])
        self.user("checkouts:\n\t- %s\n" % self.pear)
        code, out, err = self.inbox()
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(err, "FAIL  %s cannot be read at line 2: a tab; the subset indents with spaces\n" % USER)

    def test_13_the_hq_and_the_repos_beside_it(self):
        tree = os.path.join(self.T, "tree")
        hq, apple, notes = (os.path.join(tree, n) for n in ("pear-hq", "apple", "notes"))
        for path in (hq, apple, notes):
            os.makedirs(path)
        for path in (hq, apple):
            os.mkdir(os.path.join(path, ".git"))
            os.makedirs(os.path.join(path, ".claude", "agentik"))
        with open(os.path.join(hq, ".claude", "agentik", "config.yaml"), "w") as fh:
            fh.write("suite:\n  kind: hq\n")
        with open(os.path.join(apple, ".claude", "agentik", "config.yaml"), "w") as fh:
            fh.write("checkouts: [%s]\n" % self.fig)
        for path in (hq, apple):
            self.give("plain", path)
        self.save()
        code, out, err = self.inbox(cwd=apple)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "Nothing waits on you in 2 checkouts (the hq pear-hq and the repos beside it).\n\n"
                              "ok  pear-hq  nothing waits\n\nok  apple  nothing waits\n")

    def test_14_this_repo_alone_and_no_repo(self):
        lone = os.path.join(self.T, "lone")
        os.makedirs(os.path.join(lone, ".git"))
        self.give("plain", lone)
        self.save()
        code, out, err = self.inbox(cwd=lone)
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "Nothing waits on you in 1 checkout (this repo alone: no list, no hq).\n\n"
                              "ok  lone  nothing waits\n")
        self.assertEqual(err, "next: to read every checkout at once, list them under checkouts: in %s.\n" % USER)
        code, out, err = self.inbox(cwd=self.T)
        self.assertEqual((code, out, err), (2, "", "FAIL  there is no checkout to read: the cwd is in no repo, and "
                                                   "%s lists none\nnext: %s help inbox\n" % (USER, self.L)))

    def test_r6_a_second_naming_of_one_folder(self):
        code, out, err = self.inbox(self.quince, os.path.join(self.quince, "."), "--json")
        self.assertEqual(json.loads(out)["covers"]["checkouts"], [self.quince])


class CallTest(InboxHome):
    def test_15_the_calls(self):
        self.inbox(self.pear, self.quince)
        calls = self.calls_of()
        self.assertEqual(sorted(c for c in calls if c[1] != "backlog"),
                         [["bench", "charter", "show", "--json", self.pear, self.quince],
                          ["ledger", "questions", "--json", self.pear, self.quince]])
        self.assertEqual(sorted(c for c in calls if c[1] == "backlog"),
                         [["ledger", "backlog", "--json", self.pear], ["ledger", "backlog", "--json", self.quince]])
        os.unlink(os.path.join(self.side, "tool-calls"))
        self.inbox(self.pear, self.plum)
        self.assertTrue(self.calls_of())
        self.assertFalse([c for c in self.calls_of() if self.plum in c])

    def test_16_the_table(self):
        with open(os.path.join(str(LIB), "fallback.json")) as fh:
            table = json.load(fh)
        rows = {name: row["inbox"] for name, row in table.items() if row.get("inbox")}
        self.assertEqual(sorted(r["name"] for rs in rows.values() for r in rs), ["backlog", "charter", "questions"])
        folder = os.path.join(self.side, "rec")
        os.mkdir(folder)
        calls = os.path.join(self.side, "rec-calls")
        for name in rows:
            path = os.path.join(folder, "agentik-" + name)
            with open(path, "w") as fh:
                fh.write(base.RECORDER % calls)
            os.chmod(path, 0o755)
        code, out, err = self.inbox(self.pear, path="%s:%s" % (folder, SYSTEM))
        self.assertEqual(code, 0, err)
        with open(calls) as fh:
            got = sorted(fh.read().splitlines())
        want = sorted("%s %s" % (os.path.join(folder, "agentik-" + name), " ".join(r["argv"] + [self.pear]))
                      for name, rs in rows.items() for r in rs)
        self.assertEqual(got, want)
        self.assertNotIn("describe", "\n".join(got))


class HelpTest(InboxHome):
    WORDS = "Print one line for each thing that needs a hand, and exit 1 when there is one."

    def test_18_help(self):
        code, out, err = self.run_cli("help")
        self.assertRegex(out, r"(?m)^  inbox +List what waits on you in each checkout")
        code, out, err = self.run_cli("help", "inbox")
        self.assertEqual(code, 0)
        self.assertRegex(out, r"(?m)^  --check +%s$" % re.escape(self.WORDS))
        code, out, err = self.run_cli("status", "--check", "--help")
        self.assertRegex(out, r"(?m)^  --check +%s$" % re.escape(self.WORDS))


class ReadOnlyTest(InboxHome):
    def test_19_read_only_checkouts(self):
        for path in (self.pear, self.quince, self.fig):
            subprocess.run(["chmod", "-R", "a-w", path], check=True)
            self.addCleanup(subprocess.run, ["chmod", "-R", "u+w", path])
        code, out, err = self.inbox(self.pear, self.quince)
        self.assertEqual((code, out), (0, SCREEN))

    def test_20_a_name_comes_from_the_path(self):
        code, out, err = self.inbox(self.pear, self.quince)
        other = os.path.join(self.side, "U")
        os.mkdir(other)
        self.a1 = self.checkout(os.path.join(other, "a1"))
        b2 = self.checkout(os.path.join(other, "b2"))
        self.walked.append(other)
        self.give("pear", self.a1)
        self.give("quince", b2)
        # the charter's file and the handoff name the folder, as the pear-hq ones do
        self.save()
        code2, out2, err2 = self.inbox(self.a1, b2)
        swap = lambda s: s.replace(self.pear, self.a1).replace(self.quince, b2).replace(
            "pear-hq", "a1").replace("quince-hq", "b2")
        self.assertEqual((code2, out2, err2), (code, swap(out), swap(err)))
        self.assertIn("ok  b2  nothing waits", out2)


if __name__ == "__main__":
    unittest.main()
