"""Packet hn1-help-next: the help's next line asks setup's own question (R1), a status read
learned from `describe` keeps its `wall_s` (R2), and `scripts/sync --check` compares a copy's
mode as git keeps it, the owner's executable bit alone (R3).

The help's tests run the plugin's launcher, a copy of it whose fallback table gives the made-up
`alpha` a need, in a temp HOME; the read's tests are su2's ReadHome; the sync tests are sy4's
fixture, two temp checkouts. Nothing here reads or writes the live home or state.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_agentik_suite as base  # noqa: E402
import test_su2_read as su2  # noqa: E402
import test_sync as sy  # noqa: E402
from agentik_suite import tools  # noqa: E402

_COPY = []


def needy_plugin():
    """A copy of the plugin whose fallback table knows `alpha`, which needs Go: no `go` on the
    test's PATH, so step 1 reads `warn` and names no line setup would run (ic2-needs R1)."""
    if not _COPY:
        import atexit
        top = os.path.realpath(tempfile.mkdtemp(prefix="hn1-suite-"))
        atexit.register(shutil.rmtree, top, True)
        root = os.path.join(top, "suite")
        shutil.copytree(str(base.PLUGIN), root, ignore=shutil.ignore_patterns("__pycache__"))
        table = os.path.join(root, "lib", "fallback.json")
        with open(table) as fh:
            rows = json.load(fh)
        rows["alpha"] = {"lines": ["agentik alpha doctor"], "user_file": None, "needs": ["Go"], "status": []}
        with open(table, "w") as fh:
            json.dump(rows, fh)
        _COPY.append(Path(root))
    return _COPY[0]


class HelpHome(base.Home):
    """test_r2_the_closing_hint_by_state's fixture: alpha installed whole, its launcher, the
    suite's and the door placed."""

    def setUp(self):
        base.Home.setUp(self)
        self.plugin_files(os.path.join(self.home, ".claude"), {"alpha": "1.0.0"})
        self.place("agentik-alpha", "1.0.0")
        self.place("agentik-suite", base.version())
        self.place("agentik", "0")
        self.path = "%s:%s:%s" % (self.bindir, self.stubs, base.SYSTEM)

    @property
    def bindir(self):
        return os.path.join(self.home, ".local", "bin")

    def place(self, exe, ver):
        os.makedirs(self.bindir, exist_ok=True)
        with open(os.path.join(self.bindir, exe), "w") as fh:
            fh.write("#!/bin/sh\nVERSION=%s\n" % ver)
        os.chmod(os.path.join(self.bindir, exe), 0o755)

    def closes(self, **more):
        """(setup's close, the help's close): the last stderr line of each."""
        code, _, err = self.run_cli("setup", "--dry-run", "alpha", **more)
        self.assertEqual(code, 0, err)
        setup = err.splitlines()[-1]
        code, _, err = self.run_cli("--help", **more)
        self.assertEqual(code, 0, err)
        return setup, err.splitlines()[-1]


DONE = ("setup has nothing left to do", "setup has done what this version can")  # done, rest


class HelpCloseTest(HelpHome):
    def test_a1_a_warn_step_and_nothing_to_run(self):
        self.launcher = needy_plugin() / "bin" / "agentik-suite"
        steps = self.plan("alpha", PATH=self.path)["steps"]
        early = [s for s in steps if s["n"] <= 5]
        self.assertIn((1, "warn", "Go"), [(s["n"], s["state"], s["subject"]) for s in early])
        self.assertFalse([s for s in steps if s["state"] == "blocked"])
        self.assertFalse([s for s in steps if s["n"] <= 6 and s["command"]])
        setup, help_ = self.closes(PATH=self.path)
        self.assertIn(DONE[1], setup)  # hint.setup.rest
        self.assertEqual(help_, "next: %s doctor" % self.launcher)  # hint.help.done
        code, out, err = self.run_cli(PATH=self.path)  # the bare first screen closes the same
        self.assertEqual(err.splitlines()[-1], help_)

    def test_a2_the_help_agrees_with_setup(self):
        setup_line = "next: %s setup alpha" % self.launcher
        # each state test_r2_the_closing_hint_by_state covers: steps 1 to 6 ok; no claude on PATH
        states = {"all ok": {"PATH": self.path}, "no claude": {}}
        for name, more in states.items():
            if name == "no claude":
                os.remove(os.path.join(self.stubs, "claude"))
            with self.subTest(state=name):
                setup, help_ = self.closes(**more)
                if any(d in setup for d in DONE):
                    self.assertEqual(help_, "next: %s doctor" % self.launcher)
                else:  # hint.setup.next, .path or .page: the setup line
                    self.assertEqual(help_, setup_line)
                self.assertEqual(name == "all ok", any(d in setup for d in DONE), setup)

    def test_a3_a_blocked_step_one(self):
        os.remove(os.path.join(self.stubs, "claude"))
        steps = self.plan("alpha", PATH=self.path)["steps"]
        self.assertIn((1, "blocked", "claude"), [(s["n"], s["state"], s["subject"]) for s in steps])
        _, help_ = self.closes(PATH=self.path)
        self.assertEqual(help_, "next: %s setup alpha" % self.launcher)
        code, out, err = self.run_cli("--help", "-q", PATH=self.path)  # -q says nothing, as at the pin
        self.assertEqual(code, 0, err)
        self.assertNotIn("next:", out + err)


