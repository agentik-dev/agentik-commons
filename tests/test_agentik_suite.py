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
import shlex
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import termios
import time
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
STDLIB = {"ast", "datetime", "difflib", "fnmatch", "json", "os", "re", "shutil", "sys", "shlex", "agentik_install",
          "select", "signal", "subprocess", "tempfile", "time", "agentik_hygiene", "hashlib", "unicodedata"}

sys.path.insert(0, str(LIB))
from agentik_suite import catalogue, settings, term  # noqa: E402


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
        os.makedirs(os.path.dirname(path), exist_ok=True)
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

    def plugin_files(self, config, plugins, whole=True):
        """Claude Code's two files; whole, each installPath holds its plugin's launcher."""
        for name, ver in plugins.items():
            if whole:
                self.stub("../inst/%s/%s/bin/agentik-%s" % (name, ver, name))
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
        # packet ak2 R4: the suite's door is a cp of bin/agentik, placed by no script
        self.assertEqual((PLUGIN / "bin" / "agentik").read_bytes(), (ROOT / "bin" / "agentik").read_bytes())
        self.assertTrue(os.access(PLUGIN / "bin" / "agentik", os.X_OK))

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
        self.voice_rules(CATALOGUE)

    def test_r8_an_item_the_loader_cannot_read_is_red(self):
        text = CATALOGUE.read_text()
        for bad in (text.replace("- `flag.yes`:", "- `flag.Yes`:"),
                    text.replace("- `flag.yes`:", "- `flag.yes`")):
            with tempfile.TemporaryDirectory() as tmp:
                copy = Path(tmp) / "messages.md"
                copy.write_text(bad)
                with self.assertRaises((ValueError, AssertionError)):
                    self.voice_rules(copy)

    def voice_rules(self, path):
        messages = catalogue.load(str(path))
        for mid, text in messages.items():
            self.assertNotRegex(text, r"(?i)\b(successfully|please|oops)\b|!", mid)
        code = "\n".join(p.read_text() for p in package_files() if p.suffix == ".py")
        used = set(re.findall(
            r'"((?:help|hint|verb|usage|flag|version|err|setup|config|describe|setting)\.[a-z_.]+)"', code))
        dynamic = {"verb.", "usage.", "flag.", "setup.", "setting.", "config.label.", "config.state."}
        for mid in used - dynamic - {m for m in used if m.endswith((".yaml", ".json"))}:
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
        self.assertEqual(err.getvalue(), "t 1\n")  # a hint has no mark (row sc4 R1)

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
            self.assertRegex(text, r"(?m)^(?: *(\d  )?note  |next: )", args)  # a hint has no mark (sc4)
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
        self.assertNotIn("…", text)  # fix round 1, R7: nothing is cut

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
        for args in (("setup", "Bad_name"), ("setup", "-y", "Bad_name"), ("setup", "--yes", "alpha", "Bad_name")):
            code, out, err = self.run_cli(*args)
            self.assertEqual((code, out), (2, ""), args)
            self.assertEqual(len(err.splitlines()), 2)  # the cause, then next: (row sc4 R1)
            self.assertIn("\nnext: ", err)
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


class StreamTest(Home):
    """Fix round 1, R4 to R6: a stream closed or gone, a character a stream cannot hold, a file
    crafted to break the read."""

    def bash(self, line, **more):
        p = subprocess.run(["/bin/bash", "-c", line, "sh", str(LAUNCHER)], capture_output=True,
                           env=self.env(**more), timeout=60)
        return p.returncode, p.stdout, p.stderr

    def test_r4_a_closed_or_gone_stream(self):
        self.assertEqual(self.bash('"$1" --version >&-'), (0, b"", b""))
        self.assertEqual(self.bash('"$1" stup 2>&-'), (2, b"", b""))
        for quiet in (True, False):
            p = subprocess.Popen([str(LAUNCHER), "help"] + (["-q"] if quiet else []),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env())
            p.stdout.close()  # the reader has gone before the first write
            err = p.stderr.read().decode()
            p.stderr.close()
            self.assertEqual(p.wait(timeout=60), 0, err)
            if quiet:
                self.assertEqual(err, "")
            else:  # the hint alone, no word of the broken pipe
                self.assertRegex(err, r"\Anext: [^\n]*\n\Z")

    def test_r5_a_character_the_stream_cannot_hold(self):
        code, text = self.run_pty("setup", "--dry-run", cols=80, LANG="en_US.ISO8859-1")
        self.assertEqual(code, 0, text)
        self.assertNotIn("Traceback", text)
        for lang in ({}, {"LANG": "en_US.UTF-8"}):
            p = subprocess.run([str(LAUNCHER).encode(), b"\xff", b"--json"], capture_output=True,
                               env=self.env(**lang), timeout=60)
            self.assertEqual((p.returncode, p.stderr), (2, b""), lang)
            self.assertEqual(len(p.stdout.splitlines()), 1)
            obj = json.loads(p.stdout.decode("ascii"))
            self.assertEqual((obj["ok"], obj["error"]["code"]), (False, "unknown_verb"))
        out = WriterTest.stream(None, True, encoding="latin-1")
        term.Term(env={"NO_COLOR": "1"}, out=out, err=WriterTest.stream(None, True)).table(
            [("ok", ["a", "日本/x"], None)])
        self.assertEqual(out.getvalue(), "  ok  a  ??/x\n")

    def test_r6_a_crafted_file(self):
        plugins = os.path.join(self.home, ".claude", "plugins")
        os.makedirs(plugins)
        with open(os.path.join(plugins, "installed_plugins.json"), "w") as fh:
            fh.write("[" * 100000)
        code, out, err = self.run_cli("setup", "--dry-run", "alpha")
        self.assertEqual(code, 0, err)
        self.assertNotIn("Traceback", err)
        self.assertEqual([s["state"] for s in self.plan("alpha")["steps"] if s["n"] == 3], ["todo"])
        inst = os.path.join(self.home, "inst", "alpha")
        os.makedirs(os.path.join(inst, "bin"))
        with open(os.path.join(inst, "bin", "agentik-alpha"), "w") as fh:
            fh.write("#!/bin/sh\n")
        with open(os.path.join(plugins, "installed_plugins.json"), "w") as fh:
            json.dump({"plugins": {"alpha@agentik": [
                {"version": "1.0\x1b[31m\x9b2J", "installPath": inst}]}}, fh)
        odd = os.path.join(self.home, "b\x1b[2Jin")
        os.mkdir(odd)
        self.stub("agentik-zeta")
        os.rename(os.path.join(self.stubs, "agentik-zeta"), os.path.join(odd, "agentik-zeta"))
        for args in (("setup", "--dry-run", "alpha"), ("setup", "--dry-run", "alpha", "--json"),
                     ("help",), ("help", "--json")):
            code, out, err = self.run_cli(*args, PATH="%s:%s:%s" % (odd, self.stubs, SYSTEM))
            self.assertEqual(code, 0, err)
            for byte in (ESC, "\x9b", "\\u001b", "\\u009b"):
                self.assertNotIn(byte, out + err, args)
        self.assertIn("1.0[31m2J", self.run_cli("setup", "--dry-run", "alpha")[1])



