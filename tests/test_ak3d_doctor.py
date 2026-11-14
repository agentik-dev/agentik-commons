"""Packet ak3d: `doctor`, the machine checked in one read, the door's version first.

Each run is the plugin's launcher in ak1a's Home, a stub `claude` that records its calls, every
tool a made-up stub; one test runs the command in process with the deadline shortened. Lines 1
to 4 and 6 are each held to line 9: HOME the same outside the cache, no `suite/` cache folder,
and the stub `claude` called by nobody.
"""
import io
import json
import os
import signal
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import ESC, LAUNCHER, SYSTEM, Home  # noqa: E402
from agentik_suite import cli, doctor  # noqa: E402

TOOL = "agentik-suite"
CMD = str(LAUNCHER)  # a printed command with no door: the launcher's path, as typed (row sc2)
BETA = '#!/bin/sh\n[ "$1" = doctor ] || exit 9\necho "beta: two checks"\necho\necho "beta: one failed"\nexit 2\n'
ALPHA = '#!/bin/sh\n[ "$1" = doctor ] || exit 9\necho "alpha: all ok"\n'


class DoctorHome(Home):
    @property
    def bindir(self):
        return os.path.join(self.home, ".local", "bin")

    def place(self, folder, name, text, mode=0o755):
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, name)
        with open(path, "w") as fh:
            fh.write(text)
        os.chmod(path, mode)
        return path

    def doctor(self, *args, read=True, **more):
        before = self.snapshot()
        code, out, err = self.run_cli("doctor", *args, **more)
        if read:  # line 9
            self.assertEqual(self.snapshot(), before, args)
            self.assertFalse(os.path.exists(os.path.join(self.cache, "agentik", "suite")))
            self.assertFalse(os.path.exists(self.calls))
        return code, out, err

    def answer(self, *args, **more):
        code, out, err = self.doctor("--json", *args, **more)
        self.assertNotIn(ESC, out + err)
        obj = json.loads(out)
        self.assertEqual(set(obj), {"schema", "ok", "failed", "warned", "tools"})
        self.assertEqual((obj["schema"], obj["ok"]), ("agentik.doctor/1", True))
        for group in obj["tools"]:
            self.assertEqual(set(group), {"name", "checks"})
            for c in group["checks"]:
                self.assertEqual(set(c), {"name", "status", "detail", "remedy"})
                self.assertIn(c["status"], ("ok", "note", "warn", "fail"))
        every = [c["status"] for g in obj["tools"] for c in g["checks"]]
        self.assertEqual((obj["failed"], obj["warned"]), (every.count("fail"), every.count("warn")))
        self.assertEqual(code, 1 if obj["failed"] else 0)
        return code, obj

    @staticmethod
    def group(obj, name):
        return [g["checks"] for g in obj["tools"] if g["name"] == name][0]

    def suite(self, obj, name):
        return [c for c in self.group(obj, "suite") if c["name"] == name]


class EmptyHomeTest(DoctorHome):
    def test_line_1_empty_home(self):
        code, out, err = self.doctor()
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("run:", out)  # sc10: the close names the one command
        self.assertIn("next: %s setup" % CMD, err)
        code, obj = self.answer()  # line 7
        self.assertEqual(code, 0)
        self.assertEqual(obj["tools"][0]["name"], "suite")
        self.assertEqual([g["name"] for g in obj["tools"]], ["suite"])
        names = [c["name"] for c in obj["tools"][0]["checks"]]
        self.assertEqual(names[:3], ["door", "shadow", "settings"])
        market = [c for c in obj["tools"][0]["checks"] if c["name"].startswith("marketplace")]
        self.assertEqual(len(market), 1)
        self.assertEqual((market[0]["status"], market[0]["remedy"]), ("warn", "%s setup" % CMD))
        self.assertTrue(any(n.startswith("path ") for n in names))
        self.assertFalse(any(n.startswith("doctor") for n in names))  # step 7 is left out
        path = [c for c in obj["tools"][0]["checks"] if c["name"].startswith("path ")][0]
        self.assertEqual(path["remedy"], 'export PATH="$HOME/.local/bin:$PATH"')
        self.assertEqual(self.suite(obj, "door")[0]["remedy"], "%s setup" % CMD)

    def test_line_2_no_claude(self):
        os.remove(os.path.join(self.stubs, "claude"))
        code, obj = self.answer()
        self.assertEqual(code, 1)
        row = [c for c in obj["tools"][0]["checks"] if c["name"] == "prereqs claude"]
        self.assertEqual([c["status"] for c in row], ["fail"])


