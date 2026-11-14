"""Packet rp8: `issue new --render`, the narrator's script over the scrubbed draft, its
answer held to the nothing-new check, and the template as the floor.

Each test runs in `ConfigHome`, a temp HOME with a PATH of a stub folder, /usr/bin and /bin, with
a made-up narrator plugin installed there: its name and its script's path are read from
render.json at run time, and the script is a stub that records its argv, its working folder and
the files there, then writes the answer the test gave it. No test starts `claude`, the real
script or a model, reaches the network, or reads or writes the real home.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_rp6_issue as rp6  # noqa: E402
from test_agentik_suite import LIB, ROOT, ConfigHome  # noqa: E402

sys.path.insert(0, str(LIB))
from agentik_suite import form  # noqa: E402
try:
    from agentik_suite import render  # noqa: E402
except ImportError:  # at the pin, so each test is red on its own
    render = None

CONF = json.loads((LIB / "render.json").read_text()) if (LIB / "render.json").exists() else \
    {"plugin": "absent", "script": "scripts/absent.sh", "mode": None}
NAME = CONF["plugin"]
TOOL, EXPECTED, FAILING = rp6.TOOL, rp6.EXPECTED, rp6.FAILING
NOISE = "stub" + "noise-on-its-streams"
STUB = r'''#!/usr/bin/python3 -I
import json, os, sys, time
side = %r
args = sys.argv[1:]
opts = dict(zip(args[::2], args[1::2]))
with open(os.path.join(side, "behave.json")) as fh:
    behave = json.load(fh)
with open(opts["--source"], "rb") as fh:
    source = fh.read().decode("utf-8")
with open(opts["--contract"], "rb") as fh:
    contract = fh.read().decode("utf-8")
cwd = os.getcwd()
with open(os.path.join(side, "calls.jsonl"), "a") as fh:
    fh.write(json.dumps({"argv": args, "cwd": cwd, "files": sorted(os.listdir(cwd)),
                         "source": source, "contract": contract}) + "\n")
print(%r)
sys.stderr.write(%r + "\n")
sys.stdout.flush()
if behave.get("sleep"):
    import subprocess
    child = subprocess.Popen(["/bin/sleep", str(behave["sleep"])])
    with open(os.path.join(side, "pids"), "w") as fh:
        fh.write("%%d %%d\n" %% (os.getpid(), child.pid))
    time.sleep(behave["sleep"])
if behave.get("answer") is not None:
    with open(opts["--out"], "w") as fh:
        fh.write(behave["answer"])
sys.exit(behave.get("exit", 0))
'''


def gone(probe, within=3.0):
    """True once `probe` raises OSError (no such process or group), polled up to `within` s."""
    end = time.monotonic() + within
    while time.monotonic() < end:
        try:
            probe()
        except OSError:
            return True
        time.sleep(0.05)
    return False


class RenderHome(ConfigHome):
    issue, new, draft_dir, draft, reads_back = (rp6.IssueHome.issue, rp6.IssueHome.new,
                                                rp6.IssueHome.draft_dir, rp6.IssueHome.draft,
                                                rp6.IssueHome.reads_back)

    def setUp(self):
        ConfigHome.setUp(self)
        self.stub("agentik-" + TOOL, rp6.DOCTOR)
        self.work = os.path.join(self.home, "work")
        os.mkdir(self.work)
        with open(os.path.join(self.work, "err.txt"), "w") as fh:
            fh.write(rp6.OUTPUT)
        self.drafts = os.path.join(self.home, ".local", "state", "agentik-suite", "issues")
        self.record = os.path.join(self.side, "calls.jsonl")

    def install(self, narrator=True):
        plugins = {TOOL: "2.0.0", "suite": "0.7.3"}
        if narrator:
            plugins[NAME] = "1.0.0"
        self.plugin_files(os.path.join(self.home, ".claude"), plugins, whole=False)
        self.script = os.path.join(self.home, "inst", NAME, "1.0.0", CONF["script"])
        if narrator:
            os.makedirs(os.path.dirname(self.script), exist_ok=True)
            with open(self.script, "w") as fh:
                fh.write(STUB % (self.side, NOISE, NOISE))
            os.chmod(self.script, 0o755)

    def behave(self, answer=None, exit=0, sleep=0):
        with open(os.path.join(self.side, "behave.json"), "w") as fh:
            json.dump({"answer": answer, "exit": exit, "sleep": sleep}, fh)

    def script_calls(self):
        try:
            with open(self.record) as fh:
                return [json.loads(l) for l in fh]
        except FileNotFoundError:
            return []

    def fields(self):
        return form.parse(self.draft(), rp6.PUBLIC["tools"])

    def template(self, *more):
        """The template's two values, from a draft made without the flag."""
        code, out, err = self.new(*more)
        self.assertEqual(code, 0, err)
        f = self.fields()
        return f["happened"], f["expected"]

    def every_file(self):
        found = {}
        for top, _dirs, files in os.walk(self.home):
            for name in files:
                path = os.path.join(top, name)
                if not os.path.islink(path):
                    with open(path, "rb") as fh:
                        found[path] = fh.read()
        return found


