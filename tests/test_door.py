"""bin/agentik falls through to agentik-suite (packet ak2 R2, R4): a word with no agentik-<word>
on PATH goes to the suite with its args unchanged, bare and help go to the suite's help, and the
suite's own copy of the door is the same file. Each run is the door with an env of exactly HOME
(a temp folder) and PATH (folders of made-up stubs, then /usr/bin:/bin)."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOOR = ROOT / "bin" / "agentik"
SUITE_BIN = ROOT / "plugins" / "suite" / "bin"
SYSTEM = "/usr/bin:/bin"
# a stub prints its own name, then each arg between brackets, then exits with {code}
STUB = '#!/bin/sh\nprintf "%s" "${{0##*/}}"\nfor a in "$@"; do printf "[%s]" "$a"; done\necho\nexit {code}\n'


class DoorTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = os.path.realpath(tmp.name)
        self.stubs = os.path.join(self.home, "stubs")
        os.mkdir(self.stubs)

    def stub(self, name, code=0):
        path = os.path.join(self.stubs, name)
        with open(path, "w") as fh:
            fh.write(STUB.format(code=code))
        os.chmod(path, 0o755)

    def run_door(self, *args, path=None, door=DOOR):
        env = {"HOME": self.home, "PATH": path or "%s:%s" % (self.stubs, SYSTEM),
               "XDG_CACHE_HOME": os.path.join(self.home, "cache")}
        p = subprocess.run([str(door), *args], capture_output=True, text=True, env=env, timeout=60)
        return p.returncode, p.stdout, p.stderr

    def test_a1_no_suite_one_line_and_no_repo(self):
        for args in (("nosuch",), ("help", "nosuch")):
            code, out, err = self.run_door(*args)
            self.assertEqual((code, out), (3, ""), args)
            self.assertEqual(err, "agentik: nosuch is not installed here; "
                                  "agentik-commons/setup sets the suite up\n", args)
            self.assertNotIn("agentik-dev/", err)

    def test_a2_a_word_with_no_tool_goes_to_the_suite(self):
        self.stub("agentik-suite", code=5)
        self.assertEqual(self.run_door("setup", "--dry-run"), (5, "agentik-suite[setup][--dry-run]\n", ""))
        self.assertEqual(self.run_door("nosuch", "a b", "")[:2], (5, "agentik-suite[nosuch][a b][]\n"))
        for args in ((), ("help",), ("-h",), ("--help",)):
            self.assertEqual(self.run_door(*args)[:2], (5, "agentik-suite[help]\n"), args)

    def test_a2_a_tool_on_path_still_wins(self):
        self.stub("agentik-suite")
        self.stub("agentik-x", code=4)
        self.assertEqual(self.run_door("x", "a b", ""), (4, "agentik-x[a b][]\n", ""))
        self.assertEqual(self.run_door("help", "x")[:2], (4, "agentik-x[--help]\n"))
        self.assertEqual(self.run_door("help", "y")[:2], (0, "agentik-suite[help][y]\n"))
        self.assertEqual(self.run_door("suite", "config")[:2], (0, "agentik-suite[config]\n"))

    def test_a2_version_and_usage(self):
        self.stub("agentik-suite")
        self.assertEqual(self.run_door("--version"), (0, "agentik 0.2.0\n", ""))
        for args in (("--version", "x"), ("help", "x", "y"), ("Bad",), ("help", "x_y")):
            code, out, _ = self.run_door(*args)
            self.assertEqual((code, out), (2, ""), args)

    def test_a3_the_real_suite_behind_the_door(self):
        path = "%s:%s" % (SUITE_BIN, SYSTEM)
        code, out, err = self.run_door("setup", "--dry-run", path=path)
        self.assertEqual(code, 0, err)
        self.assertIn("setup", out.lower())
        self.assertRegex(out, r"(?m)^\S*\s*1\s")  # the plan's first step
        code, out, err = self.run_door(path=path)
        self.assertEqual(code, 0, err)
        self.assertRegex(out, r"(?m)^  setup  ")
        self.assertIn("next:", err)

    def test_a5_the_two_doors(self):
        copy = SUITE_BIN / "agentik"
        self.assertEqual(copy.read_bytes(), DOOR.read_bytes())
        self.assertTrue(os.access(copy, os.X_OK))
        self.assertEqual(subprocess.run(["sh", "-n", str(DOOR)]).returncode, 0)
        self.assertLess(len(DOOR.read_text().splitlines()), 100)
        # the copy dispatches from its own folder: the suite beside it is on PATH there
        code, out, _ = self.run_door("--help", path="%s:%s" % (SUITE_BIN, SYSTEM), door=copy)
        self.assertEqual(code, 0)
        self.assertRegex(out, r"(?m)^  setup  ")

    def test_a6_the_guides_rows(self):
        guide = (ROOT / "GUIDE.md").read_text()
        section = guide[guide.index("## §10"):guide.index("**The floor")]
        self.assertIn("`agentik: <word> is not installed here; agentik-commons/setup sets the suite up`",
                      section)
        self.assertNotIn("agentik-dev/agentik-<tool>", section)


if __name__ == "__main__":
    unittest.main()
