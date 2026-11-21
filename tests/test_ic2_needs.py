"""Row ic2-needs: setup names each chosen plugin's need before the yes, and plans only what it can do.

R1: step 1 has a warn for each chosen plugin's need not met (PyYAML for respeak, Go for the relay),
before the question, and setup still runs on a yes. R2: a name the suite does not know is refused
before the plan, at the dry run too; an unset HOME is refused. R3: the doctor plans the installed
plugins, and the default ones not installed are one note that never makes the close setup.
R4: a default install's doctor reads as at the pin.

Each screen runs in a temp HOME, PATH `~/.local/bin`, a folder with a stub `claude` (the plan
tests' stub, which installs the made-up plugin files) and a stand-in `python3`, then /usr/bin:/bin;
the suite starts as `./setup` from the clone's folder. Nothing here starts the real `claude` or
writes outside its temp folder."""
import json
import os
import pty
import select
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import CLAUDE_STUB, PLUGIN_BIN  # noqa: E402
from agentik_suite import catalogue, plan  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "plugins" / "suite" / "lib"
SYSTEM = "/usr/bin:/bin"
MESSAGES = catalogue.load()
# a Python with no third-party module: no user site, no PYTHONPATH
NO_YAML = '#!/bin/sh\nexec /usr/bin/python3 -I "$@"\n'
WITH_YAML = '#!/bin/sh\nPYTHONPATH=%s exec /usr/bin/python3 -s "$@"\n'
# the doctor's suite checks after a default install at the pin 17f4ed5, the door's own row aside
PIN_CHECKS = [("ok", "shadow"), ("ok", "settings"), ("ok", "prereqs claude"), ("ok", "prereqs git"),
              ("ok", "prereqs python3"), ("ok", "marketplace agentik"),
              ("ok", "plugin session@agentik"), ("ok", "plugin decisions@agentik"),
              ("ok", "plugin agents@agentik"), ("ok", "launcher ~/.local/bin/agentik-session"),
              ("ok", "launcher ~/.local/bin/agentik-decisions"),
              ("ok", "launcher ~/.local/bin/agentik-agents"), ("ok", "suite ~/.local/bin/agentik-suite"),
              ("ok", "door ~/.local/bin/agentik"), ("ok", "path ~/.local/bin")]


# row ak10c5-table-gone R8: a default install's stand-ins that answer `describe` as the suite's
# tools do, each with its own name, so the doctor reads them as at the pin, when the table spared
# them the ask; the shared PLUGIN_BIN stays silent for every other test
DESCRIBING_BIN = PLUGIN_BIN.replace("doctor) exit 0 ;;", (
    "doctor) exit 0 ;;\n"
    "describe) printf '{\"schema\": \"agentik.describe/1\", \"ok\": true, \"tool\": \"%s\", "
    "\"version\": \"1.0.0\", \"summary\": \"A stand-in.\", \"repo\": \"acme/stand-in\", "
    "\"plugin\": null, \"needs\": [], \"verbs\": [{\"name\": \"install-cli\", "
    "\"summary\": \"Place the launcher.\", \"top\": false}], \"reads\": []}\\n' "
    "\"${0##*/agentik-}\" ;;"))


class Home(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="ic2-")
        self.addCleanup(tmp.cleanup)
        self.home = os.path.realpath(tmp.name)
        self.stubs = os.path.join(self.home, "stubs")
        os.mkdir(self.stubs)
        self.bindir = os.path.join(self.home, ".local", "bin")
        template = os.path.join(self.home, "plugin-bin")
        self.stub("plugin-bin", PLUGIN_BIN, at=template)
        self.stub("claude", CLAUDE_STUB % template)
        self.stub("python3", NO_YAML)

    def stub(self, name, body, at=None):
        path = at or os.path.join(self.stubs, name)
        with open(path, "w") as fh:
            fh.write(body)
        os.chmod(path, 0o755)

    def with_yaml(self):
        """The stand-in `python3` finds a module named yaml."""
        site = os.path.join(self.home, "site")
        os.makedirs(os.path.join(site, "yaml"))
        open(os.path.join(site, "yaml", "__init__.py"), "w").close()
        self.stub("python3", WITH_YAML % site)

    def env(self):
        return {"HOME": self.home, "PATH": self.bindir + ":" + self.stubs + ":" + SYSTEM,
                "XDG_CACHE_HOME": os.path.join(self.home, "cache")}

    def run_both(self, argv, env=None):
        # a command but ./setup stands in a folder of no repository: doctor's records row reads no real config (rr2)
        p = subprocess.run(argv, cwd=str(ROOT) if argv[0] == "./setup" else tempfile.gettempdir(), env=env or self.env(), stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=300)
        return p.returncode, p.stdout

    def on_pty(self, answer, *args):
        master, slave = pty.openpty()
        p = subprocess.Popen(["./setup", *args], cwd=str(ROOT), stdin=slave, stdout=slave,
                             stderr=slave, env=self.env(), close_fds=True)
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

    def need_lines(self, text):
        return [l for l in text.splitlines() if "PyYAML" in l]

    def installed(self):
        with open(os.path.join(self.home, ".claude", "plugins", "installed_plugins.json")) as fh:
            return sorted(json.load(fh)["plugins"])

    def paste(self, line):
        """A close as printed, `~` read as HOME, run with --yes."""
        words = [self.home + w[1:] if w.startswith("~/") else w for w in line.split()]
        return self.run_both(words + ["--yes"])

    @property
    def market(self):
        return os.path.join(self.home, ".claude", "plugins", "known_marketplaces.json")