PLUGIN_BIN = """#!/bin/sh
# a plugin's own launcher, as the tests' claude stub installs it
case "$1" in
install-cli)
    exe="$HOME/.local/bin/$(basename "$0")"
    mkdir -p "$HOME/.local/bin" || exit 1
    printf '#!/bin/sh\\nVERSION=1.0.0\\nexec "%s" "$@"\\n' "$0" > "$exe" && chmod 755 "$exe" &&
    printf '#!/bin/sh\\n' > "$HOME/.local/bin/agentik" && chmod 755 "$HOME/.local/bin/agentik" ;;
doctor) exit 0 ;;
*) exit 2 ;;
esac
"""
CLAUDE_STUB = """#!/usr/bin/python3
# claude, as far as the plan's lines need it: plugin marketplace add, plugin install
import json, os, shutil, sys
d = os.path.join(os.environ["HOME"], ".claude", "plugins")
os.makedirs(d, exist_ok=True)
a = sys.argv[1:]
if a[:3] == ["plugin", "marketplace", "add"] and len(a) == 4:
    json.dump({"agentik": {}}, open(os.path.join(d, "known_marketplaces.json"), "w"))
elif a[:2] == ["plugin", "install"] and len(a) == 3 and a[2].endswith("@agentik"):
    if not os.path.exists(os.path.join(d, "known_marketplaces.json")):
        sys.exit(1)
    name = a[2].split("@")[0]
    root = os.path.join(d, "cache", "agentik", name, "1.0.0")
    os.makedirs(os.path.join(root, "bin"), exist_ok=True)
    shutil.copy(%r, os.path.join(root, "bin", "agentik-" + name))
    path = os.path.join(d, "installed_plugins.json")
    table = json.load(open(path)) if os.path.exists(path) else {"version": 2, "plugins": {}}
    table["plugins"][a[2]] = [{"scope": "user", "version": "1.0.0", "installPath": root}]
    json.dump(table, open(path, "w"))
else:
    sys.exit(2)
"""


