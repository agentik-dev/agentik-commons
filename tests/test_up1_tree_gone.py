"""Row up1-tree-gone: a command whose code is gone is seen and placed again.

A launcher names its code in its `TREE=` line and runs a runner inside it. When that folder, or
the runner in it, is gone, setup's steps 4 and 5 read the row `todo` with the source's
install-cli, whatever the versions say; `update` places it again and never calls it current; the
doctor names the gone code, its `next:` is a line that runs at a terminal, and a tool's doctor
that fails with nothing on stdout shows its last stderr line.

Each home is a temp HOME in ak4a-update's shape (a stub `claude`, `git` and `ps` on its PATH),
with made-up plugins whose command's install-cli writes a launcher in the form the suite's own
writes: `TREE=`, a test for the runner inside it, then the run. No test starts a real `claude`,
reads the live home or writes outside its temp folder."""
import json
import os
import pty
import select
import shlex
import shutil
import subprocess
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_ak4a_update as ak4a  # noqa: E402
from test_agentik_suite import LAUNCHER, LIB, version  # noqa: E402
from agentik_suite import doctor, plan, tools  # noqa: E402
import agentik_install  # noqa: E402

# a plugin's command: install-cli copies itself into its tree as `run` and writes a launcher that
# runs it, refusing as the suite's launcher does when the runner is gone
COMMAND = r'''#!/bin/sh
echo "$0 $*" >> "$HOME/ran.log"
case "$1" in
install-cli)
    tree="$HOME/.local/share/agentik-@NAME@/@VERSION@"
    mkdir -p "$tree" "$HOME/.local/bin" || exit 1
    cp "$0" "$tree/run" || exit 1
    cat > "$HOME/.local/bin/agentik-@NAME@" <<EOF || exit 1
#!/bin/sh
VERSION=@VERSION@
TREE=$tree
[ -f "\$TREE/run" ] && [ -r "\$TREE/run" ] || { echo "agentik-@NAME@: \$TREE is gone; run /@NAME@:install-cli" >&2; exit 3; }
exec /bin/sh "\$TREE/run" "\$@"
EOF
    chmod 755 "$HOME/.local/bin/agentik-@NAME@" ;;
--version) echo "agentik-@NAME@ @VERSION@" ;;
*) exit 0 ;;
esac
'''
SEED = '''import json, os
COMMAND = %r
def plugin(home, pid, ver):
    name, _, market = pid.partition("@")
    root = os.path.join(home, ".claude", "plugins", "cache", market, name, ver)
    os.makedirs(os.path.join(root, ".claude-plugin"), exist_ok=True)
    os.makedirs(os.path.join(root, "bin"), exist_ok=True)
    with open(os.path.join(root, ".claude-plugin", "plugin.json"), "w") as fh:
        json.dump({"name": name, "version": ver}, fh)
    exe = os.path.join(root, "bin", "agentik-" + name)
    with open(exe, "w") as fh:
        fh.write(COMMAND.replace("@VERSION@", ver).replace("@NAME@", name))
    os.chmod(exe, 0o755)
    return root
''' % COMMAND
CURRENT = "everything is current; nothing was placed."


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = os.path.realpath(tmp.name)

    def home(self, names, suite=False):
        """A home with each name installed at 1.0.0 and its launcher placed by its install-cli;
        with `suite`, the suite's own launcher and the door placed by its real install-cli."""
        h = ak4a.Home(os.path.join(self.tmp, "h"), listed=names)
        h.file(os.path.join(h.home, "seed.py"), SEED)
        h.roots = {}
        for name in names:
            h.roots[name] = h.install(name + "@agentik", "1.0.0", launcher=False)
            self.call(h, self.source(h, name), "install-cli")
        if suite:
            self.call(h, str(LAUNCHER), "install-cli")
        return h

    def call(self, h, *argv, code=0):
        p = subprocess.run(list(argv), capture_output=True, text=True, env=h.env(), cwd=h.home,
                           stdin=subprocess.DEVNULL, timeout=120)
        self.assertEqual(p.returncode, code, p.stdout + p.stderr)
        return p.stdout, p.stderr

    @staticmethod
    def source(h, name):
        return os.path.join(h.roots[name], "bin", "agentik-" + name)

    @staticmethod
    def tree(h, name):
        return os.path.join(h.home, ".local", "share", "agentik-" + name, "1.0.0")

    def aside(self, path):
        """The folder or file at `path` moved aside, as a hand's `mv` would."""
        self.assertTrue(os.path.exists(path), path)
        os.rename(path, path + ".aside")

    def build(self, h, *names):
        return plan.build(list(names), h.env(), str(LIB), "agentik-suite", version())

    @staticmethod
    def step(steps, n, sid):
        found = [s for s in steps if s["n"] == n and s["id"] == sid]
        return found[0]


