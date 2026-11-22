"""Row sc9-setup-live: while setup runs a command, stderr holds one line that moves.

Each run is a copy of the plugin's launcher in a temp HOME (ak3-setup's harness, its made-up
plugin `alpha`), on a pty of a set size that is the child's controlling terminal, stdout on a
pipe where a test reads stderr alone; two tests run setup in process with a stand-in plan, on a
pty too. The stub `claude`'s marketplace add prints a line, sleeps and prints another. Nothing here
starts the real `claude`, reads the live home or writes outside its temp folder."""
import fcntl
import io
import os
import re
import select
import shlex
import signal
import struct
import sys
import termios
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import CLAUDE_STUB  # noqa: E402
from test_ak3_setup import LAUNCHER, MARKET, SetupHome, alive, ended  # noqa: E402
import test_ak3_setup as ak3  # noqa: E402  (a module: its tests are not run twice)
import test_ak4a_update as ak4a  # noqa: E402
import test_sm1_setup_ask as sm1  # noqa: E402
from agentik_suite import apply, cli, plan, term  # noqa: E402

SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
CSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
TOKEN = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\r|\n|[^\x1b\r\n]+|\x1b")
BARE_CR = re.compile(r"\r(?!\n)")  # a carriage return the pty's own line ending does not explain
CURSOR = re.compile(r"\x1b\[\?25[hl]")
FIRST, SECOND = "reading the made-up marketplace", "the made-up marketplace is added"
# the stub claude: record the call; marketplace add writes its pid, group and start, prints a
# line, sleeps and prints another; then the plan tests' stub does the rest
SLOW = """#!/usr/bin/python3
import os as _o, sys as _s, time as _t
with open(%(calls)r, "a") as _f:
    _f.write(" ".join(_s.argv[1:]) + "\\n")
if _s.argv[1:4] == ["plugin", "marketplace", "add"]:
    with open(%(pid)r, "w") as _f:
        _f.write("%%d %%d %%f" %% (_o.getpid(), _o.getpgrp(), _t.time()))
    print(%(first)r, flush=True)
    _t.sleep(%(sleep)r)
    print(%(second)r, flush=True)
"""


def read(path):
    """A file's text, the file closed (row sc16 R5.3)."""
    with open(path) as fh:
        return fh.read()


def replay(text):
    """The screen the bytes leave, as lines: a carriage return to column 0, a line feed a new
    line, `ESC[2K` the line cleared, `ESC[K` and `ESC[J` cleared from the cursor, any other
    sequence nothing on screen."""
    lines, row, col = [""], 0, 0
    for tok in TOKEN.findall(text):
        if tok == "\r":
            col = 0
        elif tok == "\n":
            row, col = row + 1, 0
            if row == len(lines):
                lines.append("")
        elif re.fullmatch(r"\x1b\[[0-9]*A", tok):  # the cursor up, as the picker's redraw climbs
            row = max(0, row - int(tok[2:-1] or 1))
        elif tok == "\x1b[2K":
            lines[row] = ""
        elif tok in ("\x1b[K", "\x1b[0K"):
            lines[row] = lines[row][:col]
        elif tok in ("\x1b[J", "\x1b[0J"):
            lines[row] = lines[row][:col]
            del lines[row + 1:]
        elif tok.startswith("\x1b"):
            continue
        else:
            line = lines[row].ljust(col)
            lines[row] = line[:col] + tok + line[col + len(tok):]
            col += len(tok)
    return [l.rstrip() for l in lines]


def frames(text):
    """Each live line drawn, its escape sequences removed: the bytes taken apart at each carriage
    return, the pieces that open on a spinner frame."""
    got = []
    for piece in BARE_CR.split(text):
        shown = CSI.sub("", piece)
        if len(shown) > 2 and shown[2] in SPIN:
            got.append(shown)
    return got


def seconds(frame):
    m = re.search(r"  (\d+) s(  |$)", frame)
    return int(m.group(1)) if m else None


def rows_of(text):
    """The ended rows, (mark as a word, command, result words with the seconds out)."""
    word = {"✓": "ok", "✗": "FAIL"}
    return [(word.get(m, m), c, re.sub(r"^\d+ s", "<n> s", a)) for m, c, a in ended(text)]