class RenderTest(RenderHome):
    def test_1_a_clean_paraphrase_stands(self):
        self.install()
        happened, expected = self.template()
        self.behave("Happened: %s, and it stopped there\nExpected: %s, every time\n" % (happened, expected))
        code, out, err = self.new("--render")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.script_calls()), 1)
        f = self.fields()
        self.assertEqual(f["happened"], "%s, and it stopped there" % happened)
        self.assertEqual(f["expected"], "%s, every time" % expected)
        self.assertTrue(self.reads_back(self.draft()))
        added = [l for l in (out + err).splitlines() if l.startswith("Words the render added")]
        self.assertEqual(len(added), 1, out + err)
        for word in ("stopped", "there"):
            self.assertIn(word, added[0])
        with open(os.path.join(self.draft_dir(), "draft.json")) as fh:
            meta = json.load(fh)
        self.assertIn("stopped", meta["unsure"])
        self.assertEqual(meta["fields"]["happened"], f["happened"])
        # the draft printed at the end is the one on disk
        self.assertIn(self.draft().decode("utf-8").splitlines()[2], out)
        self.assertNotIn(NOISE, out + err)

    def test_2_a_new_name_drops_the_render(self):
        self.install()
        happened, expected = self.template()
        name = "Zor" + "blattico"
        self.behave("Happened: %s\nExpected: %s, for %s\n" % (happened, expected, name))
        code, out, err = self.new("--render")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.script_calls()), 1)
        f = self.fields()
        self.assertEqual((f["happened"], f["expected"]), (happened, expected))
        kept = [l for l in (out + err).splitlines() if "template stands" in l]
        self.assertEqual(len(kept), 1, out + err)
        self.assertNotIn(name, out + err)
        for path, data in self.every_file().items():
            self.assertNotIn(name.encode(), data, path)
        self.assertNotIn(name, json.dumps(self.script_calls()))

    def test_3_a_dropped_placeholder_or_error_text_keeps_the_template(self):
        self.install()
        path = os.path.join(self.home, "work", "profile.yaml")
        happened, expected = self.template("--expected", "doctor reads %s and passes" % path)
        ph = form.PLACEHOLDER.findall(expected)
        self.assertTrue(ph, expected)
        for answer in ("Happened: %s\nExpected: doctor reads the profile and passes\n" % happened,
                       "Happened: doctor failed on two checks\nExpected: %s\n" % expected):
            self.behave(answer)
            code, out, err = self.new("--expected", "doctor reads %s and passes" % path, "--render")
            self.assertEqual(code, 0, err)
            f = self.fields()
            self.assertEqual((f["happened"], f["expected"]), (happened, expected), answer)
            self.assertEqual(len([l for l in (out + err).splitlines() if "template stands" in l]), 1)
        self.assertEqual(len(self.script_calls()), 2)

    def test_4_no_plugin_and_a_failing_script_keep_the_template(self):
        self.install(narrator=False)
        happened, expected = self.template()
        code, out, err = self.new("--render")
        self.assertEqual(code, 0, err)
        lines = [l for l in (out + err).splitlines() if "template stands" in l]
        self.assertEqual(len(lines), 1, out + err)
        self.assertIn("installed", lines[0])
        self.assertEqual((self.fields()["happened"], self.fields()["expected"]), (happened, expected))
        self.install()
        self.behave("Happened: %s, again\nExpected: %s\n" % (happened, expected), exit=1)
        code, out, err = self.new("--render")
        self.assertEqual(code, 0, err)
        lines = [l for l in (out + err).splitlines() if "template stands" in l]
        self.assertEqual(len(lines), 1, out + err)
        self.assertIn("exited 1", lines[0])
        self.assertEqual((self.fields()["happened"], self.fields()["expected"]), (happened, expected))
        self.assertNotIn(NOISE, out + err)

    def test_4_the_wall_ends_the_group(self):
        self.install()
        self.behave("Happened: x\nExpected: y\n", sleep=30)
        why = {}
        start = time.monotonic()
        got = render.run(self.script, b"a draft\n", self.env(), wall=1.0, why=why)
        self.assertLess(time.monotonic() - start, 5.0)
        self.assertIsNone(got)
        self.assertEqual(why.get("code"), "wall")
        with open(os.path.join(self.side, "pids")) as fh:
            group, child = (int(n) for n in fh.read().split())
        self.assertTrue(gone(lambda: os.killpg(group, 0)), "the group outlived the wall")
        self.assertTrue(gone(lambda: os.kill(child, 0)), "the child outlived the wall")
        self.assertFalse(os.path.exists(self.script_calls()[0]["cwd"]))

    def test_4_an_answer_not_of_two_lines_is_none(self):
        self.install()
        for answer in (None, "", "Happened: x\n", "Expected: y\nHappened: x\n",
                       "Happened: x\nExpected: y\nmore\n", "Happened: x\x0bz\nExpected: y\n"):
            self.behave(answer)
            why = {}
            self.assertIsNone(render.run(self.script, b"d\n", self.env(), why=why), answer)
            self.assertEqual(why["code"], "nofile" if answer is None else "shape", answer)
        self.behave("Happened: x\nExpected: y")
        self.assertEqual(render.run(self.script, b"d\n", self.env()), {"happened": "x", "expected": "y"})

    def test_5_the_working_folder_holds_two_files_and_goes(self):
        self.install()
        self.behave(None, exit=1)
        code, out, err = self.new("--render")
        self.assertEqual(code, 0, err)
        (call,) = self.script_calls()
        self.assertEqual(len(call["files"]), 2, call["files"])
        opts = dict(zip(call["argv"][::2], call["argv"][1::2]))
        self.assertEqual(sorted(opts), ["--contract", "--mode", "--out", "--source"])
        self.assertEqual(opts["--mode"], CONF["mode"])
        for key in ("--source", "--contract", "--out"):
            self.assertEqual(os.path.dirname(opts[key]), call["cwd"], key)
        self.assertEqual(sorted(os.path.basename(opts[k]) for k in ("--source", "--contract")),
                         call["files"])
        self.assertEqual(call["source"].encode("utf-8"), self.draft())
        self.assertIn("Happened: ...", call["contract"])
        self.assertIn("Expected: ...", call["contract"])
        self.assertFalse(os.path.exists(call["cwd"]))

    def test_6_a_marker_in_the_folder_and_the_environment_stays_out(self):
        self.install()
        self.behave(None, exit=1)
        mark = "qx" + "plantedmark"
        work = os.path.join(self.home, "proj-" + mark)
        os.mkdir(work)
        with open(os.path.join(work, "err.txt"), "w") as fh:
            fh.write(rp6.OUTPUT)
        code, out, err = self.new("--render", cwd=work, SAMPLE_SETTING=mark + "-value")
        self.assertEqual(code, 0, err)
        (call,) = self.script_calls()
        self.assertNotIn(mark, call["source"])
        self.assertNotIn(mark, call["contract"])
        self.assertEqual(call["source"].encode("utf-8"), self.draft())

    def test_7_without_the_flag_no_call(self):
        self.install()
        self.behave("Happened: x\nExpected: y\n")
        code, out, err = self.new()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.script_calls(), [])
        self.assertNotIn("template stands", out + err)

    def test_8_help_and_the_other_words(self):
        code, out, err = self.run_cli("help", "issue")
        self.assertEqual(code, 0, err)
        self.assertIn("--render", out)
        for word in ("send", "discard", "show"):
            code, out, err = self.run_cli("issue", word, "--render")
            self.assertEqual(code, 2, (word, out, err))
            lines = err.splitlines()
            self.assertEqual(len(lines), 2, err)
            self.assertIn("--render", lines[0])
            self.assertTrue(lines[1].startswith("next: "), err)
        code, out, err = self.run_cli("issue", "--render")
        self.assertEqual(code, 2, err)
        self.assertEqual(len(err.splitlines()), 2, err)


