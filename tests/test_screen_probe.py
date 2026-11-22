"""Row sc0-screen-probe R5: `scripts/screen-probe` is run whole once and holds `go`, and each of
its five checks turns it red on a break.

Every break is made in a temp copy of `plugins/suite`, the probe pointed at it with `--root`; the
worktree's tracked files are never written. The probe runs under a HOME and a TMPDIR of the test's
own, so a run that left a file or a process behind is seen; the probe's interpreter writes no
bytecode cache of its own there (Apple's python3 keeps one under HOME's Library/Caches). Nothing here starts the real `claude`
or reads the live home."""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "screen-probe"
SUITE = ROOT / "plugins" / "suite"
CATALOGUE = Path("plugins") / "suite" / "lib" / "agentik_suite" / "messages.md"


def load():
    """The probe as a module, no bytecode written beside it."""
    loader = SourceFileLoader("screen_probe", str(PROBE))
    module = module_from_spec(spec_from_loader("screen_probe", loader))
    was, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = was
    return module


probe = load()


def files(top):
    out = {}
    for base, dirs, names in os.walk(top):
        for name in names + dirs:
            path = os.path.join(base, name)
            out[path] = os.path.getsize(path) if os.path.isfile(path) else None
    return out


class Copy(unittest.TestCase):
    """A temp copy of the suite, a HOME and a TMPDIR for the probe itself."""

    def setUp(self):
        self.top = os.path.realpath(tempfile.mkdtemp(prefix="sc0-"))
        self.addCleanup(shutil.rmtree, self.top, True)
        self.root = os.path.join(self.top, "root")
        shutil.copytree(str(SUITE), os.path.join(self.root, "plugins", "suite"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        self.home = os.path.join(self.top, "home")
        self.tmp = os.path.join(self.top, "tmp")
        os.mkdir(self.home)
        os.mkdir(self.tmp)

    def edit(self, mid, text):
        """The copy's message `mid` made `text`."""
        path = os.path.join(self.root, str(CATALOGUE))
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        at = [i for i, line in enumerate(lines) if line.startswith("- `%s`: " % mid)]
        self.assertEqual(len(at), 1, mid)
        lines[at[0]] = "- `%s`: %s" % (mid, text)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

    def run_probe(self, *args):
        p = subprocess.run(["/usr/bin/python3", str(PROBE), "--root", self.root, *args],
                           env={"HOME": self.home, "PATH": "/usr/bin:/bin", "TMPDIR": self.tmp,
                                "PYTHONDONTWRITEBYTECODE": "1"},  # the interpreter's own cache
                           cwd=self.top, stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, timeout=300)
        return p.returncode, p.stdout.splitlines(), p.stderr

    def red(self, lines):
        return [line for line in lines if line.startswith("FAIL")]


class Breaks(Copy):
    def test_a1_a_widened_message_is_red_naming_the_screen_and_the_line(self):
        self.edit("help.title", "`{tool}` `{version}`   one command for the agentik tools, "
                                "and here a clause too many for any window")
        code, out, err = self.run_probe("--only", "bare-empty")
        self.assertEqual((code, out[-1]), (1, "screen-probe: stop: 1 failed"), out)
        red = self.red(out)
        self.assertTrue(red[0].startswith("FAIL width: bare-empty "), red)
        self.assertIn("pty80 line 1 (", red[0])

    def test_a2_a_hint_naming_the_suite_through_the_door_is_red(self):
        self.edit("hint.help.done", "next: `{doctor}`, or agentik-suite doctor")
        code, out, err = self.run_probe("--only", "bare-door")
        self.assertEqual(code, 1, out)
        red = self.red(out)
        self.assertEqual(len(red), 1, out)
        self.assertTrue(red[0].startswith("FAIL name: bare-door "), red)
        self.assertIn("agentik-suite doctor", red[0])

    def test_a3_the_word_or_a_code_outside_the_list_is_red_naming_the_id(self):
        self.edit("help.row.doctor", "check this machine; it exits when done")
        self.edit("help.row.status", "the watchers and runs, `{code}` each")
        code, out, err = self.run_probe("--only", "catalogue")
        self.assertEqual(code, 1, out)
        red = self.red(out)
        self.assertEqual(len(red), 1, out)
        self.assertIn("help.row.doctor holds the word or a code", red[0])
        self.assertIn("help.row.status holds the word or a code", red[0])

    def test_a3_an_id_taken_off_the_list_is_red(self):
        text = (ROOT / CATALOGUE).read_text(encoding="utf-8")
        self.assertEqual(probe.check_v9(text), ([], []))  # the pin, as listed
        fewer = dict(probe.V9_LIST)
        del fewer["err.update.step"]
        self.assertEqual(probe.check_v9(text, fewer), (["err.update.step"], []))
        self.assertEqual(sorted(set(probe.V9_LIST.values())), ["flag", "owed"])

    def test_a4_a_screen_past_its_budget_is_red(self):
        self.edit("help.row.status", " ".join(["the watchers, sessions, gate, backlog and runs"] * 4))
        code, out, err = self.run_probe("--only", "bare-empty")
        self.assertEqual(code, 1, out)
        red = self.red(out)
        self.assertEqual(len(red), 1, out)
        self.assertTrue(red[0].startswith("FAIL budget: bare-empty "), red)
        self.assertIn("11 lines, budget 10 (sc5)", red[0])
        self.assertEqual(probe.check_budget("bare-empty", ["a row"] * 10), [])
        self.assertEqual(len(probe.check_budget("bare-empty", ["a row"] * 11)), 1)

    def test_a5_a_command_not_there_and_one_that_waits_are_red(self):
        stubs = os.path.join(self.home, "stubs")
        os.mkdir(stubs)
        os.mkfifo(os.path.join(self.home, "key"))
        waiter = os.path.join(stubs, "agentik-wait")
        with open(waiter, "w") as fh:
            fh.write('#!/bin/sh\nexec cat "$HOME/key"\n')  # waits for a key nobody types
        os.chmod(waiter, 0o755)
        env = {"HOME": self.home, "PATH": "%s:/usr/bin:/bin" % stubs}
        rows = ["Nothing to do.", "next: agentik-nothere setup", "  check  agentik-wait", "next: true"]
        commands = probe.pastes(rows)
        self.assertEqual(commands, ["agentik-nothere setup", "agentik-wait", "true"])
        missing = probe.check_paste(commands[0], env, self.home, 5)
        self.assertEqual(len(missing), 1)
        self.assertIn("exit 127", missing[0])
        start = time.monotonic()
        waits = probe.check_paste(commands[1], env, self.home, 2)
        self.assertLess(time.monotonic() - start, 4)
        self.assertEqual(waits, ["waits: still running at 2 s"])
        self.assertEqual(probe.check_paste(commands[2], env, self.home, 5), [])
        shown = io.StringIO()
        with contextlib.redirect_stdout(shown):
            probe.verdict("paste", "made-up", missing, "paste: made-up: " + commands[0])
        del probe.FAILS[:]
        self.assertTrue(shown.getvalue().startswith("FAIL paste: made-up: agentik-nothere setup"))
        ps = subprocess.run(["ps", "-axo", "command"], capture_output=True, text=True).stdout
        self.assertNotIn(self.home, ps)

    def test_f1_each_home_pastes_its_own_commands(self):
        """Review 1 F1: a `next:` that is there in the applied home and not in the declined one
        is red in the declined one, both screens asked for."""
        apply_py = os.path.join(self.root, "plugins", "suite", "lib", "agentik_suite", "apply.py")
        with open(apply_py, encoding="utf-8") as fh:
            text = fh.read()
        old = 't.hint("hint.setup.next", command=cmd.say("setup"))\n'
        self.assertEqual(text.count(old), 1)
        with open(apply_py, "w", encoding="utf-8") as fh:
            fh.write(text.replace(old, 't.hint("hint.setup.next", command="~/.local/bin/agentik doctor")\n'))
        code, out, err = self.run_probe("--only", "setup-applied,setup-no")
        self.assertEqual(code, 1, out)
        red = self.red(out)
        self.assertTrue(red, out)
        for line in red:
            self.assertTrue(line.startswith("FAIL paste: setup-no, in empty: ~/.local/bin/agentik "
                                            "doctor: not found: exit 127"), red)
        self.assertIn("ok   paste: setup-applied, in empty: ~/.local/bin/agentik doctor", out)

    def test_f2_a_line_redrawn_in_place_is_one_row_of_its_last_text(self):
        """Review 1 F2: the pty's bytes replayed as a terminal draws them, never glued."""
        live = ("  1 market\r\n\x1b[?25l  \u280b 2 marketplace  claude plugin marketplace add x  0 s"
                "\r\x1b[2K  \u2819 2 marketplace  claude plugin marketplace add x  1 s"
                "\r\x1b[2K\x1b[?25h  \u2713 2 marketplace\r\nnext: claude\r\n")
        self.assertEqual(probe.replay(live, 80), ["  1 market", "  \u2713 2 marketplace", "next: claude"])
        self.assertEqual(probe.check_width(probe.replay(live, 50), 50), [])
        self.assertEqual(probe.replay("abcdef\rxy\r\n\x1b[1;31mred\x1b[0m\x1b[K\r\n", 80),
                         ["xycdef", "red"])

    def test_f2_a_frame_its_answer_line_replaces_is_not_counted(self):
        """Review 1 F2: a picker's frame, drawn, redrawn and erased for its closing line."""
        frame = ("\x1b[2K  Run these 8 commands now?\n\x1b[2K    Run them\n"
                 "\x1b[2K  > Don't run anything\n\x1b[2K  up/down move\n\x1b[J")
        text = ("Setup plans 8 steps.\r\n" + "\x1b[?2004h\x1b[?25l\r" + frame
                + "\x1b[4A\r" + frame.replace("> Don't", "  Don't")
                + "\x1b[4A\r\x1b[J\x1b[?2004l\x1b[?25h  Run these 8 commands now?  Don't run anything\n"
                + "nothing ran\r\n")
        rows = probe.replay(text, 80)
        self.assertEqual(rows, ["Setup plans 8 steps.", "  Run these 8 commands now?  Don't run anything",
                                "nothing ran"])
        self.assertEqual(probe.count(rows), 3)
        self.assertEqual(probe.replay("a\nb\nc\x1b[2A\rX\x1b[1BY\n", 80), ["X", "bY", "c"])

    def test_usage(self):
        for args in (["--only", "no-such-screen"], ["--wall"], ["--spare"]):
            code, out, err = self.run_probe(*args)
            self.assertEqual((code, err), (2, probe.USAGE + "\n"), args)


class Whole(Copy):
    def test_a6_a7_go_at_the_pin_twice_and_nothing_left_behind(self):
        before = files(self.root)
        for _ in (1, 2):
            start = time.monotonic()
            code, out, err = self.run_probe()
            took = time.monotonic() - start
            self.assertEqual((code, out[-1]), (0, "screen-probe: go"), "\n".join(out) + err)
            self.assertEqual(self.red(out), [])
            notes = [line for line in out if line.startswith("note known: ")]
            self.assertEqual(len(notes), len(probe.KNOWN), notes)
            for line in out[:-1]:
                self.assertRegex(line, r"^(ok  |FAIL|note) ")
            self.assertEqual(os.listdir(self.tmp), [])
            self.assertEqual(os.listdir(self.home), [])
            self.assertEqual(files(self.root), before)
            ps = subprocess.run(["ps", "-axo", "command"], capture_output=True, text=True).stdout
            self.assertNotIn(self.top, ps)
        print("\nscreen-probe: whole in %.1f s" % took, file=sys.stderr)
        for screen in probe.SCREENS:
            self.assertIn(screen[0], probe.BUDGET)
        self.assertEqual(len(probe.SCREENS), 31)


if __name__ == "__main__":
    unittest.main()
