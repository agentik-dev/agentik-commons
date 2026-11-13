"""Packet ak3-setup: `setup` applied, read first: the plan run row by row, its report and journal.

Each run is the plugin's launcher in a temp HOME (the ak1a `Home`), off a terminal unless a pty,
with `claude` the plan tests' stub that also records each call and fails `install beta@agentik`
while a flag file is there; the plugins are the made-up `alpha` and `beta`, and a made-up suite
launcher is placed at this version. Two tests run the command in process, with a stand-in plan.
Nothing here starts the real `claude` or writes outside its temp folder."""
import io
import json
import os
import pty
import select
import shlex
import subprocess
import sys
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import CLAUDE_STUB, LAUNCHER, PLUGIN_BIN, SYSTEM, Home, version  # noqa: E402
from agentik_suite import cli, plan  # noqa: E402

try:
    from agentik_suite import apply
except ImportError:  # at the pin, so each test is red alone
    apply = None

MARKET = "plugin marketplace add agentik-dev/agentik-commons"
FIRST = [MARKET, "plugin install alpha@agentik", "plugin install beta@agentik"]
LAST_LINE = "beta@agentik: no such version in the marketplace"
PROFILE = 'export PATH="$HOME/.local/bin:$PATH"'
# the plan tests' stub, after two lines: record the call, and fail beta's install on the flag
RECORD = """#!/usr/bin/python3
import os as _o, sys as _s
with open(%r, "a") as _f:
    _f.write(" ".join(_s.argv[1:]) + "\\n")
if _o.path.exists(%r) and _s.argv[1:] == ["plugin", "install", "beta@agentik"]:
    print("resolving beta@agentik", flush=True)
    print(%r, file=_s.stderr)
    _s.exit(1)
"""


class SetupHome(Home):
    def setUp(self):
        Home.setUp(self)
        self.template = os.path.join(self.home, "plugin-bin")
        with open(self.template, "w") as fh:
            fh.write(PLUGIN_BIN)
        os.chmod(self.template, 0o755)
        self.flag = os.path.join(self.stubs, "fail-beta")
        self.stub("claude", RECORD % (self.calls, self.flag, LAST_LINE) + CLAUDE_STUB % self.template)
        self.place("agentik-suite", version())

    @property
    def bindir(self):
        return os.path.join(self.home, ".local", "bin")

    @property
    def journal_path(self):
        return os.path.join(self.home, ".local", "state", "agentik-suite", "setup.jsonl")

    def place(self, exe, ver):
        os.makedirs(self.bindir, exist_ok=True)
        with open(os.path.join(self.bindir, exe), "w") as fh:
            fh.write("#!/bin/sh\nVERSION=%s\n" % ver)
        os.chmod(os.path.join(self.bindir, exe), 0o755)

    def recorded(self):
        if not os.path.exists(self.calls):
            return []
        with open(self.calls) as fh:
            return fh.read().splitlines()

    def journal(self):
        if not os.path.exists(self.journal_path):
            return []
        with open(self.journal_path) as fh:
            return [json.loads(line) for line in fh.read().splitlines()]

    def installed(self, *names):
        """Steps 2 and 3 already ok: Claude Code's two files, each plugin's launcher in its folder."""
        d = os.path.join(self.home, ".claude", "plugins")
        table = {}
        for name in names:
            root = os.path.join(d, "cache", "agentik", name, "1.0.0")
            os.makedirs(os.path.join(root, "bin"))
            with open(self.template) as src, open(os.path.join(root, "bin", "agentik-" + name), "w") as dst:
                dst.write(src.read())
            os.chmod(os.path.join(root, "bin", "agentik-" + name), 0o755)
            table[name + "@agentik"] = [{"scope": "user", "version": "1.0.0", "installPath": root}]
        with open(os.path.join(d, "known_marketplaces.json"), "w") as fh:
            json.dump({"agentik": {}}, fh)
        with open(os.path.join(d, "installed_plugins.json"), "w") as fh:
            json.dump({"version": 2, "plugins": table}, fh)

    def gate(self, line):
        os.makedirs(os.path.join(self.home, ".claude"), exist_ok=True)
        with open(os.path.join(self.home, ".claude", "edit-gates"), "w") as fh:
            fh.write("# the owner's list\n\n%s\n" % line)

    def answer_on_pty(self, answer, *args):
        master, slave = pty.openpty()
        p = subprocess.Popen([str(LAUNCHER), *args], stdin=slave, stdout=slave, stderr=slave,
                             env=self.env(), close_fds=True)
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

    def lines(self, out, word):
        return [l.strip()[len(word):] for l in out.splitlines() if l.strip().startswith(word)]

    def assert_line_one(self, code, out, err):
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.recorded(), FIRST)
        ran = self.lines(out, "ran: ")
        self.assertEqual(len(ran), 5, out)
        for got, want in zip(ran, FIRST):
            self.assertTrue(got.startswith("claude " + want), got)
        for got, name in zip(ran[3:], ("alpha", "beta")):
            self.assertIn("agentik-%s install-cli" % name, got)
        self.assertTrue(all(l.endswith("exit 0") for l in ran), ran)
        wrote = self.lines(out, "wrote: ")
        for path in ("~/.local/bin/agentik-alpha", "~/.local/bin/agentik-beta", "~/.local/bin/agentik",
                     "~/.local/state/agentik-suite/setup.jsonl"):
            self.assertIn(path, wrote)
        self.assertEqual(len(self.journal()), 1)
        steps = self.plan("alpha", "beta")["steps"]
        self.assertEqual({s["state"] for s in steps if 2 <= s["n"] <= 5}, {"ok"}, steps)


