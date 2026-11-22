"""Row sc15-setup-pick: setup's yes or no is pick.confirm, a selector of two rows resting on no,
and `setup --pick` chooses the plugins through pick.ask.

Each run is a copy of the plugin's launcher in a temp HOME (sm1's harness, with the ak3-setup
stubs and the made-up plugins `alpha` and `beta`), on a pty of a set size that is the child's
controlling terminal, so Ctrl-C is the terminal's own SIGINT. Nothing here starts the real
`claude` or writes outside its temp folder."""
import fcntl
import io
import os
import re
import select
import shlex
import signal
import struct
import subprocess
import sys
import termios
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_ak3_setup import LAUNCHER, SetupHome  # noqa: E402
import test_sm1_setup_ask as sm1  # noqa: E402  (a module: its tests are not run twice)
from agentik_suite import catalogue, plan, term, tools  # noqa: E402

ESC, UP, DOWN, ENTER = b"\x1b", b"\x1b[A", b"\x1b[B", b"\r"
DECLINED = re.compile(r"(?m)^(·|note)  nothing ran(: interrupted)?$")  # a no's note (row sc8 R5)
NEEDS_YES = "nothing ran: there is no terminal to ask on"  # row sc8 R5
CLOSED = re.compile(r"(?m)^(✗|FAIL)  nothing ran: the list was closed$")  # a closed list's refusal
TYPED_MANY = "Run these 5 commands now? y for yes, n or Enter for no."  # the pin's bytes, 205dbce
TYPED_ONE = "Run this 1 command now? y for yes, n or Enter for no."
# the copy's default set, then the rest of its public.json, by name: the list's order (R5)
DEFAULT = plan.default_set(str(LAUNCHER.parent.parent / "lib"))
PUBLIC = tools.public(str(LAUNCHER.parent.parent / "lib"))["tools"]
CSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


screen = sm1.screen


