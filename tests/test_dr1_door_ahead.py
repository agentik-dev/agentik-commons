"""Row dr1-door-ahead: an older `agentik` earlier on PATH than ~/.local/bin is named, with a fix that
mends it (the install and upgrade review's findings 10 and 16).

R1: where the first `agentik` on PATH is not ~/.local/bin/agentik, which stands, and is older than
this command's door, the doctor's door row names that path and its version, and its `fix:` is the
PATH line that puts ~/.local/bin first, a command alone; `--json` carries the same remedy, and no
line tells a person to remove a file. R2: `too old to pass a verb` is said only of a door below
0.2.0. R3: the old-Python refusal names AGENTIK_PYTHON; the scaffold's Makefile uses `sha256sum`
where `shasum` is absent.

Each screen runs in a temp HOME after `./setup --yes` there with a stub `claude` (ic1-close's
harness), PATH the made-up old door's folder, ~/.local/bin, the stubs, then /usr/bin:/bin. Nothing
here starts the real `claude` or writes outside its temp folder."""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_ic1_close import MESSAGES, PROFILE, ROOT, SYSTEM, Home  # noqa: E402
from agentik_suite import cli, plan  # noqa: E402

OLD = "#!/bin/sh\n# a made-up older door\nVERSION=%s\n" \
      'echo "agentik: agentik-$1 is not on PATH; it comes from nowhere" >&2\nexit 2\n'
FIX = "fix: " + PROFILE
SCAFFOLD = ROOT / "plugins" / "suite" / "lib" / "scaffold" / "hq"
MAKE = "/usr/bin/make"
# a sha256sum stand-in: `-c --status FILE`, as coreutils' reads it, and a mark that it ran
SUM = """#!/usr/bin/python3
import hashlib, os, sys
open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "ran-" + os.path.basename(sys.argv[0])), "a").close()
args = [a for a in sys.argv[1:] if a not in ("--status", "-c", "-a", "256")]
for line in open(args[-1]):
    want, name = line.split(None, 1)
    with open(name.strip().lstrip("*"), "rb") as fh:
        if hashlib.sha256(fh.read()).hexdigest() != want:
            sys.exit(1)
"""
AGENTIK = "#!/bin/sh\n[ \"$*\" = \"decisions render --check\" ] || exit 9\n"


