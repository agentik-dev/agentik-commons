"""The suite's own command (packet ak1a): its layout and copies, the one writer, the catalogue,
the verbs and the setup plan. Each run is the plugin's launcher in a temp HOME, with an env of
exactly HOME, PATH (/usr/bin:/bin and a folder of stubs) and XDG_CACHE_HOME; fixtures use
made-up plugin names. Nothing here writes outside its temp folder."""
import ast
import fcntl
import hashlib
import json
import os
import pty
import re
import select
import struct
import subprocess
import sys
import tempfile
import termios
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "suite"
LAUNCHER = PLUGIN / "bin" / "agentik-suite"
LIB = PLUGIN / "lib"
PACKAGE = LIB / "agentik_suite"
CATALOGUE = PACKAGE / "messages.md"
MANIFEST = PLUGIN / ".claude-plugin" / "plugin.json"
SYSTEM = "/usr/bin:/bin"
RECORDER = '#!/bin/sh\necho "$0 $*" >> "%s"\n'
ESC = "\x1b"
STDLIB = {"ast", "difflib", "json", "os", "re", "shutil", "sys", "shlex", "agentik_install"}

sys.path.insert(0, str(LIB))
from agentik_suite import catalogue, term  # noqa: E402


def version():
    return json.loads(MANIFEST.read_text())["version"]


def package_files():
    return sorted(p for p in PACKAGE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)


def writes_outside_term(source):
    """Each line of the source that prints or writes a stream itself: a print call, sys.stdout or
    sys.stderr named, a .write call, or os.write."""
    hits = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id == "print":
                hits.append(node.lineno)
            elif isinstance(f, ast.Attribute) and f.attr in ("write", "writelines"):
                hits.append(node.lineno)
        elif isinstance(node, ast.Attribute) and node.attr in (
                "stdout", "stderr", "__stdout__", "__stderr__"):
            hits.append(node.lineno)
    return hits


class Home(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = os.path.realpath(tmp.name)
        self.stubs = os.path.join(self.home, "stubs")
        self.cache = os.path.join(self.home, "cache")
        os.mkdir(self.stubs)
        self.calls = os.path.join(self.home, "calls")
        self.stub("claude", RECORDER % self.calls)

    def stub(self, name, body="#!/bin/sh\nexit 0\n"):
        path = os.path.join(self.stubs, name)
        with open(path, "w") as fh:
            fh.write(body)
        os.chmod(path, 0o755)
        return path

    def env(self, **more):
        env = {"HOME": self.home, "PATH": "%s:%s" % (self.stubs, SYSTEM),
               "XDG_CACHE_HOME": self.cache}
        env.update(more)
        return env

    def run_cli(self, *args, **more):
        p = subprocess.run([str(LAUNCHER), *args], capture_output=True, text=True,
                           env=self.env(**more), timeout=60)
        return p.returncode, p.stdout, p.stderr

    def run_pty(self, *args, cols=200, **more):
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, cols, 0, 0))
        p = subprocess.Popen([str(LAUNCHER), *args], stdin=slave, stdout=slave, stderr=slave,
                             env=self.env(**more), close_fds=True)
        os.close(slave)
        chunks = []
        try:
            while True:
                ready, _, _ = select.select([master], [], [], 30)
                if not ready:
                    break
                try:
                    data = os.read(master, 65536)
                except OSError:
                    break
                if not data:
                    break
                chunks.append(data)
        finally:
            os.close(master)
        return p.wait(timeout=30), b"".join(chunks).decode("utf-8", "replace")

    def snapshot(self):
        """Every file and link under HOME with its hash, less the launcher's bytecode cache."""
        skip = os.path.join(self.cache, "agentik")
        seen = {}
        for top, dirs, files in os.walk(self.home):
            if top == skip or top.startswith(skip + os.sep):
                continue
            for name in dirs + files:
                path = os.path.join(top, name)
                if skip.startswith(path + os.sep) or path == skip:
                    continue  # the cache folder and the folders that hold it
                if os.path.isfile(path) and not os.path.islink(path):
                    with open(path, "rb") as fh:
                        seen[path] = hashlib.sha256(fh.read()).hexdigest()
                else:
                    seen[path] = "dir" if os.path.isdir(path) else "link"
        return seen

    def plugin_files(self, config, plugins):
        os.makedirs(os.path.join(config, "plugins"), exist_ok=True)
        with open(os.path.join(config, "plugins", "known_marketplaces.json"), "w") as fh:
            json.dump({"agentik": {"source": {"source": "github", "repo": "example/market"}}}, fh)
        with open(os.path.join(config, "plugins", "installed_plugins.json"), "w") as fh:
            json.dump({"version": 2, "plugins": {
                "%s@agentik" % name: [{"scope": "user", "version": ver,
                                       "installPath": os.path.join(self.home, "inst", name, ver)}]
                for name, ver in plugins.items()}}, fh)

    def plan(self, *names, **more):
        code, out, err = self.run_cli("setup", "--dry-run", "--json", *names, **more)
        self.assertEqual(code, 0, err)
        return json.loads(out)


