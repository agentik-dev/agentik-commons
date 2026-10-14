"""bin/agentik, the front door (agentik-r1 section 3): dispatch with the args
unchanged, the tool's own exit, 2 for usage and a bad name, 3 when the tool is not
on PATH, the list in PATH order, help and version. Each test runs the script
through subprocess with a scratch PATH of fake tools."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin" / "agentik"
SYSTEM = "/usr/bin:/bin"
# a fake tool prints its argc, then each arg between brackets, then exits with $CODE
FAKE = '#!/bin/sh\nprintf "%s" "$#"\nfor a in "$@"; do printf "[%s]" "$a"; done\necho\nexit {code}\n'


def fake(directory, name, code=0, mode=0o755, body=None):
    path = Path(directory, name)
    path.write_text(body if body is not None else FAKE.format(code=code))
    path.chmod(mode)
    return path


def run(*args, path=SYSTEM, cwd=None):
    env = {"PATH": path, "HOME": os.environ.get("HOME", "/")}
    p = subprocess.run([str(SCRIPT), *args], capture_output=True, text=True, env=env, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


class FrontDoorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.a = os.path.join(self.tmp.name, "a")
        self.b = os.path.join(self.tmp.name, "b")
        os.mkdir(self.a)
        os.mkdir(self.b)

    def tearDown(self):
        self.tmp.cleanup()

    def path(self):
        return "%s:%s:%s" % (self.a, self.b, SYSTEM)

    def test_dispatch_passes_args_unchanged_and_the_tools_exit(self):
        fake(self.a, "agentik-x", code=7)
        code, out, err = run("x", "a b", "", "*", "-n", "$HOME", path=self.path())
        self.assertEqual((code, out, err), (7, "5[a b][][*][-n][$HOME]\n", ""))
        fake(self.a, "agentik-two-part", code=0)
        self.assertEqual(run("two-part", path=self.path())[:2], (0, "0\n"))

    def test_not_on_path_exits_three_naming_the_repo(self):
        code, out, err = run("nosuch")
        self.assertEqual((code, out), (3, ""))
        self.assertEqual(len(err.splitlines()), 1)
        self.assertIn("agentik-dev/agentik-nosuch", err)
        # a file that is not executable is not a tool
        fake(self.a, "agentik-y", mode=0o644)
        self.assertEqual(run("y", path=self.path())[0], 3)

    def test_bad_names_exit_two(self):
        fake(self.a, "agentik-x")
        for name in ("X;y", "", "X", "-x", "x-", "x--y", "1x", "x y", "x\ny", "x/y",
                     "../x", "x_y", "é", "--nosuch"):
            code, out, _ = run(name, path=self.path())
            self.assertEqual((code, out), (2, ""), repr(name))
            self.assertEqual(run("help", name, path=self.path())[0], 2, repr(name))

    def test_list_in_path_order_first_wins(self):
        fake(self.a, "agentik-x")
        fake(self.b, "agentik-x")
        fake(self.b, "agentik-yy")
        fake(self.b, "agentik-off", mode=0o644)
        fake(self.b, "agentik-Bad")
        for args in ((), ("help",), ("--help",), ("-h",)):
            code, out, err = run(*args, path=self.path())
            self.assertEqual((code, err), (0, ""), args)
            rows = [line.split() for line in out.splitlines() if line.startswith("  ")]
            self.assertEqual(rows, [["x", os.path.join(self.a, "agentik-x")],
                                    ["yy", os.path.join(self.b, "agentik-yy")]], args)

    def test_list_with_nothing_found_exits_zero(self):
        code, out, err = run()
        self.assertEqual((code, err), (0, ""))
        self.assertIn("no agentik-* tool on PATH", out)
        self.assertEqual(run(path="")[0], 0)

    def test_empty_path_entry_is_the_current_directory(self):
        # leading, middle and trailing: each empty entry is ".", as the shell's own lookup
        fake(self.a, "agentik-w", code=4)
        here = os.path.join(".", "agentik-w")
        for path in (SYSTEM + ":", ":" + SYSTEM, "/usr/bin::/bin"):
            self.assertEqual(run("w", "z", path=path, cwd=self.a)[:2], (4, "1[z]\n"), path)
            code, out, _ = run(path=path, cwd=self.a)
            rows = [line.split() for line in out.splitlines() if line.startswith("  ")]
            self.assertEqual((code, rows), (0, [["w", here]]), path)
        self.assertEqual(run("w", path=SYSTEM, cwd=self.a)[0], 3)

    def test_help_runs_the_tools_help(self):
        fake(self.a, "agentik-x")
        self.assertEqual(run("help", "x", path=self.path())[:2], (0, "1[--help]\n"))
        self.assertEqual(run("help", "nosuch")[0], 3)
        self.assertEqual(run("help", "x", "y", path=self.path())[0], 2)

    def test_version(self):
        code, out, err = run("--version")
        self.assertEqual((code, err), (0, ""))
        self.assertRegex(out, r"\Aagentik \d+\.\d+\.\d+\n\Z")
        self.assertEqual(run("--version", "x")[0], 2)

    def test_shape(self):
        text = SCRIPT.read_text()
        self.assertTrue(text.startswith("#!/bin/sh\n"))
        self.assertLess(len(text.splitlines()), 100)
        self.assertTrue(os.access(SCRIPT, os.X_OK))
        self.assertEqual(subprocess.run(["sh", "-n", str(SCRIPT)]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