SLEEPER = r'''#!/usr/bin/python3 -I
import os, time
with open(%r, "w") as fh:
    fh.write("%%d %%s" %% (os.getpid(), os.getcwd()))
time.sleep(30)
'''
# A script with a TERM trap that ends what it moved out of its group by setsid, and a child in its
# group with a TERM trap of its own; `leave` is the script's exit, or None to sleep to the wall.
TRAPPER = r'''#!/usr/bin/python3 -I
import os, signal, subprocess, sys, time
side, leave = %r, %r
away = subprocess.Popen(["/bin/sleep", "30"], start_new_session=True)
kid = os.fork()
if kid == 0:
    def kid_term(signum, frame):
        open(os.path.join(side, "kid-termed"), "w").close()
        os._exit(0)
    signal.signal(signal.SIGTERM, kid_term)
    time.sleep(30)
    os._exit(0)
def term(signum, frame):
    open(os.path.join(side, "termed"), "w").close()
    away.kill()
    sys.exit(0)
signal.signal(signal.SIGTERM, term)
with open(os.path.join(side, "pids"), "w") as fh:
    fh.write("%%d %%d %%d\n" %% (os.getpid(), away.pid, kid))
time.sleep(0.3)  # the child's trap is set before the script goes
if leave is not None:
    sys.exit(leave)
time.sleep(30)
'''
# A script that leaves a subfolder it cannot be read from, and with `pin` a file it cannot unlink.
LEAVER = r'''#!/usr/bin/python3 -I
import os, stat, sys
pin = %r
with open(%r, "w") as fh:
    fh.write(os.getcwd())
os.mkdir("d")
open("d/f", "w").close()
if pin:
    open("pinned", "w").close()
    os.chflags("pinned", stat.UF_IMMUTABLE)
os.chmod("d", 0)
sys.exit(1)
'''