class LayoutTest(unittest.TestCase):
    """R1 and R2: the copies, the conf, the runner, the floor and no tool's name."""

    def test_copies_are_byte_equal(self):
        self.assertEqual(LAUNCHER.read_bytes(), (ROOT / "scripts" / "plugin-launcher").read_bytes())
        self.assertEqual((LIB / "agentik_install.py").read_bytes(),
                         (ROOT / "scripts" / "agentik_install.py").read_bytes())
        self.assertTrue(os.access(LAUNCHER, os.X_OK))
        self.assertFalse((PLUGIN / "bin" / "agentik").exists())  # the door is not copied in

    def test_conf_holds_its_five_keys(self):
        lines = (LIB / "agentik-tool.conf").read_text().splitlines()
        self.assertEqual([line.split("=", 1)[0] for line in lines],
                         ["tool_name", "remedy", "runner", "old_name", "old_state"])
        conf = dict(line.split("=", 1) for line in lines)
        self.assertEqual((conf["tool_name"], conf["runner"]), ("agentik-suite", "agentik-suite"))

    def test_runner_is_four_lines_on_the_floor(self):
        text = (LIB / "agentik-suite").read_text()
        self.assertEqual(len(text.splitlines()), 4)
        self.assertTrue(text.startswith("#!/usr/bin/python3\n"))

    def test_stdlib_only_at_3_9(self):
        for path in package_files() + [LIB / "agentik-suite"]:
            if path.suffix not in (".py", "") or path.name == "messages.md":
                continue
            tree = ast.parse(path.read_text(), feature_version=(3, 9))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    mods = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and not node.level:
                    mods = [node.module.split(".")[0]]
                else:
                    continue
                for mod in mods:
                    self.assertIn(mod, STDLIB | {"agentik_suite"}, "%s: %s" % (path.name, mod))

    def test_no_tool_name_in_the_package_or_these_tests(self):
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        tools = [p["name"] for p in market["plugins"] if p["name"] != "suite"]
        self.assertTrue(tools)
        pattern = re.compile(r"\b(?:%s)\b" % "|".join(map(re.escape, tools)), re.I)
        for path in package_files() + [LIB / "agentik-suite", Path(__file__)]:
            hit = pattern.search(path.read_text())
            self.assertIsNone(hit, "%s names %s" % (path.name, hit and hit.group(0)))


