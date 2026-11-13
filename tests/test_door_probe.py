"""scripts/door-probe is run by hand, never by `make check` (packet ak2 R6): its shape, its usage
exits, no Makefile target naming it, and three runs over a temp folder of made-up checkouts, each
a git repo with a main: a make writer that copies its door blindly, a careful one that writes only
a newer door, and a launcher writer built from this repo's own scripts/. The probe's wall is
shortened through DOOR_PROBE_WALL, and its temp folder goes under the test's own TMPDIR."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "door-probe"
DOOR = ROOT / "bin" / "agentik"
WHO = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t" + "@x.invalid",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t" + "@x.invalid"}
BLIND = "BINDIR ?= /nonexistent\ninstall:\n\t@mkdir -p $(BINDIR)\n\tinstall -m 0755 scripts/agentik $(BINDIR)/agentik\n"
CAREFUL = "BINDIR ?= /nonexistent\ninstall:\n\tscripts/put-door scripts/agentik $(BINDIR)/agentik\n"
# put-door SRC DEST: DEST is written only when absent, or a plain file with an older VERSION
PUT_DOOR = r"""#!/bin/sh
v() { sed -n 's/^VERSION=//p' "$1" | head -n 1 | awk -F. '{ printf "%05d%05d%05d", $1, $2, $3 }'; }
if [ -e "$2" ] || [ -L "$2" ]; then
	[ -f "$2" ] && [ ! -L "$2" ] || exit 0
	expr "x$(v "$1")" \> "x$(v "$2")" > /dev/null || exit 0
fi
cp "$1" "$2.tmp.$$" && chmod 755 "$2.tmp.$$" && mv -f "$2.tmp.$$" "$2"
"""
RUNNER = """#!/usr/bin/python3
import os, sys
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import agentik_install
agentik_install.restore_parent_env()
if sys.argv[1:3] == ["install-cli", "--prefix"] and len(sys.argv) == 4:
    sys.exit(agentik_install.install_cli(sys.argv[3]))
