"""Review 1 of su2-read: each ruled finding behind a test (R1-F1, F2, F3, F4, F6).

The same temp home as tests/test_su2_read.py: a stub `agentik-demo` that answers each read with
a saved copy, a saved listing, a fixed clock. Every process a test starts is a stub that sleeps;
nothing here reads this machine's sessions, gate or runs.
"""
import io
import json
import os
import signal
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LIB  # noqa: E402
from test_su1_status_check import NOW  # noqa: E402
from test_su2_read import FIX, ReadHome, text  # noqa: E402
from agentik_suite import cli, status, status_read  # noqa: E402

LAUNCHER = str(LIB.parent / "bin" / "agentik-suite")


def gone(pid, within=2.0):
    """True once no process has the pid (a killed grandchild is reaped by launchd soon after)."""
    end = time.monotonic() + within
    while True:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return True  # the pid was taken by another account's process: ours is gone
        if time.monotonic() >= end:
            return False
        time.sleep(0.02)


class FixHome(ReadHome):
    def pids(self, path, within=5.0):
        """The stub's pid and its child's, once the stub has written them."""
        end = time.monotonic() + within
        while time.monotonic() < end:
            if os.path.exists(path) and len(text(path).split()) == 2:
                found = [int(p) for p in text(path).split()]
                for pid in found:
                    self.addCleanup(self.kill, pid)
                return found
            time.sleep(0.02)
        self.fail("the stub never wrote its pids")

    @staticmethod
    def kill(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

    def unattended(self, obj):
        self.answer(unattended={"file": self.saved("u.json", obj)})
        got = self.read()
        run = next(r for r in got["runs"]["shown"] if r["by"] == "unattended")
        return got, run, self.source(got, "unattended")


class EveryWayOutTest(FixHome):
    """R1-F1: each started read and its child are ended and reaped before the verb is out."""

    def test_f1_an_interrupt(self):
        self.read()  # the describe cache
        path = os.path.join(self.side, "pids")
        self.answer(gate={"file": os.path.join(FIX, "gate.json"), "sleep": 10, "child": path})
        p = subprocess.Popen([LAUNCHER, "status", "--json", "--now", NOW, "--ps", self.ps],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env(TZ="UTC"),
                             cwd=self.repo)
        self.addCleanup(self.kill, p.pid)
        found = self.pids(path)
        p.send_signal(signal.SIGINT)
        p.communicate(timeout=10)
        self.assertEqual([pid for pid in found if not gone(pid)], [])

    def test_f1_on_part_raises(self):
        self.read()
        for exc in (BrokenPipeError, RuntimeError):
            with self.subTest(exc=exc.__name__):
                path = os.path.join(self.side, "pids-" + exc.__name__)
                self.answer(backlog={"file": os.path.join(FIX, "backlog.json"), "sleep": 0.5},
                            run={"file": os.path.join(FIX, "run-old.json"), "sleep": 10, "child": path})

                def on_part(name, obj):
                    if name == "backlog":
                        raise exc("the reader went away")

                with self.assertRaises(exc):
                    self.compose(text(self.ps), on_part)
                found = self.pids(path, within=0.5)
                self.assertEqual([pid for pid in found if not gone(pid)], [])


class UnattendedKindsTest(FixHome):
    """R1-F2: `row`, `age_s` and the stop reason held to a kind; a string cleaned and bounded."""

    def test_f2_a_value_of_another_kind(self):
        got, run, src = self.unattended({"run": "2026-11-13-1", "rows": {},
                                         "running": {"row": {"x": {"y": [1]}}, "age_s": "forty"},
                                         "stop": None})
        self.assertEqual((run["state"], run["row"], run["age_s"]), ("running", None, None))
        self.assertEqual((src["state"], src["fields"], got["runs"]["state"]),
                         ("changed", ["row", "age_s"], "partial"))

    def test_f2_a_stop_reason(self):
        for stop in ({"reason": {"a": [1]}}, {}):
            with self.subTest(stop=stop):
                got, run, src = self.unattended({"run": "2026-11-13-1", "rows": {}, "running": None,
                                                 "stop": stop})
                self.assertEqual((run["state"], src["state"], src["fields"]),
                                 ("stopped", "changed", ["reason"]))
        got, run, src = self.unattended({"run": "2026-11-13-1", "rows": {}, "running": None,
                                         "stop": {"reason": "budget"}})
        self.assertEqual((run["state"], src["state"], src["fields"]), ("stopped: budget", "ok", None))

    def test_f2_a_string_cleaned_and_bounded(self):
        got, run, src = self.unattended({"run": "2026-11-13-1", "rows": {}, "running": None,
                                         "stop": "x" * 5000 + "\x1b[2J"})
        self.assertTrue(run["state"].startswith("stopped: xxx"))
        self.assertLessEqual(len(run["state"]), len("stopped: ") + status_read.TEXT_MAX)
        self.assertNotIn("\x1b", run["state"])
        got, run, src = self.unattended({"run": "2026-11-13-1", "rows": {}, "stop": None,
                                         "running": {"row": "a\x1b[2J\u009bb" + "y" * 500, "age_s": 3}})
        self.assertEqual((run["row"][:6], run["age_s"], src["state"]), ("a[2Jby", 3, "ok"))
        self.assertLessEqual(len(run["row"]), status_read.TEXT_MAX)


class CleanerTest(FixHome):
    """R1-F3: U+009B and the other C1 controls are dropped with the C0 ones."""

    def test_f3_c1_controls(self):
        self.assertEqual(status_read._first_line(b"\xc2\x9b31mred\xc2\x9d!\n"), "31mred!")
        self.answer(gate={"exit": 3, "err": "\u009b31mred\nmore\n"})
        self.assertEqual(self.source(self.read(), "gate")["stderr"], "31mred")


if __name__ == "__main__":
    unittest.main()
