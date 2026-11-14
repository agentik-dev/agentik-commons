"""Row ak4a-update: `agentik-suite update` brings every installed tool and its command current.

Each home is a temp HOME in fk_homes' shape with made-up tools: Claude Code's two files under
`.claude/plugins`, the `agentik` marketplace's own list, and on the home's PATH a stub `claude`
that logs to `$HOME/ran.log` and, for `plugin update T@M`, writes the version `latest.json` names
and moves T's entry to it; a stub `git` that logs to `$HOME/git.log`; a stub `ps` that prints
`ps.txt`; a plugin's command that logs and, for `install-cli`, writes its launcher at its own
version. No test starts a real `claude`, reads the live home or the live process list."""
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LAUNCHER  # noqa: E402
from agentik_suite import cli, update  # noqa: E402

CLAUDE = r'''#!/usr/bin/python3
import json, os, sys
home = os.environ["HOME"]
a = sys.argv[1:]
with open(os.path.join(home, "ran.log"), "a") as fh:
    fh.write("claude " + " ".join(a) + "\n")
d = os.path.join(home, ".claude", "plugins")
if a[:3] == ["plugin", "marketplace", "update"] and len(a) == 4:
    sys.exit(0)
if a[:2] == ["plugin", "update"] and len(a) == 3:
    pid = a[2]
    fail = os.path.join(home, "fail")
    if os.path.exists(fail) and open(fail).read().strip() == pid:
        print("no answer from the marketplace")
        sys.exit(1)
    ver = json.load(open(os.path.join(home, "latest.json")))[pid]
    sys.path.insert(0, home)
    import seed
    root = seed.plugin(home, pid, ver)
    path = os.path.join(d, "installed_plugins.json")
    table = json.load(open(path))
    table["plugins"][pid] = [{"scope": "user", "version": ver, "installPath": root}]
    json.dump(table, open(path, "w"))
    sys.exit(0)
sys.exit(2)
'''
# a plugin's command: it logs, and its install-cli writes its launcher at its own version and the door
COMMAND = r'''#!/bin/sh
echo "$0 $*" >> "$HOME/ran.log"
case "$1" in
install-cli)
    name=$(basename "$0")
    mkdir -p "$HOME/.local/bin" || exit 1
    printf '#!/bin/sh\nVERSION=%s\nTREE=%s\nexit 0\n' "@VERSION@" "$HOME/.local/share/$name/@VERSION@" \
        > "$HOME/.local/bin/$name" && chmod 755 "$HOME/.local/bin/$name" &&
    printf '#!/bin/sh\n' > "$HOME/.local/bin/agentik" && chmod 755 "$HOME/.local/bin/agentik" ;;
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
        fh.write(COMMAND.replace("@VERSION@", ver))
    os.chmod(exe, 0o755)
    return root
''' % COMMAND
RECORD = '#!/bin/sh\necho "$*" >> "$HOME/git.log"\nexit 0\n'
MOVED = "%s %s to %s"
DOCTOR_CLOSE = re.compile(r"(failed, .* ok\.|This machine is set up\.)")


