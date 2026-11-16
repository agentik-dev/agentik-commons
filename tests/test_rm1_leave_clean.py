"""Row rm1-leave-clean: `remove --all` takes a session command of any age, its dry run says what the
run does, each plugin goes before the marketplace, and the door's closing line runs as printed.

Each home is test_ak4_remove's `RHome`, a temp HOME whose `claude` stub records every argument
list in `$HOME/ran.log`; the suite is placed by its own `install-cli` from this checkout. The
session command in its older form is built here from the second line that launcher carried before
the session tool's alpha.127, with made-up paths and link names. No test starts a real `claude`,
reads the live home or the live process list."""
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_install import APPLE_PY, DOOR, ROOT  # noqa: E402
from test_ak4_remove import UNINSTALL, RHome  # noqa: E402
from test_ak4a_update import LAUNCHER, Base  # noqa: E402

import agentik_install  # noqa: E402  (the suite's copy, on sys.path from test_agentik_suite)

# The head of the session launcher as it was written before alpha.127: line 2 exactly, then a line
# naming a made-up old name.
OLD_HEAD = ("#!/bin/sh\n"
            "# agentik-session launcher, written by `agentik-session install-cli` (design/04 §2, §3); its old\n"
            "# name, sess-old, is a link to it until r2 (agentik-r1 §4.3).\n")
OLD_LINKS = ("sess-old", "sess")
SUITE_UNINSTALL = "claude plugin uninstall suite@agentik --keep-data"
MARKET_REMOVE = "claude plugin marketplace remove agentik"
CLONE = "next: git clone https://github.com/agentik-dev/agentik-commons && agentik-commons/setup"
SETUP = "#!/bin/sh\necho setup ran\n"


def old_session(h, ver="2.0.0-alpha.118"):
    """A session plugin at the user's scope, and its command as install-cli wrote it before
    alpha.127: the launcher, its tree, the lock and two links to it."""
    h.install("session@agentik", ver, launcher=False)
    share = os.path.join(h.home, ".local", "share", "agentik-session")
    tree = os.path.join(share, "0123456789abcdef0123456789abcdef01234567")
    h.file(os.path.join(tree, "agentik-session"), "print('a made-up session')\n")
    h.file(os.path.join(share, ".lock"), "")
    launcher = os.path.join(h.bindir, "agentik-session")
    h.file(launcher, OLD_HEAD + "VERSION=%s\nTREE=%s\n" % (shlex.quote(ver), shlex.quote(tree))
           + 'exec /usr/bin/python3 -I "$TREE/agentik-session" "$@"\n')
    for link in OLD_LINKS:
        os.symlink("agentik-session", os.path.join(h.bindir, link))
    return launcher


def agentik_left(h):
    """Every entry of agentik's left in ~/.local/bin and ~/.local/share."""
    share = os.path.join(h.home, ".local", "share")
    found = [n for n in os.listdir(h.bindir) if n.startswith("agentik") or n in OLD_LINKS]
    if os.path.isdir(share):
        found += [n for n in os.listdir(share) if n.startswith("agentik")]
    return sorted(found)


class LauncherForm(unittest.TestCase):
    """R1 at the module: the older second line is the session launcher's form, for that name alone."""

    def test_the_older_second_line_is_a_session_launchers_form(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "agentik-session")
            with open(path, "w") as fh:
                fh.write(OLD_HEAD + "VERSION=1\nTREE=/nowhere\n")
            self.assertTrue(agentik_install._launcher_form(path, "agentik-session"))
            other = os.path.join(tmp, "agentik-other")
            with open(other, "w") as fh:
                fh.write(OLD_HEAD.replace("agentik-session", "agentik-other") + "VERSION=1\nTREE=/nowhere\n")
            self.assertFalse(agentik_install._launcher_form(other, "agentik-other"))
            with open(path, "w") as fh:  # a line near it is no form
                fh.write(OLD_HEAD.replace("its old\n", "its old \n") + "VERSION=1\nTREE=/nowhere\n")
            self.assertFalse(agentik_install._launcher_form(path, "agentik-session"))

    def test_both_copies_of_the_module_are_one(self):
        with open(str(ROOT / "scripts" / "agentik_install.py"), "rb") as a, \
                open(str(ROOT / "plugins" / "suite" / "lib" / "agentik_install.py"), "rb") as b:
            self.assertEqual(a.read(), b.read())


