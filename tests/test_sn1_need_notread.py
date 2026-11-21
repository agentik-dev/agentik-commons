"""Row sn1-need-notread: setup's plan finds a module where the tool finds it, and `not_read` names
every part not read.

R1: a module need is met when any interpreter of `plan.PYTHONS` imports it, each probe under
NEED_WALL, the walk stopping at the first that imports. R2: `not_read` is every part but `watchers`
whose state is `not read`, and the text screen says a part not read once. R3: with every part read
the screen is the pin's (2d96be7), byte for byte.

The plan's reads run in a temp HOME with stand-in interpreters; the status reads run through su2's
ReadHome and its stand-in `agentik-demo`. Made-up names only; nothing here writes outside its temp
folders."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LIB  # noqa: E402
from test_su1_status_check import NOW  # noqa: E402
from test_su2_read import FIX, ReadHome, describe_of, fixture  # noqa: E402
from test_su2_screen import piped  # noqa: E402
from agentik_suite import plan  # noqa: E402

LOGGED = '#!/bin/sh\necho "$0" >> "%s"\n'
NO_YAML = LOGGED + 'exec /usr/bin/python3 -I "$@"\n'
WITH_YAML = LOGGED + 'PYTHONPATH=%s exec /usr/bin/python3 -s "$@"\n'
HANGS = LOGGED + 'exec sleep 30\n'
# the screen of e2e.json with its rows and owner parts read, drawn piped at the pin 2d96be7
PIN_SCREEN = (
    "ok    watchers  lamp: running\n"
    "ok    sessions  3 live, 3 helpers busy; 1 ended in the last 30 min\n"
    "                acme-hq   295k/1M  99 turns  busy; 2 helpers busy, 1 done\n"
    "                billing   172k/1M  48 turns  waits on 1 helper\n"
    "                44444444                     live; no turn in the last 30 min\n"
    "ok    gate      1 running, 1 queued; last: flight0127 passed\n"
    "                running  acme-api: land importer-fix  14 min of est. 15 min\n"
    "                queued   acme-site                    waits on running 1 of 1\n"
    "                red      netnames                     failed\n"
    "ok    backlog   3 open steps in this checkout, acme-cli\n"
    "                first: 22 The review's builds 5 and 6\n"
    "                items: S3 1, S4 2, 1 not placed\n"
    "                skipped, no build order: acme-notes\n"
    "ok    runs      none since yesterday\n"
    "ok    rows      none in flight\n"
    "ok    owner     0 hand lines in charters; 0 build order rows waiting on the owner\n"
    "      sources   5 read in 0.1 s; the slowest, agentik-demo, took 0.1 s\n"
    "                not installed: agentik-session\n"
    "                not drawn: agentik-demo weather\n")


class NeedHome(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="sn1-")
        self.addCleanup(tmp.cleanup)
        self.home = os.path.realpath(tmp.name)
        self.stubs = os.path.join(self.home, "stubs")
        os.mkdir(self.stubs)
        self.log = os.path.join(self.home, "asked")
        site = os.path.join(self.home, "site")
        os.makedirs(os.path.join(site, "yaml"))
        open(os.path.join(site, "yaml", "__init__.py"), "w").close()
        self.site = site
        self.env = {"HOME": self.home, "PATH": self.stubs}

    def stub(self, path, body):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(body)
        os.chmod(path, 0o755)
        return path

    def later(self, name, body):
        return self.stub(os.path.join(self.home, name, "python3"), body)

    def needs(self, pythons, wall=None):
        """The plan's need rows of respeak with `pythons` as the tuple; the seconds they took."""
        with mock.patch.object(plan, "PYTHONS", pythons, create=True), \
                mock.patch.object(plan, "NEED_WALL", plan.NEED_WALL if wall is None else wall):
            start = time.monotonic()
            steps = plan.build(["respeak"], self.env, str(LIB), "agentik-suite", "0.0.1")
            took = time.monotonic() - start
        return [s for s in steps if s["id"] == "need"], took

    def asked(self):
        try:
            with open(self.log) as fh:
                return fh.read().splitlines()
        except FileNotFoundError:
            return []


