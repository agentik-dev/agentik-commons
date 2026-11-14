"""scripts/voice (packet ak1a R5): the sidecar holds the catalogue as last checked, and the
check is red on a one-word change until the scanner passes again. The scanner here is a fake
under RESPEAK_ROOT, or none at all; nothing is written outside a temp folder."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fk_homes  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "voice"
CATALOGUE = ROOT / "plugins" / "suite" / "lib" / "agentik_suite" / "messages.md"
SIDECAR = ROOT / "design" / "voice" / "checked.sha256"
FAKE = "import sys\nopen(sys.argv[0] + '.args', 'w').write(' '.join(sys.argv[1:]))\nsys.exit(%d)\n"


class VoiceTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name
        self.cat = os.path.join(self.tmp, "messages.md")
        shutil.copy(CATALOGUE, self.cat)
        self.side = os.path.join(self.tmp, "checked.sha256")

    def voice(self, *args, **env):
        base = {"HOME": self.tmp, "PATH": "/usr/bin:/bin"}
        base.update(env)
        p = subprocess.run([sys.executable, str(SCRIPT), "--catalogue", self.cat,
                            "--sidecar", self.side, *args],
                           capture_output=True, text=True, env=base, timeout=60)
        return p.returncode, p.stdout, p.stderr

    def fake(self, code):
        root = os.path.join(self.tmp, "scanner")
        os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
        path = os.path.join(root, "scripts", "respeak-measure.py")
        with open(path, "w") as fh:
            fh.write(FAKE % code)
        return root, path

    def test_the_committed_sidecar_holds_the_catalogue(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--check"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(SIDECAR.read_text().endswith(
            "  plugins/suite/lib/agentik_suite/messages.md\n"))

    def test_a7_one_word_turns_the_check_red_until_voice_runs(self):
        root, path = self.fake(0)
        self.assertEqual(self.voice("--check")[0], 1)  # no sidecar yet
        self.assertEqual(self.voice(RESPEAK_ROOT=root)[0], 0)
        self.assertIn("--fail-on warn", Path(path + ".args").read_text())
        self.assertIn("--config", Path(path + ".args").read_text())
        self.assertEqual(self.voice("--check")[0], 0)
        with open(self.cat, "a") as fh:
            fh.write("- `x.y`: one more word\n")
        code, out, err = self.voice("--check")
        self.assertEqual(code, 1)
        self.assertIn("make voice", err)
        self.assertEqual(self.voice(RESPEAK_ROOT=root)[0], 0)
        self.assertEqual(self.voice("--check")[0], 0)

    def test_a_failing_scanner_writes_nothing(self):
        root, _ = self.fake(1)
        self.assertEqual(self.voice(RESPEAK_ROOT=root)[0], 1)
        self.assertFalse(os.path.exists(self.side))

    def test_no_scanner_exits_two_and_writes_nothing(self):
        code, out, err = self.voice(CLAUDE_CONFIG_DIR=os.path.join(self.tmp, "none"))
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(self.side))
        self.assertEqual(self.voice(RESPEAK_ROOT=os.path.join(self.tmp, "none"))[0], 2)

    def scanner_in(self, root):
        d = os.path.join(root, "scripts")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "respeak-measure.py")
        with open(path, "w") as fh:
            fh.write(FAKE % 0)
        return path

    def test_fk1_the_fork_alone_gives_its_scanner(self):
        for ver in ("0.12.6", "0.12.6-acme.1"):
            h = fk_homes.FkHome(os.path.join(self.tmp, ver), tool="respeak")
            path = self.scanner_in(h.install(h.fork, ver))
            code, out, err = self.voice(HOME=h.home)
            self.assertEqual(code, 0, err)
            self.assertTrue(os.path.exists(path + ".args"), ver)
            os.remove(self.side)

    def test_fk1_a_leftover_folder_or_two_installed_exit_two(self):
        h = fk_homes.FkHome(os.path.join(self.tmp, "left"), tool="respeak")
        self.scanner_in(h.folder(h.fork, "0.12.6"))
        code, out, err = self.voice(HOME=h.home)
        self.assertEqual(code, 2)
        self.assertIn("sources", err)
        self.assertFalse(os.path.exists(self.side))
        h = fk_homes.FkHome(os.path.join(self.tmp, "two"), tool="respeak")
        self.scanner_in(h.install(h.own, "0.13.0"))
        self.scanner_in(h.install(h.fork, "0.12.6"))
        code, out, err = self.voice(HOME=h.home)
        self.assertEqual(code, 2)
        self.assertIn("sources", err)
        self.assertFalse(os.path.exists(self.side))

    def test_fk1_an_entry_with_no_string_install_path_is_not_found(self):
        # review 1, R1-F1: the finder and voice agree; voice exits 2 with its line, no traceback
        sys.path.insert(0, str(ROOT / "plugins" / "suite" / "lib"))
        from agentik_suite import sources
        for odd in (None, 5):
            h = fk_homes.FkHome(os.path.join(self.tmp, "odd-%s" % odd), tool="respeak")
            self.scanner_in(h.install(h.own, "0.1"))
            if odd is None:
                del h.table[h.own][0]["installPath"]
            else:
                h.table[h.own][0]["installPath"] = odd
            h.write()
            row = sources.read(h.env(), h.home, ["respeak"], more=False)[0]
            self.assertEqual((row["kind"], row["found"], row["root"]), ("own", False, None), odd)
            code, out, err = self.voice(HOME=h.home)
            self.assertEqual(code, 2, err)
            self.assertIn("no scanner", err)
            self.assertNotIn("Traceback", err)
            self.assertFalse(os.path.exists(self.side))


if __name__ == "__main__":
    unittest.main()