class WriterTest(unittest.TestCase):
    """R3: term is the one writer; R4: the catalogue."""

    def test_nothing_but_term_writes(self):
        for path in package_files():
            if path.suffix == ".py" and path.name != "term.py":
                self.assertEqual(writes_outside_term(path.read_text()), [], path.name)

    def test_the_check_catches_a_print(self):
        source = (PACKAGE / "cli.py").read_text()
        self.assertTrue(writes_outside_term(source + "\nprint('x')\n"))
        self.assertTrue(writes_outside_term("import sys\nsys.stderr.write('x')\n"))

    def test_catalogue_loader(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "m.md")
            with open(path, "w") as fh:
                fh.write("# T\n\nprose\n- `a.b`: `{x}` at `{x}/y` and `z`\n- `c`: plain\n")
            got = catalogue.load(path)
        self.assertEqual(got, {"a.b": "{x} at `{x}/y` and `z`", "c": "plain"})
        self.assertEqual(catalogue.fill(got["a.b"], {"x": "q"}), "q at `q/y` and `z`")

    def test_catalogue_voice_rules(self):
        messages = catalogue.load()
        for mid, text in messages.items():
            self.assertNotRegex(text, r"(?i)\b(successfully|please|oops)\b|!", mid)
        code = "\n".join(p.read_text() for p in package_files() if p.suffix == ".py")
        used = set(re.findall(r'"((?:help|hint|verb|usage|flag|version|err|setup)\.[a-z_.]+)"', code))
        dynamic = {"verb.", "usage.", "flag.", "setup."}
        for mid in used - dynamic:
            self.assertIn(mid, messages)

    def stream(self, tty, encoding="utf-8"):
        import io

        class Fake(io.StringIO):
            def isatty(self):
                return tty

            @property
            def encoding(self):
                return encoding
        return Fake()

    def test_off_a_terminal_words_and_no_escape(self):
        out, err = self.stream(False), self.stream(False)
        t = term.Term(env={}, out=out, err=err)
        t.table([("ok", ["a", term.name("b"), "x" * 300], None), ("note", ["c", "d", "e"], "run: z")])
        t.hint("version.line", tool="t", version="1")
        text = out.getvalue() + err.getvalue()
        self.assertNotIn(ESC, text)
        self.assertIn("  ok    a  b  " + "x" * 300 + "\n", text)
        self.assertIn("  note  c  d  e\n", text)
        self.assertIn("\n" + " " * 14 + "run: z\n", text)
        self.assertEqual(err.getvalue(), "note  t 1\n")

    def test_on_a_terminal_glyphs_colour_and_the_switches(self):
        for env, flag, colour in (({}, False, True), ({"NO_COLOR": "1"}, False, False),
                                  ({"TERM": "dumb"}, False, False), ({}, True, False)):
            out = self.stream(True)
            term.Term(env=env, no_color=flag, out=out, err=self.stream(True)).table(
                [("ok", ["a"], None), ("fail", ["b"], None)])
            self.assertIn("✓", out.getvalue())
            self.assertIn("✗", out.getvalue())
            self.assertEqual(ESC in out.getvalue(), colour, env)


