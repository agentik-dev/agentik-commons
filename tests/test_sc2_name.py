"""Row sc2-name: one function gives the words that start a printed command, and the title's name.

The three forms of hq design/23 §3: `agentik` where a door on PATH reaches the suite, the door's
path where it is placed off PATH, else the word typed, which the root setup and the launcher hand
on in AGENTIK_ARGV0. The paste proof runs each screen in a temp HOME whose PATH is a folder with a
stub `claude`, then /usr/bin:/bin, and pastes each printed command into `sh -c`. Nothing here
starts the real `claude` or writes outside its temp folder."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "plugins" / "suite" / "lib"
PKG = LIB / "agentik_suite"
LAUNCHER = ROOT / "plugins" / "suite" / "bin" / "agentik-suite"
sys.path.insert(0, str(LIB))
from agentik_suite import catalogue, prog  # noqa: E402

TOOL = "agentik-suite"
SYSTEM = "/usr/bin:/bin"
VERBS = "setup|doctor|config|status|help|describe|install-cli|version"
ANSI = re.compile(r"\x1b\[[0-9;]*m")
# a printed command: a word naming the suite (a path to it, `./setup`, or the door), then verbs and flags
COMMAND = re.compile(r"(?:(?<=\s)|^)((?:\S*/setup|\S*agentik(?:-suite)?)(?: (?:%s|--?[a-z-]+))+)" % VERBS)


def door(path, version):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write("#!/bin/sh\nVERSION=%s\nexit 0\n" % version)
    os.chmod(path, 0o755)


class Home(unittest.TestCase):
    def setUp(self):
        self.home = os.path.realpath(tempfile.mkdtemp(prefix="sc2-"))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.stubs = os.path.join(self.home, "stub")
        os.makedirs(self.stubs)
        with open(os.path.join(self.stubs, "claude"), "w") as fh:
            fh.write("#!/bin/sh\nexit 0\n")
        os.chmod(os.path.join(self.stubs, "claude"), 0o755)
        self.bindir = os.path.join(self.home, ".local", "bin")

    def env(self, path=None, **more):
        env = {"HOME": self.home, "PATH": path or self.stubs + ":" + SYSTEM, "LC_ALL": "C"}
        env.update(more)
        return env

    def start(self, words, env, typed=None, cwd=str(ROOT), full=False):
        return prog.start(env, str(LIB), TOOL, typed, cwd, words, full)


class FormTest(Home):
    """R2, R3, R4, R5: the three forms, the word typed, the name and the full form."""

    def test_r3_no_word_handed_on_is_the_launchers_absolute_path(self):
        self.assertEqual(self.start(["doctor"], self.env()), "%s doctor" % LAUNCHER)
        under = self.env(HOME=str(ROOT.parent))
        self.assertEqual(self.start(["doctor"], under), "~/%s/plugins/suite/bin/agentik-suite doctor" % ROOT.name)
        self.assertEqual(self.start(["doctor"], under, full=True), "%s doctor" % LAUNCHER)

    def test_r3_setup_typed_gives_setup_lines_and_the_launcher_for_others(self):
        env = self.env()
        self.assertEqual(self.start(["setup", "--dry-run"], env, "./setup"), "./setup --dry-run")
        self.assertEqual(self.start(["setup"], env, "./setup"), "./setup")
        self.assertEqual(self.start(["doctor"], env, "./setup"), "%s doctor" % LAUNCHER)
        self.assertEqual(self.start([], env, "./setup"), str(LAUNCHER))
        # from another folder the word no longer names the file
        self.assertEqual(self.start(["setup"], env, "./setup", cwd=self.home), "%s setup" % LAUNCHER)

    def test_r3_the_launcher_typed_is_kept_for_every_verb(self):
        env, word = self.env(), "plugins/suite/bin/agentik-suite"
        self.assertEqual(self.start(["config", "--changed"], env, word), word + " config --changed")
        self.assertEqual(self.start(["setup"], env, word), word + " setup")
        self.assertEqual(self.start(["config"], env, word, cwd=self.home), "%s config" % LAUNCHER)

    def test_r2_a_door_on_path_that_reaches_the_suite(self):
        bindir = os.path.join(self.home, "b")
        door(os.path.join(bindir, "agentik"), "0.2.0")
        door(os.path.join(bindir, TOOL), "9.9.9")
        env = self.env(path=bindir + ":" + SYSTEM)
        self.assertEqual(self.start(["doctor"], env, "./setup"), "agentik doctor")
        self.assertEqual(self.start(["setup", "--dry-run"], env, "./setup"), "agentik setup --dry-run")
        self.assertEqual(prog.name(env, TOOL), "agentik")
        door(os.path.join(bindir, "agentik"), "0.1.0")  # an older door hands nothing on
        self.assertEqual(self.start(["doctor"], env), "%s doctor" % LAUNCHER)
        self.assertEqual(prog.name(env, TOOL), TOOL)

    def test_r2_the_door_placed_off_path(self):
        door(os.path.join(self.bindir, "agentik"), "0.2.0")
        env = self.env()
        self.assertEqual(self.start(["doctor"], env, "./setup"), "~/.local/bin/agentik doctor")
        self.assertEqual(self.start(["doctor"], env, full=True), "%s/.local/bin/agentik doctor" % self.home)
        self.assertEqual(prog.name(env, TOOL), "agentik")

    def test_r4_no_door_the_tools_name(self):
        self.assertEqual(prog.name(self.env(), TOOL), TOOL)

    def test_a_path_with_a_space_is_quoted_after_the_tilde(self):
        self.assertEqual(prog.shown("/h/a b/c", "/h"), "~/'a b/c'")
        self.assertEqual(prog.shown("/h/a b/c", "/h", full=True), "'/h/a b/c'")


class OneFunctionTest(unittest.TestCase):
    """R1: no message and no call writes the tool's name before a verb any other way."""

    def test_r1_the_catalogue_names_a_command_by_its_verb(self):
        before = re.compile(r"\{tool\} (?:%s|-)" % VERBS)  # the loader drops a lone slot's backticks
        for mid, text in catalogue.load(str(PKG / "messages.md")).items():
            if mid.endswith(".title"):
                continue  # a title gives the name (R4)
            self.assertIsNone(before.search(text), mid)
            self.assertNotRegex(text, r"agentik(?:-suite)? (?:%s)\b" % VERBS, mid)

    def test_r1_no_source_line_writes_the_name_before_a_verb(self):
        name_then_verb = re.compile(r"""["']%s (?:%s|-)[^"']*["']\s*%%\s*\(?\s*(?:self\.|cmd\.)?tool\b""" % ("%s", VERBS))
        joined = re.compile(r"""\btool\s*\+\s*["'] """)
        as_name = re.compile(r"\btool=(?:self\.|cmd\.)?tool\b")
        for path in sorted(PKG.glob("*.py")):
            for n, line in enumerate(path.read_text().splitlines(), 1):
                for rule in (name_then_verb, joined, as_name):
                    self.assertIsNone(rule.search(line), "%s:%d: %s" % (path.name, n, line.strip()))


