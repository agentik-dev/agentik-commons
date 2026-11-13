"""Packet su2-read: `status --json` reads five sources at once and gives one object.

Each run is the plugin's launcher in su1's StatusHome with TZ=UTC, a fixed clock, a saved
listing under this test's uid, the made-up watcher `lamp`, and a stub `agentik-demo` that answers
`describe --json` and each read with a saved copy under tests/fixtures/su2/read/, recording every
call. A few tests run `compose` in process. Nothing here writes outside its temp folders.
"""
import io
import json
import os
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LIB  # noqa: E402
from test_su1_status_check import NOW, StatusHome  # noqa: E402
from agentik_suite import cli, covers, status, status_read, tools  # noqa: E402

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "su2", "read")
SAVED = {"sessions": "sessions.json", "gate": "gate.json", "backlog": "backlog.json",
         "run": "run-old.json", "unattended": "unattended-none.json"}
# The stand-in tool: a map from an argv prefix to {file, exit, err, sleep, child}.
STUB = """#!/usr/bin/python3
import json, os, subprocess, sys, time
answers, calls = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
with open(calls, "a") as fh:
    fh.write(" ".join(args) + "\\n")
table = json.load(open(answers))
for key in sorted(table, key=len, reverse=True):
    if " ".join(args).startswith(key):
        a = table[key]
        if a.get("child"):
            kid = subprocess.Popen(["/bin/sleep", "10"])
            with open(a["child"], "w") as fh:
                fh.write("%d %d" % (os.getpid(), kid.pid))
        time.sleep(a.get("sleep", 0))
        if a.get("err"):
            sys.stderr.write(a["err"])
        if a.get("file"):
            sys.stdout.write(open(a["file"]).read())
        if a.get("text"):
            sys.stdout.write(a["text"])
        sys.exit(a.get("exit", 0))
sys.exit(2)
"""


def fixture(name):
    with open(os.path.join(FIX, name)) as fh:
        return json.load(fh)


class ReadHome(StatusHome):
    def setUp(self):
        StatusHome.setUp(self)
        self.declare(beat=False)
        self.repo = os.path.join(self.side, "acme-cli")
        os.makedirs(os.path.join(self.repo, ".git"))
        self.stub_py = os.path.join(self.side, "stub.py")
        self.write(self.stub_py, STUB)
        self.tool("demo")
        self.answer(describe="describe.json", crew="sessions.json", gate="gate.json",
                    backlog="backlog.json", run="run-old.json", unattended="unattended-none.json")
        self.ps_rows()

    def tool(self, name, answers=None):
        """A stand-in `agentik-<name>` with its own answers file and call log."""
        answers = answers or os.path.join(self.side, name + ".answers")
        calls = os.path.join(self.side, name + ".calls")
        self.stub("agentik-" + name, '#!/bin/sh\nPYTHONPYCACHEPREFIX="%s" exec /usr/bin/python3 -B "%s" "%s" "%s" "$@"\n'
                  % (os.path.join(self.side, "pyc"), self.stub_py, answers, calls))
        self.write(answers, "{}")
        return answers, calls

    def answer(self, answers=None, **more):
        """Each read by its argv's first word (`describe` is `describe --json`)."""
        path = answers or os.path.join(self.side, "demo.answers")
        table = json.load(open(path))
        for word, a in more.items():
            key = "describe --json" if word == "describe" else word
            if isinstance(a, str):
                a = {"file": os.path.join(FIX, a)}
            table[key] = a
        self.write(path, json.dumps(table))

    def saved(self, name, obj):
        path = os.path.join(self.side, name)
        self.write(path, obj if isinstance(obj, str) else json.dumps(obj))
        return path

    def ps_rows(self, drop=(), more=(), edit=None):
        with open(os.path.join(FIX, "ps.txt")) as fh:
            text = fh.read().replace("{uid}", "%5d" % os.getuid()).replace("{other}", "%5d" % (os.getuid() + 1))
        lines = [l for l in text.splitlines() if not any(l.split()[0] == str(d) for d in drop)]
        lines += ["%5d     1 %5d       01:00 %s" % (p, os.getuid(), c) for p, c in more]
        text = "\n".join(lines) + "\n"
        if edit:
            text = edit(text)
        self.write(self.ps, text)

    def calls(self, name="demo"):
        try:
            with open(os.path.join(self.side, name + ".calls")) as fh:
                return fh.read().splitlines()
        except FileNotFoundError:
            return []

    def read(self, *more, cwd=None, code=0):
        args = ["status", "--json", "--now", NOW, "--ps", self.ps] + list(more)
        p = subprocess.run([str(LIB.parent / "bin" / "agentik-suite"), *args], capture_output=True,
                           text=True, env=self.env(TZ="UTC"), timeout=60, cwd=cwd or self.repo)
        self.assertEqual((p.returncode, p.stderr), (code, ""), p.stdout)
        self.assertNotIn("Traceback", p.stdout)
        obj = json.loads(p.stdout)
        return obj

    def compose(self, ps_text, on_part=None, paths=()):
        out, err = io.StringIO(), io.StringIO()
        cmd = cli.Command(["status", "--json"], self.env(TZ="UTC"), out, err)
        cmd.cwd = self.repo
        return status_read.compose(cmd, list(paths), status.when(NOW), ps_text, on_part)

    def source(self, obj, name):
        return next(s for s in obj["sources"] if s["name"] == name)


