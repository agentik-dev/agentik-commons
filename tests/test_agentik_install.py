"""The canonical install-cli and launchers (hq design/04 §2, §3; packet c1): given a tool name in a
temp HOME under PATH=/usr/bin:/bin they freeze, write a launcher that runs --version, prune, and
refuse backward, on the interpreter a bare Mac has. Nothing here writes outside its temp folder."""
import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "agentik_install.py"
LAUNCHER = ROOT / "scripts" / "plugin-launcher"
DOOR = ROOT / "bin" / "agentik"
APPLE_PY = "/usr/bin/python3"
RUNNER = """import os, sys
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import agentik_install as a
a.restore_parent_env()
verb = sys.argv[1] if len(sys.argv) > 1 else ""
if verb == "--version":
    print(a.version())
elif verb == "install-cli":
    raise SystemExit(a.install_cli())
elif verb == "refresh":
    print(a.refresh() or "")
elif verb == "pyver":
    print("%d.%d" % sys.version_info[:2])
elif verb == "file":
    print(a.__file__)
elif verb == "env":
    print("\\n".join(sorted(os.environ)))
elif verb == "hook":
    pass
else:
    raise SystemExit(9)
"""


def conf(tool, old_name="", old_state=""):
    word = tool[len("agentik-"):]
    return ("tool_name=%s\nremedy=/%s:install-cli\nrunner=%s\nold_name=%s\nold_state=%s\n"
            % (tool, word, tool, old_name, old_state))