class PlanTruthTest(Home):
    """Fix round 1, R1 to R3 and R7: each row tells the truth, and nothing is cut."""

    def whole(self, plugins, place=True):
        """The plugins installed whole, each launcher placed at its version when place is set."""
        self.plugin_files(os.path.join(self.home, ".claude"), plugins)
        for name, ver in plugins.items():
            if place:
                self.place("agentik-" + name, ver)

    def place(self, exe, ver):
        os.makedirs(self.bindir, exist_ok=True)
        with open(os.path.join(self.bindir, exe), "w") as fh:
            fh.write("#!/bin/sh\nVERSION=%s\n" % ver)
        os.chmod(os.path.join(self.bindir, exe), 0o755)

    @property
    def bindir(self):
        return os.path.join(self.home, ".local", "bin")

    def by_subject(self, *names, **more):
        return {(s["n"], s["subject"]): s for s in self.plan(*names, **more)["steps"]}

    def test_r1_the_doors_row_names_an_install_cli(self):
        """Packet ak2b R5: the door's row names this command's own install-cli, never a plugin's."""
        self.whole({"alpha": "1.0.0", "beta": "2.0.0"})
        self.place("agentik-suite", version())
        door = self.by_subject("alpha", "beta")[(5, "~/.local/bin/agentik")]
        self.assertEqual(shlex.split(door["command"]), [str(LAUNCHER), "install-cli"])
        self.assertIn("run: " + door["command"], self.run_cli("setup", "--dry-run", "alpha", "beta")[1])
        # the suite's launcher not placed: its row carries the line, and the door's row points at it
        os.remove(os.path.join(self.bindir, "agentik-suite"))
        got = self.by_subject("alpha", "beta")
        self.assertIsNone(got[(5, "~/.local/bin/agentik")]["command"])
        self.assertIn("line above", got[(5, "~/.local/bin/agentik")]["detail"])
        self.assertEqual(got[(5, "~/.local/bin/agentik-suite")]["command"], door["command"])
        # an older door is todo; a newer one and one with no version are ok
        self.place("agentik-suite", version())
        for ver, state in (("0.1.0", "todo"), ("9.0.0", "ok"), ("banana", "ok")):
            self.place("agentik", ver)
            got = self.by_subject("alpha", "beta")[(5, "~/.local/bin/agentik")]
            self.assertEqual((got["state"], bool(got["command"])), (state, state == "todo"), ver)

    def test_r2_the_closing_hint_by_state(self):
        self.whole({"alpha": "1.0.0"})
        self.place("agentik-suite", version())
        self.place("agentik", "0")
        path = "%s:%s:%s" % (self.bindir, self.stubs, SYSTEM)
        steps = self.plan("alpha", PATH=path)["steps"]
        self.assertEqual({s["state"] for s in steps if s["n"] <= 6}, {"ok"})
        code, out, err = self.run_cli("setup", "--dry-run", "alpha", PATH=path)
        self.assertIn("setup has nothing left to do", err)
        self.assertNotIn("run each", err)
        self.assertIn("yours to run later: %s doctor" % os.path.join(self.bindir, "agentik-alpha"), out)
        # no claude on PATH: the hint names it, and no line sends the reader to claude
        os.remove(os.path.join(self.stubs, "claude"))
        code, out, err = self.run_cli("setup", "--dry-run", "alpha")
        self.assertEqual(code, 0, err)
        self.assertIn("install claude", err)
        self.assertNotIn("run:", out)
        self.assertNotIn("claude plugin", out + err)

    def test_r2_r3_each_run_line_works_in_order(self):
        home = os.path.join(self.home, "a home")  # every path in a command holds a space
        os.mkdir(home)
        template = os.path.join(self.home, "plugin-bin")
        with open(template, "w") as fh:
            fh.write(PLUGIN_BIN)
        os.chmod(template, 0o755)
        self.stub("claude", CLAUDE_STUB % template)
        env = self.env(HOME=home)
        ran = []
        for _ in range(4):
            code, out, err = self.run_cli("setup", "--dry-run", "alpha", "beta", HOME=home)
            self.assertEqual(code, 0, err)
            labels = ("would run: ", "yours to run later: ")  # row sm1-setup-ask: the doctors are the reader's
            for line in [l.strip().split(": ", 1)[1] for l in out.splitlines() if l.strip().startswith(labels)]:
                words = shlex.split(line)
                if words[0].startswith("/"):
                    self.assertTrue(os.path.isfile(words[0]), line)
                p = subprocess.run(["/bin/sh", "-c", line], env=env, capture_output=True, timeout=60)
                self.assertEqual(p.returncode, 0, (line, p.stderr))
                ran.append(words[-1])
        # the suite's own install-cli first, in step 5, then step 4's two, then the doctors
        self.assertEqual(ran[:8], ["agentik-dev/agentik-commons", "alpha@agentik", "beta@agentik",
                                   "install-cli", "install-cli", "install-cli", "doctor", "doctor"])
        got = self.by_subject("alpha", "beta", HOME=home)
        self.assertEqual({s["state"] for s in got.values() if s["n"] in (2, 3, 4)}, {"ok"})
        self.assertEqual(got[(5, "~/.local/bin/agentik")]["state"], "ok")

    def test_r3_installed_means_its_files_are_there(self):
        self.plugin_files(os.path.join(self.home, ".claude"), {"alpha": "1.0.0"}, whole=False)
        got = self.by_subject("alpha")
        self.assertEqual(got[(3, "alpha@agentik")]["state"], "todo")
        self.assertEqual(got[(3, "alpha@agentik")]["command"], "claude plugin install alpha@agentik")
        self.assertIsNone(got[(4, "~/.local/bin/agentik-alpha")]["command"])
        code, out, err = self.run_cli("setup", "--dry-run", "alpha")
        self.assertNotIn(os.path.join(self.home, "inst"), out + err)

    def test_m2_a_plugin_that_ships_no_command(self):
        """Review 2's F2: an installed plugin whose folder holds no launcher is installed, and
        step 4 says it ships no command; a reinstall is never proposed for it."""
        self.plugin_files(os.path.join(self.home, ".claude"), {"notes": "1.0.0"}, whole=False)
        folder = os.path.join(self.home, "inst", "notes", "1.0.0")
        os.makedirs(os.path.join(folder, ".claude-plugin"))
        got = self.by_subject("notes")
        self.assertEqual(got[(3, "notes@agentik")]["state"], "ok")
        self.assertEqual(got[(4, "~/.local/bin/agentik-notes")]["state"], "ok")
        self.assertIn("ships no command", got[(4, "~/.local/bin/agentik-notes")]["detail"])
        self.assertEqual(got[(7, "agentik-notes")]["state"], "ok")
        for s in got.values():
            self.assertNotIn("claude plugin install", s["command"] or "")
            self.assertNotIn("agentik-notes", s["command"] or "")
        code, out, err = self.run_cli("setup", "--dry-run", "notes")
        self.assertNotIn("install it again", out + err)
        # its folder gone: then it is not whole, and the reinstall is proposed
        shutil.rmtree(folder)
        got = self.by_subject("notes")
        self.assertEqual(got[(3, "notes@agentik")]["command"], "claude plugin install notes@agentik")

    def test_m3_l1_the_hint_when_only_the_path_line_is_left(self):
        """Review 2's L1: steps 1 to 5 ok, ~/.local/bin off PATH: the hint names the add line."""
        self.whole({"alpha": "1.0.0"})
        self.place("agentik-suite", version())
        self.place("agentik", "0")
        code, out, err = self.run_cli("setup", "--dry-run", "alpha")
        self.assertIn("add to your shell profile", out)
        self.assertNotIn("run each", err)
        self.assertIn("the line marked add", err)

    def test_m3_l2_a_set_up_machine_is_no_dead_end(self):
        """Review 2's L2, under packet ak2b R5: a set-up machine's plan, the suite's launcher not
        placed, names this command's install-cli, and the hint says to run it."""
        self.whole({"alpha": "1.0.0"})
        self.place("agentik", "0")
        path = "%s:%s:%s" % (self.bindir, self.stubs, SYSTEM)
        code, out, err = self.run_cli("setup", "--dry-run", "alpha", PATH=path)
        self.assertIn("run: %s install-cli" % LAUNCHER, out)
        self.assertIn("run each", err)
        self.assertNotIn("a later version", out)

    def test_m3_l4_step_fives_path_is_one_shell_word(self):
        """Review 2's L4, under packet ak2b R5: the path in step 5's command is one shell word."""
        root = os.path.join(self.home, "pl ug", "suite")
        shutil.copytree(str(PLUGIN), root, ignore=shutil.ignore_patterns("__pycache__"))
        p = subprocess.run([os.path.join(root, "bin", "agentik-suite"), "setup", "--dry-run",
                            "--json", "alpha"], capture_output=True, text=True, env=self.env(),
                           timeout=60)
        command = [s for s in json.loads(p.stdout)["steps"] if s["id"] == "suite"][0]["command"]
        self.assertEqual(shlex.split(command), [os.path.join(root, "bin", "agentik-suite"), "install-cli"])

    def test_m1_a_blocked_plan_promises_no_line_it_withholds(self):
        """Review 2's F1: with step 1 blocked no run: line is printed, so the door's row names none."""
        self.whole({"alpha": "1.0.0"})
        self.place("agentik-suite", version())
        nogit = "%s:/bin" % self.stubs
        for gone, placed in (("git", True), ("claude", True), ("git", False)):
            self.stub("claude", RECORDER % self.calls)
            if gone == "claude":
                os.remove(os.path.join(self.stubs, "claude"))
            if not placed:
                os.remove(os.path.join(self.bindir, "agentik-alpha"))
            more = {"PATH": nogit} if gone == "git" else {}
            steps = self.plan("alpha", **more)["steps"]
            self.assertIn((1, gone, "blocked"), [(s["n"], s["subject"], s["state"]) for s in steps])
            self.assertEqual([s for s in steps if s["command"] and s["id"] != "path"], [])
            door = [s for s in steps if s["id"] == "door"][0]
            self.assertIsNone(door["command"])
            for promise in ("below", "step 4", "install-cli"):
                self.assertNotIn(promise, door["detail"], (gone, placed, door["detail"]))
            code, out, err = self.run_cli("setup", "--dry-run", "alpha", **more)
            self.assertNotIn("run:", out)

    def test_r7_nothing_is_cut_on_a_terminal(self):
        commands = [s["command"] for s in self.plan()["steps"] if s["command"]]
        self.assertTrue(commands)
        for cols in (80, 40):
            code, text = self.run_pty("setup", "--dry-run", cols=cols)
            self.assertEqual(code, 0, text)
            plain = re.sub(ESC + r"\[[0-9;]*m", "", text).replace("\r", "")
            self.assertNotIn("…", plain)
            for command in commands:
                self.assertIn(command, plain, cols)
        out = WriterTest.stream(None, True)
        term.Term(env={"NO_COLOR": "1"}, out=out, err=WriterTest.stream(None, True)).table(
            [("ok", ["a", "x" * 100], "run: z")])
        self.assertEqual(out.getvalue(), "  ✓  a\n" + " " * 8 + "x" * 100 + "\n" + " " * 8 + "run: z\n")



