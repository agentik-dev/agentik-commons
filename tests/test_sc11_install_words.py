"""Row sc11-install-words: `install-cli` says its result in one line (design/23 section 5).

A first install in a temp HOME prints `Placed <launcher> <version> and <door>.` from `~`, one line
under 80 columns, through the suite's verb and through the module's own `install_cli()`; a second
run, where no tree goes, prints no prune line; `--json` keeps the tree. The names are made up and
nothing here writes outside its temp folders."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LAUNCHER, Home, version  # noqa: E402
from test_agentik_install import Base, RUNNER, APPLE_PY  # noqa: E402

PRUNE = "prune-trees: removed"


class SuiteVerb(Home):
    def test_first_install_is_one_line_from_home(self):
        code, out, err = self.run_cli("install-cli")
        self.assertEqual(code, 0, err)
        want = "Placed ~/.local/bin/agentik-suite %s and ~/.local/bin/agentik." % version()
        self.assertEqual(out.splitlines(), [want])
        self.assertLess(len(want), 80)
        self.assertNotIn(self.home, out)

    def test_a_second_run_prints_no_prune_line(self):
        self.run_cli("install-cli")
        code, out, err = self.run_cli("install-cli")
        self.assertEqual(code, 0, err)
        self.assertNotIn("prune", out)
        self.assertTrue(out.startswith("Placed "), out)

    def test_a_prune_that_removed_a_tree_prints(self):
        self.run_cli("install-cli")
        share = Path(self.home, ".local", "share", "agentik-suite")
        for n in range(5):
            old = share / ("old%d" % n)
            old.mkdir()
            os.utime(old, (1000 + n, 1000 + n))
        code, out, err = self.run_cli("install-cli")
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("Placed ~/.local/bin/agentik-suite "), out)
        if "keeping every tree" not in out:     # a machine whose ps shows no environment fails safe
            self.assertTrue(any(l.startswith(PRUNE) and "removed 0" not in l for l in lines[1:]), out)

    def test_json_keeps_the_tree(self):
        code, out, err = self.run_cli("install-cli", "--json")
        self.assertEqual(code, 0, err)
        done = json.loads(out)
        self.assertTrue(os.path.isdir(done["tree"]), done)
        self.assertEqual(os.path.dirname(done["tree"]), os.path.join(self.home, ".local", "share", "agentik-suite"))
        self.assertEqual(done["launcher"], os.path.join(self.home, ".local", "bin", "agentik-suite"))


class ModuleVerb(Base):
    def install(self, plugin, tool="agentik-x"):
        """The first line says the result; with the bin folder on PATH it is the only line."""
        path = "%s:/usr/bin:/bin" % (self.home / ".local" / "bin")
        code, out, err = self.run_tool(plugin / "bin" / tool, "install-cli", env={"PATH": path})
        self.assertEqual((code, err), (0, ""), out)
        return out

    def test_first_install_is_one_line_from_home(self):
        plugin = self.plugin()
        out = self.install(plugin)
        want = "Placed ~/.local/bin/agentik-x 1.0.0 and ~/.local/bin/agentik."
        self.assertEqual(out.splitlines(), [want])
        self.assertLess(len(want), 80)
        self.assertNotIn(str(self.home), out)

    def test_a_second_run_prints_no_prune_line(self):
        plugin = self.plugin()
        self.install(plugin)
        out = self.install(plugin)
        self.assertEqual(len(out.splitlines()), 1, out)
        self.assertNotIn("prune", out)

    def test_a_link_is_said_after_it_on_the_same_line(self):
        plugin = self.plugin(old_name="agentik-old")
        self.install(plugin)
        (self.home / ".local" / "bin" / "agentik-old").unlink(missing_ok=True)
        os.symlink("agentik-x", self.home / ".local" / "bin" / "agentik-old")
        out = self.install(plugin)
        self.assertEqual(len(out.splitlines()), 1, out)
        self.assertIn(" and ~/.local/bin/agentik. ~/.local/bin/agentik-old links to it.", out)


if __name__ == "__main__":
    unittest.main()