class PlanTest(Base):
    """R1: steps 4 and 5 read the launcher's TREE and its runner."""

    def test_a_launcher_whose_tree_stands_reads_as_at_the_pin(self):
        h = self.home(["murmur"])
        four = self.step(self.build(h, "murmur"), 4, "launcher")
        self.assertEqual((four["state"], four["mid"], four["command"]), ("ok", "setup.launcher.ok", None))

    def test_a_tree_moved_aside_is_todo_with_the_sources_install_cli(self):
        h = self.home(["murmur"])
        self.aside(self.tree(h, "murmur"))
        four = self.step(self.build(h, "murmur"), 4, "launcher")
        self.assertEqual((four["state"], four["mid"], four["command"], four["line"]),
                         ("todo", "setup.launcher.gone",
                          "%s install-cli" % shlex.quote(self.source(h, "murmur")), "run"))
        self.assertEqual(four["values"], {"tree": "~/.local/share/agentik-murmur/1.0.0"})

    def test_a_runner_gone_from_a_tree_that_stands_is_todo(self):
        h = self.home(["murmur"])
        self.aside(os.path.join(self.tree(h, "murmur"), "run"))
        four = self.step(self.build(h, "murmur"), 4, "launcher")
        self.assertEqual((four["state"], four["mid"]), ("todo", "setup.launcher.gone"))

    def test_a_launcher_that_does_not_run_its_tree_is_read_as_at_the_pin(self):
        # a launcher with a TREE line it never runs (no `$TREE` in its text) is not read as gone
        h = self.home(["murmur"])
        h.file(os.path.join(h.bindir, "agentik-murmur"),
               "#!/bin/sh\nVERSION=1.0.0\nTREE=%s/nowhere\nexit 0\n" % h.home)
        four = self.step(self.build(h, "murmur"), 4, "launcher")
        self.assertEqual(four["mid"], "setup.launcher.ok")

    def test_the_suites_own_tree_gone_is_todo_with_this_commands_install_cli(self):
        h = self.home([], suite=True)
        five = self.step(self.build(h), 5, "suite")
        self.assertEqual((five["state"], five["mid"]), ("ok", "setup.suite.ok"))
        tree = agentik_install.read_launcher(os.path.join(h.bindir, "agentik-suite"))["tree"]
        self.aside(tree)
        steps = self.build(h)
        five = self.step(steps, 5, "suite")
        self.assertEqual((five["state"], five["mid"], five["command"]),
                         ("todo", "setup.suite.gone", "%s install-cli" % shlex.quote(str(LAUNCHER))))
        self.assertEqual(five["values"], {"tree": plan.shown(tree, h.home)})
        self.assertEqual(self.step(steps, 5, "door")["state"], "ok")


class SetupUpdateTest(Base):
    """R2 and acceptance 1: setup and update both run that line and place the command again."""

    def test_setup_dry_run_shows_the_todo_row(self):
        h = self.home(["murmur"])
        code, out, err = h.run("setup", "--dry-run", "murmur")
        self.assertEqual(code, 0, out + err)
        self.assertIn("at version 1.0.0, the same as the plugin", out)
        self.aside(self.tree(h, "murmur"))
        code, out, err = h.run("setup", "--dry-run", "murmur")
        self.assertEqual(code, 0, out + err)
        self.assertIn("its code at ~/.local/share/agentik-murmur/1.0.0 is gone", out)
        self.assertIn("would run: %s install-cli" % self.source(h, "murmur"), out)
        self.assertNotIn("the same as the plugin", out)

    def test_setup_places_it_again(self):
        h = self.home(["murmur"])
        self.aside(self.tree(h, "murmur"))
        code, out, err = h.run("setup", "--yes", "murmur")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.call(h, os.path.join(h.bindir, "agentik-murmur"), "--version")[0],
                         "agentik-murmur 1.0.0\n")

    def test_update_places_it_again_and_never_says_current(self):
        h = self.home(["murmur", "paint"])
        self.aside(self.tree(h, "murmur"))
        before = len(h.ran())
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn(CURRENT, out)
        self.assertEqual([l for l in h.ran()[before:] if l.endswith(" install-cli")],
                         ["%s install-cli" % self.source(h, "murmur")])
        self.assertEqual(self.call(h, os.path.join(h.bindir, "agentik-murmur"), "--version")[0],
                         "agentik-murmur 1.0.0\n")
        code, out, err = h.run("update", "--yes")  # its tree stands again: as at the pin
        self.assertEqual(code, 0, out + err)
        self.assertIn(CURRENT, out)