class PasteTest(Home):
    """Acceptance 1 to 4: each printed command, pasted into sh -c, finds its command."""

    def screen(self, argv, env):
        p = subprocess.run(argv, cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=120)
        return ANSI.sub("", p.stdout + p.stderr)

    def commands(self, text):
        found = [m.group(1) for line in text.splitlines() for m in COMMAND.finditer(line)]
        return [c for c in dict.fromkeys(found)
                if "--yes" not in c.split() and c.split()[-1] != "install-cli"]

    def paste(self, command, env):
        p = subprocess.run(["sh", "-c", command], cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=120)
        return p.returncode

    def test_a1_an_empty_home(self):
        env = self.env()
        screens = (["./setup", "--dry-run"], ["./setup"], [str(LAUNCHER), "doctor"],
                   ["plugins/suite/bin/agentik-suite", "doctor"])
        for argv in screens:
            text = self.screen(argv, env)
            found = self.commands(text)
            self.assertTrue(found, (argv, text))
            for c in found:
                self.assertNotEqual(self.paste(c, env), 127, (argv, c))
        hint = self.screen(["./setup", "--dry-run"], env).splitlines()[-1]
        self.assertIn("next: ./setup --dry-run", hint)
        self.assertIn(TOOL + " ", self.screen(["plugins/suite/bin/agentik-suite"], env).splitlines()[0])

    def placed(self):
        env = self.env()
        p = subprocess.run([str(LAUNCHER), "install-cli"], cwd=str(ROOT), env=env,
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        return env

    def test_a2_the_door_placed_off_path(self):
        env = self.placed()
        for argv in ([str(LAUNCHER), "doctor"], [str(LAUNCHER), "config"], [str(LAUNCHER)]):
            found = self.commands(self.screen(argv, env))
            self.assertTrue(found, argv)
            for c in found:
                self.assertTrue(c.startswith("~/.local/bin/agentik "), (argv, c))
                self.assertNotEqual(self.paste(c, env), 127, (argv, c))

    def test_a3_the_door_on_path(self):
        env = self.placed()
        env["PATH"] = self.bindir + ":" + env["PATH"]
        for argv in (["agentik", "doctor"], ["agentik"], ["agentik", "config"], ["agentik", "setup", "--dry-run"]):
            text = self.screen(argv, env)
            found = self.commands(text)
            self.assertTrue(found, argv)
            for c in found:
                self.assertTrue(c.startswith("agentik "), (argv, c))
                self.assertNotEqual(self.paste(c, env), 127, (argv, c))
            # the name is never the suite's; a file's own name in a path or a PATH listing stays
            named = [line for line in text.splitlines()
                     if re.search(r"(?<![/\w-])agentik-suite\b(?!\s+(?:~|/))", line)]
            self.assertEqual(named, [], argv)


class WordTest(Home):
    """R3: the root setup and the launcher hand on the word they were started with."""

    def echo(self):
        py = os.path.join(self.home, "py")
        with open(py, "w") as fh:
            fh.write('#!/bin/sh\necho "word=$AGENTIK_ARGV0"\n')
        os.chmod(py, 0o755)
        return py

    def word(self, argv, **more):
        env = self.env(AGENTIK_PYTHON=self.echo(), **more)
        p = subprocess.run(argv, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout.strip()

    def test_r3_the_words(self):
        self.assertEqual(self.word(["./setup", "--dry-run"]), "word=./setup")
        self.assertEqual(self.word(["plugins/suite/bin/agentik-suite", "doctor"]),
                         "word=plugins/suite/bin/agentik-suite")
        self.assertEqual(self.word([str(LAUNCHER)], AGENTIK_ARGV0="x/setup"), "word=x/setup")

    def test_r3_the_suite_takes_the_word_out_of_what_it_spawns(self):
        sys.path.insert(0, str(PKG.parent))
        from agentik_suite import cli
        env = self.env(AGENTIK_ARGV0="./setup")
        cli.Command(["version"], env, None, None)
        self.assertNotIn("AGENTIK_ARGV0", env)


if __name__ == "__main__":
    unittest.main()