class Home:
    def __init__(self, path, listed=("murmur", "paint")):
        self.home = path
        self.plugins = os.path.join(path, ".claude", "plugins")
        self.bin = os.path.join(path, "bin")
        self.bindir = os.path.join(path, ".local", "bin")
        os.makedirs(self.plugins)
        os.makedirs(self.bindir)
        self.table, self.latest = {}, {}
        self.file(os.path.join(path, "seed.py"), SEED)
        self.file(os.path.join(self.bin, "claude"), CLAUDE)
        self.file(os.path.join(self.bin, "git"), RECORD)
        self.ps_text = os.path.join(path, "ps.txt")
        self.ps("1 /sbin/launchd\n")
        self.file(os.path.join(self.bin, "ps"), "#!/bin/sh\ncat %s\necho \"2 /bin/sh "
                  "AGENTIK_PRUNE_PROBE=$AGENTIK_PRUNE_PROBE\"\n" % shlex.quote(self.ps_text))
        self.market = os.path.join(path, "market")
        self.listing(listed)

    def file(self, path, body):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(body)
        os.chmod(path, 0o755)
        return path

    def ps(self, text):
        with open(self.ps_text, "w") as fh:
            fh.write(text)

    def listing(self, listed):
        os.makedirs(os.path.join(self.market, ".claude-plugin"), exist_ok=True)
        with open(os.path.join(self.market, ".claude-plugin", "marketplace.json"), "w") as fh:
            json.dump({"name": "agentik", "plugins": [{"name": n, "description": "A made-up tool."}
                                                      for n in listed]}, fh)
        self.write(markets=("acme-tools",) if any("@acme-tools" in p for p in self.table) else ())

    def write(self, markets=()):
        known = {"agentik": {"source": {"source": "github", "repo": "agentik-dev/agentik-commons"},
                             "installLocation": self.market}}
        for m in markets:
            known[m] = {"source": {"source": "github", "repo": "acme/" + m}}
        with open(os.path.join(self.plugins, "known_marketplaces.json"), "w") as fh:
            json.dump(known, fh)
        with open(os.path.join(self.plugins, "installed_plugins.json"), "w") as fh:
            json.dump({"version": 2, "plugins": self.table}, fh)
        with open(os.path.join(self.home, "latest.json"), "w") as fh:
            json.dump(self.latest, fh)

    def install(self, pid, ver, latest=None, launcher=True):
        sys.path.insert(0, self.home)
        try:
            import importlib
            seed = importlib.import_module("seed")
            seed = importlib.reload(seed)
            root = seed.plugin(self.home, pid, ver)
        finally:
            sys.path.remove(self.home)
            sys.modules.pop("seed", None)
        self.table[pid] = [{"scope": "user", "version": ver, "installPath": root}]
        self.latest[pid] = latest or ver
        name = pid.partition("@")[0]
        if launcher:
            self.file(os.path.join(self.bindir, "agentik-" + name), "#!/bin/sh\nVERSION=%s\nTREE=%s\nexit 0\n"
                      % (ver, os.path.join(self.home, ".local", "share", "agentik-" + name, ver)))
        self.write(markets=("acme-tools",) if any("@acme-tools" in p for p in self.table) else ())
        return root

    def env(self, **more):
        env = {"HOME": self.home, "PATH": os.pathsep.join([self.bin, self.bindir, "/usr/bin", "/bin"]),
               "XDG_CACHE_HOME": self.home + "-cache", "NO_COLOR": "1"}  # the launcher's pycache: outside
        env.update(more)
        return env

    def run(self, *args):
        p = subprocess.run([str(LAUNCHER)] + list(args), capture_output=True, text=True,
                           env=self.env(), cwd=self.home, stdin=subprocess.DEVNULL, timeout=120)
        return p.returncode, p.stdout, p.stderr

    def ran(self, log="ran.log"):
        try:
            with open(os.path.join(self.home, log)) as fh:
                return fh.read().splitlines()
        except FileNotFoundError:
            return []

    def claude(self):
        return [l for l in self.ran() if l.startswith("claude ")]

    def version_of(self, name):
        with open(os.path.join(self.bindir, "agentik-" + name)) as fh:
            return re.search(r"^VERSION=(.*)$", fh.read(), re.M).group(1)

    def snapshot(self):
        seen = {}
        for top, dirs, files in os.walk(self.home):
            for f in dirs + files:
                p = os.path.join(top, f)
                st = os.lstat(p)
                seen[p] = (st.st_size, st.st_mtime_ns)
        return seen

    def command(self, *argv):
        return cli.Command(list(argv), self.env(), io.StringIO(), io.StringIO())


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = os.path.realpath(tmp.name)

    def home(self, listed=("murmur", "paint"), name="h"):
        return Home(os.path.join(self.tmp, name), listed)

    @staticmethod
    def read(h, name):
        with open(os.path.join(h.bindir, "agentik-" + name), "rb") as fh:
            return fh.read()

    def two_behind(self):
        h = self.home()
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        h.install("paint@agentik", "2.0.0", "2.1.0")
        return h


