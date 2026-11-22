"""Packet sc8-setup-screens: setup's plan, its report and its closing lines (design/23 §5).

Each run is the plugin's launcher in a temp HOME (the ak1a `Home`) with the plan tests' `claude`
stub, whose plugins' own install-cli places only the plugin's command, so the suite's own
install-cli places the door; the default set is planned. A pty run answers once the question
shows (`test_ak3_setup.on_pty`). Nothing here starts the real `claude` or writes outside its temp
folder."""
import io
import json
import os
import re
import shutil
import sys
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import CLAUDE_STUB, LAUNCHER, Home  # noqa: E402
from test_ak3_setup import on_pty  # noqa: E402
from agentik_suite import apply, catalogue, cli, plan, term  # noqa: E402

DEFAULT = plan.default_set(str(LAUNCHER.parent.parent / "lib"))  # read from the plugin, never named here
SECOND = DEFAULT[1] + "@agentik"  # the plugin whose install the failing stub refuses

# a plugin's launcher whose install-cli places its own command alone, so the door is the suite's
PLUGIN_BIN = """#!/bin/sh
case "$1" in
install-cli)
    exe="$HOME/.local/bin/$(basename "$0")"
    mkdir -p "$HOME/.local/bin" || exit 1
    printf '#!/bin/sh\\nVERSION=1.0.0\\nexec "%s" "$@"\\n' "$0" > "$exe" && chmod 755 "$exe" ;;
doctor) exit 0 ;;
*) exit 2 ;;
esac
"""
# the stub, failing the second plugin's install with seven lines of its own while a flag file is there
FAIL = """#!/usr/bin/python3
import os as _o, sys as _s
if _o.path.exists(%r) and _s.argv[1:] == ["plugin", "install", %r]:
    for i in range(1, 8):
        print("resolver line %%d of the plugin, said whole" %% i, flush=True)
    _s.exit(1)
"""
SGR = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\r")
BANNED = re.compile(r"\b(remove|left|exit|exits|exited|code)\b|run:")
OURS = ("setup.title", "setup.would", "setup.yours", "setup.step.", "setup.waiting", "setup.took",
        "setup.failed", "setup.stopped", "setup.done", "setup.nothing", "setup.declined", "setup.tail.",
        "setup.wrote", "setup.path.", "setup.other", "err.setup.", "hint.setup.")  # what this row writes


# the `undo` row's command, the one remove (row sc16 R3; review 1 F1): on the row's own line after its
# label, or alone at LEAD on the line under a label line that holds `undo` alone
UNDO = re.compile(r"^( +undo +\S*\bagentik(-suite)?) remove --all$")
UNDO_LEAD = re.compile(r"^( {%d}\S*\bagentik(-suite)?) remove --all$" % apply.LEAD)
UNDO_LABEL = re.compile(r"^ +undo *$")


def words(line, before=""):
    """The line with its paths and commands' paths left out, the words a banned word is sought in;
    `before` is the line above it on the same stream, which tells the undo row's second line."""
    row = UNDO.match(line) or (UNDO_LABEL.match(before) and UNDO_LEAD.match(line))
    if row:
        line = row.group(1)
    return " ".join(w for w in line.split() if not w.startswith(("/", "~")))


def lines_of(text):
    return [SGR.sub("", l) for l in text.splitlines()]


