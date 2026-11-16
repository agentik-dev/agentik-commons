"""Row up2-suite-origin: a clone install is upgraded by one exact line that `update` prints.

R1: `install-cli` run from a checkout writes `CHECKOUT=<path>` after `TREE=`; from a plugin's
folder none; from the frozen tree it keeps the line. R2: `update` shows the suite from a checkout
as a note, and its close ends on a reason and the one `next:` that moves it. R3: the close's row
for the suite plugin speaks of the plugin. Each run is in a temp HOME with a stub `claude`; the
checkouts are made-up folders under it, and the end-to-end clone pulls from a local bare repo.
No test starts a real `claude`, reads the live home or reaches the network."""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_agentik_install as ti  # noqa: E402
import test_ak4a_update as tu  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
APPLE_PY = "/usr/bin/python3"
SETUP = "#!/bin/sh\nexit 0\n"


def checkout_line(text):
    return re.findall(r"(?m)^CHECKOUT=(.*)$", text)


@unittest.skipUnless(os.access(APPLE_PY, os.X_OK), "no /usr/bin/python3 on this machine")
class LauncherLine(ti.Base):
    """R1, the launcher's one more line."""

    def checkout(self, where="work/kit", setup=True, git=True):
        root = self.home / where
        plugin = root / "plugins" / "x"
        (plugin / ".claude-plugin").mkdir(parents=True)
        (plugin / "bin").mkdir()
        (plugin / "lib").mkdir()
        (plugin / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "x", "version": "1.0.0"}))
        shutil.copyfile(ti.MODULE, plugin / "lib" / "agentik_install.py")
        (plugin / "lib" / "agentik-x").write_text(ti.RUNNER)
        (plugin / "lib" / "agentik-tool.conf").write_text(ti.conf("agentik-x"))
        for src, to in ((ti.DOOR, "agentik"), (ti.LAUNCHER, "agentik-x")):
            shutil.copyfile(src, plugin / "bin" / to)
            os.chmod(plugin / "bin" / to, 0o755)
        if git:
            (root / ".git").mkdir()
        if setup:
            (root / "setup").write_text(SETUP)
            os.chmod(root / "setup", 0o755)
        return root, plugin

    def text(self):
        return self.bin().read_text()

    def test_1_from_a_checkout_the_launcher_names_it(self):
        root, plugin = self.checkout()
        self.install(plugin)
        text = self.text()
        self.assertEqual(checkout_line(text), [shlex.quote(str(root))])
        lines = text.split("\n")
        at = [i for i, l in enumerate(lines) if l.startswith("TREE=")][0]
        self.assertTrue(lines[at + 1].startswith("CHECKOUT="), lines[at:at + 2])
        mod = ti.load_module()
        self.assertEqual(mod.read_launcher(str(self.bin()))["checkout"], str(root))
        self.assertTrue(mod._launcher_form(str(self.bin()), "agentik-x"))
        self.assertTrue(mod._ours(str(self.bin()), "agentik-x", str(self.share())))
        self.assertEqual(self.run_tool(self.bin(), "--version")[:2], (0, "1.0.0\n"))

    def test_2_from_a_plugins_folder_none(self):
        self.install(self.plugin())
        self.assertEqual(checkout_line(self.text()), [])
        mod = ti.load_module()
        self.assertIsNone(mod.read_launcher(str(self.bin()))["checkout"])
        self.assertTrue(mod._ours(str(self.bin()), "agentik-x", str(self.share())))

    def test_3_no_setup_no_git_or_an_equals_sign_none(self):
        for i, kw in enumerate(({"setup": False}, {"git": False}, {"where": "work/a=b/kit"})):
            root, plugin = self.checkout(where=kw.pop("where", "w%d/kit" % i), **kw)
            self.install(plugin)
            self.assertEqual(checkout_line(self.text()), [], (i, self.text()[:400]))
            mod = ti.load_module()
            self.assertTrue(mod._ours(str(self.bin()), "agentik-x", str(self.share())))

    def test_4_from_the_frozen_tree_the_line_is_kept(self):
        root, plugin = self.checkout()
        self.install(plugin)
        code, out, err = self.run_tool(self.bin(), "install-cli")
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(checkout_line(self.text()), [shlex.quote(str(root))])
        # the checkout gone: the frozen tree writes none
        shutil.rmtree(root)
        code, out, err = self.run_tool(self.bin(), "install-cli")
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(checkout_line(self.text()), [])

    def test_5_launcher_text_without_a_checkout_is_todays(self):
        mod = ti.load_module()
        conf = {"tool_name": "agentik-x", "remedy": "/x:install-cli", "runner": "agentik-x",
                "old_name": "", "old_state": ""}
        plain = mod.launcher_text("/t/tree", "1.0.0", conf)
        self.assertNotIn("CHECKOUT", plain)
        named = mod.launcher_text("/t/tree", "1.0.0", conf, checkout="/w/a kit")
        self.assertEqual(named.replace("CHECKOUT='/w/a kit'\n", ""), plain)
        path = self.home / "l"
        path.write_text(named)
        self.assertEqual(mod.read_launcher(str(path))["checkout"], "/w/a kit")
        self.assertEqual(mod.read_launcher(str(path))["tree"], "/t/tree")

    def test_6_uninstall_takes_either_form(self):
        root, plugin = self.checkout()
        self.install(plugin)
        mod = ti.load_module()
        env = dict(os.environ)
        try:
            os.environ.clear()
            os.environ.update(self.env)
            mod.PS = str(self.home / "ps")
            (self.home / "ps").write_text("#!/bin/sh\necho \"1 /sbin/launchd\"\n"
                                          "echo \"2 /bin/sh AGENTIK_PRUNE_PROBE=$AGENTIK_PRUNE_PROBE\"\n")
            os.chmod(self.home / "ps", 0o755)
            rows = mod.uninstall("agentik-x", dry=True)
        finally:
            os.environ.clear()
            os.environ.update(env)
        launcher = [fate for path, what, fate in rows if what == "launcher"]
        self.assertEqual(launcher, ["would remove"], rows)


