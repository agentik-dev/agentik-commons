"""Packet ak2b: the suite's command reaches the terminal: `install-cli`, the root `setup`,
`make install`.

Each run is in ak1a's `Home` (a temp HOME, PATH of stubs and the system's folders), with the
prefix a second temp folder; the module is run from the suite's own lib/. `make` runs only as
`make -n`, which runs no recipe. Nothing here writes outside its temp folders."""
import json
import os
import shlex
import stat
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LAUNCHER, LIB, MANIFEST, ROOT, SYSTEM, Home, version  # noqa: E402

import agentik_install  # noqa: E402  (the suite's copy, on sys.path from test_agentik_suite)

DOOR_VERSION = "0.2.0"
MODULE_RUN = "import sys; sys.path.insert(0, sys.argv[1]); import agentik_install as a; " \
             "sys.exit(a.install_cli(sys.argv[2]))"


class Reach(Home):
    def setUp(self):
        Home.setUp(self)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.prefix = os.path.join(os.path.realpath(tmp.name), "p")

    def path(self, *parts):
        return os.path.join(self.prefix, *parts)

    def call(self, argv, timeout=60, cwd=None, **more):
        p = subprocess.run([str(a) for a in argv], capture_output=True, text=True,
                           env=self.env(**more), timeout=timeout, cwd=cwd)
        return p.returncode, p.stdout, p.stderr

    def install(self, *args, timeout=60, **more):
        return self.call([LAUNCHER, "install-cli", "--prefix", self.prefix, *args],
                        timeout=timeout, **more)

    def installed(self, *args, **more):
        code, out, err = self.install("--json", *args, **more)
        self.assertEqual(code, 0, err)
        self.assertEqual(out.count("\n"), 1, out)
        return json.loads(out)

    def step_four_done(self):
        """`alpha` installed whole and its launcher placed, so step 4 has no row to do: with one,
        a plugin's install-cli places the door and its row names no line (row sm1-setup-ask R2)."""
        self.plugin_files(os.path.join(self.home, ".claude"), {"alpha": "1.0.0"})
        bindir = os.path.join(self.home, ".local", "bin")
        os.makedirs(bindir, exist_ok=True)
        with open(os.path.join(bindir, "agentik-alpha"), "w") as fh:
            fh.write("#!/bin/sh\nVERSION=1.0.0\n")
        return "alpha"


class InstallCliTest(Reach):
    def test_a1_install_cli_places_the_command(self):
        before = self.snapshot()
        code, out, err = self.install()
        self.assertEqual(code, 0, err)
        exe = self.path("bin", "agentik-suite")
        naming = [line for line in out.splitlines() if exe in line and version() in line]
        self.assertEqual(len(naming), 1, out)
        self.assertEqual(out.splitlines()[0], naming[0])
        self.assertEqual(self.call([exe, "--version"])[:2], (0, "agentik-suite %s\n" % version()))
        self.assertEqual(self.call([self.path("bin", "agentik"), "--version"])[:2],
                         (0, "agentik %s\n" % DOOR_VERSION))
        self.assertEqual(self.snapshot(), before)

    def test_a2_json_and_the_dry_run(self):
        keys = {"schema", "ok", "launcher", "tree", "version", "door", "door_fate", "on_path", "dry_run"}
        dry = self.installed("--dry-run")
        self.assertEqual(set(dry), keys)
        self.assertEqual((dry["schema"], dry["ok"], dry["tree"], dry["dry_run"]),
                         ("agentik.install-cli/1", True, None, True))
        self.assertFalse(os.path.lexists(self.prefix))
        done = self.installed()
        self.assertEqual(set(done), keys)
        self.assertEqual((done["door_fate"], done["dry_run"], done["on_path"]), ("write", False, False))
        self.assertEqual(done["launcher"], self.path("bin", "agentik-suite"))
        self.assertEqual(done["version"], version())
        self.assertTrue(os.path.isdir(done["tree"]), done)

    def test_a3_the_path_hint_and_usage(self):
        line = 'export PATH="%s:$PATH"' % self.path("bin")
        code, out, err = self.install()
        self.assertEqual(code, 0, err)
        self.assertEqual(len(err.splitlines()), 1, err)
        self.assertIn(line, err)
        self.assertNotIn(line, out)
        on = "%s:%s:%s" % (self.path("bin"), self.stubs, SYSTEM)
        self.assertEqual(self.install(PATH=on)[::2], (0, ""))
        self.assertEqual(self.install("-q")[::2], (0, ""))
        self.assertEqual(self.installed(PATH=on)["on_path"], True)
        for args, lines in ((("install-cli", "extra"), 2), (("install-cli", "--prefix"), 1)):
            code, out, err = self.call([LAUNCHER, *args])
            self.assertEqual((code, out), (2, ""), args)
            self.assertEqual(len(err.splitlines()), lines, err)  # cli.py's is two lines (row sc4 R3)
        code, out, err = self.call([LAUNCHER, "help"])
        self.assertRegex(out, r"(?m)^  install-cli  ")
        code, out, err = self.call([LAUNCHER, "help", "install-cli"])
        self.assertEqual(code, 0, err)
        self.assertIn("--prefix", out)
        self.assertIn("--dry-run", out)

    def test_a3_a_failed_install_is_one_line(self):
        os.makedirs(self.prefix)
        with open(self.path("bin"), "w") as fh:     # a file where the bin folder goes
            fh.write("x")
        code, out, err = self.install()
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(len(err.splitlines()), 1, err)