class VerbTest(Home):
    """R6 to R8, acceptance 1 to 6."""

    def test_a1_version(self):
        self.assertEqual(self.run_cli("--version"), (0, "agentik-suite %s\n" % version(), ""))
        self.assertEqual(self.run_cli("version")[:2], (0, "agentik-suite %s\n" % version()))

    def test_a2_setup_plans_seven_steps_and_writes_nothing(self):
        before = self.snapshot()
        code, out, err = self.run_cli("setup", "--dry-run")
        self.assertEqual(code, 0, err)
        steps = [line.split()[0] for line in out.splitlines()[1:] if re.match(r"  \d", line)]
        self.assertEqual(steps, [str(n) for n in range(1, 8)])
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(os.path.exists(self.calls))
        self.assertEqual(sorted({s["n"] for s in self.plan()["steps"]}), list(range(1, 8)))
        self.assertEqual(self.snapshot(), before)

    def test_a3_steps_two_to_four_read_the_plugin_files(self):
        config = os.path.join(self.home, ".claude")
        absent = self.plan("alpha", "beta")
        for s in absent["steps"]:
            if s["n"] in (2, 3, 4):
                self.assertEqual(s["state"], "todo", s)
        self.assertEqual([s["detail"] for s in absent["steps"] if s["n"] == 3],
                         ["not installed; setup would install it"] * 2)
        self.plugin_files(config, {"alpha": "1.2.0"})
        os.makedirs(os.path.join(self.home, ".local", "bin"))
        with open(os.path.join(self.home, ".local", "bin", "agentik-alpha"), "w") as fh:
            fh.write("#!/bin/sh\nVERSION=1.2.0\n")
        got = {(s["n"], s["subject"]): s for s in self.plan("alpha", "beta")["steps"]}
        self.assertEqual(got[(2, "agentik")]["state"], "ok")
        self.assertEqual(got[(3, "alpha@agentik")]["state"], "ok")
        self.assertEqual(got[(3, "beta@agentik")]["command"], "claude plugin install beta@agentik")
        self.assertEqual(got[(4, "~/.local/bin/agentik-alpha")]["state"], "ok")
        self.assertEqual(got[(4, "~/.local/bin/agentik-beta")]["state"], "todo")
        # a launcher behind its plugin names the plugin's own install-cli
        self.plugin_files(config, {"alpha": "1.3.0"})
        s = {(s["n"], s["subject"]): s for s in self.plan("alpha")["steps"]}[
            (4, "~/.local/bin/agentik-alpha")]
        self.assertEqual(s["command"], "%s install-cli" % os.path.join(
            self.home, "inst", "alpha", "1.3.0", "bin", "agentik-alpha"))
        # CLAUDE_CONFIG_DIR moves both files
        other = os.path.join(self.home, "other")
        self.plugin_files(other, {"gamma": "0.1.0"})
        moved = self.plan("gamma", CLAUDE_CONFIG_DIR=other)["steps"]
        self.assertEqual([s["state"] for s in moved if s["n"] == 3], ["ok"])

    def test_a3_default_set_is_the_manifests_dependencies(self):
        deps = json.loads(MANIFEST.read_text())["dependencies"]
        self.assertEqual(self.plan()["plugins"], deps)

    def test_a4_piped_words_no_escape(self):
        self.stub("agentik-zeta")
        for args in (("help",), ("setup", "--dry-run")):
            code, out, err = self.run_cli(*args)
            self.assertEqual(code, 0)
            text = out + err
            self.assertNotIn(ESC, text, args)
            self.assertRegex(text, r"(?m)^ *(\d  )?ok  ", args)
            self.assertRegex(text, r"(?m)^ *(\d  )?note  ", args)
        # the help lists the stub by name and path, first in PATH order winning
        self.assertIn("agentik-zeta  %s" % os.path.join(self.stubs, "agentik-zeta"),
                      self.run_cli("help")[1])

    def test_a4_on_a_pty_colour_and_glyph(self):
        code, text = self.run_pty("setup", "--dry-run")
        self.assertEqual(code, 0, text)
        self.assertIn(ESC + "[", text)
        self.assertIn("✓", text)
        code, text = self.run_pty("setup", "--dry-run", NO_COLOR="1")
        self.assertNotIn(ESC + "[", text)
        self.assertIn("✓", text)
        code, text = self.run_pty("setup", "--dry-run", "--no-color", cols=40)
        self.assertIn("…", text)

    def test_a5_json_is_one_object(self):
        for args in (("setup", "--dry-run", "--json"), ("version", "--json"), ("--json",)):
            code, out, err = self.run_cli(*args)
            self.assertEqual((code, err), (0, ""), args)
            self.assertEqual(len(out.splitlines()), 1, args)
            obj = json.loads(out)
            self.assertTrue(obj["ok"])
            self.assertRegex(obj["schema"], r"^agentik\.[a-z]+/\d+$")
        code, out, err = self.run_cli("stup", "--json")
        obj = json.loads(out)
        self.assertEqual((code, obj["ok"], obj["error"]["code"]), (2, False, "unknown_verb"))
        self.assertEqual(set(obj["error"]), {"code", "message", "remedy"})

    def test_a6_usage_exits_two(self):
        code, out, err = self.run_cli("stup")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("setup", err)
        before = self.snapshot()
        for args in (("setup",), ("setup", "-y"), ("setup", "--yes", "alpha")):
            code, out, err = self.run_cli(*args)
            self.assertEqual((code, out), (2, ""), args)
            self.assertEqual(len(err.splitlines()), 1)
            self.assertIn("setup --dry-run", err)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(os.path.exists(self.calls))
        for args in (("--jsn",), ("version", "--dry-run"), ("version", "extra"),
                     ("setup", "--dry-run", "Bad_name"), ("help", "nosuch")):
            self.assertEqual(self.run_cli(*args)[0], 2, args)

    def test_help_and_quiet(self):
        for args in ((), ("help",), ("-h",), ("--help",)):
            code, out, err = self.run_cli(*args)
            self.assertEqual(code, 0, args)
            for verb in ("help", "version", "setup"):
                self.assertRegex(out, r"(?m)^  %s  " % verb)
            self.assertIn("next:", err)
        self.assertEqual(self.run_cli("-q")[2], "")
        code, out, err = self.run_cli("setup", "--help")
        self.assertIn("--dry-run", out)


if __name__ == "__main__":
    unittest.main()