class NeedTest(Home):
    def test_r1_public_json_names_respeaks_need(self):
        with open(str(LIB / "public.json")) as fh:  # re-based (ak10c5 R4)
            table = json.load(fh)
        self.assertEqual(table["needs"]["respeak"], ["PyYAML"])
        self.assertEqual(table["needs"]["relay"], ["Go"])

    def test_r1_the_dry_run_names_the_need_in_step_1(self):
        code, text = self.run_both(["./setup", "--dry-run", "respeak"])
        self.assertEqual(code, 0, text)
        rows = self.need_lines(text)
        self.assertEqual(len(rows), 1, text)
        self.assertIn("respeak", rows[0])
        self.assertTrue(rows[0].split()[0] in ("warn", "!"), rows[0])
        lines = text.splitlines()
        self.assertLess(lines.index(rows[0]), next(i for i, l in enumerate(lines) if "agentik-dev/" in l))
        code, out = self.run_both(["./setup", "--dry-run", "--json", "respeak"])
        steps = [s for s in json.loads(out)["steps"] if s["id"] == "need"]
        self.assertEqual([(s["n"], s["state"], s["subject"]) for s in steps], [(1, "warn", "PyYAML")])
        self.assertIsNone(steps[0]["command"])

    def test_r1_the_run_shows_it_before_the_question_and_goes_on(self):
        code, text = self.on_pty("n", "respeak")
        self.assertNotEqual(code, 0, text)
        ask = text.index("Run these")
        self.assertTrue(self.need_lines(text[:ask]), text)
        code, text = self.run_both(["./setup", "--yes", "respeak"])
        self.assertEqual(code, 0, text)
        self.assertIn("ran: claude plugin install respeak@agentik, exit 0", text)
        self.assertTrue(self.need_lines(text), text)

    def test_r1_with_the_module_there_no_row(self):
        self.with_yaml()
        code, text = self.run_both(["./setup", "--dry-run", "respeak"])
        self.assertEqual(code, 0, text)
        self.assertEqual(self.need_lines(text), [], text)

    def test_r1_the_default_set_names_no_need(self):
        code, text = self.run_both(["./setup", "--dry-run"])
        self.assertEqual(code, 0, text)
        self.assertNotIn("PyYAML", text)

    def test_r1_go_for_the_relay(self):
        env = {"HOME": self.home, "PATH": self.stubs}
        rows = [s for s in plan.build(["relay"], env, str(LIB), "agentik-suite", "0.0.1") if s["id"] == "need"]
        self.assertEqual([(s["subject"], s["values"]["name"]) for s in rows], [("Go", "relay")])
        self.stub("go", "#!/bin/sh\nexit 0\n")
        rows = [s for s in plan.build(["relay"], env, str(LIB), "agentik-suite", "0.0.1") if s["id"] == "need"]
        self.assertEqual(rows, [])

    def test_f2_the_row_says_what_was_read(self):
        code, text = self.run_both(["./setup", "--dry-run", "respeak"])
        self.assertIn("the python3 first on PATH has no PyYAML; setup goes on without it",
                      self.need_lines(text)[0])

    def test_r1_the_message(self):
        text = MESSAGES["setup.need.missing"]
        self.assertIn("{name}", text)
        self.assertLessEqual(len(text.replace("{name}", "")), 76)


class RefuseTest(Home):
    def test_r2_a_name_no_plugin_holds_is_refused(self):
        for argv in (["--dry-run", "nosuch"], ["--yes", "nosuch"], ["nosuch"], ["--dry-run", "--json", "nosuch"]):
            code, text = self.run_both(["./setup"] + argv)
            self.assertEqual(code, 2, (argv, text))
            self.assertIn("nosuch", text)
            self.assertNotIn("Setup plan", text)
            self.assertFalse(os.path.exists(self.market), argv)
        code, text = self.run_both(["./setup", "--dry-run", "nosuch"])
        self.assertIn("no plugin", text.splitlines()[0].lower())
        self.assertTrue(text.splitlines()[-1].startswith("next: "), text)

    def test_r2_a_known_name_and_a_wrong_one_together(self):
        code, text = self.run_both(["./setup", "--dry-run", "respeak", "nosuch"])
        self.assertEqual(code, 2, text)
        self.assertNotIn("respeak@agentik", text)

    def test_r2_home_unset_is_refused(self):
        env = self.env()
        del env["HOME"]
        for argv in (["--dry-run"], ["--yes"], ["--dry-run", "respeak"]):
            code, text = self.run_both(["./setup"] + argv, env)
            self.assertEqual(code, 2, (argv, text))
            self.assertIn("HOME", text)
            self.assertNotIn(".local/bin", text)
        env["HOME"] = ""
        code, text = self.run_both(["./setup", "--dry-run"], env)
        self.assertEqual(code, 2, text)