class CorruptInstallTest(Home):
    """Fix round 1, R9: a plugin copy with no catalogue, or a manifest that cannot be read."""

    def copy(self):
        root = os.path.join(self.home, "plugin copy")
        shutil.copytree(str(PLUGIN), root, ignore=shutil.ignore_patterns("__pycache__"))
        return root

    def test_r9_one_plain_line_names_the_file(self):
        for broken, args in (("lib/agentik_suite/messages.md", ("--version",)),
                             (".claude-plugin/plugin.json", ("--version",)),
                             (".claude-plugin/plugin.json", ("version", "--json"))):
            root = self.copy()
            path = os.path.join(root, broken)
            if broken.endswith(".md"):
                os.remove(path)
            else:
                with open(path, "w") as fh:
                    fh.write("{nope")
            p = subprocess.run([os.path.join(root, "bin", "agentik-suite"), *args],
                               capture_output=True, text=True, env=self.env(), timeout=60)
            text = p.stdout + p.stderr
            self.assertEqual(p.returncode, 2, text)
            self.assertNotIn("Traceback", text)
            self.assertNotIn("0.0.0-unknown", text)
            self.assertIn(path, text)
            if "--json" in args:
                self.assertFalse(json.loads(p.stdout)["ok"])
            else:
                lines = 1 if broken.endswith(".md") else 2  # a manifest: the cause, then next: (row sc4)
                self.assertEqual((p.stdout, len(p.stderr.splitlines())), ("", lines))
            shutil.rmtree(root)


DEMO = """#!/usr/bin/python3
import json, os, sys
with open(%(calls)r, "a") as fh:
    fh.write(" ".join(sys.argv[1:]) + "\\n")
home = os.environ["HOME"]
user = os.path.join(home, ".config", "demo", "config.yaml")
def s(key, value, default, line, kind, live):
    src = {"layer": "user", "path": user, "line": line} if line else {"layer": "default", "path": None, "line": None}
    change = {"kind": kind, "command": "agentik-demo set %%s VALUE" %% key if kind == "command" else None,
              "path": user if kind == "edit" else None, "block": None, "note": None}
    values = [{"layer": "default", "value": default}] + ([{"layer": "user", "value": value}] if line else [])
    return {"key": key, "value": value, "default": default, "type": "string", "choices": None,
            "summary": "The %%s of each line." %% key, "source": src, "change": change, "live": live,
            "values": values, "extra": 1}
args = sys.argv[1:]
if args == ["describe", "--json"]:
    print(json.dumps({"schema": "agentik.describe/1", "ok": True, "tool": "demo", "version": "1.2.0",
        "summary": "A made-up tool.", "repo": "example/demo", "plugin": "demo@agentik", "needs": [],
        "verbs": [{"name": "set", "summary": "Set one.", "top": True}], "unknown": 1,
        "reads": [{"kind": "config", "name": "settings", "argv": ["describe", "config", "--json"]}]}))
elif args[:3] == ["describe", "config", "--json"]:
    rows = [s("colour", "dark", "light", 2, "command", False), s("width", 80, 80, None, "edit", True),
            s("mode", "plain", "plain", None, "fixed", True)]
    if args[3:]:
        rows = [r for r in rows if r["key"] == args[3]]
    print(json.dumps({"schema": "agentik.config/1", "ok": True, "tool": "demo", "settings": rows,
        "layers": [{"name": "default", "path": None, "present": True, "travels": False},
                   {"name": "user", "path": user, "present": True, "travels": True}]}))
else:
    sys.exit(2)
"""