class UpdateRow(tu.Base):
    """R2 and R3, update's row for the suite and its close."""

    def placed(self, listed=("murmur", "suite"), name=True, under_home=True):
        h = self.home(listed)
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        base = h.home if under_home else self.tmp
        checkout = os.path.join(base, "work", "agentik-commons")
        os.makedirs(os.path.join(checkout, ".git"))
        shutil.copytree(str(tu.PLUGIN), os.path.join(checkout, "plugins", "suite"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(str(ROOT / "setup"), os.path.join(checkout, "setup"))
        os.chmod(os.path.join(checkout, "setup"), 0o755)
        line = "CHECKOUT=%s\n" % shlex.quote(checkout) if name else ""
        h.file(os.path.join(h.bindir, "agentik-suite"), "#!/bin/sh\nVERSION=0.7.12\nTREE=%s\n%sexit 0\n"
               % (os.path.join(h.home, ".local", "share", "agentik-suite", "t"), line))
        return h, checkout, os.path.join(checkout, "plugins", "suite", "bin", "agentik-suite")

    def test_7_the_launcher_names_its_checkout(self):
        h, checkout, exe = self.placed()
        code, out, err = h.run("update", "--yes", exe=exe)
        self.assertEqual(code, 0, out + err)
        row = [l for l in out.splitlines() if l.lstrip().startswith("4 ")]
        self.assertEqual(len(row), 1, out)
        self.assertRegex(row[0], r"^\s*4\s+note\s+agentik-suite\s+")
        self.assertIn("~/work/agentik-commons", row[0])
        self.assertNotIn(" ok ", row[0])
        last = err.rstrip("\n").splitlines()[-2:]
        self.assertEqual(last[1], "next: git -C ~/work/agentik-commons pull --ff-only && ~/work/agentik-commons/setup")
        self.assertFalse(last[0].startswith("next:"), last)
        self.assertEqual(sum(l.startswith("next:") and "pull" in l for l in err.splitlines()), 1, err)

    def test_8_outside_home_the_path_is_whole_and_quoted(self):
        h, checkout, exe = self.placed(under_home=False)
        code, out, err = h.run("update", "--yes", exe=exe)
        self.assertEqual(code, 0, out + err)
        q = shlex.quote(checkout)
        self.assertEqual(err.rstrip("\n").splitlines()[-1], "next: git -C %s pull --ff-only && %s/setup" % (q, q))

    def test_9_no_line_says_so_and_names_the_plugin(self):
        h, checkout, exe = self.placed(name=False)
        code, out, err = h.run("update", "--yes", exe=exe)
        self.assertEqual(code, 0, out + err)
        row = [l for l in out.splitlines() if l.lstrip().startswith("4 ")][0]
        self.assertRegex(row, r"^\s*4\s+note\s+agentik-suite\s+")
        self.assertIn("does not name", row)
        self.assertEqual(err.rstrip("\n").splitlines()[-1], "next: claude plugin install suite@agentik")

    def test_10_dry_run_and_json(self):
        h, checkout, exe = self.placed()
        code, out, err = h.run("update", "--dry-run", exe=exe)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(err.rstrip("\n").splitlines()[-1],
                         "next: git -C ~/work/agentik-commons pull --ff-only && ~/work/agentik-commons/setup")
        code, out, err = h.run("update", "--dry-run", "--json", exe=exe)
        self.assertEqual(code, 0, out + err)
        obj = json.loads(out)
        step = [s for s in obj["steps"] if s["id"] == "suite"][0]
        self.assertEqual((step["n"], step["state"], step["command"]), (4, "todo", None))
        self.assertEqual([s["name"] for s in obj["skipped"]], ["suite"])

    def test_11_the_suite_plugin_current_speaks_of_the_plugin(self):
        h = self.home(("murmur", "suite"))
        h.install("murmur@agentik", "1.0.0", "1.0.0")
        h.install("suite@agentik", "0.2.0", "0.2.0")
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertIn("ok  the suite plugin 0.2.0, already current", out)
        self.assertNotIn("ok  suite 0.2.0, already current", out)
        self.assertIn("ok  murmur 1.0.0, already current", out)


@unittest.skipUnless(os.access(APPLE_PY, os.X_OK) and shutil.which("git", path="/usr/bin:/bin"),
                     "no /usr/bin/python3 or git on this machine")
class EndToEnd(tu.Base):
    """Acceptance 1: a made-up clone of a local bare repo, its setup, update's line run as printed."""

    def git(self, *args, cwd=None):
        p = subprocess.run(["git", "-c", "user.name=maker", "-c", "user.email=maker", *args], cwd=cwd,
                           capture_output=True, text=True, timeout=60,
                           env={"HOME": self.tmp, "PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1"})
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout.strip()

    def test_12_the_printed_line_pulls_the_clone_and_runs_its_setup(self):
        h = self.home(("murmur", "suite"))
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        os.unlink(os.path.join(h.bin, "git"))   # the real git, on a local repo alone
        src = os.path.join(self.tmp, "src")
        os.makedirs(src)
        shutil.copyfile(str(ROOT / "setup"), os.path.join(src, "setup"))
        os.chmod(os.path.join(src, "setup"), 0o755)
        shutil.copytree(str(tu.PLUGIN), os.path.join(src, "plugins", "suite"),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.git("init", "-q", "-b", "main", src)
        self.git("add", ".", cwd=src)
        self.git("commit", "-q", "-m", "one", cwd=src)
        origin = os.path.join(self.tmp, "origin.git")
        self.git("clone", "-q", "--bare", src, origin)
        clone = os.path.join(h.home, "agentik-commons")
        self.git("clone", "-q", origin, clone)
        code, out, err = h.run("--yes", "murmur", exe=os.path.join(clone, "setup"))
        self.assertEqual(code, 0, out + err)
        launcher = os.path.join(h.bindir, "agentik-suite")
        with open(launcher) as fh:
            self.assertEqual(checkout_line(fh.read()), [clone])
        code, out, err = h.run("update", "--yes", exe=launcher)
        self.assertEqual(code, 0, out + err)
        line = err.rstrip("\n").splitlines()[-1]
        self.assertEqual(line, "next: git -C ~/agentik-commons pull --ff-only && ~/agentik-commons/setup")
        # a new commit upstream; the line, pasted as printed, moves the clone and starts its setup
        with open(os.path.join(src, "NEWS"), "w") as fh:
            fh.write("two\n")
        self.git("add", "NEWS", cwd=src)
        self.git("commit", "-q", "-m", "two", cwd=src)
        self.git("push", "-q", origin, "main", cwd=src)
        head = self.git("rev-parse", "HEAD", cwd=src)
        p = subprocess.run(["/bin/sh", "-c", line[len("next: "):]], capture_output=True, text=True,
                           env=h.env(), cwd=self.tmp, stdin=subprocess.DEVNULL, timeout=120)
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=clone), head, p.stderr)
        self.assertIn("Setup plan", p.stdout + p.stderr)


class Readme(unittest.TestCase):
    """R4: the README's top holds the upgrade line; its maintainers' part calls no plugin line an update."""

    def test_13_the_upgrade_line(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        top = text.split("\n## ", 1)[0]
        self.assertIn("`git -C agentik-commons pull && agentik-commons/setup && agentik update`", top)
        self.assertNotIn("Updates stay", text)
        p = subprocess.run([str(ROOT / "scripts" / "readme-top"), str(ROOT / "README.md")],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main()