def unpin(folder):
    """The folder a LEAVER with `pin` left, removed by the test itself."""
    import shutil
    for top, dirs, _files in os.walk(folder):
        for d in dirs:
            os.chmod(os.path.join(top, d), 0o700)
    if os.path.lexists(os.path.join(folder, "pinned")):
        os.chflags(os.path.join(folder, "pinned"), 0)
    shutil.rmtree(folder, ignore_errors=True)


class StopTest(RenderHome):
    """Review 1 F1 to F3 and F5: every way out ends the script's group and removes its folder."""

    def put(self, text):
        self.install()
        with open(self.script, "w") as fh:
            fh.write(text)
        os.chmod(self.script, 0o755)

    def pids(self):
        with open(os.path.join(self.side, "pids")) as fh:
            return [int(n) for n in fh.read().split()]

    def test_f1_f5_a_signal_during_a_render(self):
        import signal
        from test_agentik_suite import LAUNCHER
        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            rec = os.path.join(self.side, "rec-%d" % sig)
            self.put(SLEEPER % rec)
            p = subprocess.Popen([str(LAUNCHER), "issue", "new", TOOL, "--ran", "agentik %s doctor" % TOOL,
                                  "--exit", "2", "--output", "err.txt", "--expected", EXPECTED,
                                  "--render"], env=self.env(), cwd=self.work, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, universal_newlines=True,
                                 start_new_session=True)
            end = time.monotonic() + 20
            while not os.path.exists(rec) and time.monotonic() < end:
                time.sleep(0.05)
            time.sleep(0.2)
            with open(rec) as fh:
                pid, cwd = fh.read().split(" ", 1)
            try:
                os.kill(p.pid, sig)
                out, err = p.communicate(timeout=20)
                self.assertEqual(p.returncode, 128 + sig, (sig, err))
                self.assertNotIn("Traceback", err, sig)
                self.assertTrue(gone(lambda: os.kill(int(pid), 0)), "the script outlived %d" % sig)
                self.assertFalse(os.path.exists(cwd), sig)
                lines = [l for l in err.splitlines() if "template stands" in l]
                self.assertEqual(len(lines), 1, err)
                self.assertIn(os.path.basename(self.draft_dir()), lines[0])
                self.assertIn(EXPECTED, self.draft().decode("utf-8"))
            finally:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                except OSError:
                    pass

    def test_f2_the_group_gets_sigterm_then_a_grace(self):
        for leave, code in ((None, "wall"), (1, "exit")):
            for name in ("termed", "kid-termed"):
                if os.path.exists(os.path.join(self.side, name)):
                    os.unlink(os.path.join(self.side, name))
            self.put(TRAPPER % (self.side, leave))
            why = {}
            self.assertIsNone(render.run(self.script, b"d\n", self.env(), wall=1.5, why=why))
            self.assertEqual(why["code"], code)
            _head, away, kid = self.pids()
            try:
                self.assertTrue(gone(lambda: os.kill(kid, 0)), "the group's child stayed")
                self.assertTrue(os.path.exists(os.path.join(self.side, "kid-termed")),
                                "the group's child got no SIGTERM (%s)" % code)
                if leave is None:  # at the wall the script's own trap ends what it put away
                    self.assertTrue(os.path.exists(os.path.join(self.side, "termed")))
                    self.assertTrue(gone(lambda: os.kill(away, 0)), "the away child stayed")
            finally:
                for pid in (kid, away):
                    try:
                        os.kill(pid, 9)
                    except OSError:
                        pass

    def test_f3_a_folder_the_script_shut_is_removed(self):
        rec = os.path.join(self.side, "cwd")
        self.put(LEAVER % (False, rec))
        why = {}
        self.assertIsNone(render.run(self.script, b"d\n", self.env(), why=why))
        with open(rec) as fh:
            cwd = fh.read()
        exists = os.path.exists(cwd)
        if exists:
            unpin(cwd)
        self.assertFalse(exists, "the mode 000 subfolder kept the folder")
        self.assertNotIn("left", why)

    @unittest.skipUnless(hasattr(os, "chflags"), "a user flag that holds a file")
    def test_f3_a_folder_that_stays_is_named(self):
        rec = os.path.join(self.side, "cwd")
        self.put(LEAVER % (True, rec))
        code, out, err = self.new("--render")
        with open(rec) as fh:
            cwd = fh.read()
        try:
            self.assertEqual(code, 0, err)
            self.assertTrue(os.path.exists(cwd))
            lines = [l for l in err.splitlines() if cwd in l]
            self.assertEqual(len(lines), 1, err)
            self.assertNotIn(cwd, out)
        finally:
            unpin(cwd)
        self.assertFalse(os.path.exists(cwd))


