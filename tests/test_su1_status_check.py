"""Packet su1: `status --check`, each declared watcher that is not running said in one line.

Each run is the plugin's launcher in ak1b's ConfigHome with TZ=UTC, a user file declaring the
made-up watcher `lamp`, a saved listing under this test's own uid, and a fixed clock; one test
runs the command in process, with a stand-in for ps. Nothing here writes outside its temp folders.
"""
import io
import json
import os
import re
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import CATALOGUE, LAUNCHER, PACKAGE, ConfigHome  # noqa: E402
from agentik_suite import catalogue, cli, status  # noqa: E402

NOW = "2026-11-13T12:00:00Z"
NOW_S = 1794571200  # NOW in epoch seconds
HEAD = "  PID  PPID   UID     ELAPSED COMMAND"
LAMP = "lamp: not running; start it: lampd watch --every 60"
LAMP_SINCE = "lamp: not running since 2026-11-04 13:45; start it: lampd watch --every 60"
SILENT = "lamp: running but silent; start it: lampd watch --every 60"
SILENT_SINCE = "lamp: running but silent since 2026-11-13 11:50; start it: lampd watch --every 60"
WATCHER = "  lamp:\n    match: lampd watch\n    start: lampd watch --every 60\n"


class StatusHome(ConfigHome):
    def setUp(self):
        ConfigHome.setUp(self)
        self.beat_file = os.path.join(self.home, "lamp.beat")
        self.ps = os.path.join(self.side, "ps.txt")
        self.declare()
        self.listing()

    def declare(self, beat=True, more=""):
        text = "watchers:\n" + WATCHER
        if beat:
            text += "    beat: ~/lamp.beat\n    writer: watch\n"
        self.write(self.user, text + more)

    def listing(self, *commands):
        """Each command as a row of this uid, or (command, uid)."""
        rows = [HEAD, "    1     0     0  9-00:00:00 /sbin/launchd"]
        for n, c in enumerate(commands):
            c, uid = c if isinstance(c, tuple) else (c, os.getuid())
            rows.append("%5d     1 %5d       01:00 %s" % (4242 + n, uid, c))
        self.write(self.ps, "\n".join(rows) + "\n")

    def beat(self, at, fresh=180, writer="watch", **more):
        obj = dict({"at": at, "fresh_s": fresh}, **more)
        if writer:
            obj["writer"] = writer
        self.write(self.beat_file, json.dumps(obj))

    def check(self, *more, ps=True):
        args = ["status", "--check", "--now", NOW] + (["--ps", self.ps] if ps else []) + list(more)
        code, out, err = self.cfg(*args, TZ="UTC")
        self.assertFalse(os.path.exists(os.path.join(self.cache, "agentik", "suite")))
        self.assertFalse(os.path.exists(self.demo_calls))
        return code, out, err