class BaseCaseTest(ReadHome):
    def test_1_the_base_case_and_2_the_cache(self):
        before = self.snapshot()
        obj = self.read()
        want = fixture("e2e.json")
        self.assertEqual(obj["covers"]["checkouts"], [self.repo])
        obj["covers"]["checkouts"] = want["covers"]["checkouts"]
        self.assertIsInstance(obj["ms"], int)
        obj["ms"] = want["ms"]
        for s in obj["sources"]:
            if s["ms"] is not None:
                s["ms"] = 100
        self.assertEqual(obj, want)
        calls = self.calls()
        self.assertEqual(calls.count("describe --json"), 1)
        self.assertFalse([c for c in calls if c.startswith("weather")])
        self.assertIn("backlog --json " + self.repo, calls)
        self.read()
        self.assertEqual(self.calls().count("describe --json"), 1)
        self.assertEqual(self.snapshot(), before)


class SessionsTest(ReadHome):
    def test_3_seats_against_the_listing(self):
        self.ps_rows(more=[(5555, "/opt/bin/claude")])
        s = self.read()["sessions"]
        self.assertEqual(s["ended"], 0)
        old = next(x for x in s["live"] if x["name"] == "acme-old")
        self.assertIsNone(old["pid"])
        self.write(self.ps, open(os.path.join(FIX, "ps.txt")).readline())
        s = self.read()["sessions"]
        self.assertEqual((s["live"], s["ended"]), ([], 3))

    def test_3_no_listing_in_process(self):
        ps = self.stub("ps-fails", "#!/bin/sh\nexit 1\n")
        old = status.PS
        status.PS = ps
        self.addCleanup(setattr, status, "PS", old)
        obj = self.compose(None)
        s = obj["sessions"]
        self.assertEqual((s["checked"], len(s["live"]), s["state"]), (False, 3, "partial"))
        self.assertEqual(obj["watchers"][0]["state"], "unknown")
        self.assertEqual([h["kind"] for h in obj["hand"]], ["watcher_unknown"])



class GateTest(ReadHome):
    def test_4_no_runner(self):
        want = {"part": "gate", "kind": "no_runner", "name": None, "remedy": "agentik demo gate status"}
        self.answer(gate="gate-no-runner.json")
        obj = self.read()
        self.assertEqual((obj["gate"]["state"], obj["hand"]), ("hand", [want]))
        self.answer(gate="gate.json")
        self.ps_rows(drop=[9813])
        obj = self.read()
        self.assertEqual((obj["gate"]["state"], obj["hand"], obj["gate"]["runner"]["alive"]),
                         ("hand", [want], False))
        self.answer(gate="gate-empty.json")
        obj = self.read()
        self.assertEqual((obj["gate"]["state"], obj["gate"]["last"], obj["hand"]), ("ok", None, []))


class RunsTest(ReadHome):
    def test_5_runs(self):
        self.answer(run="run-gone.json")
        obj = self.read()
        shown = obj["runs"]["shown"]
        self.assertEqual((len(shown), shown[0]["alive"], shown[0]["rows"]), (1, False, {"green": 1, "running": 1}))
        self.assertEqual(obj["hand"], [{"part": "runs", "kind": "run_gone", "name": "2026-11-13-2",
                                        "remedy": "agentik demo run status"}])
        self.assertEqual(obj["runs"]["state"], "hand")
        self.ps_rows(more=[(4242, "/opt/bin/worker")])
        obj = self.read()
        self.assertEqual((obj["runs"]["shown"][0]["alive"], obj["hand"]), (True, []))
        self.answer(run="run-old.json", unattended="unattended-live.json")
        shown = self.read()["runs"]["shown"]
        self.assertEqual(len(shown), 1)
        self.assertEqual((shown[0]["by"], shown[0]["row"], shown[0]["age_s"], shown[0]["rows"], shown[0]["pid"]),
                         ("unattended", "importer-fix", 40, {"landed": 2, "refused": 1}, None))
        self.answer(run="run-none.json", unattended="unattended-none.json")
        runs = self.read()["runs"]
        self.assertEqual((runs["shown"], runs["aged"]), ([], 0))