class Screens(Home):
    launcher = LAUNCHER

    def setUp(self):
        Home.setUp(self)
        template = os.path.join(self.home, "plugin-bin")
        with open(template, "w") as fh:
            fh.write(PLUGIN_BIN)
        os.chmod(template, 0o755)
        self.flag = os.path.join(self.stubs, "fail-second")
        self.stub("claude", FAIL % (self.flag, SECOND) + CLAUDE_STUB.replace("#!/usr/bin/python3\n", "", 1) % template)

    def journal(self):
        with open(os.path.join(self.home, ".local", "state", "agentik-suite", "setup.jsonl")) as fh:
            return [json.loads(l) for l in fh.read().splitlines()]

    def lone(self, line, cols):
        """A line past `cols` that is a lone command or path, which cannot be broken (A8)."""
        for head in ("next: ", "other plugins: "):  # a command after its head, whole by design/23 V3
            if line.startswith(head):
                return line[len(head):].startswith(("/", "~/", "./"))
        if not (re.match(" {%d}[^ ]" % apply.LEAD, line) and line.strip().startswith(("/", "~/", "claude "))):
            return False
        # the command or path and nothing more: no result words after it (review 1 F2)
        return not re.search(r" \d+ s\b|\bfailed\b|\bstopped\b|could not start", line)

    def screen(self, *args, **more):
        code, out, err = self.run_cli(*args, COLUMNS="80", **more)
        return code, lines_of(out), lines_of(err)

    @staticmethod
    def would(out):
        """The commands under `Would run`, each whole."""
        at, got = out.index("Would run, in this order:"), []
        for line in out[at + 1:out.index("Yours, after:")]:
            text = line[19:] if not line.startswith(" " * apply.LEAD + "/") else line.strip()
            if line.strip() and "more:" not in line and not re.fullmatch(r"\s+\d \w+", line):
                got.append(text.strip())
        return got

    # ---- A1, A3, A4, A8: the applied run --------------------------------------------------
    def test_a1_the_line_count(self):
        code, out, err = self.screen("setup", "--yes")
        self.assertEqual(code, 0, err)
        plan = out[:[i for i, l in enumerate(out) if l.startswith("Steps 2 to 5 are done")][0]]
        tail = out[len(plan):] + err[-1:]
        ended = err[:-1]
        lone = lambda part: sum(1 for l in part if self.lone(l, 80))
        self.assertEqual(len(plan), 14 + lone(plan), plan)
        self.assertEqual(len(ended), 8 + lone(ended), ended)
        self.assertLessEqual(len(tail), 9, tail)  # sc16's undo row, one more
        print("\nA1: plan %d, commands %d, tail %d: %d lines (--yes, no answer line)"
              % (len(plan), len(ended), len(tail), len(out) + len(err)), file=sys.stderr)

    def test_a3_the_last_line_is_claude(self):
        for _ in (1, 2):
            code, out, err = self.screen("setup", "--yes")
            self.assertEqual((code, err[-1]), (0, "next: claude"), out + err)
        self.assertIn("Nothing to do: steps 1 to 5 are done.", out)

    def test_a4_a8_no_banned_word_and_the_width(self):
        screens = [self.screen("setup", "--dry-run"), self.screen("setup", "--yes"), self.screen("setup", "--yes"),
                   self.screen("setup")]
        open(self.flag, "w").close()
        os.remove(os.path.join(self.home, ".claude", "plugins", "installed_plugins.json"))
        screens.append(self.screen("setup", "--yes"))
        for code, out, err in screens:
            for lines in (out, err):  # each stream with its own line above
                for before, line in zip([""] + lines, lines):
                    self.assertIsNone(BANNED.search(words(line, before)), line)
        os.remove(self.flag)
        shutil.rmtree(os.path.join(self.home, ".claude"))
        shutil.rmtree(os.path.join(self.home, ".local"))
        for cols, answer in (("50", "n"), ("50", "y"), ("80", "y")):  # A8 is measured on a pty
            code, text = on_pty([str(LAUNCHER), "setup"], answer, self.env(COLUMNS=cols), cwd=self.work)
            lines = lines_of(text)
            for before, line in zip([""] + lines, lines):
                self.assertIsNone(BANNED.search(words(line, before)), line)
                if len(line) > int(cols) and "Run these" not in line:
                    self.assertTrue(self.lone(line, int(cols)) or len(line.split()) == 1, (cols, line))

    def test_a8_a_pipe_row_is_one_line_a_pty_row_fits(self):
        """Off a terminal a row is one line, as sc3's table, so a pipe is searched by line; on a
        pty of 50 the same row stands within the width, its command on a line of its own."""
        code, out, err = self.screen("setup", "--dry-run")
        door = [l for l in out if re.match(r" +5 agentik +/.*install-cli$", l)]
        self.assertEqual(len(door), 1, out)
        self.assertGreater(len(door[0]), 80, door)
        self.assertFalse([l for l in out + err if re.match(" {%d}[/~]" % apply.LEAD, l)], out + err)
        code, text = on_pty([str(LAUNCHER), "setup"], "n", self.env(COLUMNS="50"), cwd=self.work)
        shown = lines_of(text)
        at = [i for i, l in enumerate(shown) if re.fullmatch(r" +5 agentik", l)]
        self.assertTrue(at and shown[at[0] + 1].strip().endswith("install-cli"), text)
        self.assertTrue(self.lone(shown[at[0] + 1], 50), text)

    def test_a1_on_a_pty_with_the_answer(self):
        """A1's sum where the answer is typed: the plan, one line for the answer, the commands,
        the tail."""
        code, text = on_pty([str(LAUNCHER), "setup"], "y", self.env(COLUMNS="80"), cwd=self.work)
        shown = lines_of(text)
        self.assertEqual((code, shown[-1]), (0, "next: claude"), text)
        ask = [i for i, l in enumerate(shown) if l.endswith("now? y for yes, n or Enter for no.")][0]
        ended = [i for i, l in enumerate(shown) if l.startswith("Steps 2 to 5 are done")][0]
        lone = lambda part: sum(1 for l in part if self.lone(l, 80))
        plan, answer, ran, tail = shown[:ask], shown[ask:ask + 2], shown[ask + 2:ended], shown[ended:]
        self.assertEqual(answer[1], "y", text)  # sm1's typed question and the pty's echo of the answer
        self.assertEqual(len(plan), 14 + lone(plan), plan)
        self.assertEqual(len(ran), 8 + lone(ran), ran)
        self.assertLessEqual(len(tail), 9, tail)  # sc16's undo row, one more
        print("\nA1 on a pty: plan %d (%d lone), answer %d, commands %d (%d lone), tail %d: %d lines"
              % (len(plan), lone(plan), len(answer), len(ran), lone(ran), len(tail), len(shown)), file=sys.stderr)

    # ---- A2, A5: what the report holds ---------------------------------------------------
    def test_a2_every_path_in_the_json_and_the_log_and_a_count_on_screen(self):
        code, out, err = self.run_cli("setup", "--yes", "--json")
        wrote = json.loads(out)["wrote"]
        self.assertEqual(self.journal()[-1]["wrote"], wrote)
        other = Screens("test_a2_every_path_in_the_json_and_the_log_and_a_count_on_screen")
        other.setUp()
        try:
            code, out2, err2 = other.screen("setup", "--yes")
        finally:
            other.doCleanups()
        log = os.path.join(self.home, ".local", "state", "agentik-suite", "setup.jsonl")
        self.assertIn(log, wrote)  # the log is a path written; the row counts the commands' (review 1 L2)
        self.assertIn("  wrote  %d files, each named in the log" % (len(wrote) - 1), out2)
        done = re.compile(r"^Steps 2 to 5 are done: %d commands in \d+ s\.$" % len(json.loads(out)["ran"]))
        at = [i for i, l in enumerate(out2) if done.match(l)]  # the seconds are the clock's, 1 s under load
        self.assertEqual(len(at), 1, out2)
        tail = out2[at[0]:]
        shown = [w.rstrip(":") for l in tail for w in l.split() if w.startswith(("~/", "/"))]
        self.assertEqual(shown, ["~/.local/state/agentik-suite/setup.jsonl", "~/.local/bin/agentik",
                                 "~/.local/bin/agentik", "~/.profile"], tail)  # the log's, the door's (check, then sc16's undo), and R2's login file

    def test_a5_the_path_rows(self):
        code, out, err = self.screen("setup", "--yes", SHELL="/bin/zsh")
        rows = [l for l in out if l.startswith("  PATH")]
        self.assertEqual(rows, ["  PATH   not needed by Claude Code; to type agentik, add to ~/.zshrc:"])
        self.assertIn('         export PATH="$HOME/.local/bin:$PATH"', out)
        on = "%s:%s:/usr/bin:/bin" % (os.path.join(self.home, ".local", "bin"), self.stubs)
        code, out, err = self.screen("setup", "--yes", PATH=on)
        self.assertFalse([l for l in out + err if "PATH" in l or "not needed by Claude Code" in l], out)
        self.assertEqual(err[-1], "next: claude")

    # ---- the dry run's close (R3, as ruled for sc8's build 3) ------------------------------
    @staticmethod
    def path_rows(out):
        """The report's PATH row and the line under it."""
        at = [i for i, l in enumerate(out) if l.startswith("  PATH ")]
        return [out[i:i + 2] for i in at]

    def test_r3_a_dry_run_that_runs_nothing_closes_as_the_second_run(self):
        """Steps 1 to 5 done, ~/.local/bin off PATH: the PATH rows as the report prints them, then
        next: claude; no screen of setup ends on next: export."""
        code, out, err = self.screen("setup", "--yes", SHELL="/bin/zsh")
        self.assertEqual(code, 0, err)
        code, again, again_err = self.screen("setup", "--yes", SHELL="/bin/zsh")
        self.assertEqual((code, again_err[-1]), (0, "next: claude"), again + again_err)
        code, out, err = self.screen("setup", "--dry-run", SHELL="/bin/zsh")
        self.assertEqual(code, 0, out + err)
        rows = self.path_rows(out)
        self.assertEqual(rows, [["  PATH   not needed by Claude Code; to type agentik, add to ~/.zshrc:",
                                 '         export PATH="$HOME/.local/bin:$PATH"']], out)
        self.assertEqual(rows, self.path_rows(again), again)
        self.assertEqual(err[-1], "next: claude", out + err)
        self.assertFalse([l for l in out + err if l.startswith("next: export")], out + err)

    def test_r3_a_dry_run_whose_plan_holds_commands_closes_on_setup(self):
        """A fresh home: the plan holds commands, so the dry run's next: is setup, as at the pin,
        and no PATH row prints, since the run's report holds them."""
        code, out, err = self.screen("setup", "--dry-run", SHELL="/bin/zsh")
        self.assertEqual(code, 0, out + err)
        self.assertIn("Would run, in this order:", out)
        self.assertTrue(err[-1].startswith("next: ") and err[-1].endswith(" setup"), out + err)
        self.assertEqual(self.path_rows(out), [], out)
        self.assertFalse([l for l in out + err if l.startswith("next: export")], out + err)

    # ---- A6: what a yes runs -------------------------------------------------------------
    def test_a6_would_run_is_what_a_yes_runs(self):
        code, out, err = self.screen("setup", "--dry-run")
        listed = self.would(out)
        self.assertEqual(len(listed), 5, out)
        self.assertIn("  4 commands     3 more: each plugin's own install-cli, once step 3 is done",
                      [l.replace("    4", "  4", 1) for l in out])
        self.screen("setup", "--yes")
        ran = [r["command"] for r in self.journal()[-1]["ran"]]
        self.assertEqual([c for c in ran if c in listed], listed)
        later = [c for c in ran if c not in listed]
        self.assertEqual(len(later), 3)
        self.assertTrue(all(c.endswith(" install-cli") for c in later))
        for c in later:
            self.assertFalse([l for l in out if c in l])
        os.remove(os.path.join(self.home, ".local", "bin", "agentik-suite"))
        code, out, err = self.screen("setup", "--dry-run")
        one = self.would(out)
        self.assertEqual(len(one), 1, out)
        self.screen("setup", "--yes")
        self.assertEqual([r["command"] for r in self.journal()[-1]["ran"]], one)

    # ---- A7, R5, R6: a no, no terminal, a failure ----------------------------------------
    def test_a7_a_no_on_a_pty(self):
        code, text = on_pty([str(LAUNCHER), "setup"], "n", self.env(COLUMNS="80"), cwd=self.work)
        shown = lines_of(text)
        self.assertEqual(code, 2, text)
        self.assertFalse([l for l in shown if "✗" in l or "FAIL" in l], text)
        at = [i for i, l in enumerate(shown) if l.endswith("nothing ran")]
        self.assertTrue(at, text)
        self.assertTrue(shown[at[0] + 1].startswith("other plugins: "), text)
        self.assertTrue(shown[at[0] + 2].startswith("next: ") and shown[at[0] + 2].endswith(" setup"), text)
        self.assertFalse(os.path.exists(os.path.join(self.home, ".claude", "plugins")))

    def test_r5_no_terminal_and_no_yes(self):
        code, out, err = self.screen("setup")
        self.assertEqual(code, 2)
        self.assertEqual(out[0], "Setup for %s. Nothing has run yet." % ", ".join(DEFAULT))
        self.assertEqual(err[-2], "FAIL  nothing ran: there is no terminal to ask on")
        self.assertTrue(err[-1].startswith("next: ") and err[-1].endswith(" setup --yes"), err)

    def test_a7_a_failed_command(self):
        open(self.flag, "w").close()
        code, out, err = self.screen("setup", "--yes")
        self.assertEqual(code, 1, err)
        row = [i for i, l in enumerate(err) if "claude plugin install " + SECOND in l]
        self.assertTrue(row and "failed" in err[row[0]], err)
        self.assertEqual(err[row[0] + 1:row[0] + 6],
                         [" " * apply.LEAD + "resolver line %d of the plugin, said whole" % i
                          for i in range(3, 8)])
        self.assertEqual(err[-2], "FAIL  setup stopped at step 3; steps 1 and 2 stand")
        self.assertTrue(err[-1].startswith("next: ") and err[-1].endswith(" setup"), err)

    # ---- review 1: F1 to F4, L1 to L4 ----------------------------------------------------
    def blocked_plan(self, out, err):
        """A blocked plan: what blocks, no `Would run` and no count of commands to come, step 6's
        line with its command, since a blocked run never reaches the report (review 1 F1)."""
        self.assertNotIn("Would run, in this order:", out)
        self.assertFalse([l for l in out + err if " more: " in l or "once step 3 is done" in l], out)
        self.assertFalse([l for l in out + err if "prints at the end" in l], out)
        six = [i for i, l in enumerate(out) if re.match(r" +6 PATH +", l)]
        self.assertEqual(len(six), 1, out)
        self.assertEqual(out[six[0] + 1].strip(), plan.PROFILE_LINE, out)
        self.assertLess(out.index("Yours, after:"), six[0], out)
        self.assertTrue(err[-1].startswith("next: ") and err[-1].endswith(" setup"), err)

    def test_f1_a_blocked_plan_says_no_would_run(self):
        os.remove(os.path.join(self.stubs, "claude"))
        for args in (("setup", "--yes"), ("setup",), ("setup", "--dry-run")):
            code, out, err = self.screen(*args)
            self.assertEqual(code, 0 if "--dry-run" in args else 2, out + err)
            self.assertTrue([l for l in out if re.match(r" +warn 1 needs +claude: not on PATH", l)], out)
            self.blocked_plan(out, err)
        self.assertFalse(os.path.exists(os.path.join(self.home, ".local", "bin")))

    def test_f1_a_python_under_the_floor_says_no_would_run(self):
        for args in (["setup", "--yes"], ["setup"]):
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(plan, "FLOOR", (3, 99)):
                code = cli.main(args, env=self.env(COLUMNS="80"), out=out, err=err)
            out, err = lines_of(out.getvalue()), lines_of(err.getvalue())
            self.assertEqual(code, 2, out + err)
            self.assertTrue([l for l in out if "older than the 3.99 minimum" in l], out)
            self.assertNotIn("Would run, in this order:", out)
            self.assertFalse([l for l in out + err if " more: " in l or "prints at the end" in l], out)
            six = [i for i, l in enumerate(out) if re.match(r" +6 PATH +", l)]
            self.assertTrue(six and out[six[0] + 1].strip() == plan.PROFILE_LINE, out)

    def test_f2_a_failed_command_stays_in_the_width_on_a_pty(self):
        silent, loud = "#!/bin/sh\nexit 1\n", "#!/bin/sh\necho 'Error: the network is unreachable from here'\nexit 1\n"
        for body, cols in ((silent, 80), (loud, 80), (silent, 50)):
            self.stub("claude", body)
            code, text = on_pty([str(LAUNCHER), "setup", "--yes"], "n", self.env(COLUMNS=str(cols), TERM="dumb"),
                                cwd=self.work)
            shown = lines_of(text)
            self.assertEqual(code, 1, text)
            row = [i for i, l in enumerate(shown) if "2 marketplace" in l][-1]
            self.assertIn("failed", " ".join(shown[row:row + 3]), text)
            for line in shown:
                if len(line) > cols:
                    self.assertTrue(self.lone(line, cols) or len(line.split()) == 1, (cols, line))

    def test_f2_an_ended_row_at_the_width_unit(self):
        """`_ended` on a terminal of 80 and 50: a wall stop, a silent failure and one with output
        each keep their result words inside the width, the command whole."""
        class Tty(io.StringIO):
            def isatty(self):
                return True
        command = "claude plugin marketplace add agentik-dev/agentik-commons"
        results = ({"why": "wall", "wall": 600, "exit": None, "last": "", "tail": []},
                   {"why": None, "wall": 600, "exit": 1, "last": "", "tail": []},
                   {"why": None, "wall": 600, "exit": 1, "last": "Error: no", "tail": ["Error: no"]})
        for cols in (80, 50):
            for result in results:
                err = Tty()
                t = term.Term(env={"COLUMNS": str(cols), "NO_COLOR": "1"}, out=Tty(), err=err)
                apply._ended(type("C", (), {"t": t})(), {"n": 2, "command": command}, result, 3)
                lines = lines_of(err.getvalue())
                self.assertTrue([l for l in lines if l.strip().startswith(command)], lines)  # whole, at LEAD
                self.assertTrue(re.search(r"failed|stopped after 600 s", " ".join(lines)), lines)
                for line in lines:
                    self.assertTrue(len(line) <= cols or self.lone(line, cols), (cols, line))

    def shut_the_log(self):
        state = os.path.join(self.home, ".local", "state", "agentik-suite")
        os.makedirs(state)
        log = os.path.join(state, "setup.jsonl")
        open(log, "w").close()
        os.chmod(log, 0o400)
        return log

    def test_f3_a_log_that_took_no_line_is_never_pointed_to(self):
        """The log cannot take the run's line: the report says so and names each path written on
        the screen, as at the pin; `--json` holds them all (review 1 F3)."""
        log = self.shut_the_log()
        code, out, err = self.screen("setup", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(os.path.getsize(log), 0)
        self.assertFalse([l for l in out + err if "named in the log" in l or l.startswith("  log ")], out)
        self.assertTrue([l for l in err if "did not take this run's line" in l], err)
        at = [i for i, l in enumerate(out) if l.startswith("  wrote  ")]
        self.assertEqual(len(at), 1, out)
        count = int(re.match(r"  wrote  (\d+) files?:$", out[at[0]]).group(1))
        listed = [l.strip() for l in out[at[0] + 1:at[0] + 1 + count]]
        self.assertTrue(all(p.startswith(("~/", "/")) and " " not in p for p in listed), listed)
        other = Screens("test_f3_a_log_that_took_no_line_is_never_pointed_to")
        other.setUp()
        try:
            other.shut_the_log()
            wrote = json.loads(other.run_cli("setup", "--yes", "--json")[1])["wrote"]
            shown = [plan.shown(p, other.home) for p in wrote]
        finally:
            other.doCleanups()
        self.assertEqual(listed, shown)
        self.assertIn("~/.local/bin/agentik", listed)

    def test_f4_the_seconds_are_the_runs_own(self):
        """A marketplace add that sleeps 2 s: its row reads 2 s, within a second, and the report's
        total is at least that and at most the run's wall time, rounded up (review 1 F4)."""
        slow = "import time as _t\nif _s.argv[1:3] == ['plugin', 'marketplace']:\n    _t.sleep(2)\n"
        template = os.path.join(self.home, "plugin-bin")
        self.stub("claude", FAIL % (self.flag, SECOND) + slow
                  + CLAUDE_STUB.replace("#!/usr/bin/python3\n", "", 1) % template)
        began = time.time()
        code, out, err = self.screen("setup", "--yes")
        wall = time.time() - began
        self.assertEqual(code, 0, out + err)
        row = [l for l in err if re.match(r" +ok 2 marketplace +claude plugin marketplace add ", l)]
        self.assertEqual(len(row), 1, err)
        self.assertIn(int(re.search(r" (\d+) s$", row[0]).group(1)), (2, 3), row)
        total = [re.match(r"^Steps 2 to 5 are done: \d+ commands in (\d+) s\.$", l) for l in out]
        total = [int(m.group(1)) for m in total if m]
        self.assertEqual(len(total), 1, out)
        self.assertTrue(2 <= total[0] <= int(wall) + 1, (total, wall))
        for line in err:  # no command's row holds more seconds than the run took
            m = re.search(r" (\d+) s$", line)
            self.assertTrue(not m or int(m.group(1)) <= int(wall) + 1, line)

    def test_l2_wrote_counts_the_commands_files_never_the_log(self):
        code, out, err = self.run_cli("setup", "--yes", "--json")
        log = os.path.join(self.home, ".local", "state", "agentik-suite", "setup.jsonl")
        made = [p for p in json.loads(out)["wrote"] if p != log]
        self.assertIn(log, json.loads(out)["wrote"])  # the document still holds every path
        other = Screens("test_l2_wrote_counts_the_commands_files_never_the_log")
        other.setUp()
        try:
            code, shown, err2 = other.screen("setup", "--yes")
            other.stub("claude", "#!/bin/sh\nexit 1\n")
            shutil.rmtree(os.path.join(other.home, ".claude"))
            code2, failed, err3 = other.screen("setup", "--yes")
        finally:
            other.doCleanups()
        self.assertIn("  wrote  %d files, each named in the log" % len(made), shown)
        self.assertEqual(code2, 1, failed + err3)  # the first command failed and wrote nothing
        self.assertFalse([l for l in failed + err3 if l.startswith("  wrote ")], failed + err3)

    def test_l3_a_dry_run_on_path_prints_no_path_row(self):
        on = "%s:%s:/usr/bin:/bin" % (os.path.join(self.home, ".local", "bin"), self.stubs)
        self.screen("setup", "--yes", PATH=on)
        code, out, err = self.screen("setup", "--dry-run", PATH=on)
        self.assertEqual((code, err[-1]), (0, "next: claude"), out + err)
        self.assertTrue([l for l in out if re.match(r"  ok 6 PATH +~/\.local/bin$", l)], out)  # the plan's step
        self.assertFalse([l for l in out + err if l.startswith("  PATH ") or plan.PROFILE_LINE in l
                          or "not needed by Claude Code" in l], out)

    def test_l4_a_failed_report_has_no_log_row(self):
        open(self.flag, "w").close()
        code, out, err = self.screen("setup", "--yes")
        self.assertEqual(code, 1, err)
        self.assertFalse([l for l in out + err if re.match(r"  (log|check|PATH) ", l)], out + err)
        self.assertEqual([l for l in out + err if l.startswith("  wrote ")],
                         ["  wrote  %d files, each named in the log" % len(self.journal()[-1]["wrote"][:-1])])

    # ---- R4, R6, R8: units ---------------------------------------------------------------
    def test_r4_undo_has_a_place_and_prints_one_row(self):  # sc16 R1 turns it on
        code, out, err = self.screen("setup", "--dry-run")
        self.assertEqual([l for l in out + err if re.match(r" +undo ", l)],  # the label: a path may hold the word
                         ["      undo         %s remove --all" % LAUNCHER])

    def test_r6_the_closing_lines(self):
        t = type("T", (), {"text": None})()
        interrupted = ("err.setup.interrupted", {"command": "claude x"}, 130, "interrupted")
        self.assertEqual(apply._closing(t, interrupted, [{"n": 2}]), ("err.setup.interrupted", {"n": 2}))
        step = ("err.setup.step.silent", {"command": "c", "exit": 1, "last": "", "wall": 120})
        self.assertEqual(apply._closing(t, step, [{"n": 2}]), ("err.setup.step.one", {"n": 2}))
        self.assertEqual(apply._closing(t, step, [{"n": 5}]), ("err.setup.step", {"n": 5, "done": "1 to 4"}))

    def test_r8_the_messages(self):
        messages = catalogue.load()
        for mid, text in messages.items():
            if mid.startswith(OURS):
                self.assertIsNone(re.search(r"\b(exit|exits|exited)\b", text), mid)
                bare = re.sub(r"\{[a-z_]+\}", "", text)
                self.assertLessEqual(len(bare), 76, mid)
                if mid.startswith("hint.setup.") and text.startswith("next:"):
                    self.assertNotIn(". ", text, mid)  # a command, never a sentence (V3)


class TheUndoRowAlone(unittest.TestCase):
    """A4's filter lets the remove command through on the `undo` row alone (row sc16 review 1 F1):
    the row on one line, or its command at LEAD under a label line that holds `undo` alone."""
    lead = " " * apply.LEAD + "~/.local/bin/agentik remove --all"

    def refused(self, line, before=""):
        return bool(BANNED.search(words(line, before)))

    def test_f1_review_lines(self):
        for line in ("next: agentik remove --all", "FAIL  setup stopped at step 3; run agentik-suite remove --all",
                     "  note  to start over: agentik remove --all"):
            self.assertTrue(self.refused(line), line)
        self.assertFalse(self.refused("      undo         ~/.local/bin/agentik remove --all"))
        self.assertFalse(self.refused("  undo         %s remove --all" % LAUNCHER))

    def test_f1_a_second_remove_on_the_undo_row(self):
        for line in ("      undo         agentik remove --all; agentik remove --all",
                     "      undo         remove agentik remove --all",
                     "      undo         agentik remove --all remove"):
            self.assertTrue(self.refused(line), line)

    def test_f1_the_command_at_lead_under_its_label(self):
        self.assertFalse(self.refused(self.lead, "      undo"))
        self.assertFalse(self.refused(self.lead, "  undo"))
        for before in ("", "      check", "  next: claude", "      undo         agentik remove --all", "  log"):
            self.assertTrue(self.refused(self.lead, before), before)
        self.assertTrue(self.refused("  " + self.lead, "      undo"))  # off the LEAD column


if __name__ == "__main__":
    unittest.main()
