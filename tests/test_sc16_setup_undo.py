"""Row sc16-setup-undo: setup names the way out, `remove --all`, before the yes and after the run.

Each run is sc8's harness: the plugin's launcher in a temp HOME (the ak1a `Home`) with the plan
tests' `claude` stub. A pasted `undo` command runs by `sh -c` in that home, stdin at /dev/null, as
the screen probe pastes it. Nothing here starts the real `claude` or writes outside its temp
folder."""
import os
import re
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LAUNCHER, Home  # noqa: E402
import test_sc8_setup_screens as sc8  # noqa: E402  (a module: its tests are not run twice)

UNDO = re.compile(r"^ +undo +(\S.*)$")


class Undo(Home):
    launcher = LAUNCHER
    setUp, screen, journal, lone = (sc8.Screens.setUp, sc8.Screens.screen, sc8.Screens.journal,
                                    sc8.Screens.lone)

    def undo_rows(self, lines):
        return [m.group(1) for m in map(UNDO.match, lines) if m]

    def kept(self):
        """What a remove would take off: the installed plugins' file and the placed commands."""
        plugins = os.path.join(self.home, ".claude", "plugins", "installed_plugins.json")
        bin_dir = os.path.join(self.home, ".local", "bin")
        text = None
        if os.path.exists(plugins):
            with open(plugins) as fh:
                text = fh.read()
        return text, sorted(os.listdir(bin_dir)) if os.path.isdir(bin_dir) else None

    def pasted(self, command):
        """The command pasted as the screen printed it, in the screen's home: (exit, seconds)."""
        p = subprocess.run(["/bin/sh", "-c", command], env=self.env(), cwd=self.work,
                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=20)
        return p.returncode, p.stdout.decode("utf-8", "replace")

    # ---- acceptance 1: the plan -----------------------------------------------------------
    def test_1_the_plan_ends_on_undo_in_the_typed_form(self):
        code, out, err = self.screen("setup", "--dry-run")
        self.assertEqual(code, 0, out + err)
        yours = out[out.index("Yours, after:") + 1:]
        self.assertTrue(UNDO.match(yours[-1]), yours)
        self.assertEqual(self.undo_rows(out), ["%s remove --all" % LAUNCHER], out)
        self.assertTrue(re.match(r" +7 doctor +", yours[-2]), yours)  # after step 7's row
        lone = sum(1 for l in out if self.lone(l, 80))
        self.assertEqual(len(out), 14 + lone, out)

    # ---- acceptance 2: the report ---------------------------------------------------------
    def test_2_the_report_holds_undo_after_check_in_the_placed_form(self):
        code, out, err = self.screen("setup", "--yes")
        self.assertEqual(code, 0, err)
        tail = out[[i for i, l in enumerate(out) if l.startswith("Steps 2 to 5 are done")][0]:]
        at = [i for i, l in enumerate(tail) if l.startswith("  check ")]
        self.assertEqual(len(at), 1, tail)
        self.assertEqual(tail[at[0] + 1], "  undo   ~/.local/bin/agentik remove --all", tail)
        on = "%s:%s:/usr/bin:/bin" % (os.path.join(self.home, ".local", "bin"), self.stubs)
        code, out, err = self.screen("setup", "--yes", PATH=on)
        self.assertEqual(code, 0, err)
        self.assertIn("  undo   agentik remove --all", out)

    # ---- acceptance 3: it runs as printed and takes nothing off ---------------------------
    def test_3_each_undo_pasted_exits_and_takes_nothing_off(self):
        code, out, err = self.screen("setup", "--dry-run")
        before = self.kept()
        for command in self.undo_rows(out):
            got, said = self.pasted(command)
            self.assertNotEqual(got, 127, said)
            self.assertEqual(self.kept(), before, said)
        code, out, err = self.screen("setup", "--yes")
        self.assertEqual(code, 0, err)
        before = self.kept()
        self.assertTrue(before[0] and before[1], before)
        commands = self.undo_rows(out[[i for i, l in enumerate(out) if l.startswith("Steps 2 to 5")][0]:])
        self.assertEqual(len(commands), 1, out)
        for command in commands:
            got, said = self.pasted(command)
            self.assertNotEqual(got, 127, said)
            self.assertEqual(self.kept(), before, said)

    # ---- acceptance 4 and R1: which screens hold the row ----------------------------------
    def test_4_a_blocked_plan_prints_no_undo(self):
        os.remove(os.path.join(self.stubs, "claude"))
        for args in (("setup", "--yes"), ("setup",), ("setup", "--dry-run")):
            code, out, err = self.screen(*args)
            self.assertIn("Yours, after:", out)
            self.assertEqual(self.undo_rows(out + err), [], out + err)

    def test_r1_a_second_run_and_a_failed_run(self):
        self.screen("setup", "--yes")
        code, out, err = self.screen("setup", "--yes")  # nothing to do: the report's tail holds it
        self.assertEqual(code, 0, err)
        self.assertEqual(self.undo_rows(out), ["~/.local/bin/agentik remove --all"], out)
        shutil.rmtree(os.path.join(self.home, ".claude"))
        shutil.rmtree(os.path.join(self.home, ".local"))
        open(self.flag, "w").close()
        code, out, err = self.screen("setup", "--yes")  # the plan holds it; a failed report does not
        self.assertEqual(code, 1, err)
        self.assertEqual(self.undo_rows(out + err), ["%s remove --all" % LAUNCHER], out + err)
        self.assertLess(out.index("Yours, after:"), [i for i, l in enumerate(out) if UNDO.match(l)][0])


if __name__ == "__main__":
    unittest.main()