@unittest.skipUnless(os.access(APPLE_PY, os.X_OK), "no /usr/bin/python3 on this machine")
class LeaveClean(Base):
    def home(self, listed=("murmur", "paint", "x", "session", "agents"), name="h"):
        h = RHome(os.path.join(self.tmp, name), listed)
        h.real_tool()
        h.place(str(LAUNCHER))  # the suite at this checkout's version: its launcher, trees, the door
        return h

    def steps(self, out):
        return json.loads(out)["steps"]

    # ---- acceptance 1: R1 ----------------------------------------------------------------------

    def test_1_an_older_session_command_goes_in_the_dry_run_and_the_run(self):
        h = self.home()
        launcher = old_session(h)
        door = os.path.join(h.bindir, "agentik")
        code, out, err = h.go("remove", "--all", "--dry-run", "--json", exe=door)
        self.assertEqual(code, 0, out + err)
        rows = {s["subject"]: s for s in self.steps(out) if s["n"] in (2, 5)}
        for path in ["~/.local/bin/agentik-session", "~/.local/bin/agentik"] \
                + ["~/.local/bin/" + n for n in OLD_LINKS] + ["~/.local/share/agentik-session"]:
            self.assertIn(path, rows, sorted(rows))
            self.assertTrue(rows[path]["detail"].endswith("would remove"), rows[path])
        code, out, err = h.go("remove", "--all", "--yes", exe=door)
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("Traceback", err)
        self.assertIn("claude plugin uninstall session@agentik --keep-data", h.claude())
        self.assertFalse(os.path.lexists(launcher))
        self.assertEqual(agentik_left(h), [])

    # ---- acceptance 2: R4 ----------------------------------------------------------------------

    def test_2_every_plugin_uninstall_comes_before_the_marketplace_goes(self):
        h = self.home()
        old_session(h)
        h.install("suite@agentik", "0.7.24", launcher=False)
        # as the lead feared: an uninstall fails where its marketplace is gone
        h.stub('    fail = os.path.join(home, "fail")\n',
               '    fail = os.path.join(home, "fail")\n'
               '    if "agentik" not in json.load(open(os.path.join(d, "known_marketplaces.json"))):\n'
               '        print("no such marketplace")\n'
               '        sys.exit(1)\n')
        code, out, err = h.go("remove", "--all", "--dry-run", "--json")
        order = [s["command"] for s in self.steps(out) if s["command"]]
        self.assertEqual(order[-2:], [SUITE_UNINSTALL, MARKET_REMOVE], order)
        code, out, err = h.go("remove", "--all", "--yes")
        self.assertEqual(code, 0, out + err)
        ran = h.claude()
        self.assertEqual(ran[-2:], [SUITE_UNINSTALL, MARKET_REMOVE], ran)
        self.assertEqual(sorted(ran[:-2]), sorted([UNINSTALL, "claude plugin uninstall session@agentik --keep-data"]))
        self.assertEqual(agentik_left(h), [])

    def test_2_a_second_call_after_a_cut_finishes(self):
        h = self.home()
        h.install("suite@agentik", "0.7.24", launcher=False)
        h.stub('if a[:3] == ["plugin", "marketplace", "remove"] and len(a) == 4:\n',
               'if a[:3] == ["plugin", "marketplace", "remove"] and len(a) == 4:\n'
               '    if os.path.exists(os.path.join(home, "cut")):\n'
               '        sys.exit(1)\n')
        h.file(os.path.join(h.home, "cut"), "")
        code, out, err = h.go("remove", "--all", "--yes")
        self.assertEqual(code, 1, out + err)
        self.assertEqual(h.claude(), [UNINSTALL, SUITE_UNINSTALL, MARKET_REMOVE])
        os.unlink(os.path.join(h.home, "cut"))
        code, out, err = h.go("remove", "--all", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(h.claude(), [UNINSTALL, SUITE_UNINSTALL, MARKET_REMOVE, MARKET_REMOVE])
        self.assertEqual(agentik_left(h), [])

    # ---- R2, and acceptance 3: R3 --------------------------------------------------------------

    def test_r2_the_dry_run_and_the_run_agree_line_for_line(self):
        h = self.home()
        h.file(os.path.join(h.bindir, "agentik-zz"), "#!/bin/sh\nexit 0\n")  # not install-cli's: it stays
        door = os.path.join(h.bindir, "agentik")
        code, out, err = h.go("remove", "--all", "--dry-run", "--json", exe=door)
        self.assertEqual(code, 0, out + err)
        dry = {s["subject"]: s["detail"] for s in self.steps(out) if s["n"] in (2, 5)}
        self.assertTrue(dry["~/.local/bin/agentik"].endswith("kept: agentik-zz stands"), dry)
        code, out, err = h.go("remove", "--all", "--yes", "--json", exe=door)
        self.assertEqual(code, 0, out + err)
        obj = json.loads(out)
        real = {p: "removed" for p in obj["removed"]}
        real.update({k["path"]: k["why"] for k in obj["kept"]})
        real = {"~/" + os.path.relpath(p, h.home): why for p, why in real.items()}
        for subject, detail in sorted(dry.items()):
            want = real.get(subject)
            self.assertIsNotNone(want, subject)
            self.assertTrue(detail.endswith("would remove" if want == "removed" else want), (subject, detail, want))
        self.assertEqual(agentik_left(h), ["agentik", "agentik-zz"])

        # acceptance 3: the door left by that run, where the clone stands
        work = os.path.join(self.tmp, "work")
        h.file(os.path.join(work, "agentik-commons", "setup"), SETUP)
        p = subprocess.run([door, "remove", "--all"], capture_output=True, text=True, env=h.env(), cwd=work,
                           stdin=subprocess.DEVNULL, timeout=60)
        self.assertEqual(p.returncode, 3, p.stderr)
        line = p.stderr.splitlines()[-1]
        self.assertEqual(line, "next: %s/agentik-commons/setup" % work)
        for where in (work, self.tmp):
            ran = subprocess.run(["/bin/sh", "-c", line[len("next: "):]], capture_output=True, text=True,
                                 cwd=where, env=h.env(), timeout=60)
            self.assertEqual((ran.returncode, ran.stdout), (0, "setup ran\n"), ran.stderr)

    # ---- R5 --------------------------------------------------------------------------------------

    def test_r5_a_folder_kept_shows_once_and_the_suites_cache_is_named(self):
        h = self.home()
        h.real_tool(name="agents")
        h.file(os.path.join(h.home, ".config", "agentik", "agents", "mine.yaml"), "mine\n")
        h.install("suite@agentik", "0.7.24", launcher=False)
        cache = os.path.join(h.plugins, "cache", "agentik", "suite")
        code, out, err = h.go("remove", "--all", "--dry-run", "--json")
        self.assertEqual(code, 0, out + err)
        kept = [os.path.normpath(k["path"]) for k in json.loads(out)["kept"]]
        self.assertEqual(kept.count(os.path.join(h.home, ".config", "agentik", "agents")), 1, kept)
        self.assertEqual(len(kept), len(set(kept)), kept)
        self.assertIn(cache, kept)
        code, out, err = h.go("remove", "--all", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.count("~/.config/agentik/agents"), 1, out)
        self.assertIn("~/.claude/plugins/cache/agentik/suite", out)

    def test_r5_the_suites_cache_gone_after_the_run_is_no_fault(self):
        h = self.home()
        h.install("suite@agentik", "0.7.24", launcher=False)
        h.stub('    shutil.rmtree(os.path.join(d, "marketplaces", a[3]), ignore_errors=True)\n',
               '    shutil.rmtree(os.path.join(d, "marketplaces", a[3]), ignore_errors=True)\n'
               '    shutil.rmtree(os.path.join(d, "cache", a[3], "suite"), ignore_errors=True)\n')
        code, out, err = h.go("remove", "--all", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("~/.claude/plugins/cache/agentik/suite", out)


class DoorLine(unittest.TestCase):
    """R3 at the door: with no suite, `agentik-commons/setup` by its path where a clone stands here,
    the clone line only where none does; each runs as printed."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = os.path.realpath(tmp.name)
        self.env = {"HOME": self.tmp, "PATH": "/usr/bin:/bin"}

    def door(self, cwd, *args):
        p = subprocess.run([str(DOOR), *(args or ("nosuch",))], capture_output=True, text=True, env=self.env,
                           cwd=cwd, timeout=60)
        return p.stderr.splitlines()[-1]

    def clone(self, where):
        path = os.path.join(where, "setup")
        os.makedirs(where, exist_ok=True)
        with open(path, "w") as fh:
            fh.write(SETUP)
        os.chmod(path, 0o755)
        return where

    def runs(self, line, cwd):
        p = subprocess.run(["/bin/sh", "-c", line[len("next: "):]], capture_output=True, text=True, cwd=cwd,
                           env=self.env, timeout=60)
        return p.returncode, p.stdout

    def test_no_clone_here_is_the_clone_line(self):
        self.assertEqual(self.door(self.tmp), CLONE)
        self.assertEqual(self.door(self.tmp, "--help"), CLONE)

    def test_a_clone_here_is_its_setup_by_its_path(self):
        clone = self.clone(os.path.join(self.tmp, "agentik-commons"))
        for args in (("nosuch",), ("--help",)):
            line = self.door(self.tmp, *args)
            self.assertEqual(line, "next: %s/setup" % clone, args)
            self.assertEqual(self.runs(line, self.tmp), (0, "setup ran\n"))
            self.assertEqual(self.runs(line, "/"), (0, "setup ran\n"))

    def test_in_the_clone_itself(self):
        clone = self.clone(os.path.join(self.tmp, "agentik-commons"))
        line = self.door(clone)
        self.assertEqual(line, "next: %s/setup" % clone)
        self.assertEqual(self.runs(line, clone), (0, "setup ran\n"))

    def test_a_path_with_a_space_is_given_from_here(self):
        where = os.path.join(self.tmp, "a b")
        self.clone(os.path.join(where, "agentik-commons"))
        line = self.door(where)
        self.assertEqual(line, "next: agentik-commons/setup")
        self.assertEqual(self.runs(line, where), (0, "setup ran\n"))

    def test_a_setup_that_cannot_run_is_no_clone(self):
        os.makedirs(os.path.join(self.tmp, "agentik-commons"))
        with open(os.path.join(self.tmp, "agentik-commons", "setup"), "w") as fh:
            fh.write(SETUP)
        self.assertEqual(self.door(self.tmp), CLONE)


if __name__ == "__main__":
    unittest.main()
