"""Row ic1-close: the last line of `setup` and of `doctor` runs as printed and names the one act left.

R1: setup's close after a run, and after "nothing to do", is the doctor command alone, and pasted it
runs. R2: with the door at ~/.local/bin and that folder off PATH, setup's close, doctor's close and
doctor's door row name the PATH line, and neither names the other. R3: plain setup with no `claude`
gives the address and closes on the command typed; a Python under the floor is called older, never
"install". R4: stdout is flushed before the question and before a refusal.

The fix of review 1: F2, an installed Python under the floor is called older, with its version and
the minimum, in setup's `--json` refusal and in update's and setup's closes, never "install", and
no close sends him into the same refusal; the PATH close is `next: export PATH=...`, which runs.

Each screen runs in a temp HOME, PATH a folder with a stub `claude` (the plan tests' stub, which
installs the made-up plugin files) then /usr/bin:/bin, the suite started as `./setup` from the
clone's folder; two tests run in process. Nothing here starts the real `claude` or writes outside
its temp folder."""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import CLAUDE_STUB, PLUGIN_BIN  # noqa: E402
from agentik_suite import catalogue, cli, plan  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LAUNCHER = ROOT / "plugins" / "suite" / "bin" / "agentik-suite"
SYSTEM = "/usr/bin:/bin"
GET = "get it: https://claude.com/claude-code"
PLUGIN = "agents"  # a name the suite knows: setup refuses one it does not (row ic2-needs R2)
PROFILE = 'export PATH="$HOME/.local/bin:$PATH"'
# a plugin's install-cli that places its own launcher and no door, so step 5 places the suite's
NO_DOOR = re.sub(r' &&\n    printf [^\n]*/agentik" ;;', " ;;", PLUGIN_BIN)
MESSAGES = catalogue.load()
# review 1's ruling: the PATH close is a command, its reason on the line above
PATH_CLOSE = "next: " + PROFILE
PATH_WHY = "The line below mends this terminal; the line marked add mends each new one."


class Home(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="ic1-")
        self.addCleanup(tmp.cleanup)
        self.home = os.path.realpath(tmp.name)
        self.stubs = os.path.join(self.home, "stubs")
        os.mkdir(self.stubs)
        self.bindir = os.path.join(self.home, ".local", "bin")
        self.template = os.path.join(self.home, "plugin-bin")
        self.stub("plugin-bin", NO_DOOR, at=self.template)
        self.stub("claude", CLAUDE_STUB % self.template)

    def stub(self, name, body, at=None):
        path = at or os.path.join(self.stubs, name)
        with open(path, "w") as fh:
            fh.write(body)
        os.chmod(path, 0o755)

    def env(self, on_path=True, path=None):
        lead = self.bindir + ":" if on_path else ""
        return {"HOME": self.home, "PATH": path or lead + self.stubs + ":" + SYSTEM,
                "XDG_CACHE_HOME": os.path.join(self.home, "cache")}

    def run_both(self, argv, env):
        """(exit, stdout and stderr through one pipe, as `2>&1 | cat` reads them)."""
        p = subprocess.run(argv, cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=300)
        return p.returncode, p.stdout

    def paste(self, line, env):
        """A `next:` line pasted into sh -c from the clone's folder, stdin closed: (exit, output)."""
        self.assertTrue(line.startswith("next: "), line)
        return self.run_both(["/bin/sh", "-c", line[len("next: "):]], env)

    def last(self, text):
        return text.splitlines()[-1]


class DoctorCloseTest(Home):
    def test_r1_the_close_after_a_run_runs_as_printed(self):
        env = self.env()
        for round_ in ("applied", "nothing to do"):
            code, text = self.run_both(["./setup", "--yes"], env)
            self.assertEqual(code, 0, text)
            if round_ == "nothing to do":
                self.assertIn("Setup has nothing to do", text)
            line = self.last(text)
            self.assertEqual(line, "next: agentik doctor", (round_, text))
            code, out = self.paste(line, env)
            self.assertIn(code, (0, 1), (round_, out))

    def test_r1_the_message_is_a_command_alone(self):
        self.assertEqual(MESSAGES["hint.setup.doctor"], "next: {doctor}")

    def test_r1_the_typed_path_runs_too(self):
        """No door on PATH and none placed (a link not ours stands there): the launcher's own path."""
        env = self.env()
        code, text = self.run_both(["./setup", "--yes"], env)
        self.assertEqual(code, 0, text)
        door = os.path.join(self.bindir, "agentik")
        os.remove(door)
        os.symlink("/nonexistent/agentik", door)
        code, text = self.run_both(["./setup", "--yes"], env)
        self.assertEqual(code, 0, text)
        line = self.last(text)
        self.assertTrue(line.endswith("agentik-suite doctor"), line)
        code, out = self.paste(line, env)
        self.assertIn(code, (0, 1), out)


