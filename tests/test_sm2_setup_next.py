"""Row sm2-setup-next: the dry run and the first screen end on setup itself.

The dry run's close, while a step from 2 to 5 has a line setup would run or step 1 is blocked, is
`next: ` and the setup command with the names it was given; a missing `claude` gains one `get it:`
line under its row; the bare screen and `help` read the plan and close on the setup command while
a step from 1 to 5 is not ok, else on the doctor command. Each screen runs in a temp HOME under a
bare environment, PATH a folder with a stub `claude` then /usr/bin:/bin; the suite starts as
`./setup` from the clone's folder unless a test says otherwise. Nothing here starts the real
`claude` or writes outside its temp folder."""
import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "plugins" / "suite" / "lib"
LAUNCHER = ROOT / "plugins" / "suite" / "bin" / "agentik-suite"
MANIFEST = ROOT / "plugins" / "suite" / ".claude-plugin" / "plugin.json"
CATALOGUE = LIB / "agentik_suite" / "messages.md"
sys.path.insert(0, str(LIB))
from agentik_suite import cli  # noqa: E402

SYSTEM = "/usr/bin:/bin"
GET = "get it: https://claude.com/claude-code"
PLUGIN = "murmur"  # a made-up plugin's name


class Home(unittest.TestCase):
    def setUp(self):
        self.home = os.path.realpath(tempfile.mkdtemp(prefix="sm2-"))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.stubs = self.folder("stub", claude=True)
        self.bindir = os.path.join(self.home, ".local", "bin")

    def folder(self, name, claude=True, links=()):
        path = os.path.join(self.home, name)
        os.makedirs(path)
        if claude:
            with open(os.path.join(path, "claude"), "w") as fh:
                fh.write("#!/bin/sh\nexit 0\n")
            os.chmod(os.path.join(path, "claude"), 0o755)
        for tool in links:
            os.symlink(os.path.join("/usr/bin", tool), os.path.join(path, tool))
        return path

    def env(self, path=None):
        return {"HOME": self.home, "PATH": path or self.stubs + ":" + SYSTEM}

    def screen(self, argv, env):
        p = subprocess.run(argv, cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout, p.stderr

    def last(self, argv, env):
        """The screen's last line, its mark taken off."""
        out, err = self.screen(argv, env)
        line = (out + err).splitlines()[-1]
        return line.split("  ", 1)[1] if line.startswith("note  ") else line

    def finished(self, on_path=True):
        """Steps 1 to 5 read ok: the marketplace known, the manifest's set installed, each shipping
        no command, and this command's install-cli run; with on_path, ~/.local/bin on PATH."""
        plugins = os.path.join(self.home, ".claude", "plugins")
        os.makedirs(plugins)
        with open(os.path.join(plugins, "known_marketplaces.json"), "w") as fh:
            json.dump({"agentik": {}}, fh)
        table = {}
        for dep in json.loads(MANIFEST.read_text())["dependencies"]:
            dep = dep["name"] if isinstance(dep, dict) else dep
            folder = os.path.join(self.home, "inst", dep)
            os.makedirs(folder)
            table["%s@agentik" % dep] = [{"version": "1.0.0", "installPath": folder}]
        with open(os.path.join(plugins, "installed_plugins.json"), "w") as fh:
            json.dump({"plugins": table}, fh)
        p = subprocess.run([str(LAUNCHER), "install-cli"], cwd=str(ROOT), env=self.env(),
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        return self.env(self.bindir + ":" + self.stubs + ":" + SYSTEM) if on_path else self.env()

    def paste(self, line, env):
        """A `next:` line pasted into sh -c from the clone's folder, stdin closed: its exit."""
        self.assertTrue(line.startswith("next: "), line)
        p = subprocess.run(["/bin/sh", "-c", line[len("next: "):]], cwd=str(ROOT), env=env,
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
        return p.returncode


class DryRunTest(Home):
    def test_a1_the_dry_run_ends_on_setup(self):
        env = self.env()
        for argv, want in ((["./setup", "--dry-run"], "next: ./setup"),
                           (["./setup", "--dry-run", PLUGIN], "next: ./setup " + PLUGIN)):
            out, err = self.screen(argv, env)
            self.assertIn("would run: ", out, argv)
            self.assertEqual(self.last(argv, env), want, argv)
            self.assertNotIn("run each", out + err, argv)
        self.assertEqual(self.last(["./setup", "--dry-run", PLUGIN, PLUGIN], env), "next: ./setup " + PLUGIN)

    def test_a2_claude_missing_names_where_it_comes_from(self):
        argv = ["./setup", "--dry-run"]
        out, err = self.screen(argv, self.env(SYSTEM))
        lines = out.splitlines()
        self.assertEqual(sum(GET in line for line in lines), 1, out)
        row = [i for i, line in enumerate(lines) if " claude " in line and "not on PATH" in line]
        self.assertEqual(len(row), 1, out)
        self.assertEqual(lines[row[0] + 1].strip(), GET)
        self.assertEqual(self.last(argv, self.env(SYSTEM)), "next: ./setup")
        # git missing, claude there: no `get it:` line, the same close
        nogit = self.folder("nogit", links=("dirname",)) + ":/bin"
        out, err = self.screen(argv, self.env(nogit))
        self.assertIn("git", [w for line in out.splitlines() if "not on PATH" in line for w in line.split()])
        self.assertNotIn("get it:", out + err)
        self.assertEqual(self.last(argv, self.env(nogit)), "next: ./setup")

    def test_a2_the_address_stands_once_in_the_catalogue(self):
        text = CATALOGUE.read_text()
        self.assertEqual(text.count("https://claude.com/claude-code"), 1)
        self.assertNotIn("would run:` line above", text)

    def test_r4_the_quiet_dry_run_prints_no_hint(self):
        out, err = self.screen(["./setup", "--dry-run", "-q"], self.env())
        self.assertEqual(err, "")


class FirstScreenTest(Home):
    def test_a3_the_first_screen_ends_on_setup_then_doctor(self):
        path = shlex.quote(str(LAUNCHER))
        env = self.env()
        for argv in ([str(LAUNCHER)], [str(LAUNCHER), "help"]):
            self.assertEqual(self.last(argv, env), "next: %s setup" % path, argv)
        env = self.finished()
        for argv in ([str(LAUNCHER)], [str(LAUNCHER), "help"]):
            self.assertEqual(self.last(argv, env), "next: agentik doctor", argv)

    def test_r3_only_the_path_line_left_ends_on_doctor(self):
        env = self.finished(on_path=False)
        self.assertEqual(self.last([str(LAUNCHER)], env), "next: ~/.local/bin/agentik doctor")

    def test_r3_help_with_a_verb_prints_no_hint(self):  # hint.verb left the catalogue (row sc5 R5)
        self.assertEqual(self.screen([str(LAUNCHER), "help", "setup"], self.env())[1], "")

    def test_r4_the_quiet_first_screen_prints_no_hint(self):
        out, err = self.screen([str(LAUNCHER), "-q"], self.env())
        self.assertEqual(err, "")
        self.assertIn("<tool>", out)  # the first screen (row sc5 R2)

    def test_a4_the_first_screen_starts_no_process(self):
        def refuse(*args, **kwargs):
            raise AssertionError("a process was started: %r" % (args,))
        for env in (self.env(), self.finished()):
            out, err = io.StringIO(), io.StringIO()
            with mock.patch("subprocess.Popen", side_effect=refuse):
                code = cli.main([], env=dict(env), out=out, err=err)
            self.assertEqual(code, 0, err.getvalue())
            self.assertIn("next: ", err.getvalue())


class PasteTest(Home):
    def test_a5_each_next_line_runs_when_pasted(self):
        env = self.env()
        lines = [self.last(["./setup", "--dry-run"], env),
                 self.last(["./setup", "--dry-run", PLUGIN], env),
                 self.last([str(LAUNCHER)], env),
                 self.last([str(LAUNCHER), "help"], env)]
        for line in lines:
            self.assertNotEqual(self.paste(line, env), 127, line)
        bare = self.env(SYSTEM)
        line = self.last(["./setup", "--dry-run"], bare)
        self.assertNotEqual(self.paste(line, bare), 127, line)
        env = self.finished()
        for argv in ([str(LAUNCHER)], [str(LAUNCHER), "help"]):
            line = self.last(argv, env)
            self.assertNotEqual(self.paste(line, env), 127, line)


if __name__ == "__main__":
    unittest.main()
