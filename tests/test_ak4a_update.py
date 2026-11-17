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
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LAUNCHER, PLUGIN  # noqa: E402
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
    for flag in ("drop", "gone"):  # review 1 F4: the entry dropped; F5: its folder removed
        at = os.path.join(home, flag)
        if os.path.exists(at) and open(at).read().strip() == pid:
            if flag == "drop":
                table["plugins"].pop(pid)
            else:
                import shutil
                shutil.rmtree(root)
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

    def run(self, *args, exe=LAUNCHER):
        p = subprocess.run([str(exe)] + list(args), capture_output=True, text=True,
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

    def snapshot(self, under=None):
        seen = {}
        for top, dirs, files in os.walk(under or self.home):
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
        self.assertIn("cannot ask here", err)
        self.assertEqual(h.ran(), [])
        code, out, err = h.run("update", "nosuch")
        self.assertEqual(code, 2, out + err)
        self.assertIn("nosuch", err)

    def test_7_the_suite_from_a_checkout_is_left_as_it_is(self):
        for listed, hint in ((("murmur", "suite"), "claude plugin install suite@agentik"),
                             (("murmur",), "claude plugin install suite@agentik")):  # up2 review 1 F2
            h = self.home(listed, name="h-" + str(len(listed[1:])))
            h.install("murmur@agentik", "1.0.0", "1.1.0")
            checkout = os.path.join(self.tmp, "checkout-" + str(len(listed)))  # review 1 lead d
            os.makedirs(os.path.join(checkout, ".git"))
            shutil.copytree(str(PLUGIN), os.path.join(checkout, "plugins", "suite"),
                            ignore=shutil.ignore_patterns("__pycache__"))
            before = h.snapshot(checkout)
            code, out, err = h.run("update", "--yes",
                                   exe=os.path.join(checkout, "plugins", "suite", "bin", "agentik-suite"))
            self.assertEqual(code, 0, out + err)
            self.assertRegex(out, r"4  note  agentik-suite +agentik-suite \S+ came from a checkout its command does not name")
            self.assertIn(hint, err)
            self.assertEqual(h.ran("git.log"), [])
            self.assertEqual(h.snapshot(checkout), before)

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


class ReviewOneTest(Base):
    """Review 1's fix: F1 to F5 and its leads, each red at eaec186."""

    def test_13_a_held_run_with_json_prints_one_object(self):
        h = self.two_behind()
        h.ps("4242 /opt/tools/relay run --row r1\n")
        for args, dry in ((("update", "--json"), False), (("update", "--dry-run", "--json"), True)):
            code, out, err = h.run(*args)
            self.assertEqual(code, 2, out + err)
            self.assertNotIn("Traceback", err)
            got = json.loads(out)
            self.assertEqual((got["schema"], got["ok"], got["held"], got["dry_run"]),
                             ("agentik.update/1", False, "a relay run is live (pid 4242)", dry))
            self.assertEqual((got["ran"], got["wrote"]), ([], []))
        self.assertEqual(h.ran(), [])

    def test_14_an_id_that_is_no_plugin_id_runs_nothing(self):
        h = self.home()
        h.install("murmur@--help", "1.0.0", "1.1.0")
        h.install("paint@acme\x1btools", "2.0.0", "2.1.0")
        code, out, err = h.run("update", "--dry-run")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("\x1b", out + err)
        self.assertEqual(out.count("as the file has it is no plugin id"), 2, out)
        self.assertFalse([l for l in out.splitlines() if "would run: claude" in l], out)
        code, out, err = h.run("update", "--dry-run", "--json")
        got = json.loads(out)
        self.assertEqual(sorted(s["name"] for s in got["skipped"] if "no plugin id" in s["why"]), ["murmur", "paint"])
        self.assertFalse([s for s in got["skipped"] if "\x1b" in s["why"]], got["skipped"])
        self.assertFalse([s for s in got["steps"] if (s["command"] or "").startswith("claude")], got["steps"])
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(h.claude(), [])

    def test_15_a_runner_under_a_path_with_a_space_holds(self):
        held = ("10 /Volumes/a b/bin/relay run", "11 /opt/x y/agentik-relay gate --row r", "12 /usr/local/bin/relay run",
                "13 /usr/bin/vim /tmp/relay run")  # the last: a false hold, the safe side
        free = ("77 /usr/bin/vim /tmp/relay run/notes.md", "78 /bin/sleep 9 NOTE=relay run", "18 vim relay-run.md",
                "80 /usr/local/bin/relay status", "19 /bin/cat /x/relay/run", "79 /opt/relay run/bin/watch",
                "81 agentik session gate run x")
        for line in held:
            self.assertEqual(update.runner_pid(line + "\n", "relay"), line.split()[0], line)
        for line in free:
            self.assertIsNone(update.runner_pid(line + "\n", "relay"), line)
        h = self.two_behind()
        h.ps("4243 /Volumes/a b/bin/relay run --row r1\n")
        code, out, err = h.run("update", "--dry-run")
        self.assertEqual(code, 2, out + err)
        self.assertIn("held install: a relay run is live (pid 4243)", err)

    def test_16_a_tool_the_second_read_finds_absent_fails(self):
        h = self.two_behind()
        h.file(os.path.join(h.home, "drop"), "murmur@agentik")
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 1, out + err)
        self.assertNotIn("None", out + err)
        row = [l for l in out.splitlines() if "no longer installed" in l]
        self.assertEqual(len(row), 1, out)
        self.assertTrue(row[0].lstrip().startswith("FAIL") and "murmur" in row[0], row)
        self.assertIn(MOVED % ("paint", "2.0.0", "2.1.0"), out)
        self.assertRegex(err, r"next: .*setup murmur ")

    def test_17_a_step_3_row_left_at_the_second_read_fails(self):
        h = self.two_behind()
        h.file(os.path.join(h.home, "gone"), "murmur@agentik")
        for _ in range(2):
            code, out, err = h.run("update", "--yes")
            self.assertEqual(code, 1, out + err)
            self.assertIn("claude plugin install murmur@agentik", out)
            self.assertIn("claude plugin install murmur@agentik", err)
            self.assertNotIn("everything is current", out)
            self.assertNotIn("claude plugin install murmur@agentik", h.claude())

    def test_18_updates_lines_name_update(self):
        h = self.two_behind()
        code, out, err = h.run("update")
        self.assertEqual(code, 2, out + err)
        self.assertIn("Update ran nothing, since it cannot ask here", err)
        self.assertNotIn("Setup", out + err)
        h.file(os.path.join(h.home, "fail"), "paint@agentik")
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 1, out + err)
        self.assertIn("Update stopped: ", err)
        self.assertNotIn("Setup", out + err)

    def test_19_a_listed_tool_not_installed_is_named(self):
        h = self.home(("murmur", "paint", "quill"))
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        code, out, err = h.run("update", "quill", "--dry-run")
        self.assertEqual(code, 0, out + err)
        self.assertIn("quill is not installed", out)
        self.assertNotIn("no tool, since none", out)
        self.assertRegex(err, r"next: .*setup quill ")

    def test_20_an_unattended_answer_holds_whatever_its_exit(self):
        h = self.two_behind()
        session = os.path.join(h.bin, "agentik-session")
        for body, held in (("echo '{\"id\": \"u1\"}'; exit 1", True), ("echo '[]'; exit 3", True),
                           ("echo 'not json'", False), ("echo null; exit 3", False), ("exit 1", False)):
            h.file(session, "#!/bin/sh\n[ \"$1 $2 $3\" = 'unattended status --json' ] || exit 2\n%s\n" % body)
            self.assertEqual(update.hold(h.command("update")) is not None, held, body)


if __name__ == "__main__":
    unittest.main()
