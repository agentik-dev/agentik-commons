"""scripts/sync <repo> (agentik-r1 7.3): the four vendored copies land
byte-identical and executable under <repo>/scripts/, scripts/vendored.sha256
verifies under `shasum -a 256 -c`, a drifted copy fails it, and usage or a
target that is not a git checkout exits 2."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts" / "sync"
COPIES = {"scripts/agentik": "bin/agentik", "scripts/hygiene": "scripts/hygiene",
          "scripts/bounded": "scripts/bounded",
          "scripts/plugin-version-check": "scripts/plugin-version-check"}


def sync(*args):
    p = subprocess.run([str(SYNC), *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def verify(repo):
    p = subprocess.run(["shasum", "-a", "256", "-c", "scripts/vendored.sha256"],
                       capture_output=True, text=True, cwd=repo)
    return p.returncode, p.stdout


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.join(self.tmp.name, "tool repo")
        os.mkdir(self.repo)
        subprocess.run(["git", "-C", self.repo, "init", "-q"], check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_copies_and_pin_file(self):
        code, out, err = sync(self.repo)
        self.assertEqual((code, err), (0, ""))
        for copy, source in COPIES.items():
            path = Path(self.repo, copy)
            self.assertEqual(path.read_bytes(), Path(ROOT, source).read_bytes(), copy)
            self.assertTrue(os.access(path, os.X_OK), copy)
        code, out = verify(self.repo)
        self.assertEqual(code, 0)
        self.assertEqual(sorted(out.splitlines()), sorted(c + ": OK" for c in COPIES))
        rows = Path(self.repo, "scripts", "vendored.sha256").read_text().splitlines()
        self.assertEqual([r.split("  ", 1)[1] for r in rows], list(COPIES))
        # nothing else is written, no scratch file is left
        self.assertEqual(sorted(os.listdir(Path(self.repo, "scripts"))),
                         ["agentik", "bounded", "hygiene", "plugin-version-check",
                          "vendored.sha256"])

    def test_rerun_refreshes_a_drifted_copy(self):
        sync(self.repo)
        Path(self.repo, "scripts", "hygiene").write_text("drifted\n")
        self.assertNotEqual(verify(self.repo)[0], 0)
        self.assertEqual(sync(self.repo)[0], 0)
        self.assertEqual(verify(self.repo)[0], 0)

    def test_usage_and_missing_target_exit_two(self):
        plain = os.path.join(self.tmp.name, "plain")
        os.mkdir(plain)
        for args in ((), (self.repo, self.repo), ("--help",),
                     (os.path.join(self.tmp.name, "missing"),), (plain,), (str(ROOT),)):
            code, out, _ = sync(*args)
            self.assertEqual((code, out), (2, ""), args)
        self.assertEqual(os.listdir(plain), [])

    def test_cdpath_is_never_followed(self):
        # a relative target names the folder under the caller's cwd, never one on CDPATH
        base = self.tmp.name
        subprocess.run(["git", "-C", base, "init", "-q", "r"], check=True)
        os.makedirs(os.path.join(base, "alt"))
        subprocess.run(["git", "-C", os.path.join(base, "alt"), "init", "-q", "r"], check=True)
        env = dict(os.environ, CDPATH=os.path.join(base, "alt"))
        p = subprocess.run([str(SYNC), "r"], capture_output=True, text=True, cwd=base, env=env)
        self.assertEqual((p.returncode, p.stderr), (0, ""))
        self.assertEqual(verify(os.path.join(base, "r"))[0], 0)
        self.assertFalse(os.path.exists(os.path.join(base, "alt", "r", "scripts")))
        self.assertEqual(len(p.stdout.splitlines()), 1)

    def test_shape(self):
        self.assertTrue(SYNC.read_text().startswith("#!/bin/sh\n"))
        self.assertEqual(subprocess.run(["sh", "-n", str(SYNC)]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
