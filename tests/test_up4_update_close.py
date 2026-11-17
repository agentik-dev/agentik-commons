"""Row up4-update-close: update's close says what it did and what is left.

R1: where a plugin moved, one line says open sessions keep the old plugins. R2: a tool whose table
row holds a `page`, its plugin moved, is a `note` naming its command's path, the page's line under
it. R3: a step 2 failure still places the commands of the tools already moved, and says so. R4:
each `next:` update prints is a command that runs as printed; a tool not installed and a name that
is no tool are said as such; update's rows speak of update. R5: an interrupt names the command it
stopped. Each run is in a temp HOME (test_ak4a_update's) with a stub `claude`; no test starts a
real `claude`, reads the live home or reaches the network."""
import json
import os
import re
import signal
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_ak4a_update as tu  # noqa: E402
from test_agentik_suite import LAUNCHER, PLUGIN  # noqa: E402
from agentik_suite import catalogue, tools, update  # noqa: E402

SESSIONS = "sessions started before this keep the old plugins until they are restarted"
REFUSED = ("is not a plugin name", "takes no", "is one more", "not found", "No such file",
           "is no known tool", "Traceback")
# a `claude` that hangs on `plugin update`, after it writes its pid (R5)
HANG = '#!/bin/sh\necho "claude $*" >> "$HOME/ran.log"\ncase "$1 $2" in\n"plugin update")\n' \
       '    echo $$ > "$HOME/child.pid"; echo waiting; sleep 30 ;;\nesac\nexit 0\n'


def nexts(err):
    return [l[len("next: "):] for l in err.splitlines() if l.startswith("next: ")]


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def seeded(h, pid, body):
    """The plugin `pid` as step 2 moves it ships `body` as its command (review 1 F2)."""
    with open(os.path.join(h.home, "seed.py"), "a") as fh:
        fh.write("\n_first = plugin\n\n\ndef plugin(home, pid, ver):\n    root = _first(home, pid, ver)\n"
                 "    if pid == %r:\n        exe = os.path.join(root, 'bin', 'agentik-' + pid.partition('@')[0])\n"
                 "        with open(exe, 'w') as fh:\n            fh.write(%r)\n        os.chmod(exe, 0o755)\n"
                 "    return root\n" % (pid, body))


def three(h):
    """murmur, paint and quill each one behind; quill's plugin update fails, so murmur and paint
    moved before the stop (review 1 F2)."""
    h.install("murmur@agentik", "1.0.0", "1.1.0")
    h.install("paint@agentik", "2.0.0", "2.1.0")
    h.install("quill@agentik", "3.0.0", "3.1.0")
    h.file(os.path.join(h.home, "fail"), "quill@agentik")


def under(err):
    """The lines under the one FAIL line."""
    lines = err.splitlines()
    fail = [i for i, l in enumerate(lines) if l.startswith("FAIL")]
    assert len(fail) == 1, err
    return lines[fail[0]], lines[fail[0] + 1:]


