"""Row sc5-first-screen: bare `agentik` is a first screen of ten lines that names the tools, `help`
is the full list, `help <verb>` shows examples, and doctor's close never offers a remedy that
answers a question for the person or removes.

Each screen runs in a temp HOME under a bare environment. The empty home has a stub `claude`, then
/usr/bin:/bin, the suite started by its launcher's path. The finished home has steps 1 to 5 ok,
the door in ~/.local/bin on PATH, three stub tools with made-up names (`murmur` answers `describe
--json`, `paint` and `quill` print nothing) and a plugin `sketch` installed with no command.
Nothing here starts the real `claude` or writes outside its temp folder."""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_sc10_doctor_checks import Checks  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "plugins" / "suite" / "lib"
LAUNCHER = ROOT / "plugins" / "suite" / "bin" / "agentik-suite"
MANIFEST = ROOT / "plugins" / "suite" / ".claude-plugin" / "plugin.json"
CATALOGUE = LIB / "agentik_suite" / "messages.md"
sys.path.insert(0, str(LIB))
from agentik_suite import catalogue, cli  # noqa: E402

SYSTEM = "/usr/bin:/bin"
DESCRIBE = {"schema": "agentik.describe/1", "ok": True, "tool": "murmur", "version": "1.7.1",
            "summary": "Whisper each change to the log.", "repo": "acme/murmur",
            "plugin": "murmur@agentik", "needs": [], "verbs": [], "reads": []}
SHARED = "--json  -q/--quiet  --no-color"
# The pin's (2fd5a80) ids a ruling keeps byte for byte (R7): sc1-voice-sweep owns them.
KEPT = re.compile(r"^(verb|flag|usage)\.")
PIN_KEPT = (33, "6bdf3fd25ecfc090c92561e5c9dcbf78e097c442448e2a60ada3e96bd9ab96f3")  # at 2fd5a80
NEW = ("help.row.setup", "help.row.doctor", "help.row.config", "help.row.status", "help.row.help",
       "help.row.tool", "help.row.tool.none", "help.row.help.all", "help.more", "help.usage.tool",
       "help.tools", "help.tools.none", "help.tool.bare", "help.eg.setup", "help.eg.setup_dry",
       "help.eg.setup_names", "help.eg.config", "help.eg.config_tool", "help.eg.config_key",
       "help.eg.help", "help.eg.help_verb", "help.eg.help_tool", "help.also")