class DoorTest(DoctorHome):
    def path(self, *first):
        return ":".join(list(first) + [self.stubs, SYSTEM])

    def test_line_3_the_door(self):
        door = self.place(self.bindir, "agentik", "#!/bin/sh\nVERSION=0.1.0\n")
        launcher = self.place(self.bindir, TOOL, "#!/bin/sh\nVERSION=0.4.0\n")
        code, obj = self.answer(PATH=self.path(self.bindir))
        got = self.suite(obj, "door")
        self.assertEqual([(c["status"], c["remedy"]) for c in got], [("fail", "%s install-cli" % CMD)])
        self.assertEqual(code, 1)
        code, out, err = self.doctor(PATH=self.path(self.bindir))
        self.assertEqual(code, 1)
        self.assertIn("next: %s install-cli" % CMD, err)  # sc10: a failing suite row's remedy
        # the door at this command's own version
        self.place(self.bindir, "agentik", "#!/bin/sh\nVERSION=0.2.0\n")
        code, obj = self.answer(PATH=self.path(self.bindir))
        self.assertEqual(self.suite(obj, "door")[0]["status"], "ok")
        self.assertEqual(code, 0)
        # the old door with no launcher: a warn, and the exit is not from it
        self.place(self.bindir, "agentik", "#!/bin/sh\nVERSION=0.1.0\n")
        os.remove(launcher)
        code, obj = self.answer(PATH=self.path(self.bindir))
        self.assertEqual(self.suite(obj, "door")[0]["status"], "warn")
        self.assertEqual(code, 0)
        # no version to read
        self.place(self.bindir, "agentik", "#!/bin/sh\n")
        code, obj = self.answer(PATH=self.path(self.bindir))
        self.assertEqual(self.suite(obj, "door")[0]["status"], "warn")
        self.assertTrue(door)

    def test_line_3_a_fifo_or_a_folder_is_passed_over(self):
        fifo = os.path.join(self.home, "fifo")
        os.makedirs(fifo)
        os.mkfifo(os.path.join(fifo, "agentik"))
        folder = os.path.join(self.home, "folder")
        os.makedirs(os.path.join(folder, "agentik"))
        door = self.place(self.bindir, "agentik", "#!/bin/sh\nVERSION=0.2.0\n")
        start = time.monotonic()
        code, obj = self.answer(PATH=self.path(fifo, folder, self.bindir))
        self.assertLess(time.monotonic() - start, 5)
        got = self.suite(obj, "door")[0]
        self.assertEqual(got["status"], "ok")
        self.assertIn("~/.local/bin/agentik", got["detail"])
        self.assertTrue(door)


class ShadowTest(DoctorHome):
    def test_line_4_a_shadowed_verb(self):
        shadow = self.stub("agentik-setup")
        code, obj = self.answer()
        got = self.suite(obj, "shadow")
        self.assertEqual([c["status"] for c in got], ["fail"])
        self.assertIn(shadow, got[0]["detail"])
        self.assertEqual(code, 1)
        os.remove(shadow)
        self.stub("agentik-alpha")
        code, obj = self.answer()
        self.assertEqual([c["status"] for c in self.suite(obj, "shadow")], ["ok"])
        self.assertEqual(code, 0)


