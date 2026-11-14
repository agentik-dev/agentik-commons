"""The join of su2-read and su2-screen: `status` with no `--json` draws the read as it is read.

The same temp home as tests/test_su2_read.py: a stub `agentik-demo` answering each read with a
saved copy, a saved listing, a fixed clock. The text path runs end to end through the plugin's
launcher, on a pipe and on a pseudo-terminal at 40, 80 and 120 columns; a few cases run in
process. Every process a test starts is a stub; nothing here reads this machine's own state.
"""
import errno
import fcntl
import io
import json
import os
import re
import select
import signal
import struct
import subprocess
import sys
import termios
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LIB  # noqa: E402
from test_su1_status_check import NOW  # noqa: E402
from test_su2_read import FIX, text  # noqa: E402
from test_su2_read_fix import LAUNCHER, FixHome, gone  # noqa: E402
from agentik_suite import catalogue, status_read, status_screen, term  # noqa: E402

SCREEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "su2", "screen")
WORDS = catalogue.load()
LABELS = ("watchers", "sessions", "gate", "backlog", "runs", "sources", "not read")
SLOTS = {"status": "agentik status", "doctor": "agentik doctor", "tool": "agentik"}  # cmd.slots()'s
WHOLE = re.compile(r"^\s*(see: |start it: |and \d+ more: )")


def masked(screen):
    """The screen with the numbers of its `sources` row, which are times, as N."""
    return "\n".join(re.sub(r"\d+(\.\d+)?", "N", line) if " sources " in line else line
                     for line in screen.split("\n"))


class JoinHome(FixHome):
    def screen(self, *more, cwd=None, code=0, env=None):
        """`status` piped, through the launcher: exit, stdout, stderr."""
        args = [LAUNCHER, "status", "--now", NOW, "--ps", self.ps] + list(more)
        p = subprocess.run(args, capture_output=True, text=True, env=env or self.env(TZ="UTC"),
                           timeout=60, cwd=cwd or self.repo)
        self.assertNotIn("Traceback", p.stdout + p.stderr)
        self.assertEqual(p.returncode, code, p.stdout + p.stderr)
        return p.stdout, p.stderr

    def on_tty(self, cols):
        """`status` on a pseudo-terminal `cols` wide, colour off: exit and the lines it drew."""
        master, slave = os.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, cols, 0, 0))
        env = self.env(TZ="UTC", NO_COLOR="1", LC_ALL="en_US.UTF-8")
        p = subprocess.Popen([LAUNCHER, "status", "--now", NOW, "--ps", self.ps], stdin=subprocess.DEVNULL,
                             stdout=slave, stderr=subprocess.PIPE, env=env, cwd=self.repo)
        os.close(slave)
        got = b""
        end = time.monotonic() + 30
        while time.monotonic() < end:
            ready, _, _ = select.select([master], [], [], 0.2)
            if ready:
                try:
                    chunk = os.read(master, 65536)
                except OSError as e:  # EIO once the terminal's last writer is gone
                    if e.errno != errno.EIO:
                        raise
                    chunk = b""
                if not chunk:
                    break
                got += chunk
            elif p.poll() is not None:
                break
        os.close(master)
        err = p.stderr.read().decode()
        p.stderr.close()
        p.wait(timeout=10)
        self.assertNotIn("Traceback", err)
        return p.returncode, got.decode("utf-8").replace("\r\n", "\n").rstrip("\n").split("\n"), err


class TextPathTest(JoinHome):
    """The row's join item 2 and J-2 to J-4: the screen of the saved objects, piped and on a terminal."""

    def test_j2_piped_base_case(self):
        out, err = self.screen()
        self.assertEqual(err, "")
        self.assertEqual(masked(out), masked(text(os.path.join(FIX, "e2e.piped.txt"))))

    def test_j3_no_runner(self):
        self.answer(gate="gate-no-runner.json")
        out, err = self.screen()
        row = next(line for line in out.splitlines() if line.startswith("warn  gate"))
        self.assertTrue(row.startswith("warn  gate      1 queued and no runner alive"), row)
        self.assertEqual(len(err.splitlines()), 1, err)
        self.assertIn("next: agentik demo gate status", err)
        out, err = self.screen("-q")
        self.assertEqual(err, "")

    def test_j4_help_and_the_catalogue(self):
        code, out, err = self.cfg("help", "status")
        self.assertEqual(code, 0, err)
        self.assertIn("usage: %s status [<path>...] [--check] [flags]" % LAUNCHER, out)  # sc2's name
        self.assertNotIn("err.status.check", WORDS)
        self.assertEqual(WORDS["verb.status"],
                         "Show the watchers, sessions, gate, backlog and runs on one screen.")

    def test_terminal_at_40_80_and_120(self):
        piped, _ = self.screen()
        piped = masked(piped).rstrip("\n").split("\n")
        for cols in (40, 80, 120):
            with self.subTest(cols=cols):
                code, lines, err = self.on_tty(cols)
                self.assertEqual((code, err), (0, ""))
                labels = [l for l in LABELS if any(line[3:].startswith(l + " ") for line in lines)]
                self.assertEqual(labels, list(LABELS), lines)
                for line in lines:
                    if not WHOLE.match(line):
                        self.assertLessEqual(len(line), cols, line)
                    self.assertFalse(line.endswith(" "), line)
                if cols == 40:
                    self.assertTrue(any(line.endswith("…") for line in lines), lines)
                if cols == 120:
                    self.assertFalse(any("…" in line for line in lines), lines)
                    self.assertEqual([line[3:] for line in masked("\n".join(lines)).split("\n")],
                                     [line[6:] for line in piped])