class UpdateTest(Base):
    def test_1_two_plugins_behind_are_moved_and_placed_then_the_doctor_reads(self):
        h = self.two_behind()
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(h.claude(), ["claude plugin marketplace update agentik",
                                      "claude plugin update murmur@agentik",
                                      "claude plugin update paint@agentik"])
        self.assertEqual((h.version_of("murmur"), h.version_of("paint")), ("1.1.0", "2.1.0"))
        rows = [MOVED % ("murmur", "1.0.0", "1.1.0"), MOVED % ("paint", "2.0.0", "2.1.0")]
        for row in rows:
            self.assertEqual(out.count(row), 1, out)
        close = DOCTOR_CLOSE.search(out)
        self.assertIsNotNone(close, out)
        self.assertLess(out.index(rows[1]), close.start())
        with open(os.path.join(h.home, ".local", "state", "agentik-suite", "setup.jsonl")) as fh:
            self.assertEqual(json.loads(fh.read().splitlines()[-1])["verb"], "update")

    def test_2_run_again_nothing_is_placed(self):
        h = self.two_behind()
        self.assertEqual(h.run("update", "--yes")[0], 0)
        before = len(h.ran())
        bytes_ = {n: self.read(h, n) for n in ("murmur", "paint")}
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertFalse([l for l in h.ran()[before:] if "install-cli" in l], h.ran())
        self.assertEqual(bytes_, {n: self.read(h, n) for n in ("murmur", "paint")})
        self.assertIn("everything is current; nothing was placed.", out)
        self.assertNotIn(" to ", out.split("nothing was placed.")[1].split("\n")[0])
        self.assertIsNotNone(DOCTOR_CLOSE.search(out), out)

    def test_3_a_relay_run_holds_the_update(self):
        h = self.two_behind()
        for line, what in (("4242 /opt/tools/relay run --row r1\n", "a relay run is live (pid 4242)"),
                           ("51 agentik relay gate\n", "a relay run is live (pid 51)"),
                           ("52 /usr/local/bin/agentik-relay plan x.md\n", "a relay run is live (pid 52)")):
            h.ps(line)
            for args in (("update", "--yes"), ("update", "--dry-run")):
                before = h.snapshot()
                code, out, err = h.run(*args)
                self.assertEqual(code, 2, out + err)
                self.assertEqual(out, "")
                lines = err.splitlines()
                self.assertTrue(lines[0].endswith("held install: " + what), err)
                self.assertTrue(lines[1].startswith("next: ") and lines[1].endswith(" once it has ended"), err)
                self.assertEqual(h.ran(), [])
                self.assertEqual(h.snapshot(), before)
        h.file(os.path.join(h.bin, "ps"), "#!/bin/sh\nexit 1\n")  # a list that cannot be read holds
        code, out, err = h.run("update", "--dry-run")
        self.assertEqual(code, 2, err)
        self.assertIn("held install: the process list cannot be read", err)

    def test_4_relay_run_inside_a_path_or_a_value_holds_nothing(self):
        h = self.two_behind()
        h.ps("77 /usr/bin/vim /tmp/relay run/notes.md\n78 /bin/sleep 9 NOTE=relay run\n"
             "79 /opt/relay run/bin/watch\n80 /usr/local/bin/relay status\n81 agentik session gate run x\n")
        self.assertIsNone(update.hold(h.command("update", "--dry-run")))
        code, out, err = h.run("update", "--dry-run")
        self.assertEqual(code, 0, out + err)

    def test_5_the_session_tools_answer(self):
        h = self.two_behind()
        session = os.path.join(h.bin, "agentik-session")
        for body, held in (("echo '{\"id\": \"u1\"}'", True), ("echo null", False), ("sleep 5; echo '{}'", False)):
            h.file(session, "#!/bin/sh\n[ \"$1 $2 $3\" = 'unattended status --json' ] || exit 2\n%s\n" % body)
            with mock.patch.object(update, "SESSION_WALL", 0.5):
                start = time.monotonic()
                got = update.hold(h.command("update"))
                self.assertLess(time.monotonic() - start, 4)
            self.assertEqual(got is not None, held, body)
            if held:
                self.assertEqual(got, "an unattended run is live")

    def test_6_the_dry_run_and_off_a_terminal(self):
        h = self.two_behind()
        code, out, err = h.run("update", "--dry-run")
        self.assertEqual(code, 0, out + err)
        self.assertIn("Update plan for murmur, paint, suite. Nothing is written.", out)
        code, out, err = h.run("update", "--dry-run", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(sorted({s["n"] for s in json.loads(out)["steps"]}), [1, 2, 3, 4, 5])
        self.assertEqual(h.ran(), [])
        code, out, err = h.run("update")
        self.assertEqual(code, 2, out + err)
        self.assertIn("Update plan for", out)
        self.assertIn("cannot ask you here", err)
        self.assertEqual(h.ran(), [])
        code, out, err = h.run("update", "nosuch")
        self.assertEqual(code, 2, out + err)
        self.assertIn("nosuch", err)

    def test_7_the_suite_from_a_checkout_is_left_as_it_is(self):
        for listed, hint in ((("murmur", "suite"), "claude plugin install suite@agentik"),
                             (("murmur",), "pull that checkout, then run install-cli of its plugins/suite/bin/agentik-suite")):
            h = self.home(listed, name="h-" + str(len(listed[1:])))
            h.install("murmur@agentik", "1.0.0", "1.1.0")
            code, out, err = h.run("update", "--yes")
            self.assertEqual(code, 0, out + err)
            self.assertRegex(out, r"agentik-suite \S+ was placed from a checkout, so this command leaves it as it is")
            self.assertIn(hint, err)
            self.assertEqual(h.ran("git.log"), [])

    def test_8_the_suites_own_plugin_is_updated_last(self):
        h = self.home(("murmur", "suite"))
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        h.install("suite@agentik", "0.1.0", "0.2.0")
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual([l for l in h.claude() if " plugin update " in l][-1], "claude plugin update suite@agentik")
        self.assertEqual(h.version_of("suite"), "0.2.0")
        self.assertIn(MOVED % ("suite", "0.1.0", "0.2.0"), out)

    def test_9_a_fork_from_another_marketplace_and_a_folder(self):
        h = self.home(("murmur", "paint", "quill"))
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        h.install("quill@acme-tools", "3.0.0", "3.1.0")
        cfg = os.path.join(h.home, ".config", "agentik", "suite", "config.yaml")
        h.file(cfg, "sources:\n  paint: ~/src/paint/plugin\n")
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(h.claude(), ["claude plugin marketplace update agentik",
                                      "claude plugin marketplace update acme-tools",
                                      "claude plugin update murmur@agentik",
                                      "claude plugin update quill@acme-tools"])
        self.assertIn("paint comes from a folder; pull it there yourself.", out)
        self.assertFalse([l for l in h.ran() if "paint" in l], h.ran())
        self.assertEqual(h.version_of("quill"), "3.1.0")

    def test_10_a_failed_update_stops_and_a_second_run_converges(self):
        h = self.home(("murmur", "paint", "quill"))
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        h.install("paint@agentik", "2.0.0", "2.1.0")
        h.install("quill@agentik", "3.0.0", "3.1.0")
        with open(os.path.join(h.home, "fail"), "w") as fh:
            fh.write("paint@agentik")
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 1, out + err)
        self.assertIn("exited 1 and said no answer from the marketplace", err)
        with open(os.path.join(h.plugins, "installed_plugins.json")) as fh:
            self.assertEqual(json.load(fh)["plugins"]["murmur@agentik"][0]["version"], "1.1.0")
        self.assertNotIn("claude plugin update quill@agentik", h.claude())
        os.remove(os.path.join(h.home, "fail"))
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual([h.version_of(n) for n in ("murmur", "paint", "quill")], ["1.1.0", "2.1.0", "3.1.0"])

    def test_11_json_and_help(self):
        h = self.two_behind()
        keys = {"schema", "ok", "held", "dry_run", "tools", "skipped", "ran", "wrote", "doctor"}
        code, out, err = h.run("update", "--dry-run", "--json")
        dry = json.loads(out)
        self.assertEqual((code, dry["schema"], dry["dry_run"]), (0, "agentik.update/1", True))
        self.assertEqual(set(dry), keys | {"steps"})
        code, out, err = h.run("update", "--yes", "--json")
        got = json.loads(out)
        self.assertEqual((code, set(got), got["ok"], got["dry_run"]), (0, keys, True, False), err)
        self.assertEqual([(t["name"], t["from"], t["to"], t["launcher"]) for t in got["tools"]],
                         [("murmur", "1.0.0", "1.1.0", "1.1.0"), ("paint", "2.0.0", "2.1.0", "2.1.0")])
        self.assertEqual(set(got["doctor"]), {"failed", "warned"})
        code, out, err = h.run("help", "update")
        self.assertEqual(code, 0, err)
        glosses = ("every installed tool and its command, after one question", "the plan; nothing is written")
        examples = [l.strip()[:-len(g)].strip() for l in out.splitlines() for g in glosses if l.endswith(g)]
        self.assertEqual(len(examples), 2, out)
        for line in examples:
            p = subprocess.run(["/bin/sh", "-c", line], capture_output=True, env=h.env(), cwd=h.home,
                               stdin=subprocess.DEVNULL, timeout=120)
            self.assertNotEqual(p.returncode, 127, line)

    def test_12_the_first_screen_keeps_nine_lines(self):
        h = self.home()
        code, out, err = h.run()
        self.assertEqual((code, len((out + err).splitlines())), (0, 9), out + err)


if __name__ == "__main__":
    unittest.main()