class Ahead(Home):
    def setUp(self):
        super().setUp()
        code, text = self.run_both(["./setup", "--yes"], self.env())
        self.assertEqual(code, 0, text)
        self.door = os.path.join(self.bindir, "agentik")
        self.assertTrue(os.path.isfile(self.door))
        self.old = os.path.join(self.home, "old")
        os.mkdir(self.old)

    def place(self, version, folder=None):
        path = os.path.join(folder or self.old, "agentik")
        with open(path, "w") as fh:
            fh.write(OLD % version)
        os.chmod(path, 0o755)
        return path

    def ahead_env(self):
        return self.env(path=":".join([self.old, self.bindir, self.stubs, SYSTEM]))

    def doctor(self, env, *args):
        return self.run_both([os.path.join(self.bindir, "agentik-suite"), "doctor"] + list(args), env)

    def door_json(self, env):
        p = subprocess.run([os.path.join(self.bindir, "agentik-suite"), "doctor", "--json"], env=env,
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
        obj = json.loads(p.stdout)
        door = [c for c in obj["tools"][0]["checks"] if c["name"] == "door"]
        self.assertEqual(len(door), 1, p.stdout)
        return door[0]

    @staticmethod
    def door_rows(text):
        lines = text.splitlines()
        return [(i, l) for i, l in enumerate(lines) if l.split()[1:2] == ["door"]], lines


class OldDoorTest(Ahead):
    def test_1_a_0_1_0_door_first_is_named_and_the_fix_mends_it(self):
        self.place("0.1.0")
        env = self.ahead_env()
        code, text = self.doctor(env)
        self.assertEqual(code, 1, text)
        rows, lines = self.door_rows(text)
        self.assertEqual(len(rows), 1, text)
        at, row = rows[0]
        self.assertEqual(row.split()[0], "FAIL", text)
        self.assertIn("~/old/agentik", row)
        self.assertIn("0.1.0", row)
        self.assertEqual(lines[at + 1].strip(), FIX, text)  # the row ends on the PATH line
        self.assertEqual(self.last(text), "next: " + PROFILE, text)
        self.assertNotIn("remove", text.lower().replace("remove <", ""), text)
        self.assertNotIn("install-cli", text)
        got = self.door_json(env)
        self.assertEqual((got["status"], got["remedy"]), ("fail", PROFILE))
        self.assertIn("~/old/agentik", got["detail"])  # the detail's form at the pin
        # at the pin `agentik doctor` here is the old door's own refusal
        code, out = self.run_both(["/bin/sh", "-c", "agentik doctor"], env)
        self.assertEqual(code, 2, out)
        # the fix pasted into that shell: `agentik doctor` reads the new door, and the FAIL is gone
        code, out = self.run_both(["/bin/sh", "-c", lines[at + 1].strip()[len("fix: "):]
                                   + "\nagentik doctor"], env)
        self.assertEqual(code, 0, out)
        self.assertNotIn("FAIL", out)
        self.assertEqual(self.door_rows(out)[0], [], out)
        code, out = self.run_both(["/bin/sh", "-c", PROFILE + "\nagentik doctor --all"], env)
        rows, _ = self.door_rows(out)
        self.assertEqual([r.split()[0] for _, r in rows], ["ok"], out)
        self.assertIn("~/.local/bin/agentik", rows[0][1])

    def test_2_a_0_2_0_door_first_is_r1s_row_and_not_too_old(self):
        self.place("0.2.0")
        env = self.ahead_env()
        code, text = self.doctor(env)
        self.assertNotIn("too old to pass a verb", text)
        rows, lines = self.door_rows(text)
        self.assertEqual(len(rows), 1, text)
        at, row = rows[0]
        self.assertEqual(row.split()[0], "warn", text)
        self.assertIn("~/old/agentik", row)
        self.assertIn("0.2.0", row)
        self.assertEqual(lines[at + 1].strip(), FIX, text)
        self.assertEqual(self.last(text), "next: " + PROFILE, text)
        got = self.door_json(env)
        self.assertEqual((got["status"], got["remedy"]), ("warn", PROFILE))
        self.assertNotIn("too old", got["detail"])
        code, out = self.run_both(["/bin/sh", "-c", PROFILE + "\nagentik doctor"], env)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.door_rows(out)[0], [], out)

    def test_2_the_door_at_local_bin_at_0_2_0_is_older_not_too_old(self):
        self.place("0.2.0", folder=self.bindir)
        code, text = self.doctor(self.env())
        self.assertNotIn("too old to pass a verb", text)
        self.assertNotIn("FAIL", text)
        got = self.door_json(self.env())
        self.assertEqual(got["status"], "warn")
        self.assertIn("0.2.0", got["detail"])

    def test_2_the_door_at_local_bin_below_0_2_0_is_too_old_as_at_the_pin(self):
        self.place("0.1.0", folder=self.bindir)
        got = self.door_json(self.env())
        self.assertEqual(got["status"], "fail")
        self.assertIn("too old to pass a verb", got["detail"])

    def test_3_no_door_ahead_reads_as_at_the_pin(self):
        env = self.env()
        code, text = self.doctor(env)
        self.assertEqual(code, 0, text)
        self.assertEqual(self.door_rows(text)[0], [], text)
        got = self.door_json(env)
        self.assertEqual(got, {"name": "door", "status": "ok", "remedy": None,
                               "detail": "~/.local/bin/agentik is at version 0.3.1; this command's door is 0.3.1"})

    def test_3_a_newer_door_ahead_reads_as_at_the_pin(self):
        self.place("9.0.0")
        got = self.door_json(self.ahead_env())
        self.assertEqual((got["status"], got["remedy"]), ("ok", None))

    def test_3_an_old_door_with_none_at_local_bin_reads_as_at_the_pin(self):
        self.place("0.1.0")
        os.remove(self.door)
        got = self.door_json(self.ahead_env())
        self.assertEqual(got["status"], "fail")
        self.assertIn("too old to pass a verb", got["detail"])
        self.assertTrue(got["remedy"].endswith("install-cli"), got)

    def test_the_new_rows_hold_the_voice(self):
        for mid in ("doctor.door.ahead", "doctor.door.ahead.old", "hint.setup.blocked.old"):
            text = MESSAGES[mid]
            self.assertLessEqual(len(re.sub(r"`\{[^}]*\}`", "", text).replace("`", "")), 76, mid)
            self.assertIsNone(re.search(r"this version|a later version|\bwould\b|\bexit|remove", text, re.I))
            self.assertLessEqual(len(re.findall(r"\b(since|so|because)\b", text, re.I)), 1)
        self.assertNotIn("too old", MESSAGES["doctor.door.ahead"])


