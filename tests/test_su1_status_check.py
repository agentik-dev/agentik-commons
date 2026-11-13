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

    def test_a_run_flag_attached_or_in_a_cluster_reads_missing(self):
        """Review 1's F1: `-c` or `-m` attached to its value or anywhere in a short cluster."""
        for row in ("python3 -mfoo lampd watch", "python3 -cprint(1) lampd watch",
                    "bash -ce lampd watch --every 60", "/bin/sh -lce lampd watch"):
            self.listing(row)
            self.assertEqual(self.check(), (1, LAMP + "\n", ""), row)
        self.declare(beat=False)
        for row in ("/usr/bin/python3 -I -X pycache_prefix=/c /opt/lib/lampd watch",
                    "/usr/bin/python3 -W ignore::DeprecationWarning /opt/bin/lampd watch",
                    "/usr/bin/python3 -Wignore -Xdev /opt/bin/lampd watch",
                    "env A=1 python3 -B /opt/bin/lampd watch"):
            self.listing(row)
            self.assertEqual(self.check(), (0, "", ""), row)

    def test_a_bare_dash_on_the_way_reads_missing(self):
        """R5 amended by review 1's ruling (L2): the program read from stdin is no match."""
        for row in ("python3 - lampd watch", "/bin/sh - lampd watch"):
            self.listing(row)
            self.assertEqual(self.check(), (1, LAMP + "\n", ""), row)

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


class JsonListingAndRecordsTest(StatusHome):
    """R4, R9 and R10: acceptance 7, 8 and 9's card."""

    def obj(self, code, out, err):
        self.assertEqual(len(out.splitlines()), 1)
        return code, json.loads(out)

    def test_a7_json(self):
        self.beat(1793799937, line="looked at 3")
        code, obj = self.obj(*self.check("--json"))
        self.assertEqual(code, 1)
        self.assertEqual(obj, {"schema": "agentik.status/1", "ok": True, "check": True, "watchers": [
            {"name": "lamp", "state": "missing", "pid": None, "since": 1793799937,
             "beat_writer": "watch", "beat_line": None, "start": "lampd watch --every 60"}]})
        self.listing("/opt/bin/lampd watch")
        self.beat(NOW_S - 600)
        code, obj = self.obj(*self.check("--json"))
        self.assertEqual((code, obj["watchers"][0]["state"], obj["watchers"][0]["pid"],
                          obj["watchers"][0]["since"]), (1, "hung", 4242, NOW_S - 600))
        self.beat(NOW_S - 100, line="looked at 3")
        code, obj = self.obj(*self.check("--json"))
        self.assertEqual((code, obj["watchers"][0]["state"], obj["watchers"][0]["beat_line"]),
                         (0, "running", "looked at 3"))
        self.beat(NOW_S - 100, writer="report", line="looked at 3")
        code, obj = self.obj(*self.check("--json"))
        self.assertEqual((code, obj["watchers"][0]["since"], obj["watchers"][0]["beat_line"],
                          obj["watchers"][0]["beat_writer"]), (0, None, None, "report"))

    def test_a8_the_real_listing(self):
        sleeper = subprocess.Popen(["/bin/sleep", "37"])
        self.addCleanup(sleeper.wait)
        self.addCleanup(sleeper.kill)
        self.declare(more="  nap:\n    match: sleep 37\n    start: sleep 37\n")
        started = time.monotonic()
        code, out, err = self.check("--json", ps=False)
        self.assertLess(time.monotonic() - started, 2)
        states = {w["name"]: w["state"] for w in json.loads(out)["watchers"]}
        self.assertEqual((code, states), (1, {"lamp": "missing", "nap": "running"}))

    def test_a8_a_listing_past_the_wall(self):
        pid_file = os.path.join(self.side, "ps.pid")
        stand_in = self.stub("ps", '#!/bin/sh\necho $$ > "%s"\nexec sleep 10\n' % pid_file)
        before = status.PS
        status.PS = stand_in
        self.addCleanup(setattr, status, "PS", before)
        out, err = io.StringIO(), io.StringIO()
        started = time.monotonic()
        code = cli.main(["status", "--check", "--now", NOW], env=self.env(), out=out, err=err)
        self.assertLess(time.monotonic() - started, 2)
        self.assertEqual((code, out.getvalue(), err.getvalue()),
                         (1, "lamp: not checked: ps gave no listing\n", ""))
        with open(pid_file) as fh:
            pid = int(fh.read())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_a9_the_four_summaries(self):
        for key, words in (("match", "The program and the words after it that find the watcher's process."),
                           ("start", "The line that starts the watcher."),
                           ("beat", "The file the watcher writes while it runs."),
                           ("writer", "The name a beat must carry to count as the watcher's own.")):
            code, out, err = self.cfg("config", "suite.watchers.lamp.%s" % key)
            self.assertEqual(code, 0, key)
            self.assertIn(words, out, key)

    def test_each_status_message_is_in_the_catalogue(self):
        messages = catalogue.load(str(CATALOGUE))
        code = (PACKAGE / "status.py").read_text()
        used = set(re.findall(r'"((?:status|hint|err)\.[a-z_.]+)"', code))
        used |= {m + ".since" for m in status.LINE.values()} | set(status.LINE.values())
        for mid in used:
            self.assertIn(mid, messages)
        self.assertEqual(LAUNCHER.name, "agentik-suite")


if __name__ == "__main__":
    unittest.main()