class ConfigHome(Home):
    """A home with the demo tool on PATH, for packet ak1b's tests."""

    def setUp(self):
        Home.setUp(self)
        side = tempfile.TemporaryDirectory()
        self.addCleanup(side.cleanup)
        self.side = os.path.realpath(side.name)
        self.demo_calls = os.path.join(self.side, "demo-calls")
        script = os.path.join(self.side, "demo.py")
        with open(script, "w") as fh:
            fh.write(DEMO % {"calls": self.demo_calls})
        self.stub("agentik-demo", '#!/bin/sh\nPYTHONPYCACHEPREFIX="%s" exec /usr/bin/python3 -B "%s" "$@"\n'
                  % (os.path.join(self.side, "pyc"), script))
        self.user = os.path.join(self.home, ".config", "agentik", "suite", "config.yaml")

    def tools(self):
        self.pid = os.path.join(self.side, "slow.pid")
        self.stub("agentik-slow", '#!/bin/sh\necho $$ > "%s"\nsleep 10\n' % self.pid)
        self.stub("agentik-mute", "#!/bin/sh\nexit 2\n")
        self.plugin_files(os.path.join(self.home, ".claude"), {"plain": "1.0.0"}, whole=False)

    def write(self, path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def cfg(self, *args, cwd=None, **more):
        """A run in HOME (no repo above it), held to A10: HOME the same outside the cache, and
        the stub claude called by nobody."""
        before = self.snapshot()
        p = subprocess.run([str(LAUNCHER), *args], capture_output=True, text=True,
                           env=self.env(**more), timeout=60, cwd=cwd or self.home)
        self.assertEqual(self.snapshot(), before, args)
        self.assertFalse(os.path.exists(self.calls), args)
        return p.returncode, p.stdout, p.stderr

    def describes(self):
        try:
            with open(self.demo_calls) as fh:
                return [l for l in fh.read().splitlines() if l == "describe --json"]
        except FileNotFoundError:
            return []


class ConfigTest(ConfigHome):
    """Packet ak1b: config, three levels down to one setting, and describe."""

    def test_a1_a4_three_levels_piped(self):
        self.tools()
        start = time.monotonic()
        code, out, err = self.cfg("config")
        self.assertLess(time.monotonic() - start, 3.0)
        self.assertEqual(code, 0, err)
        rows = {l.split()[1]: l for l in out.splitlines()[1:] if l.strip()}
        self.assertEqual(sorted(rows), ["demo", "mute", "plain", "slow", "suite"])
        self.assertRegex(rows["demo"], r"answers +3 settings +1 changed +~/\.config/demo/config\.yaml")
        self.assertIn("timed out", rows["slow"])
        self.assertIn("unreadable", rows["mute"])
        self.assertIn("no command", rows["plain"])
        with open(self.pid) as fh:
            pid = int(fh.read())
        for _ in range(50):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.02)
        else:
            self.fail("the slow stub's pid %d still runs" % pid)
        code, out2, err2 = self.cfg("config", "demo")
        self.assertEqual(code, 0, err2)
        keys = [[w for w in l.split() if w != "ok"][0] for l in out2.splitlines()[1:]]
        self.assertEqual(keys, ["colour", "width", "mode"])
        self.assertEqual([l.split()[0] for l in out2.splitlines()[1:] if "changed" in l.split()], ["ok"])
        code, out3, err3 = self.cfg("config", "demo.colour")
        self.assertEqual(code, 0, err3)
        for part in ("value", "dark", "about", "default", "light", "set by",
                     "user at ~/.config/demo/config.yaml:2", "default: light", "user: dark",
                     "run", "agentik-demo set colour VALUE", "takes hold", "next start"):
            self.assertIn(part, out3)
        for text, hint in ((out + err, err), (out2 + err2, err2), (out3 + err3, err3)):
            self.assertNotIn(ESC, text)
            self.assertIn("next:", hint)
        self.assertIn("config <tool>", err)
        self.assertIn("config demo.<key>", err2)

    def test_a2_pty(self):
        for args in (("config",), ("config", "demo"), ("config", "demo.colour")):
            code, text = self.run_pty(*args)
            self.assertEqual(code, 0, text)
            self.assertIn(ESC + "[", text)
            self.assertIn(ESC + "[2mnext: ", text)  # the hint, dim and with no mark (row sc4 R1)
            code, text = self.run_pty(*args, NO_COLOR="1")
            self.assertNotIn(ESC + "[", text)

    def test_a3_json_at_each_level(self):
        self.tools()
        for args, keys in ((("config",), {"tools"}), (("config", "demo"), {"tool", "layers", "settings"}),
                           (("config", "demo.colour"), {"tool", "key", "setting"})):
            code, out, err = self.cfg(*args, "--json")
            self.assertEqual((code, err), (0, ""))
            obj = json.loads(out)
            self.assertEqual(len(out.strip().splitlines()), 1)
            self.assertLessEqual(keys, set(obj))
        self.assertEqual(obj["setting"]["source"], {"layer": "user", "path": os.path.join(
            self.home, ".config", "demo", "config.yaml"), "line": 2})
        self.assertEqual(obj["setting"]["change"]["kind"], "command")

    def test_a5_describe_is_cached_by_the_executable(self):
        self.cfg("config")
        self.assertEqual(len(self.describes()), 1)
        self.cfg("config")
        self.assertEqual(len(self.describes()), 1)
        exe = os.path.join(self.stubs, "agentik-demo")
        os.utime(exe, (1, 1))
        self.cfg("config")
        self.assertEqual(len(self.describes()), 2)

    def test_a6_the_suites_own_settings(self):
        self.write(self.user, "# mine\ncheckouts:\n  - ~/work/one\n  - [not, here]\n"[:-17] + "\n")
        code, out, err = self.cfg("config", "suite")
        self.assertEqual(code, 0, err)
        self.assertIn("checkouts", out)
        code, out, err = self.cfg("config", "suite.checkouts")
        self.assertIn("user at ~/.config/agentik/suite/config.yaml:2", out)
        code, out, err = self.cfg("config", "suite.checkouts", "--json")
        self.assertEqual(json.loads(out)["setting"]["source"], {"layer": "user", "path": self.user, "line": 2})
        repo = os.path.join(self.home, "repo")
        os.makedirs(os.path.join(repo, ".git"))
        self.write(os.path.join(repo, ".claude", "agentik", "config.yaml"),
                   "other:\n  m: {k: v}\nsuite:\n  kind: hq\n")
        code, out, err = self.cfg("config", "suite.kind", cwd=os.path.join(repo))
        self.assertEqual(code, 0, err)
        self.assertIn("repo at ~/repo/.claude/agentik/config.yaml:4", out)

    def test_a7_a_file_outside_the_subset_and_an_unknown_tool(self):
        self.write(self.user, "checkouts:\n\t- ~/work\n")
        code, out, err = self.cfg("config", "suite")
        self.assertEqual(code, 2)
        self.assertIn("~/.config/agentik/suite/config.yaml cannot be read at line 2", err)
        code, out, err = self.cfg("config")
        self.assertEqual(code, 0, err)
        self.assertIn("line 2", out)
        code, out, err = self.cfg("config", "dmeo")
        self.assertEqual(code, 2)
        self.assertIn("dmeo is not a tool here\nnext: ", err)  # row sc4: the near word mended
        self.assertTrue(err.endswith(" config demo\n"), err)
        code, out, err = self.cfg("config", "nosuch")
        self.assertEqual(code, 2)
        self.assertTrue(err.endswith(" config\n"), err)
        code, out, err = self.cfg("config", "demo.colr")
        self.assertEqual(code, 2)
        self.assertIn("demo has no key colr\nnext: ", err)
        self.assertTrue(err.endswith(" config demo.colour\n"), err)

    def test_a8_the_fallback_table(self):
        table = json.loads((LIB / "fallback.json").read_text())
        name = next(iter(table))
        self.stub("agentik-" + name, "#!/bin/sh\nexit 2\n")
        market = os.path.join(self.side, "market")
        self.write(os.path.join(market, ".claude-plugin", "marketplace.json"), json.dumps(
            {"plugins": [{"name": name, "description": "A made-up description."}]}))
        self.write(os.path.join(self.home, ".claude", "plugins", "known_marketplaces.json"),
                   json.dumps({"agentik": {"installLocation": market}}))
        code, out, err = self.cfg("config")
        self.assertEqual(code, 0, err)
        self.assertIn("from the suite's table", out)
        self.assertIn("A made-up description.", out)
        code, out, err = self.cfg("config", name)
        self.assertEqual(code, 0, err)
        for line in table[name]["lines"]:
            self.assertIn(line, out)
        code, out, err = self.cfg("config", name + ".x")
        self.assertEqual(code, 2)

    def test_a9_describe(self):
        code, out, err = self.cfg("describe", "--json")
        obj = json.loads(out)
        self.assertEqual((code, obj["schema"], obj["reads"]), (0, "agentik.describe/1", [
            {"kind": "config", "name": "settings", "argv": ["describe", "config", "--json"]}]))
        self.write(self.user, "checkouts: [~/a, ~/b]\n")
        code, out, err = self.cfg("describe", "config", "--json", "checkouts")
        obj = json.loads(out)
        self.assertEqual((code, obj["schema"], [s["key"] for s in obj["settings"]]),
                         (0, "agentik.config/1", ["checkouts"]))
        self.assertEqual([l["name"] for l in obj["layers"]], ["user", "repo"])
        self.assertEqual(obj["settings"][0]["change"]["kind"], "edit")
        code, out, err = self.cfg("describe")
        self.assertEqual(code, 2)
        self.assertIn("--json", err)

    def test_r6_changed_user_files_and_groups(self):
        code, out, err = self.cfg("config", "--changed")
        self.assertEqual(code, 0, err)
        self.assertRegex(out, r"demo\.colour +dark +default light +user")
        code, out, err = self.cfg("config", "--user-files")
        self.assertEqual((code, out), (0, os.path.join(self.home, ".config", "demo", "config.yaml") + "\n"))
        code, out, err = self.cfg("config", "demo", "--changed")
        self.assertEqual(code, 2)
        self.write(self.user, "watchers:\n" + "".join(
            "  w%d:\n    match: m\n    start: s\n    beat: 1m\n    writer: me\n" % i for i in range(6)))
        code, out, err = self.cfg("config", "suite")
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertIn("watchers", lines)
        self.assertTrue(lines[lines.index("watchers") + 1].startswith("    "), out)