class FaultTest(JoinHome):
    """The row's join item 3: the screen words the top-level `fault`, once, with a warn mark."""

    def run_here(self, *args):
        here = os.getcwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, here)
        from agentik_suite import cli
        out, err = io.StringIO(), io.StringIO()
        code = cli.main(list(args), env=self.env(TZ="UTC"), out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def stand_in(self, body):
        from agentik_suite import status
        listing = self.saved("listing.txt", body)
        ps = self.stub("ps-stand-in", '#!/bin/sh\ncat "%s"\n' % listing)
        old = status.PS
        status.PS = ps
        self.addCleanup(setattr, status, "PS", old)
        return ps

    def test_bad_listing_words(self):
        fault = WORDS["status.fault.listing"]
        self.stand_in("garbage one\ngarbage two\n")
        code, out, err = self.run_here("status", "--now", NOW)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.count(fault), 1, out)
        self.assertEqual(out.count(WORDS["status.fault.listing.parts"]), 1, out)
        self.assertTrue(out.startswith("warn  watchers  " + fault + "\n"), out)
        self.assertNotIn("ps gave no listing", out)
        marks = {line.split()[1]: line.split()[0] for line in out.splitlines() if not line.startswith(" ")}
        self.assertEqual([marks[p] for p in ("sessions", "gate", "runs")], ["note"] * 3, out)
        self.assertEqual(marks["backlog"], "ok")

    def test_bad_listing_never_drawn_as_health(self):
        t, out = self.term()
        obj = json.loads(text(os.path.join(SCREEN, "quiet.json")))
        obj["fault"] = "bad_listing"
        status_screen.part(t, obj, "watchers", SLOTS)
        self.assertTrue(out.getvalue().startswith("warn  watchers  " + WORDS["status.fault.listing"]))
        t, out = self.term()
        obj["watchers"], obj["hand"] = [], []
        status_screen.part(t, obj, "watchers", SLOTS)
        self.assertTrue(out.getvalue().startswith("warn  watchers  " + WORDS["status.fault.listing"]),
                        out.getvalue())
        self.assertIn(WORDS["status.watcher.none"], out.getvalue())

    def test_the_fixtures_take_fault_and_fields(self):
        for name in ("quiet", "busy", "broken"):
            obj = json.loads(text(os.path.join(SCREEN, name + ".json")))
            self.assertIn("fault", obj)
            self.assertIsNone(obj["fault"])
            self.assertTrue(all("fields" in s for s in obj["sources"]), name)
        obj = json.loads(text(os.path.join(FIX, "e2e.json")))
        self.assertIsNone(obj["fault"])
        self.assertTrue(all(s["fields"] is None for s in obj["sources"]))

    def test_a_changed_source_leaves_its_fields_to_json(self):
        t, out = self.term()
        obj = json.loads(text(os.path.join(SCREEN, "quiet.json")))
        src = next(s for s in obj["sources"] if s["name"] == "gate")
        src["state"], src["fields"] = "changed", ["runner", "est"]
        obj["gate"]["state"] = "partial"
        status_screen.part(t, obj, "gate", SLOTS)
        self.assertIn("answers in a shape that has changed", out.getvalue())
        self.assertNotIn("runner", out.getvalue())

    def term(self):
        out, err = io.StringIO(), io.StringIO()
        return term.Term(env={"NO_COLOR": "1"}, out=out, err=err), out


