"""Row ak4-remove: `agentik-suite remove` takes a tool off the machine and says what it kept.

Each home is test_ak4a_update's `Home`, a temp HOME, with its `claude` stub taught `plugin
uninstall` (the entry dropped from installed_plugins.json, the cache and data folders kept, as
hq measured Claude Code 2.1.325 does with `--keep-data`) and `plugin marketplace remove` (the
entry dropped, the marketplace's folder removed). A tool `x` is placed by a real `install-cli`
from a plugin built as test_agentik_install's `Base` builds one. Every home, state, config and
cache folder is asserted under the test's temp folder before the verb runs; no test starts a
real `claude`, reads the live home or the live process list."""
import json
import os
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_install import APPLE_PY, DOOR, MODULE, RUNNER, conf  # noqa: E402
from test_agentik_install import LAUNCHER as TOOL_LAUNCHER  # noqa: E402
from test_ak4a_update import LAUNCHER, Base, Home  # noqa: E402
from test_ak4b_uninstall import snapshot  # noqa: E402

LIVE = os.path.realpath(os.path.expanduser("~"))
UNINSTALL = "claude plugin uninstall x@agentik --keep-data"
CLAUDE = r'''#!/usr/bin/python3
import json, os, shutil, sys
home = os.environ["HOME"]
a = sys.argv[1:]
with open(os.path.join(home, "ran.log"), "a") as fh:
    fh.write("claude " + " ".join(a) + "\n")
d = os.path.join(home, ".claude", "plugins")
def edit(name, change):
    path = os.path.join(d, name)
    table = json.load(open(path))
    change(table)
    json.dump(table, open(path, "w"))
if a[:2] == ["plugin", "uninstall"] and len(a) == 4 and a[3] == "--keep-data":
    fail = os.path.join(home, "fail")
    if os.path.exists(fail) and open(fail).read().strip() == a[2]:
        print("the plugin would not go")
        sys.exit(1)
    edit("installed_plugins.json", lambda t: t["plugins"].pop(a[2], None))
    sys.exit(0)
if a[:3] == ["plugin", "marketplace", "remove"] and len(a) == 4:
    edit("known_marketplaces.json", lambda t: t.pop(a[3], None))
    shutil.rmtree(os.path.join(d, "marketplaces", a[3]), ignore_errors=True)
    sys.exit(0)
sys.exit(2)
'''


