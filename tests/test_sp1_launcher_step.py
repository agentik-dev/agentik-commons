"""Row sp1-launcher-step: setup's step 4 plans `install-cli` only for a plugin whose command takes
it. A command whose counted `describe --json` lists no `install-cli` verb runs from the plugin's
own folder: its step 4 reads ok, `setup.launcher.inplace`, and step 7 names its doctor there."""
import json
import os
import shlex
import sys
import time
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LIB, Home, version  # noqa: E402
from agentik_suite import doctor, plan, tools  # noqa: E402

DESCRIBE = {"schema": "agentik.describe/1", "ok": True, "tool": "%s", "version": "1.0.0",
            "summary": "A made-up tool for the tests.", "repo": "example/agentik-%s",
            "plugin": "%s@agentik", "needs": [], "verbs": [], "reads": []}

# a command in the plug's shape: it answers describe, doctor and config, and exits 2 on the rest
COMMAND = """#!/bin/sh
echo "$*" >> "%(calls)s"
case "$1 $2" in
"describe --json") printf '%%s\\n' '%(answer)s' ;;
"doctor "*) exit 0 ;;
"config "*) exit 0 ;;
*) echo "usage: agentik-%(name)s describe --json | doctor | config" >&2; exit 2 ;;
esac
"""
SILENT = {
    "exit2": "#!/bin/sh\necho usage >&2\nexit 2\n",
    "garbage": "#!/bin/sh\necho 'not json at all {'\n",
    "hang": "#!/bin/sh\nexec sleep 30\n",
}


def answer(name, verbs):
    obj = json.loads(json.dumps(DESCRIBE).replace("%s", name))
    obj["verbs"] = [{"name": v, "summary": "The %s verb." % v, "top": False} for v in verbs]
    return json.dumps(obj)


