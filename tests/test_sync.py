"""scripts/sync <repo> (agentik-r1 7.3): the four vendored copies land
byte-identical and executable under <repo>/scripts/, scripts/vendored.sha256
verifies under `shasum -a 256 -c`, a drifted copy fails it, and usage or a
target that is not a git checkout exits 2. A repo with a plugin/lib/ also gets the
canonical module, its launcher and the door (hq design/04 §7 item 4; packet c1)."""
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts" / "sync"
COPIES = {"scripts/agentik": "bin/agentik", "scripts/hygiene": "scripts/hygiene",
          "scripts/bounded": "scripts/bounded",
          "scripts/plugin-version-check": "scripts/plugin-version-check"}


def sync(*args):
    p = subprocess.run([str(SYNC), *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def verify(repo):
    p = subprocess.run(["shasum", "-a", "256", "-c", "scripts/vendored.sha256"],
                       capture_output=True, text=True, cwd=repo)
    return p.returncode, p.stdout


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.join(self.tmp.name, "tool repo")
        os.mkdir(self.repo)
        subprocess.run(["git", "-C", self.repo, "init", "-q"], check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_copies_and_pin_file(self):
        code, out, err = sync(self.repo)
        self.assertEqual((code, err), (0, ""))
        for copy, source in COPIES.items():
            path = Path(self.repo, copy)
            self.assertEqual(path.read_bytes(), Path(ROOT, source).read_bytes(), copy)
            self.assertTrue(os.access(path, os.X_OK), copy)
        code, out = verify(self.repo)
        self.assertEqual(code, 0)
        self.assertEqual(sorted(out.splitlines()), sorted(c + ": OK" for c in COPIES))
        rows = Path(self.repo, "scripts", "vendored.sha256").read_text().splitlines()
        self.assertEqual([r.split("  ", 1)[1] for r in rows], list(COPIES))
        # nothing else is written, no scratch file is left
        self.assertEqual(sorted(os.listdir(Path(self.repo, "scripts"))),
                         ["agentik", "bounded", "hygiene", "plugin-version-check",
                          "vendored.sha256"])

    def test_rerun_refreshes_a_drifted_copy(self):
        sync(self.repo)
        Path(self.repo, "scripts", "hygiene").write_text("drifted\n")
        self.assertNotEqual(verify(self.repo)[0], 0)
        self.assertEqual(sync(self.repo)[0], 0)
        self.assertEqual(verify(self.repo)[0], 0)

    def test_usage_and_missing_target_exit_two(self):
        plain = os.path.join(self.tmp.name, "plain")
        os.mkdir(plain)
        for args in ((), (self.repo, self.repo), ("--help",),
                     (os.path.join(self.tmp.name, "missing"),), (plain,), (str(ROOT),)):
            code, out, _ = sync(*args)
            self.assertEqual((code, out), (2, ""), args)
        self.assertEqual(os.listdir(plain), [])

    def test_cdpath_is_never_followed(self):
        # a relative target names the folder under the caller's cwd, never one on CDPATH
        base = self.tmp.name
        subprocess.run(["git", "-C", base, "init", "-q", "r"], check=True)
        os.makedirs(os.path.join(base, "alt"))
        subprocess.run(["git", "-C", os.path.join(base, "alt"), "init", "-q", "r"], check=True)
        env = dict(os.environ, CDPATH=os.path.join(base, "alt"))
        p = subprocess.run([str(SYNC), "r"], capture_output=True, text=True, cwd=base, env=env)
        self.assertEqual((p.returncode, p.stderr), (0, ""))
        self.assertEqual(verify(os.path.join(base, "r"))[0], 0)
        self.assertFalse(os.path.exists(os.path.join(base, "alt", "r", "scripts")))
        self.assertEqual(len(p.stdout.splitlines()), 1)

    def test_shape(self):
        self.assertTrue(SYNC.read_text().startswith("#!/bin/sh\n"))
        self.assertEqual(subprocess.run(["sh", "-n", str(SYNC)]).returncode, 0)

    def test_no_plugin_is_todays_set_byte_for_byte(self):
        code, out, err = sync(self.repo)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "sync: %s/scripts: agentik, hygiene, bounded, plugin-version-check, "
                         "vendored.sha256\n" % os.path.realpath(self.repo))
        expected = "".join("%s  %s\n" % (hashlib.sha256(Path(ROOT, COPIES[c]).read_bytes()).hexdigest(), c)
                           for c in COPIES)
        self.assertEqual(Path(self.repo, "scripts", "vendored.sha256").read_text(), expected)
        self.assertEqual(sorted(os.listdir(self.repo)), [".git", "scripts"])


PLACED = {"plugin/lib/agentik_install.py": "scripts/agentik_install.py",
          "plugin/bin/agentik-x": "scripts/plugin-launcher", "plugin/bin/agentik": "bin/agentik"}
RUNNER = '''import os, sys
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import agentik_install as a
raise SystemExit(a.install_cli() if sys.argv[1] == "install-cli" else print(a.version()))
'''


class PluginTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = os.path.join(os.path.realpath(self.tmp.name), "tool repo")
        os.mkdir(self.repo)
        subprocess.run(["git", "-C", self.repo, "init", "-q"], check=True)
        self.manifest = Path(self.repo, "plugin", ".claude-plugin", "plugin.json")
        self.manifest.parent.mkdir(parents=True)
        self.lib = Path(self.repo, "plugin", "lib")
        self.lib.mkdir()
        self.manifest.write_text(json.dumps(
            {"author": {"name": "someone"}, "name": "x", "version": "1.2.3"}))

    def snapshot(self):
        return {str(p.relative_to(self.repo)) for p in Path(self.repo).rglob("*")
                if ".git" not in p.parts and p.is_file()}

    def test_places_the_copies_and_the_door(self):
        code, out, err = sync(self.repo)
        self.assertEqual((code, err), (0, ""))
        for copy, source in PLACED.items():
            self.assertEqual(Path(self.repo, copy).read_bytes(), Path(ROOT, source).read_bytes(), copy)
        self.assertFalse(os.access(Path(self.repo, "plugin/lib/agentik_install.py"), os.X_OK))
        for copy in ("plugin/bin/agentik-x", "plugin/bin/agentik"):
            self.assertTrue(os.access(Path(self.repo, copy), os.X_OK), copy)
        code, out = verify(self.repo)
        self.assertEqual(code, 0)
        self.assertEqual(sorted(out.splitlines()), sorted(c + ": OK" for c in [*COPIES, *PLACED]))
        # the names are the tool's, written once and listed nowhere
        conf = Path(self.repo, "plugin/lib/agentik-tool.conf").read_text()
        self.assertIn("tool_name=agentik-x\nremedy=/x:install-cli\nrunner=agentik-x\n", conf)
        self.assertNotIn("agentik-tool.conf", Path(self.repo, "scripts/vendored.sha256").read_text())
        self.assertEqual(self.snapshot(), {*COPIES, *PLACED, "scripts/vendored.sha256",
                                           "plugin/.claude-plugin/plugin.json", "plugin/lib/agentik-tool.conf"})

    def test_a_one_byte_change_in_a_placed_copy_fails_the_check(self):
        sync(self.repo)
        for copy in PLACED:
            path = Path(self.repo, copy)
            good = path.read_bytes()
            path.write_bytes(good[:-1] + bytes([good[-1] ^ 1]))
            code, out = verify(self.repo)
            self.assertNotEqual(code, 0, copy)
            self.assertIn(copy + ": FAILED", out)
            path.write_bytes(good)
            self.assertEqual(verify(self.repo)[0], 0)

    def test_a_tools_own_conf_is_kept_and_names_the_launcher(self):
        conf = Path(self.repo, "plugin/lib/agentik-tool.conf")
        text = ("tool_name=agentik-other\nremedy=/other:install-cli\nrunner=agentik-other\n"
                "old_name=agentik-old\nold_state=\n")
        conf.write_text(text)
        self.assertEqual(sync(self.repo)[0], 0)
        self.assertEqual(sync(self.repo)[0], 0)
        self.assertEqual(conf.read_text(), text)
        self.assertTrue(Path(self.repo, "plugin/bin/agentik-other").is_file())
        self.assertFalse(Path(self.repo, "plugin/bin/agentik-x").exists())
        self.assertEqual(verify(self.repo)[0], 0)

    def test_a_plugin_with_no_lib_is_todays_set_and_its_bin_stands(self):
        self.lib.rmdir()
        relay = Path(self.repo, "plugin", "bin", "agentik-relay")
        relay.parent.mkdir()
        relay.write_bytes(b"#!/bin/sh\n# the tool's own\n")
        relay.chmod(0o750)
        self.manifest.write_text(json.dumps({"name": "relay", "version": "1.2.3"}))
        code, out, err = sync(self.repo)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "sync: %s/scripts: agentik, hygiene, bounded, plugin-version-check, "
                         "vendored.sha256\n" % self.repo)
        expected = "".join("%s  %s\n" % (hashlib.sha256(Path(ROOT, COPIES[c]).read_bytes()).hexdigest(), c)
                           for c in COPIES)
        self.assertEqual(Path(self.repo, "scripts", "vendored.sha256").read_text(), expected)
        self.assertEqual(relay.read_bytes(), b"#!/bin/sh\n# the tool's own\n")
        self.assertEqual(relay.stat().st_mode & 0o777, 0o750)
        self.assertEqual(self.snapshot(), {*COPIES, "scripts/vendored.sha256",
                                           "plugin/.claude-plugin/plugin.json", "plugin/bin/agentik-relay"})

    def sync_in(self, *args, **extra):
        """sync under a temp HOME and XDG_*, with `extra` over a bare environment."""
        home = os.path.join(os.path.realpath(self.tmp.name), "home")
        env = {"HOME": home, "PATH": "/usr/bin:/bin", "XDG_CONFIG_HOME": home + "/.config",
               "XDG_CACHE_HOME": home + "/.cache", "XDG_STATE_HOME": home + "/.local/state",
               "XDG_DATA_HOME": home + "/.local/share"}
        p = subprocess.run([str(SYNC), *args], capture_output=True, text=True, env=dict(env, **extra))
        return p.returncode, p.stdout, p.stderr

    def test_a_conf_with_whitespace_or_a_cr_around_a_line_writes_nothing(self):
        good = "tool_name=agentik-x\nremedy=/x:install-cli\nrunner=agentik-x\nold_name=\nold_state=\n"
        for text in ("  " + good, good.replace("runner", " runner"), good.replace("\n", "\r\n"),
                     good + " \n", good.replace("old_state=\n", "old_state=\t")):
            with self.subTest(text=text):
                (self.lib / "agentik-tool.conf").write_bytes(text.encode())
                before = self.snapshot()
                code, out, err = self.sync_in(self.repo)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("whitespace or a CR", err)
                self.assertEqual(self.snapshot(), before)

    def test_a_name_out_of_range_is_refused_under_a_utf8_locale(self):
        for word in ("Foo", "fé"):
            for where in ("conf", "manifest"):
                with self.subTest(word=word, where=where):
                    conf = self.lib / "agentik-tool.conf"
                    if where == "conf":
                        conf.write_text("tool_name=agentik-%s\n" % word, encoding="utf-8")
                    else:
                        conf.unlink(missing_ok=True)
                        self.manifest.write_text(json.dumps({"name": word}), encoding="utf-8")
                    before = self.snapshot()
                    code, out, err = self.sync_in(self.repo, LC_ALL="en_US.UTF-8", LANG="en_US.UTF-8")
                    self.assertEqual((code, out), (2, ""), err)
                    self.assertIn("names no tool", err)
                    self.assertEqual(self.snapshot(), before)

    def test_a_plugin_that_names_no_tool_writes_nothing(self):
        for text in (None, "not json", '{"version": "1.0.0"}', '{"name": "Bad Name"}', '{"name": "1x"}'):
            with self.subTest(text=text):
                if text is None:
                    self.manifest.unlink()
                else:
                    self.manifest.write_text(text)
                before = self.snapshot()
                code, out, err = sync(self.repo)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("names no tool", err)
                self.assertEqual(self.snapshot(), before)

    @unittest.skipUnless(os.access("/usr/bin/python3", os.X_OK), "no /usr/bin/python3 on this machine")
    def test_the_placed_copy_installs_under_a_bare_path(self):
        sync(self.repo)
        Path(self.repo, "plugin/lib/agentik-x").write_text(RUNNER)
        home = os.path.join(os.path.realpath(self.tmp.name), "home")
        os.mkdir(home)
        env = {"HOME": home, "PATH": "/usr/bin:/bin"}
        launcher = Path(self.repo, "plugin/bin/agentik-x")
        p = subprocess.run([str(launcher), "install-cli"], env=env, capture_output=True, text=True)
        self.assertEqual((p.returncode, p.stderr), (0, ""))
        p = subprocess.run([os.path.join(home, ".local/bin/agentik-x"), "--version"], env=env,
                           capture_output=True, text=True)
        self.assertEqual((p.returncode, p.stdout), (0, "1.2.3\n"))


if __name__ == "__main__":
    unittest.main()
