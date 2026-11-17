"""Row up3-forward-only: no step moves a command to an older version unasked.

R1, R2: `install()` leaves a command install-cli wrote whose version is newer than the tree being
placed, says so in one line with both versions, and returns as done; `force` places anyway. A tool
and the suite each go through it. R3: setup's step 4 gives a launcher newer than its plugin an
`ok` row, so neither setup nor `update` runs an older plugin's install-cli over it. R4: the doctor
says newer, as a note. A command older than its plugin is placed as at the pin.

Each home is a temp HOME with a stub `claude`, `git` and `ps` on its PATH (ak4a-update's shape);
tool and plugin names are made up. No test starts a real `claude`, reads the live home or writes
outside its temp folder."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_ak4a_update as ak4a  # noqa: E402
import test_agentik_install as ai  # noqa: E402
from test_agentik_suite import LAUNCHER, LIB, version  # noqa: E402
from agentik_suite import plan  # noqa: E402
import agentik_install  # noqa: E402

# A tool after the sync, before its verb takes `--force`: test_agentik_install's runner, which
# calls `install_cli()`. FLAGGED is one whose verb takes it, and says so (review 1 F1).
PLAIN = ai.RUNNER
FLAGGED = ai.RUNNER.replace("raise SystemExit(a.install_cli())",
                            'raise SystemExit(a.install_cli(force="--force" in sys.argv[2:], takes_force=True))')
LONG = ("2.0.0-alpha.129", "2.0.0-alpha.104")  # long pre-release versions on both sides (review 1 L5)
WIDTH = 76  # design/23 V1, before the values, as test_sc1_voice_width counts it


def launcher_version(path):
    with open(path) as fh:
        return re.search(r"^VERSION=(.*)$", fh.read(), re.M).group(1)


class ToolTest(ai.Base):
    """R1 for a tool: the canonical module's install-cli, from a made-up plugin."""

    def plugin(self, tool="agentik-x", ver="1.0.0", runner=PLAIN, **old):
        root = ai.Base.plugin(self, tool, ver, **old)
        (root / "lib" / tool).write_text(runner)
        return root

    def place(self, ver, *args, runner=PLAIN):
        root = self.plugin(ver=ver, runner=runner)
        return self.run_tool(root / "bin" / "agentik-x", "install-cli", *args)

    def kept_line(self, have, want, runner):
        """The one line an older tree's install-cli prints over a newer command it leaves."""
        self.assertEqual(self.place(have)[0], 0)
        code, out, err = self.place(want, runner=runner)
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(launcher_version(self.bin()), have)
        lines = out.splitlines()
        self.assertEqual(len(lines), 1, out)
        return lines[0]

    def test_an_older_tree_leaves_a_newer_command_and_says_so(self):
        line = self.kept_line("2.0.0", "1.9.0", FLAGGED)
        for word in ("~/.local/bin/agentik-x", "2.0.0", "1.9.0", "newer", "--force"):
            self.assertIn(word, line)
        self.assertEqual(self.run_tool(self.bin(), "--version")[1], "2.0.0\n")

    def test_a_verb_that_takes_no_force_is_not_told_to_pass_it(self):
        # review 1 F1: install_cli's default names no flag, which a tool's verb would refuse
        line = self.kept_line("2.0.0", "1.9.0", PLAIN)
        for word in ("Left ~/.local/bin/agentik-x", "2.0.0", "1.9.0", "newer"):
            self.assertIn(word, line)
        self.assertNotIn("--force", line)
        self.assertNotIn("force", line)

    def test_the_kept_line_holds_the_width_with_long_versions(self):
        # review 1 L5: each value once, so the line before its values holds V1, in both forms
        for n, runner in enumerate((PLAIN, FLAGGED)):
            with self.subTest(form=("plain", "flagged")[n]):
                if n:
                    shutil.rmtree(self.home)
                    self.home.mkdir()
                line = self.kept_line(LONG[0], LONG[1], runner)
                values = ("~/.local/bin/agentik-x",) + LONG
                self.assertEqual([line.count(v) for v in values], [1, 1, 1], line)
                bare = line
                for v in values:
                    bare = bare.replace(v, "")
                self.assertLessEqual(len(bare), WIDTH, line)

    def test_a_newer_command_whose_runner_cannot_be_read_is_placed(self):
        # review 1 F2: the launcher refuses an unreadable runner as gone, and names install-cli
        self.assertEqual(self.place("2.0.0")[0], 0)
        runner = self.share() / self.trees()[0] / "agentik-x"
        os.chmod(runner, 0)
        self.addCleanup(lambda: runner.exists() and os.chmod(runner, 0o644))
        self.assertEqual(self.run_tool(self.bin(), "--version")[0], 3)
        code, out, err = self.place("1.9.0")
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(launcher_version(self.bin()), "1.9.0")
        self.assertEqual(self.run_tool(self.bin(), "--version")[1], "1.9.0\n")

    def test_force_places_the_older_tree(self):
        self.assertEqual(self.place("2.0.0")[0], 0)
        code, out, err = self.place("1.9.0", "--force", runner=FLAGGED)
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(launcher_version(self.bin()), "1.9.0")
        self.assertIn("Placed ~/.local/bin/agentik-x 1.9.0", out)

    def test_an_older_command_is_placed_as_at_the_pin(self):
        self.assertEqual(self.place("1.0.0")[0], 0)
        code, out, err = self.place("1.9.0")
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(launcher_version(self.bin()), "1.9.0")
        self.assertIn("Placed ~/.local/bin/agentik-x 1.9.0", out)

    def test_an_equal_command_is_placed_as_at_the_pin(self):
        self.assertEqual(self.place("1.9.0")[0], 0)
        os.unlink(self.bin())
        root = self.home / ".claude" / "plugins" / "cache" / "agentik" / "x" / "1.9.0"
        code, out, err = self.run_tool(root / "bin" / "agentik-x", "install-cli")
        self.assertEqual((code, err), (0, ""), out)
        self.assertIn("Placed ~/.local/bin/agentik-x 1.9.0", out)

    def test_a_newer_command_whose_code_is_gone_is_placed(self):
        self.assertEqual(self.place("2.0.0")[0], 0)
        for tree in self.trees():
            shutil.rmtree(self.share() / tree)
        code, out, err = self.place("1.9.0")
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(launcher_version(self.bin()), "1.9.0")

    def test_a_command_install_cli_did_not_write_is_placed_as_at_the_pin(self):
        self.bin().parent.mkdir(parents=True)
        self.bin().write_text("#!/bin/sh\nVERSION=9.9.9\nexit 0\n")
        code, out, err = self.place("1.9.0")
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(launcher_version(self.bin()), "1.9.0")

    def test_the_dry_run_says_it_leaves_it(self):
        self.assertEqual(self.place("2.0.0")[0], 0)
        mod = ai.load_module()
        root = self.plugin(ver="1.9.0")
        lib = str(root / "lib")
        self.addCleanup(setattr, mod, "_lib", mod._lib)
        mod._lib = lambda: lib
        done = mod.install(None, self.env, dry_run=True)
        self.assertEqual((done["kept"], done["version"]), ("2.0.0", "1.9.0"))
        self.assertEqual(launcher_version(self.bin()), "2.0.0")

    def test_the_suites_copy_is_the_canonical_module(self):
        self.assertEqual((LIB / "agentik_install.py").read_bytes(), ai.MODULE.read_bytes())


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = os.path.realpath(tmp.name)

    def home(self, names=("murmur",), name="h"):
        return ak4a.Home(os.path.join(self.tmp, name), listed=names)

    def call(self, h, *argv):
        p = subprocess.run(list(argv), capture_output=True, text=True, env=h.env(), cwd=h.home,
                           stdin=subprocess.DEVNULL, timeout=120)
        return p.returncode, p.stdout, p.stderr


