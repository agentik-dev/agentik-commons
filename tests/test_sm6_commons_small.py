"""Row sm6-commons-small, a small change: NICE n76 (the settings read opens a regular file only)
and n197 (one word rule for a remedy that answers or removes). Nothing here writes outside its
temp folder; a read that could block runs in a child under a deadline."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "plugins" / "suite" / "lib"
sys.path.insert(0, str(LIB))
from agentik_suite import config, doctor, settings  # noqa: E402

READ = ("import sys\nsys.path.insert(0, sys.argv[1])\nfrom agentik_suite import settings\n"
        "try:\n    print(settings.read(sys.argv[2])[0])\nexcept settings.Fault as e:\n    print('fault', e.why)\n")


class SettingsRead(unittest.TestCase):
    """n76: a FIFO at the user settings file is a Fault at once, never a read that waits."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sm6-")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def read(self, path):
        done = subprocess.run([sys.executable, "-c", READ, str(LIB), path], capture_output=True,
                              text=True, timeout=10)
        return done.stdout.strip() + done.stderr

    def test_01_a_fifo_is_refused_without_a_wait(self):
        fifo = os.path.join(self.dir, "config.yaml")
        os.mkfifo(fifo)
        self.assertEqual(self.read(fifo), "fault a file that cannot be read")

    def test_02_a_regular_file_and_an_absent_one_read_as_before(self):
        path = os.path.join(self.dir, "config.yaml")
        self.assertEqual(settings.read(path), (False, {}, {}))
        with open(path, "w") as fh:
            fh.write("checkouts:\n  - /src/a\n")
        present, tree, lines = settings.read(path)
        self.assertEqual((present, tree), (True, {"checkouts": ["/src/a"]}))
        with open(path, "wb") as fh:
            fh.write(b"checkouts: \xff\n")
        self.assertEqual(self.read(path), "fault a file that cannot be read")
        self.assertEqual(self.read(self.dir), "fault a file that cannot be read")


class OneWordRule(unittest.TestCase):
    """n197: a quoted flag, a cluster, a case or `--assume-yes` answers or removes, in both."""

    def test_03_config_and_the_close_share_the_rule(self):
        for remedy in ("murmur reset -yq", "murmur reset -qy", "murmur reset '-y'", 'murmur reset "--yes"',
                       "murmur reset --yes=1", "murmur reset --YES", "murmur REMOVE all",
                       "murmur reset --assume-yes", "murmur 'remove' all", "murmur reset -y"):
            self.assertTrue(config.asks(remedy), remedy)
            self.assertFalse(doctor._closes(remedy), remedy)
        for remedy in ("murmur reset", "murmur reset -q", "murmur reset --quiet", "murmur removed x"):
            self.assertFalse(config.asks(remedy), remedy)
            self.assertTrue(doctor._closes(remedy), remedy)


if __name__ == "__main__":
    unittest.main()