class PathLineTest(Home):
    def test_r2_off_path_setup_and_doctor_close_on_the_path_line(self):
        env = self.env(on_path=False)
        for round_ in ("applied", "nothing to do"):
            code, text = self.run_both(["./setup", "--yes"], env)
            self.assertEqual(code, 0, text)
            self.assertIn("add to your shell profile: " + PROFILE, text)
            self.assertEqual(self.last(text), PATH_CLOSE, (round_, text))
            self.assertEqual(text.splitlines()[-2], PATH_WHY, (round_, text))
            self.assertEqual(self.paste(self.last(text), env)[0], 0, text)
        self.assertTrue(os.path.isfile(os.path.join(self.bindir, "agentik")))
        code, text = self.run_both(["./setup", "--dry-run"], env)
        self.assertEqual(self.last(text), PATH_CLOSE, text)  # the dry run's close too
        self.assertEqual(text.splitlines()[-2], PATH_WHY, text)
        code, text = self.run_both([os.path.join(self.bindir, "agentik"), "doctor"], env)
        self.assertEqual(code, 0, text)
        self.assertEqual(self.last(text), PATH_CLOSE, text)
        self.assertEqual(text.splitlines()[-2], PATH_WHY, text)
        self.assertNotIn("setup", self.last(text))
        door = [l for l in text.splitlines() if l.split()[:2] == ["warn", "door"]]
        self.assertEqual(len(door), 1, text)
        self.assertIn("~/.local/bin/agentik is there, but its folder is not on PATH", door[0])
        lines = text.splitlines()
        at = lines.index(door[0])
        self.assertEqual(lines[at + 1].strip(), "fix: " + PROFILE, text)  # the door row ends on it
        self.assertIn("add to your shell profile: " + PROFILE, "\n".join(lines[at:]))

    def test_r2_doctor_json_carries_the_line(self):
        env = self.env(on_path=False)
        code, text = self.run_both(["./setup", "--yes"], env)
        self.assertEqual(code, 0, text)
        p = subprocess.run([os.path.join(self.bindir, "agentik"), "doctor", "--json"], env=env,
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
        obj = json.loads(p.stdout)
        door = [c for c in obj["tools"][0]["checks"] if c["name"] == "door"]
        self.assertEqual([(c["status"], c["remedy"]) for c in door], [("warn", PROFILE)])
        self.assertEqual(set(door[0]), {"name", "status", "detail", "remedy"})

    def test_r2_on_path_the_door_row_is_as_at_the_pin(self):
        """No door anywhere, ~/.local/bin on PATH: the door row and the close name setup."""
        env = self.env()
        p = subprocess.run([str(LAUNCHER), "doctor"], cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=120)
        self.assertIn("no agentik command on PATH", p.stdout)
        self.assertTrue(self.last(p.stderr).endswith("setup"), p.stderr)

    def test_path_no_close_is_prose_and_the_paste_runs(self):
        """Review 1's ruling: the PATH close is a command, printed by every close that names it."""
        self.assertEqual(MESSAGES["hint.setup.path"], "next: {command}")
        self.assertEqual(MESSAGES["setup.path.why"], PATH_WHY)
        code, out = self.paste(PATH_CLOSE, self.env(on_path=False))
        self.assertEqual(code, 0, out)

    def test_r2_the_new_line_holds_the_voice(self):
        for mid in ("doctor.door.off", "setup.path.why", "hint.setup.blocked.old", "err.setup.blocked.old"):
            self.voice(MESSAGES[mid])

    def voice(self, text):
        self.assertLessEqual(len(re.sub(r"`\{[^}]*\}`", "", text).replace("`", "")), 76)
        self.assertIsNone(re.search(r"this version|a later version|\bwould\b|\bexit", text, re.I))
        self.assertLessEqual(len(re.findall(r"\b(since|so|because)\b", text, re.I)), 1)


class BlockedTest(Home):
    def test_r3_no_claude_gives_the_address_and_the_command_typed(self):
        env = self.env(path=SYSTEM)
        for argv, want in ((["./setup"], "next: ./setup"), (["./setup", "--yes"], "next: ./setup"),
                           (["./setup", PLUGIN], "next: ./setup " + PLUGIN)):
            code, text = self.run_both(argv, env)
            self.assertEqual(code, 2, text)
            lines = text.splitlines()
            self.assertEqual(sum(GET in line for line in lines), 1, text)
            row = [i for i, line in enumerate(lines) if " claude " in line and "not on PATH" in line]
            self.assertEqual(len(row), 1, text)
            self.assertEqual(lines[row[0] + 1].strip(), GET)
            self.assertEqual(self.last(text), want, argv)
            self.assertNotIn("--dry-run", self.last(text))
            self.assertNotEqual(self.paste(self.last(text), env)[0], 127)

    def test_r3_a_python_under_the_floor_is_older_and_never_to_install(self):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(plan, "FLOOR", (3, 99)):
            code = cli.main(["setup"], env=self.env(), out=out, err=err)
        text = out.getvalue() + err.getvalue()
        self.assertEqual(code, 2, text)
        ver = "%d.%d.%d" % sys.version_info[:3]
        self.assertIn("Python %s at" % ver, text)
        self.assertIn("is older than the 3.99 minimum", text)
        self.assertNotIn("install python3", text)
        self.assertNotIn("install", self.last(err.getvalue()))

    def old(self, argv, env):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(plan, "FLOOR", (3, 99)):
            code = cli.main(argv, env=env, out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def test_f2_setup_json_says_older_and_names_no_dry_run(self):
        code, out, err = self.old(["setup", "--json"], self.env())
        self.assertEqual(code, 2, out + err)
        error = json.loads(out)["error"]
        ver = "%d.%d.%d" % sys.version_info[:3]
        self.assertEqual(error["code"], "blocked")
        self.assertEqual(error["message"], "Python %s is older than 3.99. Set AGENTIK_PYTHON to a newer one."
                         % ver)
        self.assertIsNone(error["remedy"])

    def test_f2_a_missing_claude_reads_as_before_in_json(self):
        out = subprocess.run(["./setup", "--json"], cwd=str(ROOT), env=self.env(path=SYSTEM),
                             stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120).stdout
        error = json.loads(out)["error"]
        self.assertEqual(error["message"], "Setup ran nothing, since step 1 needs claude. "
                                           "Install it, then run ./setup again.")
        self.assertEqual(error["remedy"], "./setup --dry-run")

    def test_f2_plain_setup_closes_on_the_older_line_and_no_loop(self):
        code, out, err = self.old(["setup"], self.env())
        self.assertEqual(code, 2, out + err)
        ver = "%d.%d.%d" % sys.version_info[:3]
        self.assertEqual(self.last(err), "Python %s is older than 3.99. Set AGENTIK_PYTHON to a newer one." % ver)
        self.assertNotIn("next:", err)  # no command of ours mends it: the GUIDE's null
        self.assertIn("is older than the 3.99 minimum", out)

    def test_f2_update_closes_on_the_older_line(self):
        env = self.env()
        code, text = self.run_both(["./setup", "--yes"], env)
        self.assertEqual(code, 0, text)
        code, out, err = self.old(["update"], env)
        self.assertEqual(code, 2, out + err)
        ver = "%d.%d.%d" % sys.version_info[:3]
        self.assertEqual(self.last(err), "Python %s is older than 3.99. Set AGENTIK_PYTHON to a newer one." % ver)
        self.assertNotIn("install", err)
        self.assertNotIn("next:", err)


class _Piped:
    """stdout into a pipe: held until flushed, then appended to the screen's log."""

    def __init__(self, log):
        self.log, self.held, self.encoding = log, [], "utf-8"

    def write(self, text):
        self.held.append(text)

    def flush(self):
        if self.held:
            self.log.append(("out", "".join(self.held)))
            self.held = []

    def isatty(self):
        return False


class _Terminal:
    """stderr on a terminal: each write reaches the screen at once."""

    def __init__(self, log):
        self.log, self.encoding = log, "utf-8"

    def write(self, text):
        self.log.append(("err", text))

    def flush(self):
        pass

    def isatty(self):
        return True


class _Keys:
    def isatty(self):
        return True

    def readline(self):
        return "n\n"


class OrderTest(Home):
    def test_r4_through_a_pipe_the_plan_prints_above_the_refusal(self):
        code, text = self.run_both(["./setup"], self.env())
        self.assertEqual(code, 2, text)
        lines = text.splitlines()
        title = [i for i, l in enumerate(lines) if l.startswith("Setup plan for")]
        fail = [i for i, l in enumerate(lines) if l.startswith("FAIL")]
        self.assertEqual(len(title), 1, text)
        self.assertEqual(len(fail), 1, text)
        self.assertLess(title[0], fail[0], text)
        self.assertTrue(lines[fail[0] - 1].strip(), text)  # the plan's last row whole above it
        self.assertTrue(all(l.startswith("next: ") for l in lines[fail[0] + 1:]), text)  # the refusal last

    def test_r4_after_a_run_next_follows_the_plan_read_again(self):
        code, text = self.run_both(["./setup", "--yes"], self.env())
        self.assertEqual(code, 0, text)
        lines = text.splitlines()
        again = lines.index(MESSAGES["setup.after"])
        nexts = [i for i, l in enumerate(lines) if l.startswith("next: ")]
        self.assertEqual(nexts, [len(lines) - 1], text)
        self.assertLess(again, nexts[0])

    def test_r4_on_a_terminal_the_question_follows_the_plan(self):
        log = []
        out, err = _Piped(log), _Terminal(log)
        env = dict(self.env(), COLUMNS="120")
        with mock.patch("sys.stdin", _Keys()):
            code = cli.main(["setup"], env=env, out=out, err=err)
        out.flush()
        self.assertEqual(code, 2, log)
        ask = [i for i, (_, text) in enumerate(log) if "commands now?" in text]
        plan_at = [i for i, (where, _) in enumerate(log) if where == "out"]
        self.assertEqual(len(ask), 1, log)
        self.assertTrue(plan_at and "Setup plan for" in log[plan_at[0]][1], log)
        self.assertLess(max(plan_at), ask[0], log)  # every byte of the plan above the question
        refusal = [i for i, (_, text) in enumerate(log) if "Setup ran nothing" in text]
        self.assertGreater(refusal[0], ask[0], log)


if __name__ == "__main__":
    unittest.main()