class RHome(Home):
    def __init__(self, path, listed=("murmur", "paint")):
        Home.__init__(self, path, listed)
        self.file(os.path.join(self.bin, "claude"), CLAUDE)
        self.cache = self.home + "-cache"

    def real_tool(self, name="x", ver="1.0.0", plugin=True):
        """A plugin built as test_agentik_install's Base builds one, placed by its own install-cli."""
        tool = "agentik-" + name
        root = os.path.join(self.plugins, "cache", "agentik", name, ver)
        for sub in (".claude-plugin", "bin", "lib"):
            os.makedirs(os.path.join(root, sub), exist_ok=True)
        with open(os.path.join(root, ".claude-plugin", "plugin.json"), "w") as fh:
            json.dump({"name": name, "version": ver}, fh)
        shutil.copyfile(str(MODULE), os.path.join(root, "lib", "agentik_install.py"))
        self.file(os.path.join(root, "lib", tool), RUNNER)
        self.file(os.path.join(root, "lib", "agentik-tool.conf"), conf(tool))
        for src, to in ((DOOR, "agentik"), (TOOL_LAUNCHER, tool)):
            shutil.copyfile(str(src), os.path.join(root, "bin", to))
            os.chmod(os.path.join(root, "bin", to), 0o755)
        self.place(os.path.join(root, "bin", tool))
        if plugin:
            self.table[name + "@agentik"] = [{"scope": "user", "version": ver, "installPath": root}]
            self.write()
        return root

    def place(self, exe):
        self.under_temp()
        p = subprocess.run([exe, "install-cli"], capture_output=True, text=True, env=self.env(),
                           cwd=self.home, stdin=subprocess.DEVNULL, timeout=120)
        assert p.returncode == 0 and not p.stderr, p.stdout + p.stderr

    def kept_folders(self, name="x"):
        found = [os.path.join(self.home, ".config", "agentik", name, "config.yaml"),
                 os.path.join(self.home, ".local", "state", "agentik-" + name, "notes"),
                 os.path.join(self.plugins, "data", name + "@agentik", "data.json")]
        for path in found:
            self.file(path, "kept\n")
        return [os.path.dirname(p) for p in found]

    def under_temp(self, env=None):
        """R11: the home and every folder the verb may write under, inside the temp folder."""
        env = env or self.env()
        top = os.path.dirname(os.path.realpath(self.home))
        for key in ("HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "CLAUDE_CONFIG_DIR"):
            if env.get(key):
                real = os.path.realpath(env[key])
                assert real.startswith(top + os.sep), (key, real)
                assert real != LIVE and not LIVE.startswith(real + os.sep), (key, real)

    def go(self, *args, exe=LAUNCHER, **more):
        env = self.env(**more)
        self.under_temp(env)
        p = subprocess.run([str(exe)] + list(args), capture_output=True, text=True, env=env,
                           cwd=self.home, stdin=subprocess.DEVNULL, timeout=120)
        return p.returncode, p.stdout, p.stderr

    def agentik(self):
        return sorted(n for n in os.listdir(self.bindir) if n.startswith("agentik"))


@unittest.skipUnless(os.access(APPLE_PY, os.X_OK), "no /usr/bin/python3 on this machine")
class Remove(Base):
    def home(self, listed=("murmur", "paint"), name="h"):
        return RHome(os.path.join(self.tmp, name), listed)

    def x(self, **kw):
        h = self.home()
        h.real_tool(**kw)
        return h, h.kept_folders()

    def test_1_no_name_both_forms_and_a_bad_name(self):
        h, _ = self.x()
        before = snapshot(h.home)
        for args in (("remove",), ("remove", "x", "--all"), ("remove", "--yes")):
            code, out, err = h.go(*args)
            self.assertEqual(code, 2, args)
            self.assertIn("remove", err)
            self.assertIn("--all", err)
        code, out, err = h.go("remove", "zzz", "--dry-run")
        self.assertEqual(code, 2, out + err)
        self.assertIn("zzz", err)
        self.assertIn("is not a plugin name", err)
        self.assertEqual(h.claude(), [])
        self.assertEqual(snapshot(h.home), before)

    def test_2_a_dry_run_names_the_plan_and_writes_nothing(self):
        h, kept = self.x()
        before = snapshot(h.home)
        code, out, err = h.go("remove", "x", "--dry-run")
        self.assertEqual(code, 0, out + err)
        self.assertIn(UNINSTALL, out)
        self.assertIn("~/.local/bin/agentik-x", out)
        self.assertIn("~/.local/share/agentik-x", out)
        self.assertIn("would remove", out)
        for path in kept:
            self.assertIn("~/" + os.path.relpath(path, h.home), out)
        self.assertEqual(snapshot(h.home), before)
        code, out, err = h.go("remove", "x", "--dry-run", "--json")
        obj = json.loads(out)
        self.assertEqual((code, obj["schema"], obj["dry_run"], obj["ok"]), (0, "agentik.remove/1", True, True))
        fates = [r["fate"] for t in obj["tools"] for r in t["rows"]]
        self.assertIn("would remove", fates)
        self.assertEqual(snapshot(h.home), before)
        self.assertEqual(h.claude(), [])

    def test_3_a_run_takes_it_off_and_keeps_config_and_state(self):
        h, kept = self.x()
        share = os.path.join(h.home, ".local", "share", "agentik-x")
        code, out, err = h.go("remove", "x", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(h.claude(), [UNINSTALL])
        self.assertFalse(os.path.lexists(os.path.join(h.bindir, "agentik-x")))
        self.assertFalse(os.path.lexists(share))
        self.assertIn("removed", out)
        self.assertIn("~/.local/share/agentik-x", out)
        for path in kept:
            self.assertTrue(os.path.isdir(path), path)
            self.assertIn("~/" + os.path.relpath(path, h.home), out)
        with open(os.path.join(h.home, ".local", "state", "agentik-suite", "setup.jsonl")) as fh:
            entry = json.loads(fh.read().splitlines()[-1])
        self.assertEqual((entry["verb"], entry["exit"], entry["plugins"]), ("remove", 0, ["x"]))
        self.assertEqual(sorted(entry), ["at", "exit", "plugins", "ran", "verb", "version", "wrote"])
        before = snapshot(h.home)
        code, out, err = h.go("remove", "x", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertIn("nothing to take off", out)
        self.assertEqual(h.claude(), [UNINSTALL])
        self.assertEqual(snapshot(h.home), before)

    def test_4_a_launcher_not_install_clis_is_kept(self):
        h = self.home()
        h.install("murmur@agentik", "1.0.0")
        code, out, err = h.go("remove", "murmur", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(h.claude(), ["claude plugin uninstall murmur@agentik --keep-data"])
        self.assertTrue(os.path.isfile(os.path.join(h.bindir, "agentik-murmur")))
        self.assertIn("~/.local/bin/agentik-murmur", out)
        self.assertIn("not the launcher install-cli wrote", out)

    def test_5_a_live_tree_or_a_relay_run_holds(self):
        for line in ("77 /usr/bin/python3 {share}/{tree}/agentik-x status\n",
                     "88 /opt/tools/agentik-relay run plan.md\n"):
            h, _ = self.x()
            share = os.path.join(h.home, ".local", "share", "agentik-x")
            tree = [n for n in os.listdir(share) if not n.startswith(".")][0]
            h.ps("1 /sbin/launchd\n" + line.format(share=share, tree=tree))
            before = snapshot(h.home)
            code, out, err = h.go("remove", "x", "--yes")
            self.assertEqual(code, 2, out + err)
            self.assertIn("held remove:", err)
            self.assertEqual(h.claude(), [])
            self.assertEqual(snapshot(h.home), before)
            shutil.rmtree(h.home)
            shutil.rmtree(h.cache, ignore_errors=True)

    def test_6_another_kind_is_kept_and_a_launcher_alone_goes(self):
        h = self.home(("murmur", "paint", "x"))
        h.real_tool(plugin=False)
        h.file(os.path.join(h.home, ".config", "agentik", "suite", "config.yaml"), "sources:\n  x: ~/src/x\n")
        code, out, err = h.go("remove", "x", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(h.claude(), [])
        self.assertTrue(os.path.isfile(os.path.join(h.bindir, "agentik-x")))
        self.assertIn("kept", out)
        h2 = self.home(name="h2")
        h2.real_tool(plugin=False)
        code, out, err = h2.go("remove", "x", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(h2.claude(), [])
        self.assertFalse(os.path.lexists(os.path.join(h2.bindir, "agentik-x")))

    def test_7_all_as_the_installed_agentik(self):
        h, kept = self.x()
        h.place(str(LAUNCHER))  # the suite by a real install-cli: its launcher, trees, the door
        os.makedirs(os.path.join(h.plugins, "marketplaces", "agentik"))
        os.makedirs(os.path.join(h.cache, "agentik", "suite"), exist_ok=True)
        cfg = h.file(os.path.join(h.home, ".config", "agentik", "suite", "config.yaml"), "# mine\n")
        self.assertIn("agentik-suite", h.agentik())
        code, out, err = h.go("remove", "--all", "--yes", exe=os.path.join(h.bindir, "agentik"))
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(h.claude(), [UNINSTALL, "claude plugin marketplace remove agentik"])
        self.assertFalse(os.path.lexists(os.path.join(h.plugins, "marketplaces", "agentik")))
        self.assertFalse(os.path.lexists(os.path.join(h.home, ".local", "share", "agentik-suite")))
        self.assertFalse(os.path.lexists(os.path.join(h.cache, "agentik")))
        self.assertEqual(h.agentik(), [])
        for path in kept + [cfg, os.path.join(h.home, ".local", "state", "agentik-suite")]:
            self.assertTrue(os.path.exists(path), path)
        self.assertIn("~/.config/agentik/suite/config.yaml", out)
        self.assertIn("~/.local/share/agentik-suite", out)

    def test_8_a_local_marketplace_is_kept_and_the_suites_plugin_goes(self):
        h, _ = self.x()
        h.install("suite@agentik", "0.7.0", launcher=False)
        path = os.path.join(h.plugins, "known_marketplaces.json")
        with open(path, "w") as fh:
            json.dump({"agentik": {"source": {"source": "directory", "path": "/src/agentik-commons"}}}, fh)
        code, out, err = h.go("remove", "--all", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(h.claude(), [UNINSTALL, "claude plugin uninstall suite@agentik --keep-data"])
        self.assertIn("claude plugin marketplace remove agentik", out)
        with open(path) as fh:
            self.assertIn("agentik", json.load(fh))

    def test_9_a_cache_link_and_a_cache_home_that_is_the_home(self):
        h, _ = self.x()
        elsewhere = os.path.join(self.tmp, "elsewhere")
        h.file(os.path.join(elsewhere, "keep.txt"), "mine\n")
        os.makedirs(h.cache, exist_ok=True)
        shutil.rmtree(os.path.join(h.cache, "agentik"), ignore_errors=True)
        os.symlink(elsewhere, os.path.join(h.cache, "agentik"))
        code, out, err = h.go("remove", "--all", "--yes", PYTHONDONTWRITEBYTECODE="1")
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.islink(os.path.join(h.cache, "agentik")))
        self.assertTrue(os.path.isfile(os.path.join(elsewhere, "keep.txt")))
        self.assertIn("kept", out)
        h2 = self.home(name="h2")
        h2.file(os.path.join(h2.home, "agentik", "keep.txt"), "mine\n")
        code, out, err = h2.go("remove", "--all", "--dry-run", XDG_CACHE_HOME=h2.home)
        self.assertEqual(code, 0, out + err)
        self.assertIn("~/agentik", out)
        code, out, err = h2.go("remove", "--all", "--yes", XDG_CACHE_HOME=h2.home)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.isfile(os.path.join(h2.home, "agentik", "keep.txt")))

    def test_10_off_a_terminal(self):
        h, _ = self.x()
        before = snapshot(h.home)
        code, out, err = h.go("remove", "x")
        self.assertEqual(code, 2, out + err)
        self.assertIn("--yes", err)
        self.assertEqual((h.claude(), snapshot(h.home)), ([], before))
        h.file(os.path.join(h.home, ".claude", "edit-gates"), "~/.claude/settings.json\n")
        before = snapshot(h.home)
        code, out, err = h.go("remove", "x", "--yes")
        self.assertEqual(code, 2, out + err)
        self.assertIn("gate list", err)
        self.assertEqual((h.claude(), snapshot(h.home)), ([], before))


if __name__ == "__main__":
    unittest.main()