class SuiteTest(Base):
    """R2: the suite's own install-cli follows R1."""

    def newer(self):
        """A home whose suite command install-cli wrote, then made newer than this tree."""
        h = self.home()
        code, out, err = self.call(h, str(LAUNCHER), "install-cli")
        self.assertEqual(code, 0, out + err)
        path = os.path.join(h.bindir, "agentik-suite")
        with open(path) as fh:
            text = fh.read()
        self.assertEqual(text.count("VERSION=%s\n" % version()), 1)
        with open(path, "w") as fh:
            fh.write(text.replace("VERSION=%s\n" % version(), "VERSION=9.0.0\n"))
        return h, path

    def test_an_older_suite_leaves_a_newer_command_and_says_so(self):
        h, path = self.newer()
        code, out, err = self.call(h, str(LAUNCHER), "install-cli")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(launcher_version(path), "9.0.0")
        lines = out.splitlines()
        self.assertEqual(len(lines), 1, out)
        for word in ("~/.local/bin/agentik-suite", "9.0.0", version(), "newer", "--force"):
            self.assertIn(word, lines[0])
        code, out, err = self.call(h, str(LAUNCHER), "install-cli", "--json")
        self.assertEqual(code, 0, out + err)
        obj = json.loads(out)
        self.assertEqual((obj["ok"], obj["kept"], obj["version"]), (True, "9.0.0", version()))

    def test_force_places_this_suite(self):
        h, path = self.newer()
        code, out, err = self.call(h, str(LAUNCHER), "install-cli", "--force")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(launcher_version(path), version())
        self.assertIn("Placed ~/.local/bin/agentik-suite %s" % version(), out)

    def test_force_is_install_clis_alone(self):
        h = self.home()
        code, out, err = self.call(h, str(LAUNCHER), "doctor", "--force")
        self.assertEqual(code, 2, out + err)

    def test_an_older_suite_command_is_placed_as_at_the_pin(self):
        h, path = self.newer()
        with open(path) as fh:
            text = fh.read()
        with open(path, "w") as fh:
            fh.write(text.replace("VERSION=9.0.0\n", "VERSION=0.0.1\n"))
        code, out, err = self.call(h, str(LAUNCHER), "install-cli")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(launcher_version(path), version())