class RunsTest(JoinHome):
    """The row's join item 3: `tool` on a gone run; a plain `stopped`."""

    def test_a_gone_run_carries_its_tool(self):
        self.answer(run="run-gone.json")
        obj = self.read()
        self.assertEqual(obj["hand"], [{"part": "runs", "kind": "run_gone", "name": "2026-11-13-2",
                                        "tool": "demo", "remedy": "agentik demo run status"}])
        out, err = self.screen()
        rows = out.splitlines()
        at = next(i for i, line in enumerate(rows) if line.startswith("warn  runs"))
        self.assertEqual(rows[at], "warn  runs      demo 2026-11-13-2: reads running, and its process "
                                   "(pid 4242) is gone")
        self.assertEqual(rows[at + 1].strip(), "see: agentik demo run status")
        self.assertIn("next: agentik demo run status", err)

    def test_a_plain_stopped(self):
        self.answer(unattended={"file": self.saved("u.json", {"run": "2026-11-13-1", "rows": {},
                                                              "running": None, "stop": {}})})
        out, err = self.screen()
        self.assertIn("unattended 2026-11-13-1: stopped\n", out)


class OrderTest(JoinHome):
    """J-5: each part is written as soon as it and every part above it is read."""

    def test_j5_a_slow_read_holds_no_part_above_it(self):
        self.read()  # the describe cache
        self.answer(run={"file": os.path.join(FIX, "run-old.json"), "sleep": 0.8})
        p = subprocess.Popen([LAUNCHER, "status", "--now", NOW, "--ps", self.ps], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=self.env(TZ="UTC"), cwd=self.repo)
        self.addCleanup(self.kill, p.pid)
        at = {}
        for line in iter(p.stdout.readline, b""):
            word = line.decode().split()[1] if not line.startswith(b" ") else None
            if word and word not in at:
                at[word] = time.monotonic()
        p.stdout.close()
        self.assertEqual(p.wait(timeout=10), 0, p.stderr.read())
        p.stderr.close()
        self.assertEqual(list(at)[:5], list(status_read.PARTS))
        self.assertGreaterEqual(at["runs"] - at["backlog"], 0.5)


class WayOutTest(JoinHome):
    """The row's join item 2: a closed pipe or an interrupt while it draws ends every read."""

    def slow_row(self):
        """The table's row with the longest wall, as a stub whose read sleeps 10 s with a child."""
        table = json.loads((LIB / "fallback.json").read_text())
        name, read = max(((n, r) for n, row in table.items() for r in row.get("status") or ()),
                         key=lambda p: p[1].get("wall_s") or 0)
        self.assertGreater(read.get("wall_s") or 0, 2.0)
        answers, _ = self.tool(name)
        path = os.path.join(self.side, "pids")
        self.answer(answers, **{" ".join(read["argv"]): {"file": os.path.join(FIX, "run-old.json"),
                                                         "sleep": 10, "child": path}})
        return path

    def test_a_closed_pipe(self):
        self.read()  # the describe cache
        path = self.slow_row()
        self.answer(crew={"file": os.path.join(FIX, "sessions.json"), "sleep": 0.5})
        start = time.monotonic()
        p = subprocess.Popen([LAUNCHER, "status", "--now", NOW, "--ps", self.ps], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=self.env(TZ="UTC"), cwd=self.repo)
        self.addCleanup(self.kill, p.pid)
        first = p.stdout.readline()
        self.assertTrue(first.startswith(b"ok    watchers"), first)
        found = self.pids(path)
        p.stdout.close()
        err = p.stderr.read().decode()
        p.stderr.close()
        code = p.wait(timeout=10)
        self.assertLess(time.monotonic() - start, 2.0)
        self.assertEqual((code, err), (128 + signal.SIGPIPE, ""))
        self.assertEqual([pid for pid in found if not gone(pid)], [])

    def test_an_interrupt_while_it_draws(self):
        self.read()
        path = self.slow_row()
        self.answer(crew={"file": os.path.join(FIX, "sessions.json"), "sleep": 0.5})

        class Breaks(io.StringIO):
            def write(self, s):
                if "sessions" in s:
                    raise KeyboardInterrupt
                return io.StringIO.write(self, s)

        here = os.getcwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, here)
        from agentik_suite import cli
        out, err = Breaks(), io.StringIO()
        start = time.monotonic()
        code = cli.main(["status", "--now", NOW, "--ps", self.ps], env=self.env(TZ="UTC"), out=out, err=err)
        self.assertLess(time.monotonic() - start, 2.0)
        self.assertEqual((code, err.getvalue()), (130, ""))
        self.assertTrue(out.getvalue().startswith("ok    watchers"))
        found = self.pids(path)
        self.assertEqual([pid for pid in found if not gone(pid)], [])


if __name__ == "__main__":
    unittest.main()
