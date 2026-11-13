"""scripts/setup-probe is run by hand, never by `make check` (packet ak3p, R5): its
shape, its usage exits, no Makefile line naming it, and its two rules (a new path in
the temp HOME, the commands `setup --json` ran) over made-up reports. Nothing here
runs claude, clones a repo or starts the probe's steps: `--help` and a bad flag
return before any of them."""
import importlib.machinery
import importlib.util
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "setup-probe"
HOME = "/tmp/probe-t/home"


def load():
    loader = importlib.machinery.SourceFileLoader("setup_probe", str(PROBE))
    spec = importlib.util.spec_from_loader("setup_probe", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def h(rel):
    return HOME + "/" + rel


class SetupProbeShapeTest(unittest.TestCase):
    def test_shape(self):
        self.assertTrue(PROBE.read_text().startswith("#!/usr/bin/env python3\n"))
        self.assertTrue(os.access(PROBE, os.X_OK))

    def test_usage(self):
        p = subprocess.run([str(PROBE), "--help"], capture_output=True, text=True, timeout=30)
        self.assertEqual((p.returncode, p.stdout),
                         (0, "usage: setup-probe [--keep] [--code DIR] [--claude PATH]\n"))
        for args in (["--bogus"], ["--code"], ["--claude"]):
            p = subprocess.run([str(PROBE), *args], capture_output=True, text=True, timeout=30)
            self.assertEqual((p.returncode, p.stdout), (2, ""), args)

    def test_make_never_runs_it(self):
        self.assertNotIn("setup-probe", (ROOT / "Makefile").read_text())


class SetupProbeRulesTest(unittest.TestCase):
    """R3 step 3's rule for a new path and step 2's for `ran`, over stubs of the report."""

    def setUp(self):
        self.p = load()

    def test_stray_paths(self):
        wrote = [h(".local/bin/agentik-demo"), h(".local/share/agentik-demo")]
        new = {h(".local"), h(".local/bin"), h(".local/bin/agentik-demo"),
               h(".local/share"), h(".local/share/agentik-demo"),
               h(".local/share/agentik-demo/lib/x.py"),
               h(".claude.json"), h(".claude"), h(".claude/plugins/cache/a.json"),
               h(".cache"), h(".cache/agentik"), h(".cache/agentik/py/x.cpython-39.pyc"),
               h(".local/bin/agentik-other"), h(".profile"), h(".cache/agentik/notes.txt"),
               h(".claude.json.bak"), h(".local/share/agentik-demo-old")}
        self.assertEqual(self.p.stray(HOME, new, wrote),
                         [h(".cache/agentik/notes.txt"), h(".claude.json.bak"),
                          h(".local/bin/agentik-other"), h(".local/share/agentik-demo-old"),
                          h(".profile")])

    def test_stray_none(self):
        self.assertEqual(self.p.stray(HOME, {h(".claude.json")}, []), [])
        # a new folder is accounted for by what it holds, never alone
        self.assertEqual(self.p.stray(HOME, {h(".local"), h(".local/empty")}, []),
                         [h(".local"), h(".local/empty")])

    def test_ran(self):
        ran = [{"n": 3, "command": "claude plugin install alpha@agentik", "exit": 0},
               {"n": 3, "command": "claude plugin install beta@agentik", "exit": 0},
               {"n": 4, "command": "'/tmp/probe-t/home/.claude/plugins/cache/agentik/alpha/1.0.0/"
                                   "bin/agentik-alpha' install-cli", "exit": 0},
               {"n": 5, "command": "/tmp/probe-t/code/agentik-commons/plugins/suite/bin/"
                                   "agentik-suite install-cli", "exit": 0}]
        self.assertEqual(self.p.ran_misses(ran, ["alpha", "beta"], ["alpha"]), ([], []))
        misses, extra = self.p.ran_misses(ran[1:] + [ran[1]], ["alpha", "beta"], ["alpha", "beta"])
        self.assertEqual(misses, ["claude plugin install alpha@agentik: ran 0 times",
                                  "claude plugin install beta@agentik: ran 2 times",
                                  "agentik-beta install-cli: ran 0 times"])
        self.assertEqual(extra, [])
        bad = [dict(ran[0], exit=1)] + ran[1:] + [{"n": 6, "command": "true", "exit": 0}]
        misses, extra = self.p.ran_misses(bad, ["alpha", "beta"], ["alpha"])
        self.assertEqual(misses, ["claude plugin install alpha@agentik: exit 1"])
        self.assertEqual(extra, ["true"])

    def test_changed(self):
        before = {h(".claude.json"): "a", h(".local/bin/agentik"): "b", h(".cache/agentik/x.pyc"): "c",
                  h(".local/bin/gone"): "d"}
        after = {h(".claude.json"): "a", h(".local/bin/agentik"): "B", h(".cache/agentik/x.pyc"): "C",
                 h(".cache/agentik/y.pyc"): "e", h(".local/new"): "f"}
        self.assertEqual(self.p.changed(HOME, before, after),
                         ["changed " + h(".local/bin/agentik"), "gone " + h(".local/bin/gone"),
                          "new " + h(".local/new")])


if __name__ == "__main__":
    unittest.main()