class LauncherStepTest(Home):
    def setUp(self):
        Home.setUp(self)
        self.table = {}

    @property
    def bindir(self):
        return os.path.join(self.home, ".local", "bin")

    def source(self, name):
        return os.path.join(self.home, ".claude", "plugins", "cache", "agentik", name, "1.0.0",
                            "bin", "agentik-" + name)

    def plugin(self, name, body):
        """`<name>@agentik` installed at 1.0.0, its bin/agentik-<name> the body given."""
        src = self.source(name)
        os.makedirs(os.path.dirname(src))
        with open(src, "w") as fh:
            fh.write(body)
        os.chmod(src, 0o755)
        self.table[name + "@agentik"] = [{"scope": "user", "version": "1.0.0",
                                          "installPath": os.path.dirname(os.path.dirname(src))}]
        d = os.path.join(self.home, ".claude", "plugins")
        with open(os.path.join(d, "known_marketplaces.json"), "w") as fh:
            json.dump({"agentik": {}}, fh)
        with open(os.path.join(d, "installed_plugins.json"), "w") as fh:
            json.dump({"version": 2, "plugins": self.table}, fh)
        return src

    def tool(self, name, verbs):
        return self.plugin(name, COMMAND % {"calls": self.calls + "-" + name, "name": name,
                                            "answer": answer(name, verbs)})

    def called(self, name):
        path = self.calls + "-" + name
        if not os.path.exists(path):
            return []
        with open(path) as fh:
            return fh.read().splitlines()

    def place(self, exe, body):
        os.makedirs(self.bindir, exist_ok=True)
        with open(os.path.join(self.bindir, exe), "w") as fh:
            fh.write(body)
        os.chmod(os.path.join(self.bindir, exe), 0o755)

    def build(self, *names, **more):
        return plan.build(list(names), self.env(**more), str(LIB), "agentik-suite", version())

    def step(self, steps, n, name):
        found = [s for s in steps if s["n"] == n and s["subject"].endswith("agentik-" + name)]
        self.assertEqual(len(found), 1, steps)
        return found[0]

    def today(self, name):
        """Today's step 4 for a plugin whose command is there and whose launcher is not placed."""
        return plan._step(4, "launcher", "todo", "~/.local/bin/agentik-" + name, "setup.launcher.missing",
                          "%s install-cli" % shlex.quote(self.source(name)))

    # line 1
    def test_l1_a_command_with_no_install_cli_runs_in_place(self):
        src = self.tool("murmur", ["describe", "doctor", "config"])
        steps = self.build("murmur")
        four = self.step(steps, 4, "murmur")
        self.assertEqual((four["state"], four["mid"], four["command"]), ("ok", "setup.launcher.inplace", None))
        self.assertFalse([s for s in steps if "install-cli" in (s["command"] or "") and src in s["command"]],
                         steps)
        seven = self.step(steps, 7, "murmur")  # R4: its doctor, from the plugin's own folder
        self.assertEqual((seven["state"], seven["mid"], seven["command"], seven["line"]),
                         ("todo", "setup.doctor.todo", "%s doctor" % shlex.quote(src), "later"))
        self.assertEqual(self.called("murmur"), ["describe --json"])

    # line 2
    def test_l2_a_command_that_lists_install_cli_keeps_todays_step(self):
        self.tool("murmur", ["describe", "doctor", "config"])
        self.tool("paint", ["paint", "doctor", "describe", "install-cli"])
        steps = self.build("murmur", "paint")
        self.assertEqual(self.step(steps, 4, "paint"), self.today("paint"))
        self.assertEqual(self.step(steps, 4, "murmur")["mid"], "setup.launcher.inplace")
        self.assertEqual(self.step(steps, 7, "paint")["mid"], "setup.doctor.wait")

    # line 3
    def test_l3_a_command_that_answers_nothing_keeps_todays_step(self):
        for kind, body in sorted(SILENT.items()):
            self.plugin(kind, body)
        start = time.monotonic()
        steps = self.build(*sorted(SILENT))
        took = time.monotonic() - start
        for kind in SILENT:
            self.assertEqual(self.step(steps, 4, kind), self.today(kind), kind)
            self.assertEqual(self.step(steps, 7, kind)["mid"], "setup.doctor.wait", kind)
        self.assertLess(took, tools.WALL + 1.0)

    def test_l3_a_placed_launcher_starts_nothing(self):
        self.tool("paint", ["paint", "describe", "install-cli"])
        self.place("agentik-paint", "#!/bin/sh\nVERSION=1.0.0\n")
        four = self.step(self.build("paint"), 4, "paint")
        self.assertEqual(four["mid"], "setup.launcher.ok")
        self.assertEqual(self.called("paint"), [])

    def test_l3_an_answer_is_read_from_the_cache_while_the_command_holds(self):
        self.tool("murmur", ["describe", "doctor", "config"])
        self.build("murmur")
        steps = self.build("murmur")
        self.assertEqual(self.step(steps, 4, "murmur")["mid"], "setup.launcher.inplace")
        self.assertEqual(self.called("murmur"), ["describe --json"])

    # line 4
    def ready(self):
        """Steps 1 to 6 ready but step 4: claude on PATH, the suite's launcher and the door placed."""
        self.place("agentik-suite", "#!/bin/sh\nVERSION=%s\n" % version())
        self.place("agentik", "#!/bin/sh\n")
        return {"PATH": "%s:%s:/usr/bin:/bin" % (self.stubs, self.bindir)}

    def test_l4_setup_dry_run_reads_as_nothing_to_do(self):
        more = self.ready()
        self.tool("paint", ["paint", "describe", "install-cli"])
        self.place("agentik-paint", "#!/bin/sh\nVERSION=1.0.0\n")
        code, out, err = self.run_cli("setup", "--dry-run", "paint", **more)
        self.assertEqual(code, 0, out + err)
        done = err.strip().splitlines()[-1]
        self.assertIn("nothing left to do", done)
        self.tool("murmur", ["describe", "doctor", "config"])
        code, out, err = self.run_cli("setup", "--dry-run", "murmur", **more)
        self.assertEqual((code, err.strip().splitlines()[-1]), (0, done), out + err)
        self.assertNotIn("install-cli", out)
        self.assertIn("runs from the plugin's own folder", out)

    def test_l4_doctor_reads_the_setup_rows_green(self):
        more = self.ready()
        self.tool("murmur", ["describe", "doctor", "config"])
        cmd = types.SimpleNamespace(lib=str(LIB), env=self.env(**more), tool="agentik-suite",
                                    version=version(), t=types.SimpleNamespace(text=lambda mid, **v: mid))
        with mock.patch.object(plan, "default_set", return_value=["murmur"]):
            rows = doctor.plan_rows(cmd)
        self.assertEqual({r["status"] for r in rows}, {"ok"}, rows)
        self.assertIn("setup.launcher.inplace", [r["detail"] for r in rows])


if __name__ == "__main__":
    unittest.main()
