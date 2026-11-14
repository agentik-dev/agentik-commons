"""bin/agentik hands every line it has no tool for to agentik-suite (packet ak2 R2, R4; packet
sc13-door R1 to R6): a first word with an agentik-<word> goes to that tool, anything else goes to
the suite as typed, bare included; the door looks on PATH, then in its own folder; with no suite it
answers --version, help and a name itself, in two lines where it refuses. Each run is the door with
an env of exactly HOME (a temp folder) and PATH (folders of made-up stubs, then /usr/bin:/bin)."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOOR = ROOT / "bin" / "agentik"
SUITE_BIN = ROOT / "plugins" / "suite" / "bin"
PLAN = ROOT / "plugins" / "suite" / "lib" / "agentik_suite" / "plan.py"
SYSTEM = "/usr/bin:/bin"
# a stub prints its own name, then each arg between brackets, then exits with {code}
STUB = '#!/bin/sh\nprintf "%s" "${{0##*/}}"\nfor a in "$@"; do printf "[%s]" "$a"; done\necho\nexit {code}\n'
SOURCE = re.search(r'^SOURCE = "([^"]+)"$', PLAN.read_text(), re.M).group(1)
NEXT = "next: git clone https://github.com/%s && agentik-commons/setup" % SOURCE
USAGE = "usage: agentik [<verb or tool> [args...]] | agentik help [<verb or tool>] | agentik --version"


def not_a_name(word):
    return "agentik: %s is not a name: lowercase letters, digits and dashes\nnext: agentik help\n" % word


class DoorTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = os.path.realpath(tmp.name)
        self.stubs = os.path.join(self.home, "stubs")
        os.mkdir(self.stubs)

    def stub(self, name, code=0, folder=None):
        path = os.path.join(folder or self.stubs, name)
        with open(path, "w") as fh:
            fh.write(STUB.format(code=code))
        os.chmod(path, 0o755)
        return path

    def run_door(self, *args, path=None, door=DOOR, cwd=None):
        env = {"HOME": self.home, "PATH": path or "%s:%s" % (self.stubs, SYSTEM),
               "XDG_CACHE_HOME": os.path.join(self.home, "cache")}
        p = subprocess.run([str(door), *args], capture_output=True, text=True, env=env, timeout=60,
                           cwd=cwd)
        return p.returncode, p.stdout, p.stderr

    def placed(self):
        """A folder off PATH that holds a copy of the door."""
        folder = os.path.join(self.home, "placed")
        os.mkdir(folder)
        door = shutil.copy(str(DOOR), os.path.join(folder, "agentik"))
        return folder, door

    # acceptance 1
    def test_1_every_flag_first_and_a_word_with_no_tool_reach_the_suite(self):
        self.stub("agentik-suite", code=5)
        for args in (("--version",), ("--version", "--json"), ("--json",), ("--no-color", "doctor"),
                     ("help", "--json"), ("help", "doctor", "extra"), ("--help", "--version"),
                     ("Config",), ("-q",), ("a_b", "x"), ("setup", "--dry-run"), ("nosuch", "a b", "")):
            want = "agentik-suite" + "".join("[%s]" % a for a in args) + "\n"
            self.assertEqual(self.run_door(*args), (5, want, ""), args)

    # acceptance 2
    def test_2_the_real_suite_behind_the_door_prints_one_version(self):
        path = "%s:%s" % (SUITE_BIN, SYSTEM)
        version = json.loads((SUITE_BIN.parent / ".claude-plugin" / "plugin.json").read_text())["version"]
        flag = self.run_door("--version", path=path)
        verb = self.run_door("version", path=path)
        self.assertEqual(flag, verb)
        self.assertEqual(flag[0], 0, flag[2])
        self.assertIn(version, flag[1])
        code, out, err = self.run_door("setup", "--dry-run", path=path)
        self.assertEqual(code, 0, err)
        self.assertRegex(out, r"(?m)^\S*\s*1\s")  # the plan's first step
        code, out, err = self.run_door(path=path)
        self.assertEqual(code, 0, err)
        self.assertRegex(out, r"(?m)^  setup  ")
        self.assertIn("next:", err)

    # acceptance 3
    def test_3_bare_reaches_the_suite_with_no_word(self):
        self.stub("agentik-suite", code=5)
        self.assertEqual(self.run_door(), (5, "agentik-suite\n", ""))
        for args in (("help",), ("-h",), ("--help",)):
            self.assertEqual(self.run_door(*args), (5, "agentik-suite[%s]\n" % args[0], ""), args)

    # acceptance 4
    def test_4_the_suite_beside_the_door_off_path(self):
        folder, door = self.placed()
        self.stub("agentik-suite", code=6, folder=folder)
        self.assertEqual(self.run_door("doctor", path=SYSTEM, door=door), (6, "agentik-suite[doctor]\n", ""))
        self.assertEqual(self.run_door(path=SYSTEM, door=door), (6, "agentik-suite\n", ""))
        self.stub("agentik-suite", code=7)
        self.assertEqual(self.run_door("doctor", door=door), (7, "agentik-suite[doctor]\n", ""))
        # started by its name from PATH, the door's own folder is that PATH entry
        code, out, _ = self.run_door("doctor", path="%s:%s" % (folder, SYSTEM), door="agentik")
        self.assertEqual((code, out), (6, "agentik-suite[doctor]\n"))

    # acceptance 5
    def test_5_a_tool_beside_the_door_off_path(self):
        folder, door = self.placed()
        self.stub("agentik-x", code=4, folder=folder)
        self.assertEqual(self.run_door("x", "a b", path=SYSTEM, door=door), (4, "agentik-x[a b]\n", ""))
        self.assertEqual(self.run_door("help", "x", path=SYSTEM, door=door), (4, "agentik-x[--help]\n", ""))
        self.stub("agentik-x", code=8)
        self.assertEqual(self.run_door("x", door=door), (8, "agentik-x\n", ""))

    # acceptance 6
    def test_6_no_suite_a_name_with_no_tool_and_the_next_line_runs(self):
        for args in (("nosuch",), ("nosuch", "--x", "y"), ("help", "nosuch")):
            self.assertEqual(self.run_door(*args),
                             (3, "", "agentik: nosuch is not installed, and neither is the agentik suite\n"
                                     + NEXT + "\n"), args)
        self.assertEqual(SOURCE, "agentik-dev/agentik-commons")
        # the next: line, pasted into a shell in any folder: a stub git that makes the clone
        with open(os.path.join(self.stubs, "git"), "w") as fh:
            fh.write('#!/bin/sh\n[ "$1 $2" = "clone https://github.com/%s" ] || exit 9\n'
                     'mkdir agentik-commons && printf "#!/bin/sh\\nexit 0\\n" > agentik-commons/setup\n'
                     'chmod +x agentik-commons/setup\n' % SOURCE)
        os.chmod(os.path.join(self.stubs, "git"), 0o755)
        work = os.path.join(self.home, "anywhere")
        os.mkdir(work)
        p = subprocess.run(["sh", "-c", NEXT[len("next: "):]], cwd=work, capture_output=True, text=True,
                           env={"HOME": self.home, "PATH": "%s:%s" % (self.stubs, SYSTEM)}, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(os.path.isfile(os.path.join(work, "agentik-commons", "setup")))

    # acceptance 7
    def test_7_no_suite_the_doors_own_answers(self):
        for args in ((), ("help",), ("-h",), ("--help",)):
            code, out, err = self.run_door(*args)
            self.assertEqual((code, err), (0, NEXT + "\n"), args)
            self.assertTrue(out.startswith(USAGE + "\n"), args)
            self.assertIn("no agentik-* tool on PATH", out)
        self.assertEqual(self.run_door("--version"), (0, "agentik 0.3.0 (no suite installed)\n", ""))
        for args in (("--json",), ("--version", "--json"), ("-q", "x"), ("help", "--json"),
                     ("help", "x", "y")):
            self.assertEqual(self.run_door(*args), (2, "", USAGE + "\n"), args)
        for word in ("Config", "a_b", "x.y", "Z-9"):
            self.assertEqual(self.run_door(word), (2, "", not_a_name(word)), word)
            self.assertEqual(self.run_door("help", word), (2, "", not_a_name(word)), word)
        for word in ("\x1b[31mred", "a b", "x/y", "", "é", "x\ny", "x;y"):
            code, out, err = self.run_door(word)
            self.assertEqual((code, out, err), (2, "", not_a_name("that word")), repr(word))

    # acceptance 8
    def test_8_a_tool_on_path_still_wins(self):
        self.stub("agentik-suite")
        self.stub("agentik-x", code=4)
        self.assertEqual(self.run_door("x", "a b", ""), (4, "agentik-x[a b][]\n", ""))
        self.assertEqual(self.run_door("help", "x")[:2], (4, "agentik-x[--help]\n"))
        self.assertEqual(self.run_door("help", "--json", "x", "y")[:2], (4, "agentik-x[--help]\n"))
        self.assertEqual(self.run_door("help", "y")[:2], (0, "agentik-suite[help][y]\n"))
        self.assertEqual(self.run_door("suite", "config")[:2], (0, "agentik-suite[config]\n"))

    # acceptance 9
    def test_9_the_two_doors(self):
        copy = SUITE_BIN / "agentik"
        data = DOOR.read_bytes()
        self.assertEqual(copy.read_bytes(), data)
        self.assertTrue(os.access(copy, os.X_OK))
        self.assertEqual(subprocess.run(["sh", "-n", str(DOOR)]).returncode, 0)
        self.assertLess(len(data.splitlines()), 100)
        self.assertRegex(data.decode("ascii"), r"(?m)^VERSION=0\.3\.0$")
        self.assertFalse(re.search(rb"[^\t\n\x20-\x7e]", data), "an escape byte or a mark")
        # the copy dispatches from its own folder: the suite beside it is on PATH there
        code, out, _ = self.run_door("--help", path="%s:%s" % (SUITE_BIN, SYSTEM), door=copy)
        self.assertEqual(code, 0)
        self.assertRegex(out, r"(?m)^  setup  ")

    def test_the_guides_rows(self):
        guide = (ROOT / "GUIDE.md").read_text()
        section = guide[guide.index("## §10"):guide.index("**The floor")]
        self.assertIn("`agentik: <word> is not installed, and neither is the agentik suite`", section)
        self.assertIn("`%s`" % NEXT, section)
        self.assertNotIn("is not installed here", section)
        self.assertNotIn("agentik-dev/agentik-<tool>", section)


if __name__ == "__main__":
    unittest.main()