class ApplyTest(SetupHome):
    def test_l1_l2_it_runs_each_row_then_has_nothing_to_do(self):
        code, out, err = self.run_cli("setup", "--yes", "alpha", "beta")
        self.assert_line_one(code, out, err)
        self.assertEqual(err.count("running "), 5, err)
        self.assertIn("doctor", err.splitlines()[-1])
        entry = self.journal()[0]
        self.assertEqual(set(entry), {"at", "version", "plugins", "ran", "wrote", "exit"})
        self.assertEqual((entry["version"], entry["plugins"], entry["exit"]), (version(), ["alpha", "beta"], 0))
        self.assertTrue(entry["at"].endswith("Z"))
        self.assertEqual([r["command"].split()[-1] for r in entry["ran"]],
                         ["agentik-dev/agentik-commons", "alpha@agentik", "beta@agentik",
                          "install-cli", "install-cli"])
        self.assertIn(self.journal_path, entry["wrote"])
        # line 2: the same again
        before = self.snapshot()
        code, out, err = self.run_cli("setup", "--yes", "alpha", "beta")
        self.assertEqual(code, 0, out + err)
        self.assertIn("nothing to do", out.splitlines()[0])
        self.assertNotIn("ran: ", out)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.recorded(), FIRST)
        self.assertEqual(len(self.journal()), 1)

    def test_l3_without_yes_off_a_terminal(self):
        before = self.snapshot()
        code, out, err = self.run_cli("setup", "alpha", "beta")
        self.assertEqual(code, 2, out + err)
        self.assertIn("run: claude " + MARKET, out)
        self.assertIn("--yes", err)
        self.assertEqual(self.recorded(), [])
        self.assertEqual(self.snapshot(), before)

    def test_l4_on_a_pty_it_asks_once(self):
        before = self.snapshot()
        code, text = self.answer_on_pty("n", "setup", "alpha", "beta")
        self.assertEqual(code, 2, text)
        self.assertEqual(text.count("y or n"), 1, text)
        self.assertEqual(self.recorded(), [])
        self.assertEqual(self.snapshot(), before)
        code, text = self.answer_on_pty("y", "setup", "alpha", "beta")
        self.assertEqual(code, 0, text)
        self.assertEqual(text.count("y or n"), 1, text)
        self.assertEqual(self.recorded(), FIRST)
        self.assertEqual(text.count("ran: "), 5, text)
        self.assertEqual(len(self.journal()), 1)

    def test_l5_a_failed_step_stops_the_run(self):
        open(self.flag, "w").close()
        code, out, err = self.run_cli("setup", "--yes", "alpha", "beta")
        self.assertEqual(code, 1, out + err)
        self.assertEqual(self.recorded(), FIRST)
        got = {(s["n"], s["subject"]): s["state"] for s in self.plan("alpha", "beta")["steps"]}
        self.assertEqual(got[(3, "alpha@agentik")], "ok")
        self.assertIn("ran: claude plugin install beta@agentik, exit 1", out)
        self.assertIn("claude plugin install beta@agentik", err)
        self.assertIn("exit 1", err)
        self.assertIn(LAST_LINE, err)
        self.assertNotIn("install-cli", out)
        self.assertFalse(os.path.exists(os.path.join(self.bindir, "agentik-beta")))
        self.assertEqual([e["exit"] for e in self.journal()], [1])
        os.remove(self.flag)
        code, out, err = self.run_cli("setup", "--yes", "alpha", "beta")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.recorded(), FIRST + ["plugin install beta@agentik"])
        self.assertEqual([e["exit"] for e in self.journal()], [1, 0])
        before = self.snapshot()
        code, out, err = self.run_cli("setup", "--yes", "alpha", "beta")
        self.assertEqual(code, 0, out + err)
        self.assertIn("nothing to do", out)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(len(self.journal()), 2)

    def test_l6_no_claude_on_path(self):
        os.remove(os.path.join(self.stubs, "claude"))
        before = self.snapshot()
        code, out, err = self.run_cli("setup", "--yes", "alpha")
        self.assertEqual(code, 2, out + err)
        self.assertIn("install claude", err)
        self.assertNotIn("ran: ", out)
        self.assertEqual(self.snapshot(), before)

    def test_l7_the_gate_list_names_the_settings_file(self):
        for line in ("~/.claude/settings.json", "~/.claude/*.json"):
            self.gate(line)
            before = self.snapshot()
            code, out, err = self.run_cli("setup", "--yes", "alpha")
            self.assertEqual(code, 2, (line, out, err))
            self.assertIn("~/.claude/settings.json", err)
            self.assertIn("terminal", err)
            self.assertEqual(len(err.strip().splitlines()), 1, err)
            self.assertEqual(self.recorded(), [])
            self.assertEqual(self.snapshot(), before)
        # with steps 2 and 3 already ok, only a launcher to place: it runs
        self.installed("alpha")
        code, out, err = self.run_cli("setup", "--yes", "alpha")
        self.assertEqual(code, 0, out + err)
        self.assertIn("agentik-alpha install-cli", self.lines(out, "ran: ")[0])
        self.assertEqual(self.recorded(), [])

    def test_l7_on_a_pty_the_gated_run_asks_and_runs(self):
        self.gate("~/.claude/*.json")
        code, text = self.answer_on_pty("y", "setup", "alpha", "beta")
        self.assertEqual(code, 0, text)
        self.assertEqual(text.count("y or n"), 1, text)
        self.assertEqual(self.recorded(), FIRST)

    def test_l8_json(self):
        code, out, err = self.run_cli("setup", "--yes", "--json", "alpha", "beta")
        self.assertEqual((code, err), (0, ""))
        obj = json.loads(out)
        keys = {"schema", "ok", "dry_run", "plugins", "steps", "ran", "wrote", "nothing", "journal"}
        self.assertEqual(set(obj), keys)
        self.assertEqual((obj["schema"], obj["ok"], obj["dry_run"], obj["nothing"]),
                         ("agentik.setup/1", True, False, False))
        self.assertEqual(obj["plugins"], ["alpha", "beta"])
        self.assertEqual(set(obj["steps"][0]), {"n", "id", "state", "subject", "detail", "command"})
        self.assertEqual([r["exit"] for r in obj["ran"]], [0] * 5)
        self.assertEqual(set(obj["ran"][0]), {"n", "command", "exit"})
        self.assertEqual(obj["journal"], self.journal_path)
        self.assertIn(self.journal_path, obj["wrote"])
        self.assertIn(os.path.join(self.bindir, "agentik"), obj["wrote"])
        self.assertTrue(all(p.startswith("/") for p in obj["wrote"]))
        code, out, err = self.run_cli("setup", "--yes", "--json", "alpha", "beta")
        obj = json.loads(out)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual((obj["ok"], obj["nothing"], obj["ran"], obj["wrote"], obj["journal"]),
                         (True, True, [], [], None))
        self.assertEqual(set(obj), keys)

    def test_l8_json_for_a_failed_step(self):
        open(self.flag, "w").close()
        code, out, err = self.run_cli("setup", "--yes", "--json", "alpha", "beta")
        self.assertEqual((code, err), (1, ""))
        obj = json.loads(out)
        self.assertEqual((obj["ok"], obj["error"]["code"]), (False, "step_failed"))
        self.assertIn(LAST_LINE, obj["error"]["message"])
        self.assertEqual(obj["ran"][-1], {"n": 3, "command": "claude plugin install beta@agentik", "exit": 1})
        self.assertEqual(obj["journal"], self.journal_path)
        self.assertFalse(obj["nothing"])

    def test_l10_off_path_the_add_line_closes_and_nothing_else_is_new(self):
        before = self.snapshot()
        code, out, err = self.run_cli("setup", "--yes", "alpha", "beta")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.splitlines()[-1].strip(), "add to your shell profile: " + PROFILE)
        h = self.home
        places = [os.path.join(h, ".claude.json"), os.path.join(h, ".claude", "settings.json"),
                  os.path.join(h, ".claude", "plugins", "known_marketplaces.json"),
                  os.path.join(h, ".claude", "plugins", "installed_plugins.json"), self.calls]
        roots = [os.path.join(h, ".claude", "plugins", "cache", "agentik", n, "1.0.0") + "/"
                 for n in ("alpha", "beta")]
        roots += [self.bindir + "/", os.path.dirname(self.journal_path) + "/",
                  os.path.join(h, ".local", "share", "agentik-")]
        new = [p for p, kind in self.snapshot().items() if p not in before and kind != "dir"]
        self.assertTrue(new)
        for path in new:
            self.assertTrue(path in places or path.startswith(tuple(roots)), path)
        # with ~/.local/bin on PATH no add line is printed
        code, out, err = self.run_cli("setup", "--yes", "alpha", "beta",
                                      PATH="%s:%s:%s" % (self.bindir, self.stubs, SYSTEM))
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("add to your shell profile", out)


