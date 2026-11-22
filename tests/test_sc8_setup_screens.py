"""Packet sc8-setup-screens: setup's plan, its report and its closing lines (design/23 §5).

Each run is the plugin's launcher in a temp HOME (the ak1a `Home`) with the plan tests' `claude`
stub, whose plugins' own install-cli places only the plugin's command, so the suite's own
install-cli places the door; the default set is planned. A pty run answers once the question
shows (`test_ak3_setup.on_pty`). Nothing here starts the real `claude` or writes outside its temp
folder."""
import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import CLAUDE_STUB, LAUNCHER, Home  # noqa: E402
from test_ak3_setup import on_pty  # noqa: E402
from agentik_suite import apply, catalogue  # noqa: E402

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
# the stub, failing `install decisions@agentik` with seven lines of its own while a flag file is there
FAIL = """#!/usr/bin/python3
import os as _o, sys as _s
if _o.path.exists(%r) and _s.argv[1:] == ["plugin", "install", "decisions@agentik"]:
    for i in range(1, 8):
        print("resolver line %%d of decisions@agentik, said whole" %% i, flush=True)
    _s.exit(1)
"""
SGR = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\r")
BANNED = re.compile(r"\b(remove|left|exit|exits|exited|code)\b|run:")
OURS = ("setup.title", "setup.would", "setup.yours", "setup.step.", "setup.waiting", "setup.took",
        "setup.failed", "setup.stopped", "setup.done", "setup.nothing", "setup.declined", "setup.tail.",
        "setup.wrote", "setup.path.", "setup.other", "err.setup.", "hint.setup.")  # what this row writes


def words(line):
    """The line with its paths and commands' paths left out, the words a banned word is sought in."""
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
        self.flag = os.path.join(self.stubs, "fail-decisions")
        self.stub("claude", FAIL % self.flag + CLAUDE_STUB.replace("#!/usr/bin/python3\n", "", 1) % template)

    def journal(self):
        with open(os.path.join(self.home, ".local", "state", "agentik-suite", "setup.jsonl")) as fh:
            return [json.loads(l) for l in fh.read().splitlines()]

    def lone(self, line, cols):
        """A line past `cols` that is a lone command or path, which cannot be broken (A8)."""
        if line.startswith("next: "):  # a `next:` command, whole by design/23 V3
            return line[6:].startswith(("/", "~/", "./"))
        return bool(re.match(" {%d}[^ ]" % apply.LEAD, line)) and line.strip().startswith(("/", "~/", "claude "))

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
        self.assertEqual(len(plan), 13 + lone(plan), plan)
        self.assertEqual(len(ended), 8 + lone(ended), ended)
        self.assertLessEqual(len(tail), 8, tail)
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
            for line in out + err:
                self.assertIsNone(BANNED.search(words(line)), line)
                if len(line) > 80:
                    self.assertTrue(self.lone(line, 80), line)
        code, text = on_pty([str(LAUNCHER), "setup"], "n", self.env(COLUMNS="50"), cwd=self.work)
        for line in lines_of(text):
            self.assertIsNone(BANNED.search(words(line)), line)
            if len(line) > 50 and "Run these" not in line:
                self.assertTrue(self.lone(line, 50) or len(line.split()) == 1, line)

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
        self.assertIn("  wrote  %d files, each named in the log" % len(wrote), out2)
        tail = out2[out2.index("Steps 2 to 5 are done: %d commands in 0 s." % len(json.loads(out)["ran"])):]
        shown = [w.rstrip(":") for l in tail for w in l.split() if w.startswith(("~/", "/"))]
        self.assertEqual(shown, ["~/.local/state/agentik-suite/setup.jsonl", "~/.local/bin/agentik",
                                 "~/.profile"], tail)  # the log's, the door's, and R2's login file

    def test_a5_the_path_rows(self):
        code, out, err = self.screen("setup", "--yes", SHELL="/bin/zsh")
        rows = [l for l in out if l.startswith("  PATH")]
        self.assertEqual(rows, ["  PATH   not needed by Claude Code; to type agentik, add to ~/.zshrc:"])
        self.assertIn('         export PATH="$HOME/.local/bin:$PATH"', out)
        on = "%s:%s:/usr/bin:/bin" % (os.path.join(self.home, ".local", "bin"), self.stubs)
        code, out, err = self.screen("setup", "--yes", PATH=on)
        self.assertFalse([l for l in out + err if "PATH" in l or "not needed by Claude Code" in l], out)
        self.assertEqual(err[-1], "next: claude")

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
        self.assertEqual(out[0], "Setup for session, decisions, agents. Nothing has run yet.")
        self.assertEqual(err[-2], "FAIL  nothing ran: there is no terminal to ask on")
        self.assertTrue(err[-1].startswith("next: ") and err[-1].endswith(" setup --yes"), err)

    def test_a7_a_failed_command(self):
        open(self.flag, "w").close()
        code, out, err = self.screen("setup", "--yes")
        self.assertEqual(code, 1, err)
        row = [i for i, l in enumerate(err) if "claude plugin install decisions@agentik" in l]
        self.assertTrue(row and "failed" in err[row[0]], err)
        self.assertEqual(err[row[0] + 1:row[0] + 6],
                         [" " * apply.LEAD + "resolver line %d of decisions@agentik, said whole" % i
                          for i in range(3, 8)])
        self.assertEqual(err[-2], "FAIL  setup stopped at step 3; steps 1 and 2 stand")
        self.assertTrue(err[-1].startswith("next: ") and err[-1].endswith(" setup"), err)

    # ---- R4, R6, R8: units ---------------------------------------------------------------
    def test_r4_undo_has_a_place_and_prints_none(self):
        self.assertIsNone(apply.undo(None))
        code, out, err = self.screen("setup", "--dry-run")
        self.assertFalse([l for l in out + err if "undo" in l])

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


if __name__ == "__main__":
    unittest.main()