LAG = """#!/bin/sh
if [ "$1 $2" = "describe --json" ]; then
  echo '{"schema": "agentik.describe/1", "ok": true, "tool": "lag", "version": "1", "summary": "s",
   "repo": "r", "plugin": "lag@agentik", "needs": [], "verbs": [],
   "reads": [{"kind": "config", "name": "settings", "argv": ["describe", "config", "--json"]}]}'
  exit 0
fi
echo $$ > "%s"
sleep 10
"""


class WallTest(ConfigHome):
    """Review 1 of ak1b, F1 to F4: one 2 s wall from the first spawn holds every describe and
    config read; a tool's stdout is read to a cap; no group outlives the run."""

    def py(self, name, code, *args):
        """A stub that runs a Python line, its bytecode kept out of HOME."""
        return self.stub(name, '#!/bin/sh\nPYTHONPYCACHEPREFIX="%s" exec /usr/bin/python3 -c %s %s\n'
                         % (os.path.join(self.side, "pyc"), shlex.quote(code),
                            " ".join(shlex.quote(a) for a in args)))

    def timed(self, *args):
        start = time.monotonic()
        code, out, err = self.cfg(*args)
        took = time.monotonic() - start
        self.assertEqual(code, 0, err)
        self.assertLess(took, 3.0, out)
        return out

    def groups_gone(self, *files):
        for path in files:
            with open(path) as fh:
                group = int(fh.read())
            for _ in range(50):
                try:
                    os.killpg(group, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.02)
            else:
                self.fail("group %d of %s still runs" % (group, path))

    def test_f1_a_slow_describe_and_a_lagging_config_read_share_one_wall(self):
        self.tools()
        lag = os.path.join(self.side, "lag.pid")
        self.stub("agentik-lag", LAG % lag)
        for _ in range(2):  # the second run has lag's describe from the cache
            out = self.timed("config")
            self.assertIn("timed out", next(l for l in out.splitlines() if " slow " in l + " "))
            self.groups_gone(self.pid, lag)

    def test_f2_twenty_slow_tools_add_nothing_past_the_wall(self):
        files = []
        for i in range(20):
            files.append(os.path.join(self.side, "slow%d.pid" % i))
            self.stub("agentik-slow%d" % i, '#!/bin/sh\necho $$ > "%s"\nsleep 10\n' % files[-1])
        out = self.timed("config")
        self.assertEqual(out.count("timed out"), 20, out)
        self.groups_gone(*files)

    def test_f3_a_flood_is_cut_at_the_cap(self):
        count = os.path.join(self.side, "spew.count")
        self.py("agentik-spew", "import os, sys\nn, log = 0, open(sys.argv[1], 'a', buffering=1)\n"
                "while True:\n    os.write(1, b'a' * 65536)\n    n += 65536\n    log.write('%d\\n' % n)", count)
        out = self.timed("config")
        self.assertIn("unreadable", next(l for l in out.splitlines() if " spew " in l + " "))
        with open(count) as fh:  # the last whole line: the bytes written when the cut came
            written = int([l for l in fh.read().split("\n")[:-1] if l][-1])
        cap = 1 << 20
        self.assertGreaterEqual(written, cap - 65536)
        self.assertLessEqual(written, cap + (512 << 10))

    def test_f4_a_child_that_left_the_group_and_holds_stdout(self):
        groups, escaped = [], []
        for i in range(5):
            groups.append(os.path.join(self.side, "esc%d.group" % i))
            escaped.append(os.path.join(self.side, "esc%d.pid" % i))
            self.stub("agentik-esc%d" % i, (
                '#!/bin/sh\nPYTHONPYCACHEPREFIX="%s" /usr/bin/python3 -c "import os, sys, time; '
                'os.setsid(); open(sys.argv[1], \'w\').write(str(os.getpid())); time.sleep(10)" "%s" &\n'
                'echo $$ > "%s"\nsleep 10\n') % (os.path.join(self.side, "pyc"), escaped[-1], groups[-1]))
        self.addCleanup(self.kill_escaped, escaped)
        out = self.timed("config")
        self.assertEqual(out.count("timed out"), 5, out)
        self.groups_gone(*groups)

    def kill_escaped(self, files):
        for path in files:
            try:
                with open(path) as fh:
                    os.kill(int(fh.read()), signal.SIGKILL)
            except (OSError, ValueError):
                pass


