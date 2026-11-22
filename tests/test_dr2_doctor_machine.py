"""Packet dr2-doctor-machine: `agentik doctor` judges the machine alone and reads the same from
every folder.

Each run is the plugin's launcher in row sc10's ready home (a temp HOME, steps 1 to 6 ok), with a
stub tool `quill`, a made-up name, whose `doctor --json` puts the folder it was started in into a
warn check's detail and logs each start, with that folder, to a file under the temp folder. The
command runs from four folders outside HOME: (a) a checkout whose records are set, (b) a folder of
no repository, (c) a new empty git repo, (d) a checkout whose records key is broken. No test
starts a real tool's doctor, reads the live home or writes outside its temp folders.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LAUNCHER  # noqa: E402
from test_sc10_doctor_checks import Checks  # noqa: E402
from test_rr2_records import git, quiet_env, repo  # noqa: E402

T = "quill"
ROWS = re.compile(r"^\s+\S+\s+records\s")  # a row of the suite's group named `records`


class Machine(Checks):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.top = os.path.realpath(tmp.name)
        self.log = os.path.join(self.top, "started.log")

    def quill(self, answer=True, describe=None):
        """The stub: each start logs `<folder> <words>`; `doctor --json` (and `checks --json`, a
        named read's words) answers one warn check whose detail is the folder, or with
        answer=False prints no object; plain `doctor` exits 0."""
        check = ('{"schema": "agentik.doctor/1", "ok": true, "tool": "%s", "failed": 0, "warned": 1, '
                 '"checks": [{"name": "where", "status": "warn", "detail": "%%s", "remedy": null}]}' % T)
        body = '#!/bin/sh\nhere=$(pwd -P)\necho "$here $*" >> "%s"\n' % self.log
        if describe is not None:
            body += ('if [ "$1" = describe ]; then\ncat <<\'EOF\'\n%s\nEOF\nexit 0\nfi\n'
                     % json.dumps(describe))
        body += 'if [ "$2" = --json ]; then\n'
        body += ('printf \'%s\\n\' "$here"\n' % check) if answer else 'echo "no object here"\n'
        body += 'exit 0\nfi\nexit 0\n'
        return self.stub("agentik-" + T, body)

    def started(self):
        try:
            with open(self.log) as fh:
                return [l.split(" ", 1) for l in fh.read().splitlines()]
        except FileNotFoundError:
            return []

    def folders(self):
        """The four folders, by letter; each repo is made with no user or system git file."""
        env = quiet_env(self.top)
        a = os.path.join(self.top, "code", "widget")
        repo(env, a)
        os.makedirs(os.path.join(self.top, "hq", "widget"))
        git(env, os.path.join(self.top, "hq"), "init", "-q", "-b", "main")
        git(env, a, "config", "--local", "agentik.records", os.path.join(self.top, "hq", "widget"))
        b = os.path.join(self.top, "loose")
        os.mkdir(b)
        c = os.path.join(self.top, "empty")
        os.mkdir(c)
        git(env, c, "init", "-q", "-b", "main")
        d = os.path.join(self.top, "code2", "gadget")
        repo(env, d)
        git(env, d, "config", "--local", "agentik.records", "relative/gadget")
        return {"a": a, "b": b, "c": c, "d": d}

    def from_folder(self, folder, *args, **more):
        self.work = folder
        return self.doctor(*args, read=False, **more)


class SameFromEveryFolderTest(Machine):
    def test_1_the_object_is_the_same_from_every_folder(self):
        path = self.ready()
        self.quill()
        objs = {}
        for k, folder in self.folders().items():
            code, out, err = self.from_folder(folder, "--json", PATH=path)
            objs[k] = json.loads(out)
            where = [c["detail"] for g in objs[k]["tools"] if g["name"] == T for c in g["checks"]]
            self.assertEqual(where, [self.home], k)
            self.assertEqual([c for g in objs[k]["tools"] for c in g["checks"] if c["name"] == "records"], [], k)
        for k in "bcd":
            self.assertEqual(objs[k], objs["a"], k)

    def test_2_the_screen_is_the_same_from_every_folder(self):
        path = self.ready()
        self.quill()
        screens = {}
        for k, folder in self.folders().items():
            self.work = folder
            code, text = self.run_pty("doctor", cols=80, PATH=path)
            screens[k] = text.replace("\r\n", "\n")
            self.assertFalse([l for l in screens[k].splitlines() if ROWS.match(l)], (k, screens[k]))
        for k in "bcd":
            self.assertEqual(screens[k], screens["a"], k)


class StartsInHomeTest(Machine):
    def test_3_the_second_round_starts_in_the_home(self):
        path = self.ready()
        self.quill(answer=False)
        folder = self.folders()["a"]
        code, out, err = self.from_folder(folder, "--json", PATH=path)
        doctors = [w for w in self.started() if w[1].startswith("doctor")]
        self.assertEqual(doctors, [[self.home, "doctor --json"], [self.home, "doctor"]], out)

    def test_3_a_named_doctor_read_starts_in_the_home(self):
        path = self.ready()
        d = {"schema": "agentik.describe/1", "ok": True, "tool": T, "version": "0.1.0",
             "summary": "A made-up tool.", "repo": "acme/quill", "plugin": "quill@acme-tools",
             "needs": [], "verbs": [], "reads": [{"kind": "doctor", "name": "doctor", "argv": ["checks", "--json"]}]}
        self.quill(describe=d)
        folder = self.folders()["d"]
        code, out, err = self.from_folder(folder, "--json", PATH=path)
        named = [w for w in self.started() if w[1] == "checks --json"]
        self.assertEqual(named, [[self.home, "checks --json"]], self.started())
        obj = json.loads(out)
        self.assertEqual([c["detail"] for g in obj["tools"] if g["name"] == T for c in g["checks"]], [self.home])

    def test_4_no_home_starts_the_tools_in_the_root(self):
        path = self.ready()
        self.quill()
        folder = self.folders()["b"]
        env = self.env(PATH=path)
        for home in (None, "", os.path.join(self.top, "nowhere")):
            run = dict(env)
            if home is None:
                del run["HOME"]
            else:
                run["HOME"] = home
            os.remove(self.log) if os.path.exists(self.log) else None
            p = subprocess.run([str(LAUNCHER), "doctor", "--json"], capture_output=True, text=True,
                               env=run, timeout=60, cwd=folder)
            self.assertIn(p.returncode, (0, 1), p.stderr)
            self.assertNotIn("Traceback", p.stderr)
            obj = json.loads(p.stdout)
            self.assertEqual([c["detail"] for g in obj["tools"] if g["name"] == T for c in g["checks"]], ["/"], home)
            self.assertEqual({w[0] for w in self.started() if w[1].startswith("doctor")}, {"/"}, home)


class RecordsStaysTest(Machine):
    def test_5_records_reads_the_folder_it_stands_in(self):
        """`agentik records` in (a) and (d): what it printed at the pin."""
        f = self.folders()
        code, out, err = self.run_in(f["a"], "records")
        self.assertEqual((code, err), (0, ""))
        rows = out.splitlines()
        self.assertIn("repo: " + f["a"], rows)
        self.assertIn("records: " + os.path.join(self.top, "hq", "widget"), rows)
        self.assertIn("state: out", rows)
        code, out, err = self.run_in(f["d"], "records")
        self.assertEqual((code, err), (0, ""))
        rows = out.splitlines()
        self.assertIn("state: broken", rows)
        self.assertEqual(rows[-1], "why: agentik.records is not an absolute path; agentik.records is relative/gadget")

    def run_in(self, folder, *args):
        self.work = folder
        return self.run_cli(*args)


def where_of(obj):
    return [c["detail"] for g in obj["tools"] if g["name"] == T for c in g["checks"]]


class PathEntryTest(Machine):
    """Review 1's F1: a tool found through a relative or an empty PATH entry is still asked, in the
    home folder, as it was before the row (brief 2 R1)."""

    def test_6_a_relative_path_entry(self):
        path = self.ready()
        w = os.path.join(self.top, "w")
        os.makedirs(os.path.join(w, "bin"))
        os.rename(self.quill(), os.path.join(w, "bin", "agentik-" + T))
        code, out, err = self.from_folder(w, "--json", PATH="bin:" + path)
        self.assertEqual(where_of(json.loads(out)), [self.home], out)
        self.assertEqual([s for s in self.started() if s[1].startswith("doctor")],
                         [[self.home, "doctor --json"]], self.started())

    def test_6_an_empty_path_entry(self):
        path = self.ready()
        w = os.path.join(self.top, "w")
        os.makedirs(w)
        os.rename(self.quill(), os.path.join(w, "agentik-" + T))
        objs = {}
        for shape in (path + ":", ":" + path, path.replace(":", "::", 1)):
            os.remove(self.log) if os.path.exists(self.log) else None
            code, out, err = self.from_folder(w, "--json", PATH=shape)
            objs[shape] = json.loads(out)
            self.assertEqual(where_of(objs[shape]), [self.home], (shape, out))
            self.assertEqual([s for s in self.started() if s[1].startswith("doctor")],
                             [[self.home, "doctor --json"]], (shape, self.started()))
        self.assertEqual(len({json.dumps(o, sort_keys=True) for o in objs.values()}), 1)


class HomeShapeTest(Machine):
    """Review 1's F2: HOME counts only where it is an absolute path to a folder that can be entered;
    else every doctor starts in `/` (brief 2 R2)."""

    def launch(self, folder, home, path):
        os.remove(self.log) if os.path.exists(self.log) else None
        run = dict(self.env(PATH=path), HOME=home)
        p = subprocess.run([str(LAUNCHER), "doctor", "--json"], capture_output=True, text=True,
                           env=run, timeout=60, cwd=folder)
        self.assertIn(p.returncode, (0, 1), (home, p.stderr))
        self.assertNotIn("Traceback", p.stderr, home)
        obj = json.loads(p.stdout)
        self.assertEqual(where_of(obj), ["/"], (home, p.stdout))
        self.assertEqual({s[0] for s in self.started() if s[1].startswith("doctor")}, {"/"}, home)
        return obj

    def test_7_a_relative_home_reads_the_same_from_two_folders(self):
        path = self.ready()
        self.quill()
        x = os.path.join(self.top, "x")
        y = os.path.join(self.top, "y")
        os.makedirs(os.path.join(x, "h"))
        os.makedirs(y)
        self.assertEqual(self.launch(x, "h", path), self.launch(y, "h", path))

    def test_7_a_home_that_is_no_folder_to_enter(self):
        path = self.ready()
        self.quill()
        b = self.folders()["b"]
        afile = os.path.join(self.top, "afile")
        open(afile, "w").close()
        loop = os.path.join(self.top, "loop1")
        os.symlink(os.path.join(self.top, "loop2"), loop)
        os.symlink(loop, os.path.join(self.top, "loop2"))
        shut = os.path.join(self.top, "shut")
        os.mkdir(shut)
        self.launch(b, afile, path)
        self.launch(b, loop, path)
        os.chmod(shut, 0)
        try:
            self.launch(b, shut, path)
        finally:
            os.chmod(shut, 0o755)

    def test_7_an_absolute_home_folder_is_the_start(self):
        from agentik_suite import doctor
        self.assertEqual(doctor.home_folder({"HOME": self.top}), self.top)
        self.assertEqual(doctor.home_folder({"HOME": os.path.basename(self.top)}), "/")


PWD_STUB = '''#!/usr/bin/python3
import json, os, sys
if sys.argv[1:] == ["doctor", "--json"]:
    d = "getcwd=%%s PWD=%%s OLDPWD=%%s" %% (os.getcwd(), os.environ.get("PWD"), os.environ.get("OLDPWD"))
    print(json.dumps({"schema": "agentik.doctor/1", "ok": True, "tool": "%s", "failed": 0, "warned": 1,
                      "checks": [{"name": "where", "status": "warn", "detail": d, "remedy": None}]}))
sys.exit(0)
''' % T


class PwdTest(Machine):
    """Review 1's F3: a doctor started in the home folder sees PWD name it, and no OLDPWD; a job
    given no folder keeps its environment (brief 2 R3)."""

    def test_8_pwd_names_the_home(self):
        path = self.ready()
        self.stub("agentik-" + T, PWD_STUB)
        f = self.folders()
        for k in "ab":
            code, out, err = self.from_folder(f[k], "--json", PATH=path, PWD=f[k], OLDPWD=self.top)
            self.assertEqual(where_of(json.loads(out)),
                             ["getcwd=%s PWD=%s OLDPWD=None" % (self.home, self.home)], k)

    def test_8_run_all_given_no_folder_keeps_the_environment(self):
        from agentik_suite import tools
        env = {"PATH": "/usr/bin:/bin", "PWD": "/elsewhere", "OLDPWD": "/before", "LC_ALL": "C"}

        def seen(**cwd):
            out = tools.run_all([("k", ["/usr/bin/env"])], env, **cwd)["k"][1].decode()
            return {l.split("=", 1)[0]: l.split("=", 1)[1] for l in out.splitlines() if "=" in l}

        self.assertEqual(seen(), env)
        self.assertEqual(seen(cwd=self.top), {"PATH": "/usr/bin:/bin", "PWD": self.top, "LC_ALL": "C"})
        self.assertEqual(env["PWD"], "/elsewhere")

    def test_8_run_all_starts_a_relative_file_in_the_folder_given(self):
        from agentik_suite import tools
        os.makedirs(os.path.join(self.top, "w", "bin"))
        os.makedirs(os.path.join(self.top, "there"))
        self.stub_at(os.path.join(self.top, "w", "bin", "pwd-of"), '#!/bin/sh\npwd -P\n')
        here = os.getcwd()
        os.chdir(os.path.join(self.top, "w"))
        self.addCleanup(os.chdir, here)
        there = os.path.join(self.top, "there")
        got = tools.run_all([("k", ["bin/pwd-of"]), ("d", ["./bin/pwd-of"])], {"PATH": "/usr/bin:/bin"}, cwd=there)
        self.assertEqual({k: v[:2] for k, v in got.items()}, {"k": (0, there.encode() + b"\n"), "d": (0, there.encode() + b"\n")})

    @staticmethod
    def stub_at(path, body):
        with open(path, "w") as fh:
            fh.write(body)
        os.chmod(path, 0o755)


if __name__ == "__main__":
    unittest.main()