class Child:
    """The launcher on a pty that is its controlling terminal; stdout on the pty or a pipe."""

    def __init__(self, env, args, cols=80, rows=24, pipe_out=False, stdin=None, exe=None):
        self.master, self.slave = os.openpty()
        fcntl.ioctl(self.slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        self.before = termios.tcgetattr(self.master)
        self.out_r, out_w = os.pipe() if pipe_out else (None, None)
        self.pid = os.fork()
        if self.pid == 0:
            try:
                os.setsid()
                fcntl.ioctl(self.slave, termios.TIOCSCTTY, 0)
                os.dup2(self.slave if stdin is None else stdin, 0)
                os.dup2(out_w if pipe_out else self.slave, 1)
                os.dup2(self.slave, 2)
                exe = str(exe or LAUNCHER)
                os.execve(exe, [exe] + list(args), env)
            finally:
                os._exit(99)
        if pipe_out:
            os.close(out_w)
        self.seen, self.out, self.status = b"", b"", None

    def read(self, wait=0.1):
        while select.select([self.master], [], [], wait)[0]:
            try:
                chunk = os.read(self.master, 65536)
            except OSError:
                break
            if not chunk:
                break
            self.seen += chunk
            wait = 0.05
        if self.out_r is not None:
            while select.select([self.out_r], [], [], 0)[0]:
                chunk = os.read(self.out_r, 65536)
                if not chunk:
                    break
                self.out += chunk
        return self.seen

    def until(self, needle, timeout=30.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if needle in self.read():
                return True
            if self.done():
                return needle in self.read()
        return False

    def done(self):
        if self.status is None:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                self.status = -os.WTERMSIG(status) if os.WIFSIGNALED(status) else os.WEXITSTATUS(status)
        return self.status is not None

    def send(self, *keys):
        for k in keys:
            os.write(self.master, k)
            time.sleep(0.1)

    def wait(self, timeout=60.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end and not self.done():
            self.read(0.05)
        self.read(0.1)
        return self.status

    def close(self):
        if not self.done():
            os.kill(self.pid, signal.SIGKILL)
            self.wait(5)
        for fd in (self.master, self.slave, self.out_r):
            if fd is not None:
                os.close(fd)


def tree(home):
    """Every path under HOME with its size, the suite's cache folder left out: any run writes
    its bytecode there, the pin's too."""
    found = set()
    for root, dirs, files in os.walk(home):
        for name in dirs + files:
            path = os.path.join(root, name)
            if os.path.relpath(path, home).split(os.sep)[0] == "cache":
                continue
            found.add((os.path.relpath(path, home), os.path.isdir(path) or os.path.getsize(path)))
    return found


class Base(SetupHome):
    known, plan_of_one, ran = sm1.AskTest.known, sm1.AskTest.plan_of_one, sm1.AskTest.ran  # helpers only

    def term_env(self, **more):
        env = dict(self.env(), TERM="xterm-256color", LANG="en_US.UTF-8")
        env.update(more)
        return {k: v for k, v in env.items() if v is not None}

    def drive(self, args, keys, wait_for=b"now?", cols=80, rows=24, **more):
        """(exit, the pty's text, the modes before and after) for `keys` sent once `wait_for` shows."""
        c = Child(self.term_env(**more), args, cols, rows)
        try:
            self.assertTrue(c.until(wait_for), c.seen)
            time.sleep(0.2)
            c.send(*keys)
            code = c.wait()
            return code, c.seen.decode("utf-8", "replace"), c.before, termios.tcgetattr(c.master)
        finally:
            c.close()

    def question(self, text):
        return [l for l in screen(CSI.sub("", text)) if "now?" in l]


class Selector(Base):
    def test_r1_each_question_is_its_typed_message_s_first_sentence(self):
        t = term.Term(env={"LANG": "en_US.UTF-8"}, out=io.StringIO(), err=io.StringIO(),
                      messages=dict(catalogue.load()))
        for count, ask, typed in ((5, "setup.confirm", "setup.ask"), (1, "setup.confirm.one", "setup.ask.one")):
            first = t.text(typed, count=count).split("?")[0] + "?"
            self.assertEqual(t.text(ask, count=count), first)
        self.assertEqual(t.text("setup.confirm.yes"), "Run them")
        self.assertEqual(t.text("setup.confirm.yes.one"), "Run it")
        self.assertEqual(t.text("setup.confirm.no"), "Don't run anything")

    def test_a1_the_frame_and_enter_alone(self):
        before = tree(self.home)
        code, text, _, _ = self.drive(["setup", "alpha", "beta"], [ENTER], wait_for=b"Esc cancel")
        for line in ("Run these 5 commands now?", "  Run them", "❯ Don't run anything",
                     "↑↓ move  Enter choose  Esc cancel"):
            self.assertIn(line, CSI.sub("", text).replace("\r", ""), text)
        self.assertIn("Run these 5 commands now?  Don't run anything", CSI.sub("", text))
        self.assertEqual((code, self.recorded()), (2, []), text)
        self.assertRegex("\n".join(screen(CSI.sub("", text))), DECLINED)
        self.assertEqual(tree(self.home), before)

    def test_a2_y_and_the_up_arrow_run_the_count_asked(self):
        for plan, args, count in ((self.plan_of_one, ["setup", "alpha"], 1), (None, ["setup", "alpha", "beta"], 5)):
            for keys in ([b"y", ENTER], [UP, ENTER]):
                self.tearDown()
                self.setUp()
                if plan:
                    plan()
                code, text, _, _ = self.drive(args, keys, wait_for=b"Esc cancel")
                self.assertEqual(code, 0, text)
                word = "Run it" if count == 1 else "Run them"
                self.assertIn("%s now?  %s" % ("Run this 1 command" if count == 1 else
                                               "Run these %d commands" % count, word), CSI.sub("", text))
                self.assertEqual(len(self.ran(text)), count, text)

    def test_a3_each_no_runs_nothing_and_keeps_the_modes(self):
        for keys in ([b"n", ENTER], [ESC], [b"\x04"], [b"\x03"]):
            code, text, before, after = self.drive(["setup", "alpha", "beta"], keys, wait_for=b"Esc cancel")
            self.assertEqual((code, self.recorded()), (2, []), (keys, text))
            self.assertRegex("\n".join(screen(CSI.sub("", text))), DECLINED)
            self.assertEqual(before, after, keys)


class Typed(Base):
    def test_a4_the_typed_question_is_the_pin_s(self):
        for more in ({"TERM": "dumb"}, {"cols": 30}, {"AGENTIK_PLAIN": "1"}):
            for answer, yes in ((b"y", True), (b"YES", True), (b"n", False), (b"run", False), (b"", False)):
                self.tearDown()
                self.setUp()
                cols = more.get("cols", 80)
                env = {k: v for k, v in more.items() if k != "cols"}
                code, text, _, _ = self.drive(["setup", "alpha", "beta"], [answer + b"\r"], cols=cols, **env)
                self.assertEqual(self.question(text)[:1], [TYPED_MANY], (more, text))
                self.assertEqual(code, 0 if yes else 2, (more, answer, text))
                self.assertEqual(bool(self.recorded()), yes, (more, answer))
        self.plan_of_one()
        code, text, _, _ = self.drive(["setup", "alpha"], [b"n\r"], TERM="dumb")
        self.assertEqual(self.question(text)[:1], [TYPED_ONE], text)

    def test_a5_yes_closed_and_piped_stdin_and_ci(self):
        for stdin in (subprocess.DEVNULL, None):
            p = subprocess.run([str(LAUNCHER), "setup", "alpha"], stdin=stdin, input=None if stdin else "y\n",
                               capture_output=True, text=True, env=self.env(), timeout=60)
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertIn(NEEDS_YES, p.stderr)
        c = Child(self.term_env(CI="1"), ["setup", "alpha"])
        try:
            code = c.wait()
            text = c.seen.decode("utf-8", "replace")
        finally:
            c.close()
        self.assertEqual((code, self.recorded()), (2, []), text)
        self.assertIn(NEEDS_YES, text)
        self.assertNotIn("now?", text)
        code, out, err = self.run_cli("setup", "--yes", "alpha")  # last: it runs the plan
        self.assertEqual((code, len(self.recorded())), (0, 2), err)


class CiElsewhere(Base):
    """`CI` counts as no terminal on setup's path alone (review 1 F1): remove and update, which
    share `apply._terminal`, ask their question on a pty under `CI=1` as at the pin."""

    def asks(self, verb):
        self.installed("alpha")
        self.place("agentik-alpha", "0.0.1")
        for ci in ("1", None):  # a no each time, so the same HOME serves both
            c = Child(self.term_env(CI=ci, TERM="dumb"), verb)
            try:
                asked = c.until(b"now?", timeout=20)
                if asked:
                    time.sleep(0.3)
                    c.send(b"n\r")
                code = c.wait()
                text = c.seen.decode("utf-8", "replace")
            finally:
                c.close()
            self.assertTrue(asked, (ci, text))
            self.assertEqual((code, self.recorded()), (2, []), text)
            self.assertNotIn(NEEDS_YES, text)

    def test_f1_remove_asks_under_ci_as_at_the_pin(self):
        self.asks(["remove", "alpha"])

    def test_f1_update_asks_under_ci_as_at_the_pin(self):
        self.asks(["update"])

    def test_f1_setup_under_ci_still_asks_nothing(self):
        c = Child(self.term_env(CI="1"), ["setup", "alpha"])
        try:
            code = c.wait()
            text = c.seen.decode("utf-8", "replace")
        finally:
            c.close()
        self.assertEqual((code, self.recorded()), (2, []), text)
        self.assertIn(NEEDS_YES, text)
        self.assertNotIn("now?", text)


class Other(Base):
    def test_a9_the_other_plugins_line(self):
        code, text, _, _ = self.drive(["setup"], [ENTER], wait_for=b"Esc cancel")
        self.assertEqual(code, 2, text)
        lines = screen(CSI.sub("", text))
        at = [i for i, l in enumerate(lines) if l.startswith("other plugins: ")]
        self.assertEqual(len(at), 1, text)
        self.assertTrue(lines[at[0]].endswith("setup --pick"), lines[at[0]])
        # design/23 §5: the no's note, then other plugins:, then next: setup
        self.assertRegex(lines[at[0] - 1], DECLINED)
        self.assertTrue(lines[at[0] + 1].startswith("next: ") and lines[at[0] + 1].endswith(" setup"), text)
        self.assertFalse(lines[at[0]].startswith("next:"))
        code, text, _, _ = self.drive(["setup", "alpha"], [ENTER], wait_for=b"Esc cancel")
        self.assertNotIn("other plugins:", text)
        code, out, err = self.run_cli("setup")
        self.assertEqual(code, 2)
        self.assertNotIn("other plugins:", out + err)


class Pick(Base):
    def pick(self, keys, *more, pipe_out=False):
        c = Child(self.term_env(), ["setup", "--pick"] + list(more), pipe_out=pipe_out)
        try:
            self.assertTrue(c.until(b"Esc cancel"), c.seen)
            time.sleep(0.2)
            c.send(*keys)
            if keys[-1:] == [ENTER] and b"same as:" not in c.seen:
                c.until(b"same as:", timeout=5)
            return c
        except Exception:
            c.close()
            raise

    def test_a6_relay_ticked_is_the_same_as_its_line(self):
        c = self.pick([DOWN] * 5 + [b" ", ENTER], "--dry-run", pipe_out=True)
        try:
            code = c.wait()
            text, out = c.seen.decode("utf-8", "replace"), c.out.decode()
        finally:
            c.close()
        self.assertEqual(code, 0, text)
        same = [l for l in screen(CSI.sub("", text)) if l.startswith("same as: ")]
        self.assertEqual(len(same), 1, text)
        self.assertTrue(same[0].endswith("setup --dry-run %s relay" % " ".join(DEFAULT)), same[0])
        argv = shlex.split(same[0][len("same as: "):])
        p = subprocess.run(argv, capture_output=True, text=True, env=self.env(), timeout=60,
                           stdin=subprocess.DEVNULL)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(out, p.stdout)
        self.assertIn(", ".join(DEFAULT + ["relay"]), out)

    def test_a6_from_the_clone_the_marketplace_s_names_and_notes(self):
        """The clone's own `setup`, so the list is its marketplace file's: relay is the fourth."""
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        c = Child(self.term_env(), ["--pick", "--dry-run"], pipe_out=True, exe=os.path.join(root, "setup"))
        try:
            self.assertTrue(c.until(b"Esc cancel"), c.seen)
            self.assertIn(b"Runs a queue of written tasks", c.seen)
            time.sleep(0.2)
            c.send(DOWN, DOWN, DOWN, b" ", ENTER)
            code = c.wait()
            text, out = CSI.sub("", c.seen.decode("utf-8", "replace")), c.out.decode()
        finally:
            c.close()
        self.assertEqual(code, 0, text)
        same = [l for l in screen(text) if l.startswith("same as: ")]
        self.assertTrue(same and same[0].endswith("/setup --dry-run %s relay" % " ".join(DEFAULT)), text)
        p = subprocess.run(shlex.split(same[0][len("same as: "):]), capture_output=True, text=True,
                           env=self.env(), timeout=60, stdin=subprocess.DEVNULL)
        self.assertEqual((p.returncode, p.stdout), (0, out), p.stderr)

    def test_f2_a_name_setup_does_not_take_is_no_row(self):
        """A copy of the tree whose marketplace file names one plugin more than the suite knows
        (review 1 F2): the list shows no row for it, so no ticked row is refused after it."""
        import json
        import shutil
        import tempfile
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        copy = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, copy, True)
        shutil.copy2(os.path.join(root, "setup"), copy)
        shutil.copytree(os.path.join(root, ".claude-plugin"), os.path.join(copy, ".claude-plugin"))
        shutil.copytree(os.path.join(root, "plugins", "suite"), os.path.join(copy, "plugins", "suite"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        path = os.path.join(copy, ".claude-plugin", "marketplace.json")
        market = json.load(open(path))
        market["plugins"].append({"name": "newtool", "source": "./newtool", "description": "A made-up tool."})
        with open(path, "w") as f:
            json.dump(market, f)
        c = Child(self.term_env(), ["--pick", "--dry-run"], exe=os.path.join(copy, "setup"))
        try:
            self.assertTrue(c.until(b"Esc cancel"), c.seen)
            time.sleep(0.3)
            c.read()
            text = CSI.sub("", c.seen.decode("utf-8", "replace"))
            c.send(ESC)
            self.assertEqual(c.wait(), 2, text)
        finally:
            c.close()
        rows = [r.split("]", 1)[1].split()[0] for r in screen(text) if "[x]" in r or "[ ]" in r]
        self.assertNotIn("newtool", rows, text)
        self.assertNotIn("A made-up tool", text)
        self.assertEqual(rows[:len(DEFAULT)], DEFAULT, text)
        self.assertEqual(rows[-1], "other", text)

    def test_a6_the_options_their_notes_and_installed(self):
        self.installed("alpha")
        c = self.pick([ESC])
        try:
            code = c.wait()
            text = CSI.sub("", c.seen.decode("utf-8", "replace"))
        finally:
            c.close()
        self.assertEqual((code, self.recorded()), (2, []), text)
        self.assertRegex("\n".join(screen(text)), CLOSED)
        self.assertIn("Which plugins does setup install?", text)
        rows = [l for l in screen(text) if "[x]" in l or "[ ]" in l]
        self.assertEqual([r.split("]", 1)[1].split()[0] for r in rows[:8]],
                         DEFAULT + sorted(set(PUBLIC) - set(DEFAULT)) + ["other"], text)
        self.assertIn("installed", [r for r in rows if "alpha" in r][0])

    def test_a7_no_tick_and_a_bad_name_stay(self):
        c = self.pick([b" ", DOWN, b" ", DOWN, b" ", ENTER])
        try:
            self.assertTrue(c.until(b"tick at least one", timeout=5), c.seen)
            self.assertFalse(c.done())
            c.send(*([DOWN] * 5), b"B", b"a", b"d", b" ", b"N", b"a", b"m", b"e", UP, ENTER)
            self.assertTrue(c.until(b"is not a plugin name", timeout=5), c.seen)
            time.sleep(0.3)
            self.assertFalse(c.done())
            c.send(ESC)
            self.assertEqual(c.wait(), 2)
            self.assertEqual(self.recorded(), [])
        finally:
            c.close()

    def test_a8_no_terminal_reads_nothing(self):
        r, w = os.pipe()
        os.write(w, b"session\n")
        p = subprocess.run([str(LAUNCHER), "setup", "--pick"], stdin=r, capture_output=True, text=True,
                           env=self.env(), timeout=60)
        left = os.read(r, 100) if select.select([r], [], [], 0)[0] else b""
        os.close(w)
        os.close(r)
        self.assertEqual(left, b"session\n")
        q = subprocess.run([str(LAUNCHER), "setup"], stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, env=self.env(), timeout=60)
        self.assertEqual((p.returncode, p.stdout, p.stderr), (q.returncode, q.stdout, q.stderr))
        code, out, err = self.run_cli("setup", "--pick", "--yes", "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn(", ".join(DEFAULT), out)
        code, out, err = self.run_cli("status", "--pick")
        self.assertEqual(code, 2)
        self.assertIn("--pick is not a flag of status", err)

    def test_r7_help_setup_names_pick_and_plain(self):
        code, out, err = self.run_cli("help", "setup")
        self.assertEqual(code, 0, err)
        self.assertEqual(len([l for l in out.splitlines() if "--pick" in l]), 1, out)
        self.assertEqual(len([l for l in out.splitlines() if "AGENTIK_PLAIN" in l]), 1, out)


if __name__ == "__main__":
    unittest.main()