class DescribedWallTest(su2.ReadHome):
    """R2: the gate read, learned from demo's describe, under the wall its `wall_s` names."""

    def described(self, **wall):
        """demo's describe with the gate read's `wall_s` set (absent where none is given), the
        gate answering after 1.5 s, and the describe cache cleared."""
        desc = su2.fixture("describe.json")
        for read in desc["reads"]:
            if read["name"] == "gate":
                read.update(wall)
        self.answer(describe={"file": self.saved("describe-wall.json", desc)},
                    gate={"file": os.path.join(su2.FIX, "gate.json"), "sleep": 1.5})
        cached = os.path.join(tools.cache_dir(self.env()), "demo.json")
        if os.path.exists(cached):
            os.unlink(cached)
        return self.source(self.read(), "gate")

    def test_a4_a_described_wall_is_kept(self):
        start = time.monotonic()
        g = self.described(wall_s=6)
        self.assertEqual((g["state"], g["wall_s"]), ("ok", 6))
        self.assertGreaterEqual(g["ms"], 1400)
        self.assertLess(time.monotonic() - start, 6)

    def test_a5_a_wall_out_of_range_is_one_second(self):
        for wall in ({"wall_s": 0}, {"wall_s": -1}, {"wall_s": 11}, {"wall_s": True},
                     {"wall_s": "6"}, {}):
            with self.subTest(wall=wall):
                g = self.described(**wall)
                self.assertEqual((g["state"], g["ms"], g["wall_s"]), ("timed out", 1000, 1.0))


class SyncModeTest(unittest.TestCase):
    """R3: `--check` reads a copy's mode as git keeps it, the owner's executable bit alone."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = os.path.join(os.path.realpath(tmp.name), "tool repo")
        os.mkdir(self.repo)
        subprocess.run(["git", "-C", self.repo, "init", "-q"], check=True)
        manifest = Path(self.repo, "plugin", ".claude-plugin", "plugin.json")
        manifest.parent.mkdir(parents=True)
        Path(self.repo, "plugin", "lib").mkdir()
        manifest.write_text(json.dumps({"name": "x", "version": "1.2.3"}))
        self.assertEqual(sy.sync(self.repo)[0], 0)
        self.exe = Path(self.repo, "scripts", "hygiene")  # the table's 755
        self.plain = Path(self.repo, "plugin", "lib", "agentik_install.py")  # the table's 644
        self.assertEqual((self.exe.stat().st_mode & 0o777, self.plain.stat().st_mode & 0o777), (0o755, 0o644))

    def test_a7_the_group_bit_is_not_compared(self):
        clean = (0, "sync: %s: every copy is commons'\n" % self.repo, "")
        for exe, plain in ((0o775, 0o664), (0o700, 0o600), (0o755, 0o644)):
            with self.subTest(exe=oct(exe), plain=oct(plain)):
                self.exe.chmod(exe)
                self.plain.chmod(plain)
                self.assertEqual(sy.sync("--check", self.repo), clean)

    def test_a8_the_executable_bit_is_compared(self):
        self.exe.chmod(0o644)
        self.plain.chmod(0o755)
        self.assertEqual(sy.sync("--check", self.repo),
                         (1, "behind plugin/lib/agentik_install.py\nbehind scripts/hygiene\n", ""))
        self.exe.chmod(0o675)  # the group's bit without the owner's
        self.plain.chmod(0o644)
        self.assertEqual(sy.sync("--check", self.repo), (1, "behind scripts/hygiene\n", ""))


if __name__ == "__main__":
    unittest.main()
