"""Row sc14-config-pick: `config --pick` chooses one key from a list through pick.ask and prints
its card (design/23 §4 and 4a.7's first row, R1 to R7).

Each run starts the suite's launcher in a temp HOME under an env of exactly HOME, PATH,
XDG_CACHE_HOME, TERM and LANG, with the made-up tool `loom` (row sc6's fixture, 24 keys, 4
changed), its command wrapped so each argv it is given is logged under HOME. A pty run uses
sc15's `Child`, the pty the child's controlling terminal, and sends a key only once the list
shows, since a key typed ahead is dropped. No test reads the live home or the real terminal."""
import os
import re
import shlex
import subprocess
import sys
import tempfile
import termios
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_sc3_table import LAUNCHER, pty_run  # noqa: E402
from test_sc6_config import ANSI, loom_home  # noqa: E402
from test_sc15_setup_pick import Child, tree  # noqa: E402
from agentik_suite import catalogue  # noqa: E402

ESC, ENTER, CTRL_C = b"\x1b", b"\r", b"\x03"
LISTED = b"Esc cancel"  # the frame's last line: the list shows


def text(data):
    return ANSI.sub("", data.decode("utf-8", "replace") if isinstance(data, bytes) else data).replace("\r", "")


class Pick(unittest.TestCase):
    def setUp(self):
        self._home = tempfile.TemporaryDirectory()
        self.home = os.path.realpath(self._home.name)
        self.env = loom_home(self.home)
        wrapped = os.path.join(self.home, "stubs", "agentik-loom")
        with open(wrapped, "w") as fh:  # each argv logged, so a `change` line that ran would show
            fh.write('#!/bin/sh\necho "$*" >> "$HOME/argv.log"\nexec /usr/bin/python3 -B "%s" "$@"\n'
                     % os.path.join(self.home, "loom.py"))
        self.tty_env = dict(self.env, TERM="xterm-256color", LANG="en_US.UTF-8")

    def tearDown(self):
        self._home.cleanup()

    def pipe(self, *args, **more):
        return subprocess.run([str(LAUNCHER), *args], env=dict(self.env, **more), capture_output=True,
                              cwd=self.home, timeout=60, stdin=subprocess.DEVNULL)

    def drive(self, args, keys, wait_for=LISTED, **more):
        """(exit, stdout, the pty's text, modes before, modes after): `keys` sent once `wait_for`
        shows, after each a pause, stdout a pipe."""
        c = Child(dict(self.tty_env, **more), args, pipe_out=True, exe=LAUNCHER)
        try:
            if keys:
                self.assertTrue(c.until(wait_for), text(c.seen))
            for k in keys:
                c.send(k)
                c.read(0.3)
            code = c.wait()
            return code, c.out, text(c.seen), c.before, termios.tcgetattr(c.master)
        finally:
            c.close()

    def frame(self, args, keys=(), **more):
        """The list's text, once it shows, with `keys` typed; then Esc."""
        c = Child(dict(self.tty_env, **more), args, pipe_out=True, exe=LAUNCHER)
        try:
            self.assertTrue(c.until(LISTED), text(c.seen))
            for k in keys:
                c.send(k)
            c.read(0.5)
            shown = text(c.seen)
            c.send(ESC)
            self.assertEqual(c.wait(), 0)
            return shown
        finally:
            c.close()

    def same_as(self, seen):
        lines = [line for line in seen.splitlines() if line.strip()]
        self.assertTrue(lines and lines[-1].startswith("same as: "), seen)
        return lines[-1][len("same as: "):]

    def test_a1_a_filter_that_leaves_one_key_and_enter_print_its_card(self):
        code, out, seen, _, _ = self.drive(["config", "--pick"], [b"tension", ENTER])
        self.assertEqual(code, 0, seen)
        card = self.pipe("config", "loom.spool.tension")
        self.assertEqual(card.returncode, 0)
        self.assertEqual(out, card.stdout)
        self.assertIn(b"loom.spool.tension = d-spool.tension", out)
        line = self.same_as(seen)
        self.assertTrue(line.endswith("config loom.spool.tension"), line)
        again = subprocess.run(shlex.split(line), env=self.env, capture_output=True, cwd=self.home,
                               timeout=60, stdin=subprocess.DEVNULL)
        self.assertEqual((again.returncode, again.stdout), (0, out))

    def test_a2_esc_and_ctrl_c_print_nothing_and_exit_0(self):
        for keys in ([ESC], [CTRL_C]):
            code, out, seen, before, after = self.drive(["config", "--pick"], keys)
            self.assertEqual((code, out), (0, b""), (keys, seen))
            self.assertNotIn("same as:", seen)
            self.assertEqual(before, after, keys)

    def test_a3_no_list_off_a_terminal_under_json_and_under_ci(self):
        for path in ([], ["loom"], ["loom.ink"], ["spool"]):
            flat = self.pipe("config", *path, "--all")
            for got in (self.pipe("config", *path, "--pick"), self.pipe("config", *path, "--pick", CI="1")):
                self.assertEqual((got.returncode, got.stdout), (0, flat.stdout), path)
                self.assertNotIn(b"\x1b", got.stdout + got.stderr)
            got = self.pipe("config", *path, "--pick", "--json")
            self.assertEqual(got.stdout, self.pipe("config", *path, "--json").stdout, path)
            code, out, seen, _, _ = self.drive(["config", *path, "--pick"], [], CI="1")
            self.assertEqual((code, out), (0, flat.stdout), path)
            self.assertNotIn("Which key?", seen)
            self.assertNotIn(b"\x1b", out)

    def test_a4_a_tool_a_word_and_one_key(self):
        shown = self.frame(["config", "loom", "--pick"])
        self.assertIn("Which key?  24 keys", shown)
        self.assertNotIn("suite.", shown)
        self.assertIn("loom.mode", shown)
        shown = self.frame(["config", "spool", "--pick"])
        self.assertIn("Which key?  4 keys", shown)
        self.assertIn("loom.spool.tension", shown)
        shown = self.frame(["config", "loom.ink", "--pick"])
        self.assertIn("Which key?  4 keys", shown)
        self.assertNotIn("loom.mode", shown)
        bare = self.frame(["config", "--pick"])
        self.assertIn("Which key?  26 keys", bare)
        code, out, seen, _, _ = self.drive(["config", "loom.mode", "--pick"], [])
        self.assertEqual((code, out), (0, self.pipe("config", "loom.mode").stdout))
        self.assertNotIn("Which key?", seen)
        self.assertNotIn("same as:", seen)

    def test_a5_a_row_holds_the_value_the_mark_and_the_summary_and_a_value_finds_it(self):
        shown = self.frame(["config", "loom", "--pick"])
        row = [line for line in shown.splitlines() if "loom.mode " in line][0]
        self.assertRegex(row, r"loom\.mode +fast\* +The mode of the loom\.")
        row = [line for line in shown.splitlines() if "loom.speed " in line][0]
        self.assertRegex(row, r"loom\.speed +d-speed +The speed of the loom\.")
        self.assertNotIn("d-speed*", row)
        code, out, seen, _, _ = self.drive(["config", "--pick"], [b"tight", ENTER])
        self.assertIn("1 of 26 keys", seen)
        self.assertEqual((code, out), (0, self.pipe("config", "loom.weave.twill").stdout))
        self.assertTrue(self.same_as(seen).endswith("config loom.weave.twill"))

    def test_a6_from_a_list_one_line_above_next_on_a_terminal_alone(self):
        lines = [line for line in text(pty_run(LAUNCHER, ["config"], self.tty_env, 80)).splitlines()
                 if line.strip()]
        at = [i for i, line in enumerate(lines) if line.startswith("next: ")]
        self.assertEqual(len(at), 1, lines)
        self.assertTrue(lines[at[0] - 1].startswith("from a list: "), lines)
        self.assertTrue(lines[at[0] - 1].endswith(" config --pick"), lines)
        piped = self.pipe("config")
        self.assertNotIn(b"from a list", piped.stdout + piped.stderr)
        nexts = [line for line in piped.stderr.decode().splitlines() if line.startswith("next: ")]
        self.assertEqual(nexts, [lines[at[0]]])
        ci = text(pty_run(LAUNCHER, ["config"], dict(self.tty_env, CI="1"), 80))
        self.assertNotIn("from a list", ci)

    def test_a7_help_names_the_flag_and_no_path_changes_a_setting(self):
        helped = self.pipe("help", "config").stdout.decode()
        row = [line for line in helped.splitlines() if line.strip().startswith("--pick")]
        self.assertEqual(len(row), 1, helped)
        self.assertIn("exits 0", row[0])
        self.assertIn("Esc prints nothing", row[0])
        self.assertEqual(catalogue.load()["flag.pick"], "Choose the plugins from a list first.")
        before = tree(self.home) - {(p, s) for p, s in tree(self.home) if p == "argv.log"}
        for args, keys in ((["config", "--pick"], [b"mode", ENTER]), (["config", "loom", "--pick"], [ESC]),
                           (["config", "loom", "--pick"], [CTRL_C]), (["config", "--pick"], [])):
            self.drive(args, keys) if keys else self.pipe(*args)
        code, out, _, _, _ = self.drive(["config", "loom", "--pick"], [b"\x04"], AGENTIK_PLAIN="1",
                                        wait_for=b"Which key?")  # the typed form, then the end of input
        self.assertEqual((code, out), (0, b""))
        after = {(p, s) for p, s in tree(self.home) if p != "argv.log"}
        self.assertEqual(after, before)
        with open(os.path.join(self.home, "argv.log")) as fh:
            ran = fh.read().splitlines()
        self.assertTrue(ran)
        self.assertEqual([line for line in ran if not line.startswith("describe ")], [], ran)


if __name__ == "__main__":
    unittest.main()