def executable(path, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(body)
    os.chmod(path, 0o755)
    return path


class Homes(unittest.TestCase):
    def setUp(self):
        self.home = os.path.realpath(tempfile.mkdtemp(prefix="sc5-"))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.stubs = os.path.join(self.home, "stub")
        executable(os.path.join(self.stubs, "claude"), "#!/bin/sh\nexit 0\n")
        self.bindir = os.path.join(self.home, ".local", "bin")

    def empty(self):
        return {"HOME": self.home, "PATH": self.stubs + ":" + SYSTEM}

    def finished(self):
        plugins = os.path.join(self.home, ".claude", "plugins")
        os.makedirs(plugins)
        with open(os.path.join(plugins, "known_marketplaces.json"), "w") as fh:
            json.dump({"agentik": {}}, fh)
        table = {}
        deps = [d["name"] if isinstance(d, dict) else d
                for d in json.loads(MANIFEST.read_text())["dependencies"]]
        for dep in deps + ["sketch"]:
            folder = os.path.join(self.home, "inst", dep)
            os.makedirs(folder)
            table["%s@agentik" % dep] = [{"version": "1.0.0", "installPath": folder}]
        with open(os.path.join(plugins, "installed_plugins.json"), "w") as fh:
            json.dump({"plugins": table}, fh)
        p = subprocess.run([str(LAUNCHER), "install-cli"], cwd=self.home, env=self.empty(),
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        tools = os.path.join(self.home, "tools")
        executable(os.path.join(tools, "agentik-murmur"),
                   "#!/bin/sh\n[ \"$1\" = describe ] && cat <<'EOF'\n%s\nEOF\nexit 0\n" % json.dumps(DESCRIBE))
        executable(os.path.join(tools, "agentik-paint"), "#!/bin/sh\nexit 0\n")
        executable(os.path.join(tools, "agentik-quill"), "#!/bin/sh\nexit 0\n")
        return {"HOME": self.home, "PATH": ":".join([self.bindir, tools, self.stubs, SYSTEM])}

    def run_(self, argv, env, code=0):
        p = subprocess.run(argv, cwd=self.home, env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, code, p.stdout + p.stderr)
        return p.stdout, p.stderr

    def suite(self, *words, env, code=0):
        return self.run_([str(LAUNCHER)] + list(words), env, code)

    def door(self, *words, env):
        return self.run_([os.path.join(self.bindir, "agentik")] + list(words), env)

    def pin_hint(self, env, *words):
        """The close the pin's sm2 gives: the plan read as do_help reads it."""
        out, err = self.suite(*words, env=env)
        return err.splitlines()[-1]


class FirstScreenTest(Homes):
    def test_a1_empty_no_word(self):
        out, err = self.suite(env=self.empty())
        lines = (out + err).splitlines()
        self.assertLessEqual(len(lines), 10, out + err)
        rows = out.splitlines()
        self.assertTrue(rows[-1].lstrip().startswith("<tool>"), out)
        self.assertTrue(rows[-1].endswith("none is installed yet"), out)
        self.assertEqual(err, "next: %s setup\n" % str(LAUNCHER).replace(self.home, "~"))
        self.assertIn("one command for the agentik tools", rows[0])

    def test_a2_finished_no_word(self):
        env = self.finished()
        for out, err in (self.suite(env=env), self.door(env=env)):
            lines = (out + err).splitlines()
            self.assertLessEqual(len(lines), 10, out + err)
            last = out.splitlines()[-1]
            self.assertTrue(last.endswith("run a tool: murmur, paint, quill"), out)
            self.assertNotIn("sketch", out + err)
            self.assertNotIn("/", out + err)
            self.assertEqual(err, "next: agentik doctor\n")
            words = [l.split()[0] for l in out.splitlines()[2:]]
            self.assertEqual(words, ["setup", "doctor", "config", "status", "help", "<tool>"], out)
            self.assertIn("the watchers, sessions, gate, backlog and runs on one screen", out)

    def test_a3_no_process(self):
        def refuse(*args, **kwargs):
            raise OSError("no process may start: %r" % (args,))
        for env in (self.empty(), self.finished()):
            out, err = io.StringIO(), io.StringIO()
            with mock.patch("subprocess.Popen", side_effect=refuse):
                code = cli.main([], env=dict(env), out=out, err=err)
            self.assertEqual(code, 0, err.getvalue())
            self.assertIn("<tool>", out.getvalue())
            self.assertIn("next: ", err.getvalue())

    def test_a5_the_first_screen_is_not_the_list(self):
        env = self.finished()
        first = "".join(self.suite(env=env))
        full = "".join(self.suite("help", env=env))
        self.assertNotIn("usage:", first)
        self.assertNotIn("tools", first.split("\n"))
        self.assertIn("usage:", full)
        self.assertIn("tools", full.splitlines())

    def test_r1_quiet_first_screen(self):
        out, err = self.suite("-q", env=self.empty())
        self.assertEqual(err, "")
        self.assertIn("<tool>", out)


class FullListTest(Homes):
    def test_a4_help_h_and_help_are_one_screen(self):
        env = self.finished()
        screens = [self.suite(w, env=env) for w in ("help", "-h", "--help")]
        self.assertEqual(screens[0], screens[1])
        self.assertEqual(screens[0], screens[2])
        out, err = screens[0]
        self.assertNotIn(self.home, out + err)
        lines = out.splitlines()
        self.assertIn("one command for the agentik tools", lines[0])
        self.assertEqual(lines[1], "usage: agentik <verb> [<name>...] [flags]")
        self.assertEqual(lines[2], "       agentik <tool> [<its words>...]")
        order = [lines.index(t) for t in ("verbs", "tools")]
        self.assertLess(order[0], order[1])
        self.assertTrue(lines[-1].startswith("flags  "), out)
        self.assertEqual(lines[-1].split(None, 1)[1].strip(), "--json  -q/--quiet  --no-color  -h/--help")
        verbs = lines[order[0] + 1:order[1]]
        self.assertEqual([r.split()[0] for r in verbs if r.strip()],
                         ["setup", "doctor", "config", "status", "help", "more"])
        more = [r for r in verbs if r.split()[:1] == ["more"]][0]
        for verb in ("version", "describe", "install-cli"):
            self.assertIn(verb, more.split())
        tools = {r.split()[0]: r.split(None, 1)[1:] for r in lines[order[1] + 1:] if r.startswith("  ")}
        self.assertEqual(tools["murmur"][0].split(None, 1), ["1.7.1", "Whisper each change to the log."])
        self.assertEqual(tools["paint"], [])
        self.assertEqual(tools["sketch"], ["a plugin with no command"])
        self.assertNotIn("suite", tools)
        self.assertEqual(err, "next: agentik doctor\n")

    def test_r4_empty_list_has_no_tool(self):
        out, err = self.suite("help", env=self.empty())
        lines = out.splitlines()
        at = lines.index("tools")
        self.assertEqual(lines[at + 1].strip(), "none is installed yet")
        self.assertTrue(lines[2].strip().startswith("agentik-<tool> [<its words>...]"), out)

    def test_a8_json_tools(self):
        env = self.finished()
        for words in ((), ("help",)):
            out, err = self.suite("--json", *words, env=env)
            obj = json.loads(out)
            self.assertEqual(list(obj), ["schema", "ok", "tool", "version", "verbs", "flags",
                                         "on_path", "tools"])
            tools = {t["name"]: t for t in obj["tools"]}
            self.assertEqual(tools["murmur"], {"name": "murmur", "version": "1.7.1",
                                               "summary": "Whisper each change to the log.",
                                               "command": True})
            self.assertEqual(tools["paint"], {"name": "paint", "version": None, "summary": None,
                                              "command": True})
            self.assertEqual(tools["sketch"], {"name": "sketch", "version": None, "summary": None,
                                               "command": False})
            self.assertNotIn("suite", tools)

    def test_a8_other_keys_keep_the_pin(self):
        """The verbs' summaries and usages are the pin's catalogue words (R7 keeps them)."""
        env = self.finished()
        obj = json.loads(self.suite("--json", env=env)[0])
        self.assertEqual(obj["schema"], "agentik.help/1")
        self.assertEqual(obj["flags"], ["--json", "--quiet", "--no-color", "--help"])
        self.assertEqual([v["name"] for v in obj["verbs"]], list(cli.VERBS))
        self.assertEqual(obj["verbs"][0]["summary"],
                         "List the verbs, the flags and the agentik commands on PATH.")
        self.assertEqual([e["name"] for e in obj["on_path"]],
                         ["agentik-suite", "agentik-murmur", "agentik-paint", "agentik-quill"])


class VerbHelpTest(Homes):
    def examples(self, out):
        """The rows between the first blank and the second."""
        blocks = out.split("\n\n")
        return [l for l in blocks[1].splitlines() if l.strip()] if len(blocks) > 2 else []

    def test_a6_three_examples_each(self):
        env = self.finished()
        for verb in ("setup", "config", "help"):
            out, err = self.suite("help", verb, env=env)
            self.assertEqual(err, "", verb)
            rows = self.examples(out)
            self.assertEqual(len(rows), 3, out)
            for row in rows:
                self.assertTrue(row.strip().startswith("agentik " + verb), row)
            for row in rows:
                if "<" in row:
                    continue
                line = re.split(r"  +", row.strip())[0]
                p = subprocess.run(["/bin/sh", "-c", line], cwd=self.home, env=env,
                                   stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
                self.assertNotEqual(p.returncode, 127, line)
            also = [l for l in out.splitlines() if l.split()[:1] == ["also"]]
            self.assertEqual(len(also), 1, out)
            self.assertEqual(also[0].split(None, 1)[1].strip(), SHARED)
            self.assertNotIn("--json", out.replace(also[0], ""))

    def test_a7_no_example(self):
        env = self.finished()
        for verb in ("doctor", "version", "status"):
            out, err = self.suite("help", verb, env=env)
            self.assertEqual(err, "", verb)
            lines = out.splitlines()
            self.assertTrue(lines[0].startswith("usage: "), out)
            self.assertEqual(lines[1], cli.term.Term(env={}).text("verb." + verb))
            self.assertEqual(lines[2], "")
            self.assertEqual(lines[3], "flags", out)
            self.assertEqual(out.count("\n\n"), 1, out)
            self.assertEqual(lines[-1].split(None, 1), ["also", SHARED])

    def test_r5_hint_verb_leaves(self):
        self.assertNotIn("hint.verb", catalogue.load())


class CatalogueTest(unittest.TestCase):
    def test_a9_kept_ids_and_bounds(self):
        now = catalogue.load()
        kept = sorted((k, v) for k, v in now.items() if KEPT.match(k))
        self.assertEqual((len(kept), hashlib.sha256("".join("%s\t%s\n" % kv for kv in kept).encode())
                          .hexdigest()), PIN_KEPT)
        for mid in ("help.path", "help.path.none", "hint.verb"):
            self.assertNotIn(mid, now)
        for mid in NEW + ("help.title",):
            self.assertIn(mid, now)
            before = now[mid].split("{")[0]
            self.assertLessEqual(len(before), 76, mid)
            self.assertNotIn("setting", now[mid], mid)
            self.assertNotIn("/", now[mid], mid)


class DoctorCloseTest(Checks):
    def close(self, remedy, status="fail"):
        path = self.ready()
        checks = self.ok_checks(1) + [{"name": "reset", "status": status, "detail": "the log is stale",
                                       "remedy": remedy}]
        self.tool("murmur", self.answer_of("murmur", checks), code=1 if status == "fail" else 0)
        code, out, err = self.screen(PATH=path)
        return out, err

    def stands(self, remedy, status="fail"):
        """Review 1 F1: the close names the tool's own doctor through the door, the line that runs;
        `agentik doctor murmur` exits 2 (doctor takes no name)."""
        out, err = self.close(remedy, status)
        self.assertEqual(err.splitlines()[-1], "next: agentik murmur doctor", remedy)
        self.assertIn("fix: " + remedy, [l.strip() for l in out.splitlines()], out)

    def test_r8_a_remedy_that_answers_stays_on_its_row(self):
        self.stands("agentik-murmur reset --yes")

    def test_r8_a_remedy_that_removes_stays_on_its_row(self):
        self.stands("agentik-murmur remove stale-log")

    def test_r8_a_warned_remedy_that_answers_stays_on_its_row(self):
        self.stands("agentik-murmur reset -y", status="warn")

    def test_r8_a_write_stays_the_close(self):
        out, err = self.close("agentik-murmur install-cli")
        self.assertEqual(err.splitlines()[-1], "next: agentik-murmur install-cli")


class DoctorClosePasteTest(Homes):
    def test_f1_the_close_runs_when_pasted(self):
        """Review 1 F1: in the finished home, a tool's check that fails with a remedy that answers
        for the person closes on a line that, pasted under `sh -c`, neither exits 2 nor 127."""
        env = self.finished()
        answer = json.dumps({"schema": "agentik.doctor/1", "ok": True, "tool": "murmur", "failed": 1,
                             "warned": 0, "checks": [{"name": "reset", "status": "fail",
                                                      "detail": "the log is stale",
                                                      "remedy": "agentik-murmur reset --yes"}]})
        executable(os.path.join(self.home, "tools", "agentik-murmur"),
                   "#!/bin/sh\n[ \"$1\" = describe ] && cat <<'EOF'\n%s\nEOF\n"
                   "[ \"$1\" = doctor ] && [ \"$2\" = --json ] && cat <<'EOF' && exit 1\n%s\nEOF\n"
                   "exit 0\n" % (json.dumps(DESCRIBE), answer))
        p = subprocess.run([os.path.join(self.bindir, "agentik"), "doctor"], cwd=self.home, env=env,
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        last = p.stderr.splitlines()[-1]
        self.assertTrue(last.startswith("next: "), p.stderr)
        line = last[len("next: "):]
        q = subprocess.run(["/bin/sh", "-c", line], cwd=self.home, env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=120)
        self.assertNotIn(q.returncode, (2, 127), "%s: %s%s" % (line, q.stdout, q.stderr))


if __name__ == "__main__":
    unittest.main()