class InProcessTest(SetupHome):
    """Lines 6 and 9: a stand-in plan whose step 5 row names a stub, run in process."""

    def setUp(self):
        SetupHome.setUp(self)
        self.marker = os.path.join(self.home, "placed")
        self.ran = os.path.join(self.home, "ran")

    def stand_in(self, command):
        def build(names, env, lib, tool, ver):
            done = os.path.exists(self.marker)
            return [plan._step(1, "prereqs", "ok", "claude", "setup.cmd.found", path="/x"),
                    plan._step(2, "marketplace", "ok", "agentik", "setup.market.ok"),
                    plan._step(5, "suite", "ok" if done else "todo", "~/.local/bin/agentik-suite",
                               "setup.suite.ok" if done else "setup.suite.missing",
                               None if done else command, version=ver, path="/x"),
                    plan._step(6, "path", "ok", "~/.local/bin", "setup.path.ok"),
                    plan._step(7, "doctor", "todo", "agentik-alpha", "setup.doctor.todo",
                               "/x doctor")]
        return build

    def run_in_process(self, command, *args):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(plan, "build", self.stand_in(command)):
            code = cli.main(["setup", "--yes", *args], env=self.env(), out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def test_l9_a_step_5_row_runs_as_any_row(self):
        stub = self.stub("install-cli-stand-in", '#!/bin/sh\necho "$*" >> "%s"\n: > "%s"\n'
                         % (self.ran, self.marker))
        code, out, err = self.run_in_process("%s install-cli" % shlex.quote(stub), "alpha")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.lines(out, "ran: "), ["%s install-cli, exit 0" % stub])
        self.assertNotIn("doctor", out)
        with open(self.ran) as fh:
            self.assertEqual(fh.read(), "install-cli\n")

    def test_l9_a_row_left_todo_has_failed(self):
        stub = self.stub("install-cli-stand-in", '#!/bin/sh\necho "$*" >> "%s"\n' % self.ran)
        code, out, err = self.run_in_process("%s install-cli" % shlex.quote(stub), "--json", "alpha")
        self.assertEqual(code, 1, out + err)
        obj = json.loads(out)
        self.assertEqual(obj["error"]["code"], "step_failed")
        self.assertEqual(obj["ran"], [{"n": 5, "command": "%s install-cli" % stub, "exit": 0}])
        with open(self.ran) as fh:
            self.assertEqual(fh.read(), "install-cli\n")

    def test_l6_past_the_wall_its_group_is_gone(self):
        pidfile = os.path.join(self.home, "pid")
        stub = self.stub("slow", '#!/bin/sh\necho $$ > "%s"\nsleep 30 &\nsleep 30\n' % pidfile)
        start = time.monotonic()
        with mock.patch.object(apply, "WALL", 1):
            code, out, err = self.run_in_process(shlex.quote(stub), "alpha")
        self.assertLess(time.monotonic() - start, 10)
        self.assertEqual(code, 1, out + err)
        self.assertIn(stub, err)
        with open(pidfile) as fh:
            group = int(fh.read())
        for _ in range(50):
            try:
                os.killpg(group, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            self.fail("the group %d is still there" % group)

    def test_a_file_that_cannot_start_is_a_failed_step(self):
        code, out, err = self.run_in_process(os.path.join(self.home, "nosuch") + " install-cli", "alpha")
        self.assertEqual(code, 1, out + err)
        self.assertIn("nosuch", err)


if __name__ == "__main__":
    unittest.main()
