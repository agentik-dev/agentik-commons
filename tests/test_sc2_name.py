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
COMMAND = re.compile(r"(?:(?<=\s)|^)((?:\S*/setup|\S*agentik(?:-suite)?)(?: (?:%s|--?[a-z-]+))+)(?![\w:-])"
                     % VERBS)  # a title, `<name> doctor:`, is no command


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

    def commands(self, text, every=False):
        """Each printed command; with every False, not those that would write: --yes, install-cli."""
        found = list(dict.fromkeys(m.group(1) for line in text.splitlines() for m in COMMAND.finditer(line)))
        return found if every else [c for c in found if "--yes" not in c.split() and c.split()[-1] != "install-cli"]

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
            self.assertTrue(self.commands(text, every=True), (argv, text))
            for c in found:
                self.assertNotEqual(self.paste(c, env), 127, (argv, c))
        hint = self.screen(["./setup", "--dry-run"], env).splitlines()[-1]
        self.assertEqual(hint, "next: ./setup")  # row sm2 R1; no mark before next: (row sc4)
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


class FrozenTest(PasteTest):
    """Review 1's R1-F1: in a tree install-cli froze, a printed command names the launcher at
    <prefix>/bin/<tool>, never the content-hashed runner under <prefix>/share, which install-cli
    prunes and which skips the launcher's -I and its parent-env record."""
    RUNNER = re.compile(r"share/%s/[^/\s]+/" % TOOL)
    SCREENS = (["config", "sesion"], ["doctor"], [])

    def frozen(self, prefix=None):
        env = self.env()
        argv = [str(LAUNCHER), "install-cli"] + (["--prefix", prefix] if prefix else [])
        p = subprocess.run(argv, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        return env

    def check(self, launcher, env, start):
        later = []  # sc10: doctor may name install-cli alone; it is pasted once the screens are read
        for words in self.SCREENS:
            text = self.screen([launcher] + words, env)
            self.assertIsNone(self.RUNNER.search(text), (words, text))
            found, safe = self.commands(text, every=True), self.commands(text)
            self.assertTrue(found, (words, text))
            for c in found:
                self.assertTrue(c.startswith(start + " "), (words, c))
                if c in safe:
                    self.assertNotEqual(self.paste(c, env), 127, (words, c))
                elif c.split()[-1] == "install-cli" and c not in later:
                    later.append(c)
        for c in later:
            self.assertNotEqual(self.paste(c, env), 127, c)

    def test_f1_no_door_on_path(self):
        env = self.frozen()
        os.remove(os.path.join(self.bindir, "agentik"))
        env["PATH"] = self.bindir + ":" + SYSTEM
        self.check(TOOL, env, "~/.local/bin/" + TOOL)

    def test_f1_an_older_door_first_on_path(self):
        env = self.frozen()
        old = os.path.join(self.home, "old")
        door(os.path.join(old, "agentik"), "0.1.0")
        env["PATH"] = old + ":" + self.bindir + ":" + SYSTEM
        self.check(TOOL, env, "~/.local/bin/" + TOOL)

    def test_f1_a_prefix_off_path(self):
        prefix = os.path.join(self.home, "opt")
        env = self.frozen(prefix)
        self.check(os.path.join(prefix, "bin", TOOL), env, "~/opt/bin/" + TOOL)


class InPlaceTest(Home):
    """Phase 2, sp1-launcher-step's line: a plugin whose command lists no install-cli verb runs
    from its own folder, and setup's step 7 prints that file's doctor to run later. The line names
    the file by its path, as the plan's other file lines do, and it runs when pasted."""
    screen, commands, paste = PasteTest.screen, PasteTest.commands, PasteTest.paste
    ANSWER = ('{"schema":"agentik.describe/1","ok":true,"tool":"murmur","version":"1.0.0",'
              '"summary":"A made-up tool.","repo":"example/agentik-murmur","plugin":"murmur@agentik",'
              '"needs":[],"reads":[],"verbs":[{"name":"doctor","summary":"Checks.","top":false}]}')

    def plugin(self):
        src = os.path.join(self.home, ".claude", "plugins", "cache", "agentik", "murmur", "1.0.0",
                           "bin", "agentik-murmur")
        os.makedirs(os.path.dirname(src))
        with open(src, "w") as fh:
            fh.write("#!/bin/sh\ncase \"$1 $2\" in\n\"describe --json\") echo '%s' ;;\n"
                     "\"doctor \"*) exit 0 ;;\n*) exit 2 ;;\nesac\n" % self.ANSWER)
        os.chmod(src, 0o755)
        d = os.path.join(self.home, ".claude", "plugins")
        with open(os.path.join(d, "known_marketplaces.json"), "w") as fh:
            fh.write('{"agentik": {}}')
        with open(os.path.join(d, "installed_plugins.json"), "w") as fh:
            fh.write('{"version": 2, "plugins": {"murmur@agentik": [{"scope": "user", "version": "1.0.0",'
                     ' "installPath": "%s"}]}}' % os.path.dirname(os.path.dirname(src)))
        return src

    def test_p2_the_in_place_doctor_line_runs_when_pasted(self):
        src, env = self.plugin(), self.env()
        for argv in (["./setup", "murmur", "--dry-run"], [str(LAUNCHER), "setup", "murmur", "--dry-run"]):
            text = self.screen(argv, env)
            later = [line.split("later: ", 1)[1].strip().strip("`") for line in text.splitlines()
                     if "later: " in line]
            self.assertEqual(later, ["%s doctor" % src], (argv, text))
            self.assertEqual(self.paste(later[0], env), 0, (argv, later[0]))
            for c in self.commands(text):  # the suite's own lines, through the one function
                self.assertNotEqual(self.paste(c, env), 127, (argv, c))


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