class DataTest(unittest.TestCase):
    def test_f4_the_page(self):
        with open(str(ROOT / "docs" / "issue-render.md")) as fh:
            text = fh.read()
        self.assertLessEqual(len(text.splitlines()), 10)
        for fact in ("CLAUDE.md", "environment", "disk"):
            self.assertIn(fact, text)

    def test_r2_the_plugin_is_a_public_tool(self):
        self.assertEqual(sorted(CONF), ["mode", "plugin", "script"])
        self.assertIn(NAME, rp6.PUBLIC["tools"])
        self.assertEqual(CONF["mode"], "technical")
        self.assertTrue(CONF["script"].startswith("scripts/"))

    def test_r1_no_tool_name_in_this_file(self):
        tools = [t for t in rp6.PUBLIC["tools"] if t != "suite"]
        pattern = re.compile(r"\b(?:%s)\b" % "|".join(map(re.escape, tools)), re.I)
        with open(__file__) as fh:
            self.assertIsNone(pattern.search(fh.read()))

    def test_8_hygiene_outside_the_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"HOME": tmp, "PATH": "/usr/bin:/bin",
                   "AGENTIK_HYGIENE_PRIVATE": os.path.join(tmp, "none.tsv")}
            p = subprocess.run([str(ROOT / "scripts" / "hygiene"), "--json", "--repo", str(ROOT)],
                               capture_output=True, text=True, env=env, timeout=60, cwd=str(ROOT))
        got = json.loads(p.stdout)
        self.assertEqual(got["groups"]["sibling"]["outside_lines"], 0, p.stdout)

    def test_find(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"HOME": tmp}
            self.assertIsNone(render.find(env, str(LIB)))
            root = os.path.join(tmp, "inst")
            script = os.path.join(root, CONF["script"])
            os.makedirs(os.path.dirname(script))
            os.makedirs(os.path.join(tmp, ".claude", "plugins"))
            with open(os.path.join(tmp, ".claude", "plugins", "installed_plugins.json"), "w") as fh:
                json.dump({"version": 2, "plugins": {"%s@%s" % (NAME, rp6.PUBLIC["marketplace"]): [
                    {"scope": "user", "version": "1.0.0", "installPath": root}]}}, fh)
            self.assertIsNone(render.find(env, str(LIB)))  # absent
            with open(script, "w") as fh:
                fh.write("#!/bin/sh\n")
            self.assertIsNone(render.find(env, str(LIB)))  # not executable
            os.chmod(script, 0o755)
            self.assertEqual(render.find(env, str(LIB)), script)
            self.assertEqual(render.find({"HOME": "/nonexistent", "CLAUDE_CONFIG_DIR":
                                          os.path.join(tmp, ".claude")}, str(LIB)), script)


if __name__ == "__main__":
    unittest.main()