class MatchAndDeclarationTest(StatusHome):
    """R2 to R5: acceptance 2, 3, 5, 6 and 9."""

    def test_a2_each_row_alone_reads_missing(self):
        for row in ("/bin/sh -c lampd watch", "grep lampd watch", "otherd wait lampd watch",
                    "python3 -c lampd watch", "lampd", "lampd report watch",
                    ("/opt/bin/lampd watch", os.getuid() + 1), "/bin/bash -lc lampd watch"):
            self.listing(row)
            self.assertEqual(self.check(), (1, LAMP + "\n", ""), row)

    def test_a3_each_row_reads_running(self):
        self.declare(beat=False)
        target = os.path.join(self.side, "lampd")
        self.write(target, "")
        link = os.path.join(self.side, "oldlamp")
        os.symlink(target, link)
        for row in ("/opt/bin/lampd watch --every 60", "/opt/py/bin/python3 /opt/bin/lampd watch",
                    "/usr/bin/python3 -I -X pycache_prefix=/c /opt/lib/lampd watch",
                    link + " watch", "/usr/bin/env A=1 python3 -B /opt/bin/lampd watch"):
            self.listing(row)
            self.assertEqual(self.check(), (0, "", ""), row)

    def test_a5_one_line_for_the_one_missing(self):
        self.declare(beat=False, more="  bulb:\n    match: bulbd run\n    start: bulbd run --loud\n")
        self.listing("/opt/bin/lampd watch")
        self.assertEqual(self.check(), (1, "bulb: not running; start it: bulbd run --loud\n", ""))
        self.write(self.user, "checkouts:\n  - /src/alpha\n")
        self.assertEqual(self.check(), (0, "", ""))
        os.remove(self.user)
        self.assertEqual(self.check(), (0, "", ""))

    def test_a6_a_file_outside_the_subset_and_an_unchecked_watcher(self):
        self.write(self.user, "watchers:\n\tlamp: x\n")
        code, out, err = self.check()
        self.assertEqual((code, out, len(err.splitlines())), (2, "", 1))
        self.assertIn("config.yaml", err)
        self.assertIn("line 2", err)
        self.write(self.user, "watchers: lamp\n")
        self.assertEqual(self.check()[:2], (2, ""))
        self.write(self.user, "watchers:\n  lamp: on\n")
        self.assertEqual(self.check()[:2], (2, ""))
        self.declare(beat=False, more="  bulb:\n    match: bulbd run\n")
        self.listing("/opt/bin/lampd watch")
        code, out, err = self.check()
        self.assertEqual((code, out, len(err.splitlines())), (0, "", 1))
        self.assertIn("bulb", err)
        self.assertIn("config.yaml", err)
        self.assertEqual(self.check("-q"), (0, "", ""))

    def test_a9_usage(self):
        code, out, err = self.cfg("status")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("--check", err)
        self.assertEqual(self.cfg("status", "--check", "--now", "soon")[:2], (2, ""))
        self.assertEqual(self.cfg("status", "--check", "--ps", self.ps + ".none")[:2], (2, ""))
        self.assertEqual(self.cfg("status", "--check", "--ps")[:2], (2, ""))
        self.assertEqual(self.cfg("config", "--check")[0], 2)
        self.assertEqual(self.cfg("config", "--now", NOW)[0], 2)
        self.assertEqual(self.cfg("status", "--check", "extra")[0], 2)
        self.assertEqual(self.check("--ps=" + self.ps, ps=False), (1, LAMP + "\n", ""))
        code, out, err = self.cfg()
        self.assertRegex(out, r"(?m)^  status  ")
        code, out, err = self.cfg("status", "--help")
        self.assertIn("--check", out)


class BeatTest(StatusHome):
    """R6 to R8: acceptance 1 and 4."""

    def test_a1_missing_since_its_own_beat(self):
        self.beat(1793799937)
        self.assertEqual(self.check(), (1, LAMP_SINCE + "\n", ""))
        self.beat(1793799937, writer="report")
        self.assertEqual(self.check(), (1, LAMP + "\n", ""))
        self.write(self.beat_file, "not json")
        self.assertEqual(self.check(), (1, LAMP + "\n", ""))
        os.remove(self.beat_file)
        self.assertEqual(self.check(), (1, LAMP + "\n", ""))

    def test_a4_running_and_silent(self):
        self.listing("/opt/bin/lampd watch")
        for writer in ("watch", "report"):
            self.beat(NOW_S - 100, writer=writer)
            self.assertEqual(self.check(), (0, "", ""), writer)
        self.beat(NOW_S - 600)
        self.assertEqual(self.check(), (1, SILENT_SINCE + "\n", ""))
        self.beat(NOW_S - 600, writer="report")
        self.assertEqual(self.check(), (1, SILENT + "\n", ""))
        self.beat(NOW_S + 3600)
        self.assertEqual(self.check(), (0, "", ""))
        for bad in ({"at": "soon", "fresh_s": 1}, {"at": 1}, [1, 2], {"at": 1, "fresh_s": True}):
            self.write(self.beat_file, json.dumps(bad))
            self.assertEqual(self.check(), (0, "", ""), bad)

    def test_the_clock_reads_an_offset_and_local_time(self):
        self.assertEqual(status.when("2026-11-13T13:00:00+01:00"), NOW_S)
        self.assertEqual(status.when("2026-11-13T12:00:00Z"), NOW_S)
        self.assertIsNotNone(status.when("2026-11-13T12:00"))
        self.assertIsNone(status.when("2026-13-13T12:00:00Z"))


if __name__ == "__main__":
    unittest.main()