DEFAULT = plan.default_set(str(LIB))  # the suite's default set, by its manifest


class PlanTest(Base):
    """R3, R4: a launcher newer than its plugin reads ok to setup, a note to the doctor, and update
    leaves it; one older than its plugin is placed as at the pin."""

    def at(self, have, want="1.9.0", name="h", tool="murmur", runner=None):
        """A home whose launcher is at `have` and its plugin at `want`. With `runner`, a mode, the
        launcher tests its runner as install-cli's does, and the runner stands with that mode."""
        h = self.home(names=(tool,), name=name)
        h.install(tool + "@agentik", want, launcher=False)
        tree = os.path.join(h.home, ".local", "share", "agentik-" + tool, have)
        test = '' if runner is None else '[ -f "$TREE/agentik-%s" ] && [ -r "$TREE/agentik-%s" ] || exit 3\n' % (
            tool, tool)
        h.file(os.path.join(h.bindir, "agentik-" + tool), "#!/bin/sh\nVERSION=%s\nTREE=%s\n%sexit 0\n"
               % (have, tree, test))
        os.makedirs(tree)
        if runner is not None:
            path = os.path.join(tree, "agentik-" + tool)
            with open(path, "w") as fh:
                fh.write("print('runs')\n")
            os.chmod(path, runner)
            self.addCleanup(lambda: os.path.exists(path) and os.chmod(path, 0o644))
        return h

    def row(self, h):
        steps = plan.build(["murmur"], h.env(), str(LIB), "agentik-suite", version())
        return [s for s in steps if s["n"] == 4][0]

    def doctor_row(self, have, runner=None, name="h"):
        """The doctor's launcher row for a tool of the suite's default set: its plan rows read
        that set alone."""
        tool = sorted(DEFAULT)[0]
        h = self.at(have, tool=tool, runner=runner, name=name)
        code, out, err = h.run("doctor", "--all", "--json")
        rows = [c for g in json.loads(out)["tools"] for c in g["checks"]
                if c["name"] == "launcher ~/.local/bin/agentik-" + tool]
        self.assertEqual(len(rows), 1, out)
        return rows[0]

    def test_step_4_reads_a_newer_launcher_ok(self):
        s = self.row(self.at("1.9.3"))
        self.assertEqual((s["state"], s["mid"], s["command"]), ("ok", "setup.launcher.newer", None))
        self.assertEqual(s["values"], {"have": "1.9.3", "want": "1.9.0"})

    def test_the_doctor_says_newer_as_a_note(self):
        c = self.doctor_row("1.9.3")
        self.assertEqual(c["status"], "note", c)
        self.assertIn("1.9.3", c["detail"])
        self.assertIn("newer", c["detail"])
        self.assertNotIn("older", c["detail"])

    def test_the_doctor_says_older_where_it_is_older(self):
        c = self.doctor_row("1.0.0")
        self.assertEqual((c["status"], c["detail"]), ("warn", "at 1.0.0, older than 1.9.0"))

    def test_update_leaves_a_newer_launcher(self):
        h = self.at("1.9.3")
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(h.version_of("murmur"), "1.9.3")
        self.assertEqual([l for l in h.ran() if l.endswith(" install-cli")], [])

    def test_setup_leaves_a_newer_launcher(self):
        h = self.at("1.9.3")
        h.run("setup", "--yes", "murmur")
        self.assertEqual(h.version_of("murmur"), "1.9.3")
        self.assertEqual([l for l in h.ran() if l.endswith("agentik-murmur install-cli")], [])

    def test_a_newer_launcher_with_a_readable_runner_reads_newer(self):
        s = self.row(self.at("1.9.3", runner=0o644))
        self.assertEqual((s["state"], s["mid"]), ("ok", "setup.launcher.newer"))

    def test_a_newer_launcher_whose_runner_cannot_be_read_is_gone(self):
        # review 1 F2: as the launcher reads it, so setup and update place it again
        s = self.row(self.at("1.9.3", runner=0))
        self.assertEqual((s["state"], s["mid"]), ("todo", "setup.launcher.gone"))
        c = self.doctor_row("1.9.3", runner=0, name="d")
        self.assertNotEqual(c["status"], "note", c)
        self.assertIn("gone", c["detail"])
        self.assertNotIn("newer", c["detail"])
        for n, verb in enumerate((("update", "--yes"), ("setup", "--yes", "murmur"))):
            h = self.at("1.9.3", name="g%d" % n, runner=0)
            code, out, err = h.run(*verb)
            self.assertEqual(code, 0, out + err)
            self.assertEqual(len([l for l in h.ran() if l.endswith("agentik-murmur install-cli")]), 1, verb)

    def test_an_older_launcher_is_placed_by_setup_and_update(self):
        s = self.row(self.at("1.0.0"))
        self.assertEqual((s["state"], s["mid"]), ("todo", "setup.launcher.behind"))
        for n, verb in enumerate((("update", "--yes"), ("setup", "--yes", "murmur"))):
            h = self.at("1.0.0", name="h%d" % n)
            code, out, err = h.run(*verb)
            self.assertEqual(code, 0, out + err)
            self.assertEqual(h.version_of("murmur"), "1.9.0", verb)
            self.assertEqual(len([l for l in h.ran() if l.endswith("agentik-murmur install-cli")]), 1)


if __name__ == "__main__":
    unittest.main()