class Close(tu.Base):
    def test_1_a_moved_tool_holds_the_sessions_line_once_and_none_moved_none(self):
        h = self.home()
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual((out + err).count(SESSIONS), 1, out + err)
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn(SESSIONS, out + err)

    def test_2_a_tool_with_a_page_is_a_note_with_its_path_and_its_page(self):
        h = self.home(("murmur", "relay"))
        h.install("relay@agentik", "0.2.3", "0.2.4")
        h.file(os.path.join(h.bindir, "agentik-relay"), "#!/bin/sh\necho 0.2.2\n")  # a stand-in
        page = tools.page(tools.fallback(str(PLUGIN / "lib")), "relay")
        self.assertTrue(page)
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 0, out + err)
        lines = out.splitlines()
        rows = [i for i, l in enumerate(lines) if "relay" in l and "0.2.3 to 0.2.4" in l]
        self.assertEqual(len(rows), 1, out)
        row = lines[rows[0]].strip()
        self.assertTrue(row.startswith("note"), row)
        self.assertIn("~/.local/bin/agentik-relay", row)
        self.assertIn("its page has the line: " + page, lines[rows[0] + 1])
        self.assertNotRegex(out + err, r"setup (would|leaves)")
        self.assertIn(SESSIONS, out + err)

    def test_3_a_failed_step_2_places_the_moved_commands_and_says_so(self):
        h = self.home(("murmur", "paint", "quill"))
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        h.install("paint@agentik", "2.0.0", "2.1.0")
        h.install("quill@agentik", "3.0.0", "3.1.0")
        h.file(os.path.join(h.home, "fail"), "paint@agentik")
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 1, out + err)
        self.assertEqual([h.version_of(n) for n in ("murmur", "paint", "quill")], ["1.1.0", "2.0.0", "3.0.0"])
        lines = err.splitlines()
        fail = [i for i, l in enumerate(lines) if l.startswith("FAIL")]
        self.assertEqual(len(fail), 1, err)
        self.assertIn("claude plugin update paint@agentik", lines[fail[0]])
        self.assertIn("agentik-murmur 1.1.0", "\n".join(lines[fail[0] + 1:]), err)
        self.assertNotIn("agentik-paint", "\n".join(lines[fail[0] + 1:]))
        self.assertIn(SESSIONS, out + err)
        os.remove(os.path.join(h.home, "fail"))
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertIn("murmur 1.1.0, already current", out)
        self.assertIn(tu.MOVED % ("paint", "2.0.0", "2.1.0"), out)
        self.assertIn(tu.MOVED % ("quill", "3.0.0", "3.1.0"), out)
        self.assertEqual([h.version_of(n) for n in ("murmur", "paint", "quill")], ["1.1.0", "2.1.0", "3.1.0"])

    def test_4_each_next_line_runs_as_printed(self):
        h = self.home(("murmur", "paint", "quill"))
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        h.install("paint@agentik", "2.0.0")
        seen = []
        h.ps("4242 /opt/tools/relay run --row r1\n")
        seen.append(h.run("update", "--yes"))
        ps = os.path.join(h.bin, "ps")
        with open(ps) as fh:
            kept = fh.read()
        h.file(ps, "#!/bin/sh\necho 'ps: no such option' >&2\nexit 1\n")  # a list that cannot be read
        seen.append(h.run("update", "--yes"))
        h.file(ps, kept)
        h.ps("1 /sbin/launchd\n")
        seen.append(h.run("update", "quill", "--yes"))
        seen.append(h.run("update", "nosuch", "--yes"))
        h.file(os.path.join(h.home, "drop"), "murmur@agentik")
        seen.append(h.run("update", "--yes"))
        os.remove(os.path.join(h.home, "drop"))
        lines = [n for _, _, err in seen for n in nexts(err)]
        for want in (r"update$", r"setup quill$", r"setup murmur$", r"claude plugin install suite@agentik$"):
            self.assertTrue(any(re.search(want, l) for l in lines), (want, lines))
        for line in dict.fromkeys(lines):
            p = subprocess.run(["/bin/sh", "-c", line], capture_output=True, text=True, env=h.env(),
                               cwd=h.home, stdin=subprocess.DEVNULL, timeout=120)
            self.assertNotIn(p.returncode, (126, 127), (line, p.stderr))
            for word in REFUSED:
                self.assertNotIn(word, p.stdout + p.stderr, line)

    def test_5_a_tool_not_installed_and_a_name_that_is_no_tool(self):
        h = self.home(("murmur", "paint", "quill"))
        h.install("murmur@agentik", "1.0.0")
        code, out, err = h.run("update", "quill", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("everything is current", out + err)
        self.assertIn("quill is not installed", err)
        self.assertRegex(nexts(err)[0], r"setup quill$")
        code, out, err = h.run("update", "nosuch", "--yes")
        self.assertEqual(code, 2, out + err)
        self.assertIn("nosuch is no known tool", err)
        self.assertNotIn("is not a plugin name", err)

    def test_6_updates_rows_speak_of_update(self):
        h = self.home()
        h.install("murmur@agentik", "1.1.0")
        h.file(os.path.join(h.bindir, "agentik-murmur"), "#!/bin/sh\nVERSION=1.0.0\nTREE=%s\nexit 0\n"
               % os.path.join(h.home, ".local", "share", "agentik-murmur", "1.0.0"))
        code, out, err = h.run("update", "--dry-run")
        self.assertEqual(code, 0, out + err)
        self.assertIn("murmur", out)
        self.assertNotRegex(out + err, r"setup (would|leaves)")
        messages = catalogue.load()
        said = [m for m in messages if re.match(r"setup\.(launcher|suite|door)\.", m)
                and re.search(r"setup(?:'s)? (would|leaves|to place)|not setup's", messages[m])]
        self.assertTrue(said)
        for mid in said:
            self.assertIn(mid, update.SAYS)
            self.assertNotIn("setup", messages[update.SAYS[mid]], mid)
            self.assertNotIn("would", messages[update.SAYS[mid]], mid)

    def test_7_an_interrupt_names_the_command_it_stopped(self):
        h = self.home()
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        h.file(os.path.join(h.bin, "claude"), HANG)
        pidfile = os.path.join(h.home, "child.pid")
        p = subprocess.Popen([str(LAUNCHER), "update", "--yes"], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, env=h.env(), cwd=h.home,
                             stdin=subprocess.DEVNULL, start_new_session=True)
        for _ in range(200):
            if os.path.exists(pidfile) and open(pidfile).read().strip():
                break
            time.sleep(0.1)
        child = int(open(pidfile).read())
        os.killpg(p.pid, signal.SIGINT)
        out, err = p.communicate(timeout=60)
        for _ in range(50):
            if not alive(child):
                break
            time.sleep(0.1)
        self.assertFalse(alive(child), "the command still runs")
        self.assertEqual(p.returncode, 130, out + err)
        self.assertNotIn("Traceback", err)
        fail = [l for l in err.splitlines() if l.startswith("FAIL")]
        self.assertEqual(len(fail), 1, err)
        self.assertIn("interrupted", fail[0])
        self.assertIn("claude plugin update murmur@agentik", fail[0])
        self.assertNotIn("between steps", err)
        self.assertRegex(nexts(err)[-1], r"update$")
        with open(os.path.join(h.home, ".local", "state", "agentik-suite", "setup.jsonl")) as fh:
            entry = json.loads(fh.read().splitlines()[-1])
        self.assertEqual(entry["exit"], 130)
        self.assertIn({"n": 2, "command": "claude plugin update murmur@agentik", "exit": None}, entry["ran"])


    def test_8_a_missing_claude_closes_on_its_reason_and_a_command_alone(self):
        h = self.home()
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        os.remove(os.path.join(h.bin, "claude"))
        code, out, err = h.run("update", "murmur", "--yes")
        self.assertEqual(code, 2, out + err)
        lines = err.splitlines()
        self.assertEqual(len(nexts(err)), 1, err)
        line = nexts(err)[0]
        self.assertRegex(line, r"update murmur$")
        self.assertEqual(lines[-1], "next: " + line)
        self.assertIn("claude", lines[-2])
        self.assertIn("https://claude.com/claude-code", lines[-2])
        self.assertNotIn("then", line)
        p = subprocess.run(["/bin/sh", "-c", line], capture_output=True, text=True, env=h.env(),
                           cwd=h.home, stdin=subprocess.DEVNULL, timeout=120)
        self.assertEqual(p.returncode, 2, (line, p.stdout, p.stderr))  # it runs, and is blocked again
        for word in REFUSED:
            self.assertNotIn(word, p.stdout + p.stderr, line)
        # setup's own close is setup's, as it was
        self.assertEqual(catalogue.load()["hint.setup.blocked"],
                         "next: install {missing}, then {setup} --dry-run again.")

    def test_9_an_interrupt_while_placing_keeps_what_was_placed_and_its_cause(self):
        h = self.home(("murmur", "paint", "quill"))
        three(h)
        seeded(h, "paint@agentik", '#!/bin/sh\necho "$0 $*" >> "$HOME/ran.log"\n'
               'echo $$ > "$HOME/child.pid"\nsleep 30\n')
        pidfile = os.path.join(h.home, "child.pid")
        p = subprocess.Popen([str(LAUNCHER), "update", "--yes"], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, env=h.env(), cwd=h.home,
                             stdin=subprocess.DEVNULL, start_new_session=True)
        for _ in range(300):
            if os.path.exists(pidfile) and open(pidfile).read().strip():
                break
            time.sleep(0.1)
        time.sleep(0.3)
        os.killpg(p.pid, signal.SIGINT)
        out, err = p.communicate(timeout=60)
        self.assertEqual(p.returncode, 130, out + err)
        self.assertNotIn("Traceback", err)
        fail, rest = under(err)
        self.assertIn("interrupted", fail)
        self.assertIn("agentik-paint install-cli", fail)
        self.assertIn("placed before the stop: agentik-murmur 1.1.0", rest, err)
        self.assertTrue(any("claude plugin update quill@agentik" in l for l in rest), err)
        self.assertRegex(rest[-1], r"^next: .*update$")
        self.assertEqual(len(nexts(err)), 1, err)
        self.assertEqual([h.version_of(n) for n in ("murmur", "paint", "quill")], ["1.1.0", "2.0.0", "3.0.0"])
        with open(os.path.join(h.home, ".local", "state", "agentik-suite", "setup.jsonl")) as fh:
            entry = json.loads(fh.read().splitlines()[-1])
        self.assertEqual(entry["exit"], 130)
        self.assertIn({"n": 2, "command": "claude plugin update quill@agentik", "exit": 1}, entry["ran"])

    def test_10_a_placement_that_fails_is_named_under_the_fail(self):
        h = self.home(("murmur", "paint", "quill"))
        three(h)
        seeded(h, "paint@agentik", '#!/bin/sh\necho "$0 $*" >> "$HOME/ran.log"\n'
               'echo "no room on the disk"\nexit 1\n')
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 1, out + err)
        fail, rest = under(err)
        self.assertIn("claude plugin update quill@agentik", fail)  # the step 2 failure stays the FAIL
        self.assertIn("placed before the stop: agentik-murmur 1.1.0", rest, err)
        named = [l for l in rest if "agentik-paint install-cli" in l]
        self.assertEqual(len(named), 1, err)
        self.assertIn("failed", named[0])
        self.assertEqual([h.version_of(n) for n in ("murmur", "paint", "quill")], ["1.1.0", "2.0.0", "3.0.0"])

    def test_11_updates_step_1_and_step_3_rows_speak_of_update(self):
        h = self.home()
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        h.install("paint@agentik", "2.0.0", "2.1.0")
        h.file(os.path.join(h.home, "gone"), "murmur@agentik")  # a step 3 row left (review 1 F5)
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 1, out + err)
        self.assertIn("murmur@agentik", out)
        self.assertNotRegex(out + err, r"setup (would|leaves|stops)")
        os.remove(os.path.join(h.bin, "claude"))
        code, out, err = h.run("update", "--dry-run")
        self.assertEqual(code, 0, out + err)
        self.assertIn("not on PATH", out)
        self.assertNotRegex(out + err, r"setup (would|leaves|stops)")
        code, out, err = h.run("setup", "--dry-run")  # setup's own rows stay setup's
        self.assertIn("not on PATH; setup stops here until it is installed", out + err)
        messages = catalogue.load()
        said = [m for m in messages if re.match(r"setup\.(cmd|python|plugin|launcher|suite|door)\.", m)
                and re.search(r"setup(?:'s)? (would|leaves|stops|to place)|not setup's", messages[m])]
        self.assertTrue(said)
        for mid in said:
            self.assertIn(mid, update.SAYS)
            self.assertNotIn("setup", messages[update.SAYS[mid]], mid)
            self.assertNotIn("would", messages[update.SAYS[mid]], mid)

if __name__ == "__main__":
    unittest.main()