class SubsetTest(unittest.TestCase):
    """R8: GUIDE section 3's strict subset, each key's line kept, anything else refused by line."""

    def test_the_subset(self):
        tree, lines = settings.parse("# c\na:\n  b: 1  # n\n  c: [x, 'y z']\nd:\n- one\n- \"t#o\"\n"
                                     "e: {k: v, n: 2}\nf:\ng: ~\n")
        self.assertEqual(tree, {"a": {"b": 1, "c": ["x", "y z"]}, "d": ["one", "t#o"],
                                "e": {"k": "v", "n": 2}, "f": None, "g": None})
        self.assertEqual(lines, {"a": 2, "a.b": 3, "a.c": 4, "d": 5, "e": 8, "f": 9, "g": 10})

    def test_what_it_refuses(self):
        for text, line in (("a: &x 1\n", 1), ("a: |\n  t\n", 1), ("a:\n  - b: 1\n", 2),
                           ("a: [x, [y]]\n", 1), ("a: {k: {j: 1}}\n", 1), ("a: 1\na: 2\n", 2),
                           ("a:\n\tb: 1\n", 2), ("a: 1\n   b: 2\n", 2), ("- x\n", 1),
                           ("a: 'open\n", 1), ("just words\n", 1)):
            with self.assertRaises(settings.Fault, msg=text) as caught:
                settings.parse(text)
            self.assertEqual(caught.exception.line, line, text)


if __name__ == "__main__":
    unittest.main()


ODD = """#!/usr/bin/python3
import json, sys
with open(%(spec)r) as fh:
    spec = json.load(fh)
if sys.argv[1:] == ["describe", "--json"]:
    print(json.dumps({"schema": spec.get("schema", "agentik.describe/1"), "ok": True, "tool": "odd",
        "version": "1", "summary": "s", "repo": "r", "plugin": "odd@agentik", "needs": [], "verbs": [],
        "reads": [{"kind": "config", "name": "settings", "argv": ["describe", "config", "--json"]}]}))
else:
    s = dict({"key": "colour", "value": "dark", "default": "light", "type": "choice",
              "choices": ["dark", "light"], "summary": "x", "source": {}, "change": {"kind": "fixed"},
              "live": True}, **spec.get("setting", {}))
    print(json.dumps(dict({"schema": "agentik.config/1", "ok": True, "tool": "odd", "layers": [],
                           "settings": [s]}, **spec.get("config", {}))))
"""