class OldPythonTest(Home):
    def test_3_the_refusal_names_agentik_python(self):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(plan, "FLOOR", (3, 99)):
            code = cli.main(["setup"], env=self.env(), out=out, err=err)
        self.assertEqual(code, 2, out.getvalue() + err.getvalue())
        last = self.last(err.getvalue())
        self.assertIn("AGENTIK_PYTHON", last)
        self.assertIn("3.99", last)
        self.assertNotIn("next:", err.getvalue())


class ScaffoldSumTest(unittest.TestCase):
    """Acceptance 4: a scaffolded hq's `make check` with `shasum` off PATH and `sha256sum` on it."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="dr1-")
        self.addCleanup(tmp.cleanup)
        self.top = os.path.realpath(tmp.name)
        self.hq = os.path.join(self.top, "pear-hq")
        shutil.copytree(str(SCAFFOLD), self.hq)
        self.bin = os.path.join(self.top, "bin")
        os.mkdir(self.bin)
        self.tool("agentik", AGENTIK)
        os.symlink("/usr/bin/python3", os.path.join(self.bin, "python3"))

    def tool(self, name, body):
        path = os.path.join(self.bin, name)
        with open(path, "w") as fh:
            fh.write(body)
        os.chmod(path, 0o755)

    def check(self):
        env = {"HOME": self.top, "PATH": self.bin}
        p = subprocess.run([MAKE, "check"], cwd=self.hq, env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=120)
        return p.returncode, p.stdout + p.stderr

    @unittest.skipUnless(os.access(MAKE, os.X_OK), "no make")
    def test_4_sha256sum_where_shasum_is_absent(self):
        self.tool("sha256sum", SUM)
        code, out = self.check()
        self.assertEqual(code, 0, out)
        self.assertTrue(os.path.exists(os.path.join(self.bin, "ran-sha256sum")), out)
        with open(os.path.join(self.hq, "scripts", "recordlint"), "a") as fh:
            fh.write("\n")
        code, out = self.check()
        self.assertEqual(code, 2, out)
        self.assertIn("recordlint: scripts/recordlint is not the file", out)

    @unittest.skipUnless(os.access(MAKE, os.X_OK), "no make")
    def test_4_shasum_where_it_stands(self):
        self.tool("shasum", SUM)
        self.tool("sha256sum", SUM)
        code, out = self.check()
        self.assertEqual(code, 0, out)
        self.assertTrue(os.path.exists(os.path.join(self.bin, "ran-shasum")), out)
        self.assertFalse(os.path.exists(os.path.join(self.bin, "ran-sha256sum")), out)


if __name__ == "__main__":
    unittest.main()