class DoorFateTest(Reach):
    def door(self, kind):
        os.makedirs(self.path("bin"), exist_ok=True)
        door = self.path("bin", "agentik")
        if os.path.isdir(door) and not os.path.islink(door):
            os.rmdir(door)
        elif os.path.lexists(door):
            os.unlink(door)
        if kind == "fifo":
            os.mkfifo(door)
        elif kind == "link":
            os.symlink(self.path("elsewhere"), door)
        else:
            with open(door, "wb") as fh:
                fh.write(b"#!/bin/sh\nVERSION=" + kind + b"\n")
        return door

    def module(self, **more):
        return self.call(["/usr/bin/python3", "-c", MODULE_RUN, LIB, self.prefix], timeout=5, **more)

    def test_a4_each_door(self):
        door = self.door("fifo")
        self.assertEqual(self.installed(timeout=5)["door_fate"], "unversioned")
        self.assertTrue(stat.S_ISFIFO(os.lstat(door).st_mode))
        code, out, err = self.module()
        self.assertEqual(code, 0, err)
        self.assertIn("left alone", out)
        self.assertTrue(stat.S_ISFIFO(os.lstat(door).st_mode))

        door = self.door(b"0.2.\xff")
        before = open(door, "rb").read()
        utf8 = {"LC_ALL": "en_US.UTF-8"}
        for code, out, err in (self.install(timeout=5, **utf8), self.module(**utf8)):
            self.assertEqual(code, 0, err)
            self.assertNotIn("Traceback", err)
        note = [line for line in out.splitlines() if "left alone" in line]
        self.assertEqual(len(note), 1, out)
        self.assertTrue(note[0].isascii() and "\\xff" in note[0], note)
        self.assertEqual(self.installed(timeout=5, **utf8)["door_fate"], "unversioned")
        self.assertEqual(open(door, "rb").read(), before)

        door = self.door(b"0.9.0")
        before = open(door, "rb").read()
        self.assertEqual(self.installed(timeout=5)["door_fate"], "keep")
        self.assertEqual(open(door, "rb").read(), before)

        door = self.door(b"0.1.0")
        self.assertEqual(self.installed(timeout=5)["door_fate"], "write")
        self.assertEqual(agentik_install.read_launcher(door)["version"], DOOR_VERSION)

        door = self.door("link")
        self.assertEqual(self.installed(timeout=5)["door_fate"], "link")
        self.assertEqual(os.readlink(door), self.path("elsewhere"))

    def test_door_fate_reads_and_never_raises(self):
        ours = str(ROOT / "bin" / "agentik")
        fate = agentik_install.door_fate
        self.assertEqual(fate(self.path("bin", "agentik"), ours), "write")
        for kind, want in ((b"0.1.0", "write"), (b"0.2.0", "keep"), (b"9.0.0", "keep"),
                           (b"banana", "unversioned"), ("fifo", "unversioned"), ("link", "link")):
            self.assertEqual(fate(self.door(kind), ours), want, kind)
        os.unlink(self.path("bin", "agentik"))
        os.mkdir(self.path("bin", "agentik"))
        self.assertEqual(fate(self.path("bin", "agentik"), ours), "unversioned")
        self.assertEqual(fate(self.door(b"0.1.0"), self.path("none")), "unversioned")