def load_module():
    spec = importlib.util.spec_from_file_location("agentik_install_under_test", MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(os.path.realpath(tmp.name))
        self.env = {"HOME": str(self.home), "PATH": "/usr/bin:/bin"}

    def plugin(self, tool="agentik-x", ver="1.0.0", **old):
        word = tool[len("agentik-"):]
        root = self.home / ".claude" / "plugins" / "cache" / "agentik" / word / ver
        (root / ".claude-plugin").mkdir(parents=True)
        (root / "bin").mkdir()
        (root / "lib").mkdir()
        (root / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": word, "version": ver}))
        shutil.copyfile(MODULE, root / "lib" / "agentik_install.py")
        (root / "lib" / tool).write_text(RUNNER)
        (root / "lib" / "agentik-tool.conf").write_text(conf(tool, **old))
        for src, to in ((DOOR, "agentik"), (LAUNCHER, tool)):
            shutil.copyfile(src, root / "bin" / to)
            os.chmod(root / "bin" / to, 0o755)
        return root

    def run_tool(self, path, *args, env=None, cwd=None):
        p = subprocess.run([str(path), *args], capture_output=True, text=True, stdin=subprocess.DEVNULL,
                           env=dict(self.env, **(env or {})), cwd=cwd or str(self.home))
        return p.returncode, p.stdout, p.stderr

    def install(self, plugin, tool="agentik-x"):
        code, out, err = self.run_tool(plugin / "bin" / tool, "install-cli")
        self.assertEqual((code, err), (0, ""), out)
        return out

    def bin(self, name="agentik-x"):
        return self.home / ".local" / "bin" / name

    def share(self, name="agentik-x"):
        return self.home / ".local" / "share" / name

    def trees(self, name="agentik-x"):
        return sorted(p.name for p in self.share(name).iterdir() if not p.name.startswith("."))


@unittest.skipUnless(os.access(APPLE_PY, os.X_OK), "no /usr/bin/python3 on this machine")
class Generic(Base):
    def test_freezes_and_the_launcher_runs_version(self):
        plugin = self.plugin()
        out = self.install(plugin)
        self.assertIn("installed %s -> " % self.bin(), out)
        self.assertNotIn("links to it", out)
        tree = self.share() / self.trees()[0]
        self.assertTrue(re.fullmatch(r"[0-9a-f]{40}", tree.name))
        self.assertEqual(sorted(os.listdir(tree)), sorted(
            ["agentik", "agentik-tool.conf", "agentik-x", "agentik_install.py", "plugin.json"]))
        self.assertEqual(self.run_tool(self.bin(), "--version")[:2], (0, "1.0.0\n"))
        # the launcher runs the tree, not the plugin, and the door reaches it from PATH
        self.assertEqual(self.run_tool(self.bin(), "file")[1].strip(), str(tree / "agentik_install.py"))
        path = {"PATH": "%s:/usr/bin:/bin" % self.bin().parent}
        self.assertEqual(self.run_tool(self.bin("agentik"), "x", "--version", env=path)[:2], (0, "1.0.0\n"))
        self.assertTrue(os.access(self.bin(), os.X_OK))

    def test_a_floor_run(self):
        # Python 3.9 is the floor: the source parses at it, and /usr/bin/python3 ran it, whichever
        # that is. On this Mac it is 3.9.
        ast.parse(MODULE.read_text(), feature_version=(3, 9))
        plugin = self.plugin()
        self.install(plugin)
        apple = subprocess.run([APPLE_PY, "-c", "import sys;print('%d.%d' % sys.version_info[:2])"],
                               capture_output=True, text=True).stdout.strip()
        for path in (self.bin(), plugin / "bin" / "agentik-x"):
            self.assertEqual(self.run_tool(path, "pyver")[:2], (0, apple + "\n"))
        self.assertGreaterEqual(tuple(int(n) for n in apple.split(".")), (3, 9))

    def test_two_tools_byte_identical_and_apart(self):
        x, y = self.plugin("agentik-x", "1.0.0"), self.plugin("agentik-y", "2.0.0")
        self.install(x)
        self.install(y, "agentik-y")
        for rel in ("lib/agentik_install.py",):
            self.assertEqual((x / rel).read_bytes(), (y / rel).read_bytes())
        self.assertEqual((x / "bin/agentik-x").read_bytes(), (y / "bin/agentik-y").read_bytes())
        self.assertEqual(len(self.trees("agentik-x")), 1)
        self.assertEqual(len(self.trees("agentik-y")), 1)
        self.assertEqual(self.run_tool(self.bin("agentik-y"), "--version")[1], "2.0.0\n")
        self.assertEqual(self.run_tool(self.bin("agentik-x"), "--version")[1], "1.0.0\n")

    def test_prunes_old_trees_and_keeps_the_newest(self):
        plugin = self.plugin()
        self.share().mkdir(parents=True)
        for n in range(5):
            old = self.share() / ("old%d" % n)
            old.mkdir()
            os.utime(old, (1000 + n, 1000 + n))
        out = self.install(plugin)
        tree = self.run_tool(self.bin(), "file")[1].strip().split("/")[-2]
        if "keeping every tree" in out:     # a machine whose ps shows no environment fails safe
            self.assertEqual(len(self.trees()), 6)
        else:
            self.assertIn("prune-trees: removed 3, kept 3", out)
            self.assertEqual(self.trees(), sorted(["old3", "old4", tree]))

    def test_a_reinstall_is_the_same_tree(self):
        plugin = self.plugin()
        self.install(plugin)
        first = self.trees()
        self.install(plugin)
        self.assertEqual(self.trees(), first)

    def test_a_decoy_in_the_cwd_never_runs(self):
        plugin = self.plugin()
        self.install(plugin)
        decoy = self.home / "decoy"
        decoy.mkdir()
        (decoy / "agentik_install.py").write_text("raise SystemExit(42)\n")
        for path in (self.bin(), plugin / "bin" / "agentik-x"):
            self.assertEqual(self.run_tool(path, "--version", cwd=str(decoy))[:2], (0, "1.0.0\n"))

    def test_what_the_launchers_add_never_reaches_the_tool(self):
        plugin = self.plugin()
        self.install(plugin)
        for path in (self.bin(), plugin / "bin" / "agentik-x"):
            keys = self.run_tool(path, "env")[1].split()
            self.assertEqual([k for k in keys if k.startswith("AGENTIK_PARENT")
                              or k in ("SDKROOT", "CPATH", "LIBRARY_PATH", "MANPATH")], [])

    # ---- the forward refresh ----

    def refresh(self, plugin, tool="agentik-x"):
        return self.run_tool(plugin / "bin" / tool, "refresh", env={"CLAUDE_PLUGIN_ROOT": str(plugin)})

    def test_refresh_moves_forward(self):
        self.install(self.plugin(ver="1.0.0"))
        newer = self.plugin(ver="1.1.0")
        self.assertEqual(self.refresh(newer), (0, "\n", ""))
        self.assertEqual(self.run_tool(self.bin(), "--version")[1], "1.1.0\n")

    def test_refresh_refuses_backward_and_equal(self):
        for ver, older in (("2.0.0", "1.9.0"), ("2.0.0", "2.0.0-alpha.9"),
                           ("2.0.0-alpha.10", "2.0.0-alpha.9")):
            with self.subTest(ver=ver, older=older):
                self.setUp()
                self.install(self.plugin(ver=ver))
                before = self.bin().read_bytes()
                self.assertEqual(self.refresh(self.plugin(ver=older)), (0, "\n", ""))
                self.assertEqual(self.bin().read_bytes(), before)
                self.assertEqual(len(self.trees()), 1)
        self.setUp()
        plugin = self.plugin()
        self.install(plugin)
        before = self.bin().read_bytes()
        self.assertEqual(self.refresh(plugin), (0, "\n", ""))
        self.assertEqual(self.bin().read_bytes(), before)

    def test_refresh_creates_no_launcher_and_follows_only_its_root(self):
        plugin = self.plugin()
        self.assertEqual(self.refresh(plugin), (0, "\n", ""))
        self.assertFalse(self.bin().exists())
        self.install(plugin)
        before = self.bin().read_bytes()
        newer = self.plugin(ver="1.1.0")
        stray = {"CLAUDE_PLUGIN_ROOT": str(plugin)}     # the root names another plugin
        self.assertEqual(self.run_tool(newer / "bin/agentik-x", "refresh", env=stray)[0], 0)
        self.assertEqual(self.bin().read_bytes(), before)

    def test_refresh_never_raises(self):
        plugin = self.plugin()
        self.install(plugin)
        newer = self.plugin(ver="1.1.0")
        share = self.share()
        os.chmod(share, 0o555)
        self.addCleanup(os.chmod, share, 0o755)
        code, out, err = self.refresh(newer)
        os.chmod(share, 0o755)
        self.assertEqual((code, err), (0, ""))
        self.assertIn("agentik-x: the launcher did not move to 1.1.0", out)
        self.assertIn("run /x:install-cli", out)
        self.assertEqual(self.run_tool(self.bin(), "--version")[1], "1.0.0\n")

    # ---- what is gone ----

    def test_a_gone_tree(self):
        plugin = self.plugin()
        self.install(plugin)
        tree = self.share() / self.trees()[0]
        shutil.rmtree(tree)
        code, out, err = self.run_tool(self.bin(), "status")
        self.assertEqual((code, out), (3, ""))
        self.assertIn("run /x:install-cli", err)
        code, out, err = self.run_tool(self.bin(), "hook", "SessionStart")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("run /x:install-cli", json.loads(out)["systemMessage"])
        marker = self.home / ".local/state/agentik-x/install-needed"
        self.assertEqual(marker.read_text().strip(), str(tree))
        code, out, err = self.run_tool(self.bin(), "hook", "Stop")
        self.assertEqual((code, out, err), (0, "", ""))      # once, and the marker said it
        self.install(plugin)
        self.assertFalse(marker.exists())

    def test_a_gone_interpreter(self):
        plugin = self.plugin()
        self.install(plugin)
        none = {"AGENTIK_PYTHON": "/nonexistent", "PATH": str(self.home / "empty")}
        for path in (self.bin(), plugin / "bin" / "agentik-x"):
            self.assertEqual(self.run_tool(path, "status", env=none)[0], 3)
            self.assertEqual(self.run_tool(path, "hook", "Stop", env=none)[0], 0)
            code, out, _ = self.run_tool(path, "hook", "SessionStart", env=none)
            self.assertEqual(code, 0)
            self.assertIn("agentik-x", json.loads(out)["systemMessage"])

    # ---- the names ----

    def test_no_old_name_leaves_no_trace(self):
        self.install(self.plugin())
        text = self.bin().read_text()
        self.assertNotIn("renamed", text)
        self.assertNotIn('dir="$state/"', text)
        self.assertEqual(sorted(p.name for p in self.bin().parent.iterdir()), ["agentik", "agentik-x"])

    def test_an_old_name_links_and_its_state_folder_holds_the_marker(self):
        plugin = self.plugin(old_name="agentik-oldx", old_state="agentik-oldstate")
        out = self.install(plugin)
        self.assertIn("links to it", out)
        link = self.bin("agentik-oldx")
        self.assertEqual(os.readlink(link), "agentik-x")
        self.assertEqual(self.run_tool(link, "--version")[1], "1.0.0\n")
        old = self.home / ".local/state/agentik-oldstate"
        old.mkdir(parents=True)
        shutil.rmtree(self.share() / self.trees()[0])
        self.run_tool(self.bin(), "hook", "Stop")
        self.assertTrue((old / "install-needed").exists())
        self.install(plugin)
        self.assertFalse((old / "install-needed").exists())

    def test_the_plugin_launcher_with_no_names_or_no_runner(self):
        for missing in ("agentik-tool.conf", "agentik-x"):
            with self.subTest(missing=missing):
                self.setUp()
                plugin = self.plugin()
                (plugin / "lib" / missing).unlink()
                launcher = plugin / "bin" / "agentik-x"
                self.assertEqual(self.run_tool(launcher, "status")[0], 3)
                self.assertEqual(self.run_tool(launcher, "hook", "PreToolUse"), (0, "", ""))
                code, out, _ = self.run_tool(launcher, "hook", "SessionStart")
                self.assertEqual(code, 0)
                self.assertIn("agentik-x: no ", json.loads(out)["systemMessage"])

    def test_a_malformed_conf_refuses_and_writes_nothing(self):
        for text in ("", "tool_name=agentik-x\n", conf("agentik-x") + "extra=1\n",
                     conf("agentik-x").replace("tool_name=agentik-x", "tool_name=x"),
                     conf("agentik-x") + "runner=again\n", "tool_name=a b\n"):
            with self.subTest(text=text):
                self.setUp()
                plugin = self.plugin()
                (plugin / "lib" / "agentik-tool.conf").write_text(text)
                code, out, err = self.run_tool(plugin / "bin" / "agentik-x", "install-cli")
                # a conf too broken to name a runner refuses at the launcher, exit 3
                self.assertIn(code, (1, 3))
                self.assertEqual(out, "")
                self.assertTrue(err)
                self.assertFalse((self.home / ".local").exists())


class Text(unittest.TestCase):
    def test_the_canonical_forms_name_no_tool(self):
        word = re.compile(r"claude[-_]session|agentik-session|/session:|claude_session|OLD_APP")
        for path in (MODULE, LAUNCHER):
            self.assertIsNone(word.search(path.read_text()), path)

    def test_shape(self):
        self.assertTrue(LAUNCHER.read_text().startswith("#!/bin/sh\n"))
        self.assertTrue(os.access(LAUNCHER, os.X_OK))
        self.assertEqual(subprocess.run(["sh", "-n", str(LAUNCHER)]).returncode, 0)

    def test_light_at_import(self):
        # a hook imports it: no heavy module and no file read at import
        code = ("import sys; before=set(sys.modules); import importlib.util as u;"
                "s=u.spec_from_file_location('m', %r); m=u.module_from_spec(s); s.loader.exec_module(m);"
                "print([n for n in ('subprocess','shutil','argparse','hashlib','tempfile','secrets')"
                " if n in sys.modules and n not in before])" % str(MODULE))
        p = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True)
        self.assertEqual(p.stdout.strip(), "[]", p.stderr)

    def test_the_launcher_text_is_one_pass(self):
        mod = load_module()
        names = {"tool_name": "agentik-x", "remedy": "/x:install-cli", "runner": "agentik-x",
                 "old_name": "", "old_state": ""}
        text = mod.launcher_text("/t/__APPLE__", "1.0.0-__TREE__", names)
        self.assertIn("/t/__APPLE__", text)
        self.assertIn("1.0.0-__TREE__", text)
        self.assertNotIn("__NAME__", text)


class Prune(unittest.TestCase):
    """prune() against a stand-in ps, so that what counts as live does not depend on the machine."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(os.path.realpath(tmp.name))
        self.share = self.dir / "share"
        self.share.mkdir()
        self.mod = load_module()
        for n, name in enumerate(("a", "b", "c", "d", "new")):
            (self.share / name).mkdir()
            os.utime(self.share / name, (1000 + n, 1000 + n))
        (self.share / ".lock").write_text("")

    def ps(self, body):
        path = self.dir / "ps"
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(0o755)
        return str(path)

    def names(self):
        return sorted(os.listdir(self.share))

    def test_a_live_tree_stays(self):
        ps = self.ps('echo "1 python -I %s/b/agentik-x run AGENTIK_PRUNE_PROBE=$AGENTIK_PRUNE_PROBE"' % self.share)
        code, lines = self.mod.prune(self.share, "new", keep=1, ps=ps)
        self.assertEqual(code, 0)
        self.assertEqual(self.names(), [".lock", "b", "new"])
        self.assertEqual(lines[-1], "prune-trees: removed 3, kept 2 (1 live, the newest 1)")

    def test_a_tree_named_through_a_symlink_stays(self):
        os.symlink(self.share, self.dir / "alias")
        ps = self.ps('echo "1 x=%s/c/f AGENTIK_PRUNE_PROBE=$AGENTIK_PRUNE_PROBE"' % (self.dir / "alias"))
        self.mod.prune(self.share, "new", keep=1, ps=ps)
        self.assertEqual(self.names(), [".lock", "c", "new"])

    def test_on_doubt_nothing_goes(self):
        for body in ("exit 1", "echo no environment here"):
            code, lines = self.mod.prune(self.share, "new", keep=1, ps=self.ps(body))
            self.assertEqual(code, 0)
            self.assertIn("keeping every tree", lines[-1])
            self.assertEqual(len(self.names()), 6)
        code, lines = self.mod.prune(self.share, "new", keep=1, ps=str(self.dir / "nosuch"))
        self.assertIn("keeping every tree", lines[-1])

    def test_a_bad_new_is_usage(self):
        for new in ("nosuch", "../share", "", "."):
            self.assertEqual(self.mod.prune(self.share, new, ps="false")[0], 2, new)
        self.assertEqual(self.mod.prune(self.share, "new", keep=0, ps="false")[0], 2)


if __name__ == "__main__":
    unittest.main()