class ToolTest(DoctorHome):
    def test_line_5_each_tools_own_doctor(self):
        self.stub("agentik-alpha", ALPHA)
        self.stub("agentik-beta", BETA)
        self.plugin_files(os.path.join(self.home, ".claude"), {"gamma": "1.0.0"}, whole=False)
        code, obj = self.answer(read=False)
        self.assertEqual([g["name"] for g in obj["tools"]], ["suite", "alpha", "beta", "gamma"])
        self.assertEqual([(c["name"], c["status"]) for c in self.group(obj, "alpha")], [("doctor", "ok")])
        beta = self.group(obj, "beta")
        self.assertEqual([(c["name"], c["status"], c["detail"], c["remedy"]) for c in beta],
                         [("doctor", "fail", "its doctor failed", "%s/agentik-beta doctor" % self.stubs)])
        self.assertEqual([c["status"] for c in self.group(obj, "gamma")], ["note"])
        self.assertEqual(code, 1)
        code, out, err = self.doctor(read=False)
        self.assertEqual(code, 1)
        self.assertNotIn("beta: one failed", out)  # sc10: a tool's own lines are not printed
        self.assertIn("its doctor failed", [l.split("  ")[-1].strip() for l in out.splitlines() if "beta" in l])
        self.assertIn("next: %s setup" % CMD, err)  # steps 2 to 5 are left, so setup comes first

    def test_line_5_a_slow_doctor_in_process(self):
        pid = os.path.join(self.home, "slow.pid")
        self.stub("agentik-slow", '#!/bin/sh\necho $$ > "%s"\nsleep 10\n' % pid)
        self.stub("agentik-alpha", ALPHA)
        saved = doctor.DEADLINE
        doctor.DEADLINE = 1.0
        self.addCleanup(setattr, doctor, "DEADLINE", saved)
        out, err = io.StringIO(), io.StringIO()
        start = time.monotonic()
        code = cli.Command(["doctor", "--json"], self.env(), out, err).run()
        self.assertLess(time.monotonic() - start, 3)
        obj = json.loads(out.getvalue())
        self.assertEqual([c["status"] for c in self.group(obj, "slow")], ["warn"])
        self.assertEqual([c["status"] for c in self.group(obj, "alpha")], ["ok"])
        self.assertEqual(code, 0)
        with open(pid) as fh:
            group = int(fh.read())
        for _ in range(50):
            try:
                os.killpg(group, 0)
            except ProcessLookupError:
                break
            time.sleep(0.02)
        else:
            os.killpg(group, signal.SIGKILL)
            self.fail("the slow doctor's group outlived the run")


class SettingsTest(DoctorHome):
    def user(self, text):
        self.place(os.path.join(self.home, ".config", "agentik", "suite"), "config.yaml", text, 0o644)

    def test_line_6_the_user_file(self):
        self.user("watchers:\n\tlamp: x\n")
        code, obj = self.answer()
        got = self.suite(obj, "settings")
        self.assertEqual([c["status"] for c in got], ["fail"])
        self.assertIn("~/.config/agentik/suite/config.yaml", got[0]["detail"])
        self.assertIn("line 2", got[0]["detail"])
        self.assertEqual(code, 1)
        self.user("watchers:\n  lamp:\n    match: lampd watch\n    start: lampd watch\n"
                  "  dim:\n    match: dimd\n")
        code, obj = self.answer()
        got = self.suite(obj, "settings")
        self.assertEqual([c["status"] for c in got], ["warn"])
        for word in ("dim", "match", "start"):
            self.assertIn(word, got[0]["detail"])
        self.assertNotIn("lamp", got[0]["detail"])
        self.assertEqual(code, 0)


class VerbTest(DoctorHome):
    def test_line_8_the_verb(self):
        code, out, err = self.doctor("extra")
        self.assertEqual(code, 2)
        self.assertIn("extra", err)
        code, out, err = self.run_cli("help")
        self.assertIn("doctor", out)
        code, out, err = self.run_cli("doctor", "--help")
        self.assertEqual((code, out.splitlines()[0]), (0, "usage: %s doctor [flags]" % CMD))
        code, out, err = self.doctor("-q")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("door", out)

    def test_line_7_piped_text_has_no_escape(self):
        self.stub("agentik-alpha", ALPHA)
        code, out, err = self.doctor()
        self.assertNotIn(ESC, out + err)


if __name__ == "__main__":
    unittest.main()