class PlanTest(Reach):
    def suite_rows(self, steps):
        return {s["id"]: s for s in steps if s["n"] == 5}

    def test_a5_the_frozen_command_plans_the_default_set(self):
        self.assertEqual(self.install()[0], 0)
        code, out, err = self.call([self.path("bin", "agentik-suite"), "setup", "--dry-run", "--json"])
        self.assertEqual(code, 0, err)
        got = json.loads(out)
        self.assertEqual(got["plugins"], json.loads(MANIFEST.read_text())["dependencies"])
        word = shlex.split(self.suite_rows(got["steps"])["suite"]["command"])[0]
        self.assertTrue(os.path.isfile(word), word)
        self.assertEqual(self.call([word, "--version"])[0], 0)

    def test_a6_step_five_names_this_commands_install_cli(self):
        rows = self.suite_rows(self.plan()["steps"])
        command = "%s install-cli" % shlex.quote(str(LAUNCHER))
        self.assertEqual((rows["suite"]["state"], rows["suite"]["command"]), ("todo", command))
        self.assertEqual(rows["door"]["state"], "todo")
        self.assertIsNone(rows["door"]["command"])
        self.assertIn("line above", rows["door"]["detail"])
        p = subprocess.run(["/bin/sh", "-c", command], env=self.env(), capture_output=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = self.suite_rows(self.plan()["steps"])
        self.assertEqual((rows["suite"]["state"], rows["door"]["state"]), ("ok", "ok"))
        # the suite's launcher at this version, an older door: the door's row carries the command
        door = os.path.join(self.home, ".local", "bin", "agentik")
        with open(door, "w") as fh:
            fh.write("#!/bin/sh\nVERSION=0.1.0\n")
        rows = self.suite_rows(self.plan()["steps"])
        self.assertEqual(rows["suite"]["state"], "ok")
        self.assertEqual((rows["door"]["state"], rows["door"]["command"]), ("todo", None))
        rows = self.suite_rows(self.plan(self.step_four_done())["steps"])
        self.assertEqual((rows["door"]["state"], rows["door"]["command"]), ("todo", command))
        p = subprocess.run(["/bin/sh", "-c", command], env=self.env(), capture_output=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(agentik_install.read_launcher(door)["version"], DOOR_VERSION)
        self.assertEqual(self.suite_rows(self.plan()["steps"])["door"]["state"], "ok")


class RootTest(Reach):
    def test_a7_the_root_setup(self):
        setup = ROOT / "setup"
        for argv in ([str(setup)], [os.path.relpath(str(setup), self.home)]):
            code, out, err = self.call(argv + ["--dry-run"], cwd=self.home)
            self.assertEqual(code, 0, err)
            self.assertIn("Setup plan", out)
        self.assertEqual(subprocess.run(["sh", "-n", str(setup)]).returncode, 0)
        self.assertLessEqual(len(setup.read_text().splitlines()), 6)
        self.assertTrue(os.access(str(setup), os.X_OK))

    def test_a8_make_install_is_one_line(self):
        env = {"HOME": self.home, "PATH": SYSTEM}
        for args, end in ((["PREFIX=/x"], 'install-cli --prefix "/x"'), ([], "install-cli")):
            p = subprocess.run(["make", "-n", "--no-print-directory", "install", *args], cwd=str(ROOT),
                               env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(len(p.stdout.splitlines()), 1, p.stdout)
            self.assertTrue(p.stdout.rstrip("\n").endswith(end), p.stdout)
            self.assertTrue(p.stdout.startswith("plugins/suite/bin/agentik-suite install-cli"), p.stdout)


class ReviewOneTest(Reach):
    """Review 1's mends: F1, F8 and F12 a missing --prefix; F2 no launcher moves backward; F6
    HOME's marker; F5 a prefix from ~; F4 the root setup through a link; F15 no read blocks."""

    def test_f1_f8_f12_a_missing_prefix_is_exit_two(self):
        cwd = os.path.join(self.home, "cwd")
        os.mkdir(cwd)
        before = self.snapshot()
        for args in (["--prefix", "--dry-run"], ["--prefix", "-q", "--json"], ["--prefix"],
                     ["--prefix", ""], ["--prefix="]):
            code, out, err = self.call([LAUNCHER, "install-cli"] + args, cwd=cwd)
            if "--json" in args:     # the refusal is the JSON object on stdout
                self.assertEqual((code, err), (2, ""), args)
                out, err = "", json.loads(out)["error"]["message"]
            self.assertEqual((code, out), (2, ""), args)
            self.assertEqual(len(err.splitlines()), 1, (args, err))
            self.assertIn("--prefix", err)
            self.assertIn("folder", err)
            self.assertEqual(os.listdir(cwd), [], args)
        self.assertEqual(self.snapshot(), before)

    def test_f2_a_newer_launcher_is_left_as_it_is(self):
        bindir = os.path.join(self.home, ".local", "bin")
        os.makedirs(bindir)
        own = os.path.join(bindir, "agentik-suite")
        with open(own, "w") as fh:
            fh.write("#!/bin/sh\nVERSION=9.0.0\n")
        os.chmod(own, 0o755)
        rows = {s["id"]: s for s in self.plan()["steps"] if s["n"] == 5}
        self.assertEqual((rows["suite"]["state"], rows["suite"]["command"]), ("ok", None))
        self.assertIn("newer", rows["suite"]["detail"])
        # the door's line is the newer launcher's own install-cli, never this older command's
        self.assertIsNone(rows["door"]["command"])  # until step 4's install-cli has run
        door = {s["id"]: s for s in self.plan(self.step_four_done())["steps"] if s["n"] == 5}["door"]
        self.assertEqual(door["command"], "%s install-cli" % shlex.quote(own))
        for line in [s["command"] for s in self.plan()["steps"] if s["command"] and s["n"] <= 5]:
            self.assertNotIn(str(LAUNCHER), line)
        self.assertEqual(agentik_install.read_launcher(own)["version"], "9.0.0")
        # an older one is todo with this command's line
        with open(own, "w") as fh:
            fh.write("#!/bin/sh\nVERSION=0.0.1\n")
        rows = {s["id"]: s for s in self.plan()["steps"] if s["n"] == 5}
        self.assertEqual((rows["suite"]["state"], rows["suite"]["command"]),
                         ("todo", "%s install-cli" % shlex.quote(str(LAUNCHER))))

    def test_f6_only_homes_own_prefix_clears_homes_marker(self):
        marker = os.path.join(self.home, ".local", "state", "agentik-suite", "install-needed")
        os.makedirs(os.path.dirname(marker))
        with open(marker, "w") as fh:
            fh.write("/old/tree\n")
        before = self.snapshot()
        self.assertEqual(self.install("-q")[0], 0)
        self.assertEqual(self.snapshot(), before)
        code, out, err = self.call([LAUNCHER, "install-cli", "-q"])
        self.assertEqual(code, 0, err)
        self.assertFalse(os.path.exists(marker))

    def test_f5_a_prefix_from_the_home_folder(self):
        code, out, err = self.call([LAUNCHER, "install-cli", "--prefix", "~/x", "--dry-run", "--json"],
                                   cwd=self.stubs)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["launcher"], os.path.join(self.home, "x", "bin", "agentik-suite"))
        p = subprocess.run(["/bin/zsh", "-fc", "make -n --no-print-directory install PREFIX=~/x"],
                           cwd=str(ROOT), env={"HOME": self.home, "PATH": SYSTEM},
                           capture_output=True, text=True, timeout=60)
        self.assertTrue(p.stdout.rstrip("\n").endswith('--prefix "~/x"'), p.stdout)

    def test_f4_the_root_setup_through_a_link(self):
        links = os.path.join(self.home, "a link dir")
        os.mkdir(links)
        os.symlink(str(ROOT / "setup"), os.path.join(links, "setup"))
        os.symlink(os.path.join(links, "setup"), os.path.join(links, "again"))
        for name in ("setup", "again"):
            code, out, err = self.call([os.path.join(links, name), "--dry-run"], cwd=self.stubs)
            self.assertEqual(code, 0, err)
            self.assertIn("Setup plan", out)

    def test_f15_no_read_of_a_file_that_is_not_regular(self):
        plugins = os.path.join(self.home, ".claude", "plugins")
        bindir = os.path.join(self.home, ".local", "bin")
        os.makedirs(plugins)
        os.makedirs(bindir)
        for path in (os.path.join(plugins, "installed_plugins.json"),
                     os.path.join(plugins, "known_marketplaces.json"),
                     os.path.join(bindir, "agentik-suite"), os.path.join(bindir, "agentik-alpha")):
            os.mkfifo(path)
        code, out, err = self.call([LAUNCHER, "setup", "--dry-run", "--json", "alpha"], timeout=5)
        self.assertEqual(code, 0, err)
        state = {(s["n"], s["id"]): s["state"] for s in json.loads(out)["steps"]}
        self.assertEqual(state[(2, "marketplace")], "todo")
        self.assertEqual(state[(3, "plugin")], "todo")
        self.assertEqual(state[(5, "suite")], "todo")
        self.assertIsNone(agentik_install.read_launcher(os.path.join(bindir, "agentik-suite")))


if __name__ == "__main__":
    unittest.main()