class ModuleNeedTest(NeedHome):
    def test_a1_a_later_interpreter_that_imports_meets_the_need(self):
        first = self.stub(os.path.join(self.stubs, "python3"), NO_YAML % self.log)
        later = self.later("later", WITH_YAML % (self.log, self.site))
        rows, _ = self.needs(("python3", later))
        self.assertEqual(rows, [])
        self.assertEqual(self.asked(), [first, later])

    def test_a1_every_interpreter_failing_warns_naming_them(self):
        self.stub(os.path.join(self.stubs, "python3"), NO_YAML % self.log)
        later = self.later("later", NO_YAML % self.log)
        rows, _ = self.needs(("python3", later))
        self.assertEqual([(s["state"], s["subject"], s["mid"]) for s in rows],
                         [("warn", "PyYAML", "setup.need.module")])
        self.assertEqual(rows[0]["values"]["tried"], "python3, " + later)
        from agentik_suite import catalogue
        line = catalogue.load()["setup.need.module"]
        self.assertNotIn("first on PATH", line)
        self.assertIn("{tried}", line)

    def test_a1_one_interpreter_met_twice_is_asked_once(self):
        first = self.stub(os.path.join(self.stubs, "python3"), NO_YAML % self.log)
        rows, _ = self.needs(("python3", first, os.path.join(self.home, "none", "python3")))
        self.assertEqual([s["values"]["tried"] for s in rows], ["python3"])
        self.assertEqual(self.asked(), [first])

    def test_a1_no_interpreter_standing_is_missing(self):
        rows, _ = self.needs(("python3", os.path.join(self.home, "none", "python3")))
        self.assertEqual([(s["subject"], s["mid"]) for s in rows], [("PyYAML", "setup.need.missing")])

    def test_a2_every_interpreter_hanging_is_bounded(self):
        self.stub(os.path.join(self.stubs, "python3"), HANGS % self.log)
        pythons = ("python3",) + tuple(self.later("hang%d" % i, HANGS % self.log) for i in range(2))
        rows, took = self.needs(pythons, wall=0.5)
        self.assertEqual(len(self.asked()), 3)  # each asked once, under its own wall
        self.assertLess(took, 3 * 0.5 + 0.9)
        self.assertEqual([s["mid"] for s in rows], ["setup.need.module"])

    def test_a2_the_tuple_is_respeaks_list(self):
        self.assertEqual(plan.PYTHONS, ("python3", "/usr/bin/python3", "/opt/homebrew/bin/python3",
                                        "/usr/local/bin/python3", "python3.13", "python3.12"))
        self.assertEqual(plan.NEEDS["Go"], ("go", None))  # R3


class NotReadHome(ReadHome):
    def slow_sessions(self):
        """The sessions read under a 0.5 s wall that it never answers in."""
        reads = [dict(r, wall_s=0.5) if r["name"] == "sessions" else r
                 for r in fixture("describe.json")["reads"]]
        path = self.saved("demo-describe.json", dict(fixture("describe.json"), reads=reads))
        self.answer(describe={"file": path})
        self.read()  # the describe cache
        self.answer(crew={"sleep": 10})

    def screen(self):
        p = subprocess.run([str(LIB.parent / "bin" / "agentik-suite"), "status", "--now", NOW, "--ps", self.ps],
                           capture_output=True, text=True, env=self.env(TZ="UTC"), timeout=60, cwd=self.repo)
        self.assertNotIn("Traceback", p.stdout + p.stderr)
        return p.stdout.splitlines()


class NotReadTest(NotReadHome):
    def test_a3_a_sessions_source_timed_out(self):
        self.slow_sessions()
        obj = self.read()
        self.assertEqual((self.source(obj, "sessions")["state"], obj["sessions"]["state"]),
                         ("timed out", "not read"))
        self.assertIn("sessions", obj["not_read"])
        parts = ("sessions", "gate", "backlog", "runs", "rows", "owner")
        self.assertEqual(obj["not_read"], [p for p in parts if obj[p]["state"] == "not read"])
        lines = self.screen()
        said = [l for l in lines if "not read" in l and ("sessions" in l or "agentik-demo gave no answer" in l)]
        self.assertEqual(len(said), 1, lines)
        self.assertTrue(said[0].startswith("note  sessions  not read"), said)
        self.assertFalse([l for l in lines if l[6:].startswith("not read")], lines)

    def test_a4_every_part_read(self):
        obj = json.loads(open(os.path.join(FIX, "e2e.json")).read())
        obj["rows"], obj["owner"] = {"state": "ok", "rows": []}, {"state": "ok", "hands": 0, "steps": 0}
        obj["not_read"] = []
        self.assertEqual(piped(obj), (PIN_SCREEN, ""))
        su2 = json.loads(open(os.path.join(FIX, "..", "screen", "quiet.json")).read())
        self.assertEqual(su2["not_read"], ["owner", "rows"])  # an object of su2's shape: still said
        self.assertTrue(piped(su2)[0].endswith("not read  what waits on the owner, the rows in flight\n"))

    def test_a4_not_read_is_empty_with_every_part_read(self):
        from agentik_suite import status_read
        parts = {p: {"state": "ok"} for p in status_read.PARTS if p != "watchers"}
        self.assertEqual(status_read.not_read(parts), [])
        parts["owner"]["state"] = parts["sessions"]["state"] = "not read"
        self.assertEqual(status_read.not_read(parts), ["sessions", "owner"])


if __name__ == "__main__":
    unittest.main()