class CoversTest(ReadHome):
    def backlog_call(self):
        return [c for c in self.calls() if c.startswith("backlog")][-1].split()

    def test_6_each_rule(self):
        a, b = os.path.join(self.side, "a"), os.path.join(self.side, "b")
        os.makedirs(a), os.makedirs(b)
        obj = self.read(a, b)
        self.assertEqual((obj["covers"]["rule"], obj["covers"]["checkouts"]), ("args", [a, b]))
        self.assertEqual(self.backlog_call()[-2:], [a, b])
        self.write(self.user, open(self.user).read() + "checkouts:\n  - ~/w/one\n")
        obj = self.read()
        self.assertEqual(obj["covers"], {"rule": "checkouts", "hq": None,
                                         "checkouts": [os.path.join(self.home, "w", "one")]})
        self.declare(beat=False)
        hq = os.path.join(self.side, "acme-hq")
        os.makedirs(os.path.join(hq, ".git"))
        self.write(os.path.join(hq, ".claude", "agentik", "config.yaml"), "suite:\n  kind: hq\n")
        self.write(os.path.join(hq, "HANDOFF.md"), "# Handoff\n")
        obj = self.read()
        self.assertEqual(obj["covers"], {"rule": "hq", "hq": hq, "checkouts": [hq, self.repo]})
        call = self.backlog_call()
        self.assertEqual(call[call.index("--order") + 1], os.path.join(hq, "HANDOFF.md"))
        self.assertEqual(call[-2:], [hq, self.repo])
        n = len(self.calls())
        obj = self.read(cwd=self.home)
        self.assertEqual((obj["covers"]["rule"], obj["backlog"]["state"]), ("none", "not read"))
        self.assertNotIn("backlog", [s["name"] for s in obj["sources"]])
        self.assertFalse([c for c in self.calls()[n:] if c.startswith("backlog")])
        p = subprocess.run([str(LIB.parent / "bin" / "agentik-suite"), "status", "nosuchdir", "--json"],
                           capture_output=True, text=True, env=self.env(), cwd=self.home, timeout=60)
        self.assertEqual((p.returncode, json.loads(p.stdout)["error"]["code"]), (2, "bad_path"))

    def test_covers_in_process(self):
        got = covers.covers(self.env(), self.repo, [])
        self.assertEqual(got, {"rule": "cwd", "hq": None, "checkouts": [self.repo]})


class FailingSourceTest(ReadHome):
    def test_7_unreadable(self):
        self.answer(gate={"exit": 3, "err": "\n  the queue is locked\x07\nsecond line\n"})
        obj = self.read()
        g = self.source(obj, "gate")
        self.assertEqual((g["state"], g["exit"], g["stderr"], obj["gate"]["state"]),
                         ("unreadable", 3, "the queue is locked", "not read"))
        self.answer(gate={"text": "[1,"})
        self.assertEqual(self.source(self.read(), "gate")["state"], "unreadable")

    def test_7_timed_out(self):
        self.read()  # the describe cache, so the clock below holds the read alone
        pids = os.path.join(self.side, "pids")
        self.answer(gate={"sleep": 10, "child": pids})
        start = time.monotonic()
        obj = self.read()
        self.assertLess(time.monotonic() - start, 1.6)
        g = self.source(obj, "gate")
        self.assertEqual((g["state"], g["ms"]), ("timed out", 1000))
        time.sleep(0.1)
        for pid in map(int, open(pids).read().split()):
            with self.assertRaises(OSError):
                os.kill(pid, 0)

    def test_7_changed(self):
        sessions = fixture("sessions.json")
        rows = next(v for v in sessions.values() if isinstance(v, list))
        del rows[0]["context"]
        self.answer(crew={"file": self.saved("s.json", sessions)})
        obj = self.read()
        self.assertEqual((self.source(obj, "sessions")["state"], obj["sessions"]["state"]), ("changed", "partial"))
        seat = next(x for x in obj["sessions"]["live"] if x["name"] == "acme-hq")
        self.assertIsNone(seat["context"])
        gate = dict(fixture("gate.json"), schema="x/2")
        self.answer(crew="sessions.json", gate={"file": self.saved("g.json", gate)})
        self.assertEqual(self.source(self.read(), "gate")["state"], "changed")