class DoctorTest(Home):
    def doctor(self, *args):
        return self.run_both([os.path.join(self.bindir, "agentik-suite"), "doctor"] + list(args))

    def test_r3_after_one_plugin_the_absent_defaults_are_one_note(self):
        code, text = self.run_both(["./setup", "--yes", "respeak"])
        self.assertEqual(code, 0, text)
        code, text = self.doctor()
        self.assertNotIn("setup", text.splitlines()[-1], text)
        notes = [l for l in text.splitlines() if "session" in l and "decisions" in l and "agents" in l]
        self.assertEqual(len(notes), 1, text)
        self.assertTrue(notes[0].split()[0] in ("note", "·"), notes[0])
        self.assertNotIn("not installed: session@agentik", text)
        code, out = self.doctor("--json")
        checks = json.loads(out)["tools"][0]["checks"]
        absent = [c for c in checks if c["status"] == "note"]
        self.assertEqual(len(absent), 1, checks)
        self.assertIsNone(absent[0]["remedy"])
        names = [c["name"] for c in checks]
        self.assertIn("plugin respeak@agentik", names)
        self.assertNotIn("plugin session@agentik", names)
        self.assertNotIn("need PyYAML", names)  # its own doctor names it (R1)

    def test_r4_a_default_install_reads_as_at_the_pin(self):
        self.stub("plugin-bin", DESCRIBING_BIN, at=os.path.join(self.home, "plugin-bin"))  # ak10c5 R8
        code, text = self.run_both(["./setup", "--yes"])
        self.assertEqual(code, 0, text)
        code, out = self.doctor("--json")
        checks = json.loads(out)["tools"][0]["checks"]
        self.assertEqual([(c["status"], c["name"]) for c in checks[1:]], PIN_CHECKS)
        code, text = self.doctor()
        self.assertNotIn("next:", text)

    def mended(self, broken, chosen):
        """Review 1 F1: after `setup --yes <chosen>` and `broken`, the doctor's row and its close
        name `setup` with the chosen names; the close pasted with --yes mends the row and installs
        no plugin that was not there."""
        code, text = self.run_both(["./setup", "--yes"] + chosen)
        self.assertEqual(code, 0, text)
        before = self.installed()
        broken()
        code, text = self.doctor()
        close = text.splitlines()[-1]
        want = " setup " + " ".join(chosen)
        self.assertTrue(close.startswith("next: ") and close.endswith(want), text)
        code, out = self.doctor("--json")
        rows = [c for c in json.loads(out)["tools"][0]["checks"] if c["status"] in ("warn", "fail")
                and c["remedy"] and " setup" in c["remedy"] and not c["name"].startswith("door")]
        self.assertTrue(rows, out)
        for c in rows:
            self.assertTrue(c["remedy"].endswith(want), c)
        code, text = self.paste(close[len("next: "):])
        self.assertEqual(code, 0, text)
        self.assertEqual(self.installed(), before, text)
        return self.doctor()[1]

    def test_f1_a_chosen_plugins_launcher_gone(self):
        launcher = os.path.join(self.bindir, "agentik-respeak")
        text = self.mended(lambda: os.remove(launcher), ["respeak"])
        self.assertTrue(os.path.exists(launcher))
        self.assertNotIn("not placed", text)

    def test_f1_a_chosen_plugins_folder_gone(self):
        folder = os.path.join(self.home, ".claude", "plugins", "cache", "agentik", "session")
        text = self.mended(lambda: shutil.rmtree(folder), ["session", "respeak"])
        self.assertTrue(os.path.isdir(folder))
        self.assertNotIn("folder gone", text)


class ScreenTest(Home):
    """Review 1 lead 1: the bare command's close plans what the doctor plans."""
    def screen(self, exe=None):
        code, text = self.run_both([exe or os.path.join(self.bindir, "agentik-suite")])
        self.assertEqual(code, 0, text)
        return text.splitlines()[-1]

    def test_lead1_after_one_plugin_the_close_names_it(self):
        code, text = self.run_both(["./setup", "--yes", "respeak"])
        self.assertEqual(code, 0, text)
        before = self.installed()
        self.assertFalse(self.screen().endswith(" setup"))
        os.remove(os.path.join(self.bindir, "agentik-respeak"))
        close = self.screen()
        self.assertTrue(close.startswith("next: ") and close.endswith(" setup respeak"), close)
        code, text = self.paste(close[len("next: "):])
        self.assertEqual(code, 0, text)
        self.assertEqual(self.installed(), before, text)

    def test_lead1_the_default_set_or_none_as_at_the_pin(self):
        none = self.screen(str(ROOT / "plugins" / "suite" / "bin" / "agentik-suite"))
        self.assertTrue(none.endswith(" setup"), none)
        code, text = self.run_both(["./setup", "--yes"])
        self.assertEqual(code, 0, text)
        self.assertTrue(self.screen().endswith(" doctor"))


if __name__ == "__main__":
    unittest.main()