sys.exit(2)
"""
CONF = "tool_name=agentik-demo\nremedy=/demo:install-cli\nrunner=demo\nold_name=\nold_state=\n"


class DoorProbeTest(unittest.TestCase):
    def test_shape(self):
        self.assertTrue(PROBE.read_text().startswith("#!/usr/bin/env python3\n"))
        self.assertTrue(os.access(PROBE, os.X_OK))

    def test_usage(self):
        p = subprocess.run([str(PROBE), "--help"], capture_output=True, text=True, timeout=30)
        self.assertEqual((p.returncode, p.stdout), (0, "usage: door-probe [--code DIR] [--rounds N] [--keep]\n"))
        for args in (["--bogus"], ["--code"], ["--rounds"], ["--rounds", "0"], ["--rounds", "x"]):
            p = subprocess.run([str(PROBE), *args], capture_output=True, text=True, timeout=30)
            self.assertEqual((p.returncode, p.stdout), (2, ""), args)

    def test_make_never_runs_it(self):
        self.assertNotIn("door-probe", (ROOT / "Makefile").read_text())


class DoorProbeRunTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(os.path.realpath(tmp.name))
        self.code = self.root / "code"
        self.tmp = self.root / "tmp"
        self.code.mkdir()
        self.tmp.mkdir()

    def write(self, repo, rel, text, mode=0o644):
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(mode)

    def checkout(self, name, files):
        repo = self.code / name
        repo.mkdir()
        for rel, (text, mode) in files.items():
            self.write(repo, rel, text, mode)
        env = dict(WHO, PATH="/usr/bin:/bin", HOME=str(self.root), GIT_CONFIG_NOSYSTEM="1")
        for argv in (["init", "-q", "-b", "main"], ["add", "."], ["commit", "-q", "-m", "a made-up tool"]):
            subprocess.run(["git", *argv], cwd=str(repo), env=env, check=True, capture_output=True)
        return repo

    def old_door(self):
        return DOOR.read_text().replace("VERSION=0.2.0", "VERSION=0.1.0")

    def probe(self):
        env = {"PATH": "/usr/bin:/bin", "HOME": str(self.root), "TMPDIR": str(self.tmp),
               "DOOR_PROBE_WALL": "6"}
        p = subprocess.run([str(PROBE), "--code", str(self.code), "--rounds", "2"], capture_output=True,
                           text=True, env=env, timeout=300)
        self.assertEqual(os.listdir(str(self.tmp)), [], "the probe's temp folder is removed")
        return p.returncode, p.stdout.splitlines(), p.stderr

    def row(self, lines, name, writer, case):
        hits = [line.split(None, 4) for line in lines if line.split()[:3] == [name, writer, case]]
        self.assertEqual(len(hits), 1, lines)
        return hits[0][3], hits[0][4] if len(hits[0]) > 4 else ""

    def test_a7_a_blind_make_writer_fails_kept(self):
        self.checkout("blind-tool", {"Makefile": (BLIND, 0o644), "scripts/agentik": (self.old_door(), 0o755)})
        code, lines, err = self.probe()
        self.assertEqual(code, 1, err)
        kind, text = self.row(lines, "blind-tool", "make", "kept")
        self.assertEqual(kind, "FAIL")
        self.assertIn("VERSION 0.1.0", text)
        self.assertEqual(self.row(lines, "blind-tool", "make", "absent")[0], "ok")
        for case in ("fifo", "raw", "race"):
            self.assertEqual(self.row(lines, "blind-tool", "make", case)[0], "note", case)
        self.assertEqual(lines[-1], "door-probe: stop: 1 failed")

    def test_a7_a_careful_make_writer_alone_goes(self):
        self.checkout("careful-tool", {"Makefile": (CAREFUL, 0o644), "scripts/agentik": (self.old_door(), 0o755),
                                       "scripts/put-door": (PUT_DOOR, 0o755)})
        code, lines, err = self.probe()
        self.assertEqual((code, lines[-1]), (0, "door-probe: go"), lines)
        self.assertEqual(self.row(lines, "careful-tool", "make", "kept")[0], "ok")
        self.assertEqual(self.row(lines, "careful-tool", "make", "absent")[0], "ok")
        self.assertRegex(self.row(lines, "careful-tool", "make", "race")[1], r"\A\d+ of 2 rounds ended below 0\.9\.0")
        self.assertFalse(subprocess.run(["git", "status", "--porcelain"], cwd=str(self.code / "careful-tool"),
                                        capture_output=True, text=True).stdout)

    def test_a7_a_launcher_writer_from_this_repos_scripts(self):
        repo = self.checkout("launch-tool", {
            "plugin/bin/agentik": (DOOR.read_text(), 0o755),
            "plugin/bin/agentik-demo": ((ROOT / "scripts" / "plugin-launcher").read_text(), 0o755),
            "plugin/lib/agentik_install.py": ((ROOT / "scripts" / "agentik_install.py").read_text(), 0o644),
            "plugin/lib/agentik-tool.conf": (CONF, 0o644),
            "plugin/lib/demo": (RUNNER, 0o755),
            "plugin/.claude-plugin/plugin.json": (json.dumps({"name": "demo", "version": "1.0.0"}), 0o644),
            # a makefile beside it: the launcher shape wins
            "Makefile": (BLIND, 0o644), "scripts/agentik": (self.old_door(), 0o755)})
        code, lines, err = self.probe()
        self.assertEqual(self.row(lines, "launch-tool", "launcher", "kept")[0], "ok", lines)
        kind, text = self.row(lines, "launch-tool", "launcher", "absent")
        self.assertEqual(kind, "ok", lines)
        self.assertIn("VERSION 0.2.0", text)
        self.assertFalse([line for line in lines if line.split()[:2] == ["launch-tool", "make"]])
        self.assertEqual((code, lines[-1]), (0, "door-probe: go"), lines)
        self.assertTrue(repo.is_dir())

    def test_a7_a_checkout_with_neither_is_not_listed(self):
        self.checkout("plain-tool", {"README.md": ("a made-up tool\n", 0o644)})
        (self.code / "not-a-repo").mkdir()
        code, lines, _ = self.probe()
        self.assertEqual(code, 0)
        self.assertFalse([line for line in lines if line.startswith("plain-tool")])
        self.assertEqual(lines[-1], "door-probe: go")


if __name__ == "__main__":
    unittest.main()