DEFAULT = plan.default_set(str(LIB))  # the suite's default set, by its manifest


class DoctorTest(Base):
    """R3: the doctor names the gone code, its next: runs at a terminal, and a silent doctor's
    stderr line stands in place of "printed nothing"."""

    def test_doctor_names_the_gone_code_and_its_next_runs_as_printed(self):
        self.assertIn("session", DEFAULT)
        h = self.home(DEFAULT, suite=True)
        code, out, err = h.run("doctor")
        self.assertEqual(code, 0, out + err)
        self.aside(self.tree(h, "session"))
        code, out, err = h.run("doctor")
        self.assertEqual(code, 1, out + err)
        self.assertIn("its code at ~/.local/share/agentik-session/1.0.0 is gone", out)
        self.assertNotIn("printed nothing", out)
        self.assertIn("its doctor failed, and said: agentik-session: %s is gone" % self.tree(h, "session"), out)
        nexts = [l.strip()[len("next: "):] for l in (out + err).splitlines() if l.strip().startswith("next: ")]
        self.assertEqual(nexts, ["agentik setup"], out + err)
        self.assertFalse(nexts[0].startswith("/"))
        code, text = self.on_pty(h, "y", nexts[0])
        self.assertEqual(code, 0, text)
        self.assertEqual(self.call(h, os.path.join(h.bindir, "agentik-session"), "--version")[0],
                         "agentik-session 1.0.0\n")

    def on_pty(self, h, answer, line):
        """`line` run by sh on a terminal, `answer` typed: (its exit, what it printed)."""
        master, slave = pty.openpty()
        p = subprocess.Popen(["/bin/sh", "-c", line], stdin=slave, stdout=slave, stderr=slave,
                             env=h.env(), cwd=h.home, close_fds=True)
        os.close(slave)
        os.write(master, answer.encode() + b"\n")
        chunks = []
        try:
            while True:
                ready, _, _ = select.select([master], [], [], 60)
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

    def own(self, body):
        """own_doctors' check for one made-up tool whose command is `body`."""
        d = os.path.join(self.tmp, "bin")
        os.makedirs(d, exist_ok=True)
        exe = os.path.join(d, "agentik-murmur")
        with open(exe, "w") as fh:
            fh.write(body)
        os.chmod(exe, 0o755)
        env = {"HOME": self.tmp, "PATH": "/usr/bin:/bin", "XDG_CACHE_HOME": os.path.join(self.tmp, "c")}
        cmd = types.SimpleNamespace(lib=str(LIB), env=env, tool="agentik-suite", opts={"json": False},
                                    t=types.SimpleNamespace(text=lambda mid, **v: (mid, v)),
                                    say=lambda *w: " ".join(("agentik",) + w))
        groups = doctor.own_doctors(cmd, [{"name": "murmur", "exe": exe, "source": None}], described={})
        return groups[0]["checks"][-1]

    def test_a_silent_doctors_last_stderr_line_is_shown(self):
        c = self.own("#!/bin/sh\necho 'first words' >&2\nprintf 'agentik-murmur: its last\\a words\\n\\n' >&2\n"
                     "exit 3\n")
        self.assertEqual((c["status"], c["detail"]),
                         ("fail", ("doctor.tool.said", {"last": "agentik-murmur: its last words"})))

    def test_a_doctor_silent_on_both_reads_as_at_the_pin(self):
        c = self.own("#!/bin/sh\nexit 3\n")
        self.assertEqual((c["status"], c["detail"]), ("fail", ("doctor.tool.silent", {})))

    def test_a_doctor_that_prints_on_stdout_reads_as_at_the_pin(self):
        c = self.own("#!/bin/sh\necho 'out'\necho 'err' >&2\nexit 3\n")
        self.assertEqual((c["status"], c["detail"]), ("fail", ("doctor.tool.failed", {})))


if __name__ == "__main__":
    unittest.main()
