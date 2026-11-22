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


if __name__ == "__main__":
    unittest.main()
