"""scripts/suite-probe is run by hand, never by `make check` (packet c2, act 4):
its shape, its usage exits, and no Makefile target names it. Nothing here runs
claude or clones a repo: `--help` and a bad flag return before either."""
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "suite-probe"


class SuiteProbeTest(unittest.TestCase):
    def test_shape(self):
        self.assertTrue(PROBE.read_text().startswith("#!/usr/bin/env python3\n"))
        self.assertTrue(os.access(PROBE, os.X_OK))

    def test_usage(self):
        p = subprocess.run([str(PROBE), "--help"], capture_output=True, text=True, timeout=30)
        self.assertEqual((p.returncode, p.stdout), (0, "usage: suite-probe [--keep] [--code DIR] [--claude PATH]\n"))
        for args in (["--bogus"], ["--code"], ["--claude"]):
            p = subprocess.run([str(PROBE), *args], capture_output=True, text=True, timeout=30)
            self.assertEqual((p.returncode, p.stdout), (2, ""), args)

    def test_make_never_runs_it(self):
        self.assertNotIn("suite-probe", (ROOT / "Makefile").read_text())


if __name__ == "__main__":
    unittest.main()