class TableTest(ReadHome):
    def test_8_the_table(self):
        os.unlink(os.path.join(self.stubs, "agentik-demo"))
        table = json.loads((LIB / "fallback.json").read_text())
        stubs = []
        for name, row in table.items():
            answers, calls = self.tool(name)
            stubs.append(calls)
            for read in row.get("status") or ():
                self.answer(answers, **{" ".join(read["argv"]): SAVED[read["name"]]})
        obj = self.read()
        drawn = [s for s in obj["sources"] if s["state"] != "not drawn"]
        self.assertEqual([s["state"] for s in drawn], ["ok"] * 5)
        for calls in stubs:
            self.assertNotIn("describe --json", open(calls).read() if os.path.exists(calls) else "")
        for name in table:
            os.unlink(os.path.join(self.stubs, "agentik-" + name))
        start = time.monotonic()
        obj = self.read()
        self.assertLess(time.monotonic() - start, 0.5)
        self.assertEqual([s["state"] for s in obj["sources"]], ["not installed"] * 5)
        self.assertEqual([obj[p]["state"] for p in status_read.PARTS[1:]], ["not read"] * 4)


class OnPartTest(ReadHome):
    def test_9_on_part(self):
        seen = []
        self.answer(crew={"file": os.path.join(FIX, "sessions.json"), "sleep": 0.3})
        self.read()  # the cache
        text = open(self.ps).read()
        self.compose(text, lambda name, obj: seen.append((name, time.monotonic(), sorted(obj))))
        self.assertEqual([s[0] for s in seen], list(status_read.PARTS))
        self.assertIn("sessions", seen[1][2])
        self.assertNotIn("gate", seen[1][2])
        seen.clear()
        self.answer(crew="sessions.json", run={"file": os.path.join(FIX, "run-old.json"), "sleep": 0.8})
        self.compose(text, lambda name, obj: seen.append((name, time.monotonic(), sorted(obj))))
        at = dict((s[0], s[1]) for s in seen)
        self.assertGreaterEqual(at["runs"] - at["backlog"], 0.5)


class CheckTest(ReadHome):
    def test_10_a_capital_interpreter(self):
        self.ps_rows(edit=lambda t: t.replace("/opt/bin/lampd watch --every 60",
                                              "/opt/py/Python.app/Contents/MacOS/Python -I /opt/lib/lampd watch"))
        code, out, err = self.cfg("status", "--check", "--ps", self.ps, "--now", NOW, TZ="UTC")
        self.assertEqual((code, out), (0, ""))
        code, out, err = self.cfg("status", "--check", "--json", "--ps", self.ps, "--now", NOW, TZ="UTC")
        w = json.loads(out)["watchers"][0]
        self.assertEqual((w["writer"], w["beat_at"]), (None, None))

    def test_11_a_tab_and_run_all_unchanged(self):
        self.write(self.user, "watchers:\n\tlamp: x\n")
        p = subprocess.run([str(LIB.parent / "bin" / "agentik-suite"), "status", "--json"], capture_output=True,
                           text=True, env=self.env(), cwd=self.repo, timeout=60)
        self.assertEqual(p.returncode, 2)
        self.assertIn("config.yaml", p.stdout)
        got = tools.run_all([("a", ["/bin/sh", "-c", "echo hi; echo no >&2; exit 4"])], self.env(),
                            deadline=time.monotonic() + 2)
        self.assertEqual(got, {"a": (4, b"hi\n", "ran")})
        errs, times = {}, {}
        got = tools.run_all([("a", ["/bin/sh", "-c", "echo hi; echo no >&2; exit 4"]),
                             ("b", ["/bin/sleep", "5"])], self.env(), walls={"a": 1.0, "b": 0.3},
                            errs=errs, times=times)
        self.assertEqual(got, {"a": (4, b"hi\n", "ran"), "b": (None, b"", "timed out")})
        self.assertEqual(errs["a"], b"no\n")
        self.assertLess(times["b"], 0.6)


if __name__ == "__main__":
    unittest.main()