class AnswerTest(ConfigHome):
    """Review 1 of ak1b, F5 to F7 and the schema: a wrong type in a tool's answer, or a removed
    cwd, gives a row or a line, never a traceback; only `agentik.describe/1` counts."""

    def odd(self, **spec):
        path = os.path.join(self.side, "odd.json")
        with open(path, "w") as fh:
            json.dump(spec, fh)
        script = os.path.join(self.side, "odd.py")
        with open(script, "w") as fh:
            fh.write(ODD % {"spec": path})
        self.stub("agentik-odd", '#!/bin/sh\nPYTHONPYCACHEPREFIX="%s" exec /usr/bin/python3 -B "%s" "$@"\n'
                  % (os.path.join(self.side, "pyc"), script))

    def clean(self, *args):
        code, out, err = self.cfg(*args)
        self.assertNotIn("Traceback", out + err, args)
        self.assertEqual(code, 0, err)
        return out

    def test_f5_warnings_that_are_not_a_list_of_objects(self):
        for warnings in ([1, "x", {"key": "k", "path": "/p", "line": 3}], 5, "x"):
            self.odd(config={"warnings": warnings})
            out = self.clean("config", "odd")
            self.assertIn("colour", out)
            self.assertEqual("unknown key k" in out, isinstance(warnings, list), out)

    def test_f6_choices_that_are_not_a_list(self):
        for choices in (5, "abc", {"a": 1}):
            self.odd(setting={"choices": choices})
            out = self.clean("config", "odd.colour")
            self.assertNotIn("choices", out)
        self.odd()
        self.assertIn("dark, light", self.clean("config", "odd.colour"))

    def test_f7_a_removed_cwd(self):
        dead = os.path.join(self.side, "dead")
        for args in (("config",), ("config", "suite"), ("config", "suite.kind")):
            os.mkdir(dead)
            p = subprocess.run(["/bin/sh", "-c", 'cd "$1" && rmdir "$1" && shift && exec "$@"', "sh",
                                dead, str(LAUNCHER), *args],
                               capture_output=True, text=True, env=self.env(), timeout=60)
            self.assertNotIn("Traceback", p.stdout + p.stderr, args)
            self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("checkouts", subprocess.run(
            ["/bin/sh", "-c", 'mkdir "$1" && cd "$1" && rmdir "$1" && exec "$2" config suite', "sh",
             dead, str(LAUNCHER)], capture_output=True, text=True, env=self.env(), timeout=60).stdout)

    def test_only_describe_schema_one_counts(self):
        self.odd(schema="agentik.describe/0")
        out = self.clean("config")
        self.assertIn("unreadable", next(l for l in out.splitlines() if " odd " in l + " "))


class LineTest(ConfigHome):
    """Review 1 of ak1b, F8 to F13: each line says only what is known in its state."""

    def test_f8_the_suites_own_nearest_key(self):
        code, out, err = self.cfg("config", "suite.checkout")
        self.assertEqual(code, 2)
        self.assertIn("suite has no key checkout\nnext: ", err)
        self.assertTrue(err.endswith(" config suite.checkouts\n"), err)

    def test_f9_a_config_read_that_fails_says_so_at_every_level(self):
        self.stub("agentik-lag", LAG % os.path.join(self.side, "lag.pid"))
        self.stub("agentik-bad", (LAG % os.path.join(self.side, "bad.pid")).replace(
            "sleep 10", "echo nope").replace('"tool": "lag"', '"tool": "bad"'))
        for name, words in (("lag", "reading its settings ran past 2 s"),
                            ("bad", "its settings answer cannot be read")):
            code, out, err = self.cfg("config")
            row = next(l for l in out.splitlines() if " %s " % name in l + " ")
            self.assertRegex(row, r"warn +%s +answers +%s" % (name, words))
            code, out, err = self.cfg("config", name)
            self.assertEqual(code, 0, err)
            self.assertIn("%s answers, but %s" % (name, words), out)
            code, out, err = self.cfg("config", name + ".colour")
            self.assertEqual(code, 2)
            keys = words.replace("its settings answer", "the answer of its keys").replace("settings", "keys")
            self.assertIn("%s answers, but %s" % (name, keys), err)  # a cause says key (row sc4 R8)
            for text in (out, err):
                self.assertNotIn("describe", text)

    def test_f10_changed_and_user_files_name_the_tools_that_did_not_answer(self):
        self.stub("agentik-mute", "#!/bin/sh\nexit 2\n")
        code, out, err = self.cfg("config", "--changed")
        self.assertEqual(code, 0, err)
        self.assertIn("gave no settings, so their changes are not here: mute", out)
        code, out, err = self.cfg("config", "--user-files")
        self.assertEqual((code, out), (0, os.path.join(self.home, ".config", "demo", "config.yaml") + "\n"))
        self.assertIn("gave no settings, so their user files are not here: mute", err)
        self.stub("agentik-demo", "#!/bin/sh\nexit 2\n")
        code, out, err = self.cfg("config", "--changed")
        self.assertIn("Every setting that was read holds its default.", out)
        self.assertIn("not here: demo, mute", out)
        code, out, err = self.cfg("config", "--user-files")
        self.assertEqual((code, out), (0, ""))
        self.assertIn("No tool that gave settings names a user file that travels.", err)
        self.assertNotIn("next: no layer", err)

    def test_f11_a_known_key_with_a_value_outside_its_choices(self):
        repo = os.path.join(self.home, "repo")
        os.makedirs(os.path.join(repo, ".git"))
        self.write(os.path.join(repo, ".claude", "agentik", "config.yaml"), "suite:\n  kind: hub\n  odd: 1\n")
        code, out, err = self.cfg("config", "suite", cwd=repo)
        self.assertEqual(code, 0, err)
        self.assertIn("kind holds hub, which is not one of its choices", out)
        self.assertNotIn("unknown key suite.kind", out)
        self.assertIn("unknown key suite.odd", out)

    def test_f12_a_dot_with_no_name_or_no_key(self):
        for word in (".key", "."):
            code, out, err = self.cfg("config", word)
            self.assertEqual(code, 2)
            self.assertIn("a tool's name goes before the dot\n", err)
        code, out, err = self.cfg("config", "demo.")
        self.assertEqual(code, 2)
        self.assertIn("a key goes after the dot\n", err)
        self.assertEqual(self.describes(), [])

    def test_f13_a_user_file_that_cannot_be_opened_has_no_line(self):
        conf = os.path.join(self.side, "conf")
        user = os.path.join(conf, "agentik", "suite", "config.yaml")
        os.makedirs(user)
        code, out, err = self.cfg("config", "suite", XDG_CONFIG_HOME=conf)
        self.assertEqual(code, 2)
        self.assertIn("config.yaml cannot be read: a file that cannot be read", err)
        os.rmdir(user)
        self.write(user, "checkouts: []\n")
        os.chmod(user, 0)
        for args in (("config", "suite"), ("config",)):
            code, out, err = self.cfg(*args, XDG_CONFIG_HOME=conf)
            self.assertIn("config.yaml cannot be read: a file that cannot be read", out + err)
            self.assertNotIn("line 0", out + err)