class Pty:
    """argv on a pty that is its controlling terminal, at a set size, in `cwd`; stdout on the pty
    or a pipe. Each chunk read is kept with the time it came."""

    def __init__(self, env, argv, cols=80, rows=24, pipe_out=False, cwd=None):
        self.master, self.slave = os.openpty()
        fcntl.ioctl(self.slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        self.before = termios.tcgetattr(self.master)
        self.out_r, out_w = os.pipe() if pipe_out else (None, None)
        self.pid = os.fork()
        if self.pid == 0:
            try:
                os.setsid()
                fcntl.ioctl(self.slave, termios.TIOCSCTTY, 0)
                os.dup2(self.slave, 0)
                os.dup2(out_w if pipe_out else self.slave, 1)
                os.dup2(self.slave, 2)
                if cwd:
                    os.chdir(cwd)
                os.execve(str(argv[0]), [str(a) for a in argv], env)
            finally:
                os._exit(99)
        if pipe_out:
            os.close(out_w)
        self.chunks, self.out, self.status = [], b"", None

    @property
    def seen(self):
        return b"".join(c for _, c in self.chunks)

    @property
    def text(self):
        return self.seen.decode("utf-8", "replace")

    def read(self, wait=0.05):
        while select.select([self.master], [], [], wait)[0]:
            try:
                chunk = os.read(self.master, 65536)
            except OSError:
                break
            if not chunk:
                break
            self.chunks.append((time.time(), chunk))
            wait = 0.01
        while self.out_r is not None and select.select([self.out_r], [], [], 0)[0]:
            chunk = os.read(self.out_r, 65536)
            if not chunk:
                break
            self.out += chunk

    def until(self, test, timeout=30.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self.read()
            if test(self.text):
                return True
            if self.done():
                self.read()
                return test(self.text)
        return False

    def done(self):
        if self.status is None:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                self.status = -os.WTERMSIG(status) if os.WIFSIGNALED(status) else os.WEXITSTATUS(status)
        return self.status is not None

    def wait(self, timeout=60.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end and not self.done():
            self.read()
        self.read(0.1)
        return self.status

    def close(self):
        if not self.done():
            os.kill(self.pid, signal.SIGKILL)
            self.wait(5)
        for fd in (self.master, self.slave, self.out_r):
            if fd is not None:
                os.close(fd)


class Job(Pty):
    """argv as a shell's job on the pty (row sc16 R5.2): a session leader holds the terminal and
    puts argv in a process group of its own in the foreground, so Ctrl-Z stops it (a group with no
    parent in its session, as Pty's, is never stopped). The leader says `S` on `status` when argv
    stops and sends SIGCONT for each byte on `go`; it ends with argv's exit."""

    def __init__(self, env, argv, cols=80, rows=24):
        self.master, self.slave = os.openpty()
        fcntl.ioctl(self.slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        self.before = termios.tcgetattr(self.master)
        self.out_r, out_w = os.pipe()
        self.status_r, status_w = os.pipe()
        go_r, self.go_w = os.pipe()
        self.pid = os.fork()
        if self.pid == 0:
            try:
                os.setsid()
                fcntl.ioctl(self.slave, termios.TIOCSCTTY, 0)
                signal.signal(signal.SIGTTOU, signal.SIG_IGN)
                job = os.fork()
                if job == 0:
                    os.setpgid(0, 0)
                    os.dup2(self.slave, 0)
                    os.dup2(out_w, 1)
                    os.dup2(self.slave, 2)
                    os.execve(str(argv[0]), [str(a) for a in argv], env)
                os.setpgid(job, job)
                os.tcsetpgrp(self.slave, job)
                while True:
                    _, status = os.waitpid(job, os.WUNTRACED)
                    if os.WIFSTOPPED(status):
                        os.write(status_w, b"S")
                        os.read(go_r, 1)
                        os.killpg(job, signal.SIGCONT)
                        continue
                    os._exit(os.WEXITSTATUS(status) if os.WIFEXITED(status) else 99)
            finally:
                os._exit(99)
        for fd in (out_w, status_w, go_r):
            os.close(fd)
        self.chunks, self.out, self.status = [], b"", None

    def stopped(self, timeout=10.0):
        """True once the leader says argv stopped, the pty read meanwhile."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self.read()
            if select.select([self.status_r], [], [], 0.05)[0]:
                return os.read(self.status_r, 1) == b"S"
        return False

    def go(self):
        os.write(self.go_w, b"c")

    def close(self):
        if not self.done():  # a job left stopped by a failed test goes on, and ends with its leader
            try:
                self.go()
            except OSError:
                pass
        Pty.close(self)
        for fd in (self.status_r, self.go_w):
            os.close(fd)


def in_pty(env, run, cols=80, rows=24):
    """`run(err)` in process with stderr a text stream on a pty of a set size, read as it comes:
    (its result, what the pty showed)."""
    master, slave = os.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
    chunks, stop = [], threading.Event()

    def drain():
        while True:
            if select.select([master], [], [], 0.05)[0]:
                try:
                    data = os.read(master, 65536)
                except OSError:
                    break
                if not data:
                    break
                chunks.append(data)
            elif stop.is_set():
                break

    reader = threading.Thread(target=drain)
    reader.start()
    err = open(slave, "w", encoding="utf-8", closefd=False)
    try:
        got = run(err)
        err.flush()
        time.sleep(0.2)
    finally:
        stop.set()
        reader.join(10)
        err.close()
        os.close(slave)
        os.close(master)
    return got, b"".join(chunks).decode("utf-8", "replace")


class Base(SetupHome):
    known, plan_of_one = sm1.AskTest.known, sm1.AskTest.plan_of_one  # helpers only

    def setUp(self):
        SetupHome.setUp(self)
        self.pidfile = os.path.join(self.home, "market.pid")
        self.plan_of_one()  # the marketplace alone is left

    def fresh(self):
        """The marketplace unknown again, so the next run's one command is its add."""
        if os.path.exists(self.known):
            os.remove(self.known)

    def slow(self, sleep=3, first=FIRST, second=SECOND):
        self.stub("claude", SLOW % {"calls": self.calls, "pid": self.pidfile, "first": first,
                                    "second": second, "sleep": sleep} + CLAUDE_STUB % self.template)

    def term_env(self, **more):
        env = dict(self.env(), TERM="xterm-256color", LANG="en_US.UTF-8")
        env.update(more)
        return {k: v for k, v in env.items() if v is not None}

    def setup(self, env, *args, cols=80, pipe_out=True, keys=None):
        """(exit, the pty's text, the Pty) for setup --yes alpha on a pty."""
        c = Pty(env, [LAUNCHER, "setup", "--yes", "alpha", *args], cols=cols, pipe_out=pipe_out)
        self.addCleanup(c.close)
        if keys:
            keys(c)
        code = c.wait()
        return code, c.text, c

    def in_process(self, command, env, cols, wall=None):
        ip = ak3.InProcessTest("run_in_process")
        ip.home, ip.marker = self.home, os.path.join(self.home, "placed")

        def run(err):
            patches = [mock.patch.object(plan, "build", ip.stand_in(command)),
                       mock.patch.object(plan, "known", lambda env, lib: ["alpha"])]
            if wall:
                patches.append(mock.patch.object(apply, "WALL", wall))
            for p in patches:
                p.start()
            try:
                return cli.main(["setup", "--yes", "alpha"], env=env, out=io.StringIO(), err=err)
            finally:
                for p in patches:
                    p.stop()
        return in_pty(env, run, cols)

    def market_rows(self, text):
        """The marketplace's ended row, the terminal's own echo of a Ctrl-C (`^C`, the pin's
        bytes where no live line clears it) taken off the line's start."""
        screen = [re.sub(r"^\^C", "", l) for l in replay(text)]
        return [r for r in rows_of("\n".join(screen)) if r[1] == "claude " + MARKET]


class LiveLine(Base):
    def test_a1_the_live_line_moves_and_leaves_the_ended_row(self):
        """At 80 columns the marketplace's command and its seconds fill the line, so its output
        gives way (R2); at 120 the first output line shows beside them."""
        for cols in (80, 120):
            self.fresh()
            self.slow()
            code, text, c = self.setup(self.term_env(), cols=cols)
            self.assertEqual(code, 0, text)
            started = float(read(self.pidfile).split()[2])
            market = [(at, CSI.sub("", piece)) for at, chunk in c.chunks
                      for piece in BARE_CR.split(chunk.decode("utf-8", "replace"))
                      if "2 marketplace" in piece and CSI.sub("", piece)[2:3] in tuple(SPIN)]
            self.assertTrue(market, text)
            shown = [f for _, f in market]
            self.assertGreaterEqual(len({seconds(f) for f in shown}), 2, shown)  # the seconds move
            if cols == 120:
                self.assertTrue([f for f in shown if FIRST in f], shown)  # the newest output line
                self.assertIn("\x1b[2m" + FIRST, text)  # dim
            self.assertLess(market[0][0] - started, 0.25 + 0.1, market[0])  # drawn at the start
            span = market[-1][0] - market[0][0]
            self.assertLessEqual(len(market), 10 * span + 2, (len(market), span))  # ten a second at most
            screen = replay(text)
            self.assertFalse([l for l in screen if set(l) & set(SPIN)], screen)  # no trace of a live line
            self.assertEqual(self.market_rows(text), [("ok", "claude " + MARKET, "<n> s")], screen)
            self.assertEqual(CURSOR.findall(text)[-1], "\x1b[?25h")

    def test_a2_no_live_line_passes_the_width(self):
        long_out = "progress " + "x" * 150
        for cols in (80, 50):
            self.fresh()
            self.slow(sleep=1.2, first=long_out, second=long_out + " done")
            code, text, _ = self.setup(self.term_env(), cols=cols)
            self.assertEqual(code, 0, text)
            drawn = frames(text)
            self.assertTrue(drawn, text)
            for f in drawn:
                self.assertLessEqual(term.columns(f), cols, (cols, f))
                self.assertIsNotNone(seconds(f), f)  # the seconds always show

    def test_a2_a_command_longer_than_the_window(self):
        stub = self.stub("install-cli-stand-in-" + "long-" * 14,
                         '#!/bin/sh\necho "%s"\nsleep 1.2\necho "%s"\n: > "%s"\n'
                         % ("y" * 150, "z" * 150, os.path.join(self.home, "placed")))
        command = "%s install-cli" % shlex.quote(stub)
        self.assertGreater(len(command), 80)
        for cols in (80, 50):
            if os.path.exists(os.path.join(self.home, "placed")):
                os.remove(os.path.join(self.home, "placed"))
            code, text = self.in_process(command, self.term_env(), cols)
            self.assertEqual(code, 0, text)
            drawn = frames(text)
            self.assertTrue(drawn, text)
            for f in drawn:
                self.assertLessEqual(term.columns(f), cols, (cols, f))
                self.assertIsNotNone(seconds(f), f)
                self.assertIn("…", f)  # the command cut
            self.assertIn(("ok", command, "<n> s"), rows_of("\n".join(replay(text))))

    def test_r2_the_output_gives_way_first_then_the_command(self):
        s = term.Term(env={}, out=io.StringIO(), err=io.StringIO()).err
        cmd = "claude plugin marketplace add agentik-dev/agentik-commons"
        whole = apply.live_text(s, 120, "⠋", 2, "marketplace", cmd, "3 s", "fetching")
        self.assertEqual(whole, "  ⠋ 2 marketplace  %s  3 s  fetching" % cmd)
        no_out = apply.live_text(s, 19 + len(cmd) + 2 + 3 + 3, "⠋", 2, "marketplace", cmd, "3 s", "fetching")
        self.assertEqual(no_out, "  ⠋ 2 marketplace  %s  3 s" % cmd)
        cut = apply.live_text(s, 49, "⠋", 2, "marketplace", cmd, "13 s", "fetching")
        self.assertTrue(cut.endswith("…  13 s"), cut)
        self.assertEqual(term.columns(cut), 49)

    def test_sc16_r5_1_the_label_gives_way_before_the_seconds(self):
        """Under about 26 columns the label is cut and the seconds stay (row sc16 R5.1)."""
        s = term.Term(env={}, out=io.StringIO(), err=io.StringIO()).err
        cmd = "claude plugin marketplace add agentik-dev/agentik-commons"
        for room in (19, 22, 25):
            for took in ("3 s", "13 s", "125 s"):
                line = apply.live_text(s, room, "⠋", 2, "marketplace", cmd, took, "fetching")
                self.assertTrue(line.endswith("  " + took), (room, line))
                self.assertTrue(line.startswith("  ⠋ 2 "), (room, line))
                self.assertLessEqual(term.columns(line), room, (room, line))
        self.slow(sleep=1.2)
        code, text, _ = self.setup(self.term_env(), cols=20)
        self.assertEqual(code, 0, text)
        drawn = frames(text)
        self.assertTrue(drawn, text)
        for f in drawn:
            self.assertLessEqual(term.columns(f), 20, f)
            self.assertRegex(f, r"  \d+ s$")  # every frame ends with the seconds

    def test_r4_no_color_keeps_the_line_without_its_dim(self):
        self.slow(sleep=1.2)
        code, text, _ = self.setup(self.term_env(NO_COLOR="1"), cols=120)
        self.assertEqual(code, 0, text)
        self.assertTrue([f for f in frames(text) if FIRST in f], text)
        self.assertNotIn("\x1b[2m", text)
        self.assertFalse(re.search(r"\x1b\[[0-9;]*m", text), text)


class WhereNothingIsRedrawn(Base):
    def assert_plain(self, err, what):
        self.assertFalse(BARE_CR.search(err), (what, err))
        self.assertNotIn("\x1b", err, what)
        self.assertFalse(set(err) & set(SPIN), what)

    def test_a3_a_pipe_dumb_and_quiet_draw_nothing_and_end_as_the_pin(self):
        self.slow(sleep=1)
        code, text, _ = self.setup(self.term_env())
        self.assertEqual(code, 0, text)
        self.assertTrue(frames(text), text)  # on a terminal the line is drawn
        drawn = rows_of("\n".join(replay(text)))
        self.fresh()
        code, out, err = self.run_cli("setup", "--yes", "alpha")
        self.assertEqual(code, 0, err)
        self.assert_plain(err, "a pipe")
        self.assertEqual(rows_of(err), drawn)
        for env, what in ((self.term_env(TERM="dumb"), "TERM=dumb"), (self.term_env(TERM=None), "no TERM")):
            self.fresh()
            code, text, _ = self.setup(env)
            self.assertEqual(code, 0, text)
            if env.get("TERM"):  # dumb: no colour either; with no TERM the pin's colour stays
                self.assert_plain(text.replace("\r\n", "\n"), what)
            self.assertFalse(BARE_CR.search(text), what)
            self.assertFalse(set(text) & set(SPIN), what)
            self.assertEqual(rows_of(text), drawn, what)
        self.fresh()
        code, text, _ = self.setup(self.term_env(NO_COLOR="1"), "-q")
        self.assertEqual(code, 0, text)
        self.assert_plain(text.replace("\r\n", "\n"), "-q")
        self.assertEqual(rows_of(text), [])

    def test_sc16_r5_4_under_ci_no_live_line(self):
        """CI set: no live line on a pty, as the picker draws no list there; each command is its
        ended row alone, with no carriage return (row sc16 R5.4)."""
        self.slow(sleep=1)
        code, text, _ = self.setup(self.term_env())
        self.assertEqual(code, 0, text)
        drawn = rows_of("\n".join(replay(text)))
        self.fresh()
        code, text, _ = self.setup(self.term_env(CI="1"))
        self.assertEqual(code, 0, text)
        self.assertFalse(BARE_CR.search(text), text)
        self.assertFalse(set(text) & set(SPIN), text)
        self.assertFalse(CURSOR.search(text), text)
        self.assertEqual(rows_of(text), drawn)

    def test_r4_a_stream_that_cannot_encode_the_frames(self):
        class Ascii(io.StringIO):
            encoding = "ascii"

            def isatty(self):
                return True
        cmd = mock.Mock(opts={"json": False})
        cmd.t = term.Term(env={"TERM": "xterm"}, out=io.StringIO(), err=Ascii())
        self.assertFalse(apply.drawn(cmd))
        cmd.t = term.Term(env={"TERM": "xterm"}, out=io.StringIO(), err=type("U", (Ascii,), {"encoding": "utf-8"})())
        self.assertTrue(apply.drawn(cmd))
        cmd.opts = {"json": True}
        self.assertFalse(apply.drawn(cmd))


class Ends(Base):
    def interrupted(self, send):
        """The interrupt while the line shows, then the same with TERM=dumb, the pin's path: the
        closing lines and the stopped row are the same."""
        got = {}
        for what, env in (("live", self.term_env()), ("pin", self.term_env(TERM="dumb"))):
            self.fresh()
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)
            self.slow(sleep=20)
            c = Pty(env, [LAUNCHER, "setup", "--yes", "alpha"], cols=120, pipe_out=True)
            self.addCleanup(c.close)
            if what == "live":
                self.assertTrue(c.until(lambda t: FIRST in "".join(frames(t))), c.text)  # the line shows
            else:
                self.assertTrue(c.until(lambda t: os.path.exists(self.pidfile) and read(self.pidfile)))
                time.sleep(0.3)
            pid, group = [int(v) for v in read(self.pidfile).split()[:2]]
            send(c)
            code = c.wait()
            text = got[what] = c.text
            self.assertEqual(code, 130, text)
            for _ in range(50):
                if not alive(pid):
                    break
                time.sleep(0.1)
            self.assertFalse(alive(pid), "the command still runs")
            with self.assertRaises(ProcessLookupError):  # no pid of its group alive
                os.killpg(group, 0)
            self.assertEqual(termios.tcgetattr(c.master), c.before)  # the modes as before
            self.assertEqual(self.market_rows(text), [("FAIL", "claude " + MARKET, "<n> s, stopped")])
        self.assertEqual(CURSOR.findall(got["live"])[-1], "\x1b[?25h")
        screens = {w: [l for l in replay(t) if l.strip()] for w, t in got.items()}
        self.assertFalse([l for l in screens["live"] if set(l) & set(SPIN)], screens["live"])
        self.assertEqual(screens["live"][-2], "✗  setup stopped at step 2: interrupted")
        self.assertEqual(screens["live"][-2:], screens["pin"][-2:])

    def test_sc16_r5_2_ctrl_z_shows_the_cursor_and_fg_draws_again(self):
        """Ctrl-Z while the line shows: the line cleared and the cursor shown before setup stops;
        after SIGCONT the line is drawn again; the terminal's modes as before in both states."""
        self.slow(sleep=5)
        c = Job(self.term_env(), [LAUNCHER, "setup", "--yes", "alpha"], cols=120)
        self.addCleanup(c.close)
        self.assertTrue(c.until(lambda t: FIRST in "".join(frames(t))), c.text)  # the line shows
        os.write(c.master, b"\x1a")
        self.assertTrue(c.stopped(), c.text)
        time.sleep(0.3)
        c.read()
        held = c.text
        self.assertEqual(CURSOR.findall(held)[-1], "\x1b[?25h", held)  # the cursor shown
        self.assertFalse([l for l in replay(held) if set(l) & set(SPIN)], replay(held))  # cleared
        self.assertEqual(termios.tcgetattr(c.master), c.before)
        c.go()
        self.assertTrue(c.until(lambda t: frames(t[len(held):])), c.text[len(held):])  # drawn again
        self.assertEqual(CURSOR.findall(c.text[len(held):])[0], "\x1b[?25l")  # hidden again
        self.assertEqual(c.wait(), 0, c.text)
        text = c.text
        self.assertEqual(termios.tcgetattr(c.master), c.before)
        self.assertEqual(CURSOR.findall(text)[-1], "\x1b[?25h")
        self.assertFalse([l for l in replay(text) if set(l) & set(SPIN)], replay(text))
        self.assertEqual(self.market_rows(re.sub(r"\^Z", "", text)), [("ok", "claude " + MARKET, "<n> s")])

    def test_a4_ctrl_c_while_the_line_shows(self):
        self.interrupted(lambda c: os.write(c.master, b"\x03"))

    def test_a4_sigterm_while_the_line_shows(self):
        self.interrupted(lambda c: os.kill(c.pid, signal.SIGTERM))

    def test_a5_a_command_past_its_limit(self):
        pidfile = os.path.join(self.home, "slow.pid")
        stub = self.stub("slow", '#!/bin/sh\necho $$ > "%s"\necho still going\nsleep 30 &\nsleep 30\n' % pidfile)
        got = {}
        for env, what in ((self.term_env(), "live"), (self.term_env(TERM="dumb"), "pin")):
            code, text = self.in_process(shlex.quote(stub), env, 80, wall=1)
            self.assertEqual(code, 1, text)
            got[what] = text
            for _ in range(50):
                if not alive(int(read(pidfile))):
                    break
                time.sleep(0.1)
            self.assertFalse(alive(int(read(pidfile))))
        self.assertTrue(frames(got["live"]), got["live"])
        self.assertFalse(frames(got["pin"]))
        self.assertEqual(replay(got["live"]), replay(got["pin"]))  # the row and the closing lines
        self.assertIn(("FAIL", shlex.quote(stub), "stopped after 1 s"), rows_of(got["pin"]))


class Closed(unittest.TestCase):
    def test_sc16_r5_3_no_file_is_left_open(self):
        """No bare `open(...).read()` in this module, which left two pid files open (row sc16 R5.3)."""
        import ast
        with open(__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        bare = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Call)
                and getattr(n.func.value.func, "id", None) == "open"]
        self.assertEqual(bare, [])


class OtherVerbs(Base):
    def test_a6_remove_draws_nothing_on_a_pty(self):  # alpha is installed (plan_of_one)
        c = Pty(self.term_env(), [LAUNCHER, "remove", "--yes", "alpha"], pipe_out=True)
        self.addCleanup(c.close)
        c.wait()
        self.assertTrue([l for l in self.recorded() if l.startswith("plugin uninstall alpha@agentik")],
                        self.recorded())
        self.assertFalse(BARE_CR.search(c.text), c.text)
        self.assertFalse(set(c.text) & set(SPIN))

    def test_a6_update_draws_nothing_on_a_pty(self):
        b = ak4a.Base("setUp")
        b.setUp()
        self.addCleanup(b.doCleanups)
        h = b.two_behind()
        c = Pty(h.env(TERM="xterm-256color", LANG="en_US.UTF-8"), [ak4a.LAUNCHER, "update", "--yes"],
                pipe_out=True, cwd=h.home)
        self.addCleanup(c.close)
        self.assertEqual(c.wait(120), 0, c.text)
        self.assertTrue(h.claude())
        self.assertFalse(BARE_CR.search(c.text), c.text)
        self.assertFalse(set(c.text) & set(SPIN))

    def test_r5_execute_returns_the_pin_s_shape(self):
        stub = self.stub("talk", "#!/bin/sh\necho one\necho\necho '  two  '\nexit 3\n")
        got = apply.execute(shlex.quote(stub), self.env())
        self.assertEqual(got, {"exit": 3, "last": "two", "why": None, "wall": apply.WALL,
                               "tail": ["one", "two"]})

    def test_sc16_l1_the_two_handlers_go_back(self):
        """After a command ends, by its end and by an exception, SIGTSTP's and SIGCONT's handlers
        are what they were before it (row sc16-setup-undo review 1 L1)."""
        class Quiet(apply.Live):  # hold and release as built; nothing drawn
            def draw(self, elapsed, chunks):
                pass

        sigs = (signal.SIGTSTP, signal.SIGCONT)
        for sig in sigs:
            self.addCleanup(signal.signal, sig, signal.getsignal(sig))
        before = {signal.SIGTSTP: lambda *a: None, signal.SIGCONT: signal.SIG_IGN}
        for sig, fn in before.items():
            signal.signal(sig, fn)
        cmd = mock.Mock()
        cmd.t.text.return_value = "step"
        stub = shlex.quote(self.stub("brief", "#!/bin/sh\necho done\n"))
        self.assertEqual(apply.execute(stub, self.env(), Quiet(cmd, {"n": 1}))["exit"], 0)
        self.assertEqual({s: signal.getsignal(s) for s in sigs}, before, "by its end")
        with mock.patch.object(apply, "_read", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                apply.execute(stub, self.env(), Quiet(cmd, {"n": 1}))
        self.assertEqual({s: signal.getsignal(s) for s in sigs}, before, "by an exception")


if __name__ == "__main__":
    unittest.main()
