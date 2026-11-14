"""Row fk2-plan: the suite lists and runs what the finder names, and setup plans by it.

Each home is fk_homes' in a temp HOME, with a stub `claude` and the `agentik` marketplace's own
file listing the made-up tool; a command logs each run to `$HOME/ran.log`. No test runs `setup`
without `--dry-run`, starts the real `claude` or reads the real home."""
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fk_homes import RAN, T, build  # noqa: E402
from test_agentik_suite import LAUNCHER, LIB, version  # noqa: E402
from agentik_suite import apply, cli, plan, tools  # noqa: E402

U, F = T + "@agentik", T + "@acme-tools"
SUITE = "agentik-suite"


@contextlib.contextmanager
def inside(folder):
    """The calls in process read the cwd as the command does, so each runs from the home's."""
    old = os.getcwd()
    os.chdir(folder)
    try:
        yield
    finally:
        os.chdir(old)


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = os.path.realpath(tmp.name)

    def home(self, name, *listed, folder=None):
        path = os.path.join(self.tmp, folder or name)
        os.mkdir(path)
        return build(name, path).ready(*listed)

    def env(self, h, *more, **extra):
        return h.env(path=h.terminal(h.stubs, *more), XDG_CACHE_HOME=os.path.join(h.home, "cache"), **extra)

    def cli(self, h, *args, more=(), cwd=None):
        p = subprocess.run([str(LAUNCHER)] + list(args), capture_output=True, text=True,
                           env=self.env(h, *more), cwd=cwd or h.cwd, timeout=60)
        return p.returncode, p.stdout, p.stderr

    def plan(self, h, *names, cwd=None):
        """The steps in process and through `setup --dry-run --json`, checked to agree."""
        names = list(names) or [T]
        with inside(cwd or h.cwd):
            steps = plan.build(names, self.env(h), str(LIB), SUITE, version())
        code, out, err = self.cli(h, "setup", "--dry-run", "--json", *names, cwd=cwd)
        self.assertEqual(code, 0, err)
        dry = json.loads(out)["steps"]
        self.assertEqual([(s["n"], s["state"], s["subject"], s["command"]) for s in steps],
                         [(s["n"], s["state"], s["subject"], s["command"]) for s in dry])
        for s, d in zip(steps, dry):
            s["detail"] = d["detail"]
        return steps

    def of(self, steps, name=T):
        """The steps that name `name`: steps 3, 4 and 7 and a held row."""
        return [s for s in steps if s["n"] in (3, 4, 7) and name in s["subject"]]

    def one(self, steps, n, name=T):
        found = [s for s in self.of(steps, name) if s["n"] == n]
        self.assertEqual(len(found), 1, found)
        return found[0]


class Fk2Test(Base):
    # line 1
    def test_1_a_fork_alone_reads_ok_and_nothing_is_installed(self):
        h = self.home("hA")
        steps = self.plan(h)
        s3 = self.one(steps, 3)
        self.assertEqual((s3["state"], s3["subject"], s3["command"]), ("ok", F, None))
        self.assertIn("0.12.6", s3["detail"])
        self.assertFalse([s for s in steps if "plugin install" in (s["command"] or "")])
        self.assertEqual(self.one(steps, 4)["mid"], "setup.launcher.none")

    # line 2
    def test_2_two_plugins_of_one_name_are_one_held_row(self):
        for name in ("hB", "hH", "hI"):
            h = self.home(name)
            rows = self.of(self.plan(h))
            self.assertEqual(len(rows), 1, (name, rows))
            self.assertEqual((rows[0]["state"], rows[0]["command"], rows[0]["mid"]),
                             ("todo", None, "setup.plugin.held"), name)
            self.assertIn("suite.sources.%s" % T, rows[0]["detail"], name)
            self.assertIn("2", rows[0]["detail"], name)

    # line 3
    def test_3_pc_held_and_with_the_line_names_the_file_earlier_on_path(self):
        h = self.home("pC")
        rows = self.of(self.plan(h))
        self.assertEqual([(s["state"], s["command"], s["mid"]) for s in rows],
                         [("todo", None, "setup.plugin.held")])
        h.user_file("sources:\n  %s: %s\n" % (T, U))
        steps = self.plan(h)
        s3, s4 = self.one(steps, 3), self.one(steps, 4)
        self.assertEqual((s3["state"], s3["subject"], s3["mid"]), ("ok", U, "setup.plugin.ok"))
        self.assertEqual((s4["state"], s4["command"], s4["mid"]), ("todo", None, "setup.launcher.earlier"))
        self.assertIn("~/bin/agentik-" + T, s4["detail"])
        self.assertEqual(apply.planned(steps), len(apply.runnable(steps)))  # R7

    # line 4
    def test_4_a_projects_older_entry_moves_no_launcher_backward(self):
        h = self.home("pB")
        h.commands()
        steps = self.plan(h)
        self.assertFalse([s for s in self.of(steps) if s["n"] in (3, 4) and s["state"] == "todo"])
        self.assertEqual(self.one(steps, 3)["values"], {"version": "0.13.0"})
        s4 = self.one(steps, 4)
        self.assertEqual((s4["mid"], s4["values"]), ("setup.launcher.ok", {"version": "0.13.0"}))

    # line 5
    def test_5_a_declared_folder_that_is_gone_is_a_row_with_no_command(self):
        h = self.home("hJ")
        steps = self.plan(h, T, "paint")
        s3 = self.one(steps, 3, "paint")
        self.assertEqual((s3["state"], s3["command"], s3["mid"]), ("todo", None, "setup.plugin.declared"))
        self.assertIn("~/.config/agentik/suite/config.yaml:3", s3["detail"])
        self.assertEqual([s["n"] for s in self.of(steps, "paint")], [3])
        self.assertEqual(self.one(steps, 3)["subject"], F)

    # line 6
    def test_6_absent_and_the_line_for_the_own_plugin_install_it(self):
        h = self.home("hG")
        s3 = self.one(self.plan(h), 3)
        self.assertEqual((s3["state"], s3["subject"], s3["command"], s3["mid"]),
                         ("todo", U, "claude plugin install " + U, "setup.plugin.missing"))
        h.install(F, "0.12.6")
        h.user_file("sources:\n  %s: %s\n" % (T, U))
        s3 = self.one(self.plan(h), 3)
        self.assertEqual((s3["state"], s3["subject"], s3["command"]), ("todo", U, "claude plugin install " + U))

    # line 7
    def test_7_config_and_doctor_run_the_standing_file_and_never_one_that_does_not_stand(self):
        for name in ("pA", "hD"):
            h = self.home(name)
            cmd = h.commands()[F]
            for verb in ("config", "doctor"):
                code, out, err = self.cli(h, verb, "--json")
                self.assertEqual(code, 0, err)
            lines = h.ran()
            self.assertTrue(lines, name)
            self.assertTrue(all(line.startswith(cmd + " ") for line in lines), (name, lines))
            self.assertIn(cmd + " describe --json", lines, name)
        h = self.home("hB")
        h.commands()
        for verb in ("config", "doctor", "status"):  # status's read too (R3)
            code, out, err = self.cli(h, verb, "--json", more=h.bins())
            self.assertEqual(code, 0, err)
        self.assertEqual(h.ran(), [])

    # line 8
    def test_8_config_lists_a_fork_alone(self):
        h = self.home("hA")
        code, out, err = self.cli(h, "config", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual([t["name"] for t in json.loads(out)["tools"]], ["suite", T])

    # R4 to R6, beyond the lines
    def test_r4_a_lone_plugin_a_repos_settings_brought_is_held(self):
        h = self.home("hG")
        project = os.path.join(h.home, "work", "app")
        os.makedirs(project)
        h.install(U, "0.11.0", scope="project", project=project)
        rows = self.of(self.plan(h, cwd=project))
        self.assertEqual([(s["state"], s["command"], s["mid"]) for s in rows],
                         [("todo", None, "setup.plugin.held.repo")])

    def test_r5_a_link_to_the_sources_own_file_reads_ok_and_step_7_names_it(self):
        h = self.home("hC")
        steps = self.plan(h)
        self.assertEqual(self.one(steps, 4)["mid"], "setup.launcher.link")
        self.assertEqual(self.one(steps, 7)["command"], h.link + " doctor")

    def test_r5_another_sources_version_is_never_called_behind(self):
        h = self.home("hD")
        h.launcher(os.path.join(".local", "bin"), "0.11.0")
        s4 = self.one(self.plan(h), 4)
        self.assertEqual((s4["state"], s4["mid"], s4["values"]),
                         ("todo", "setup.launcher.other", {"have": "0.11.0", "want": "0.12.6"}))
        self.assertEqual(s4["command"], h.cmd + " install-cli")
        self.assertNotRegex(s4["detail"], r"behind|older|newer")

    def test_r6_step_7_names_the_file_that_runs_and_the_door_waits_on_no_row(self):
        h = self.home("pC")
        h.user_file("sources:\n  %s: %s\n" % (T, U))
        h.file(os.path.join(h.home, ".local", "bin", SUITE), "#!/bin/sh\nVERSION=%s\nTREE=%s/t\n" % (version(), h.home))
        steps = self.plan(h)
        self.assertEqual(self.one(steps, 7)["command"], os.path.join(h.home, "bin", "agentik-" + T) + " doctor")
        self.assertEqual([s["mid"] for s in steps if s["id"] == "door"], ["setup.door.place"])

    # R1, R2
    def test_r1_installed_names_the_known_whose_kind_is_not_absent(self):
        h = self.home("hA")
        h.install("zap@acme-tools", "1.0.0")  # another marketplace's plugin of no known name
        env = self.env(h)
        with inside(h.cwd):
            self.assertEqual(tools.installed(env), [T])
            self.assertNotIn("zap", tools.plugin_names(env, str(LIB)))
            h = self.home("hJ")
            self.assertIn("paint", tools.plugin_names(self.env(h), str(LIB)))
            self.assertIn("paint", tools.installed(self.env(h)))  # declared, not found: not absent

    def test_r2_listed_gives_the_finders_file_and_row(self):
        h = self.home("hD")
        with inside(h.cwd):
            entry = [e for e in tools.listed("suite", [], self.env(h)) if e["name"] == T][0]
        self.assertEqual((entry["exe"], entry["plugin"]), (h.cmd, True))
        self.assertEqual((entry["source"]["kind"], entry["source"]["plugin"]), ("plugin", F))
        other = os.path.join(h.home, "elsewhere", "agentik-other")
        h.file(other, RAN)
        with inside(h.cwd):
            found = tools.listed("suite", [{"name": "agentik-other", "path": other}], self.env(h))
        self.assertEqual([e for e in found if e["name"] == "other"],
                         [{"name": "other", "exe": other, "plugin": False, "source": None}])

    # R7
    def test_r7_install_root_takes_the_finders_root(self):
        h = self.home("pB")
        with inside(h.cwd):
            root, there = apply.install_root(self.env(h), U)
        self.assertEqual((root, there), (h.table[U][1]["installPath"], True))

    def test_r7_a_held_row_is_no_command_to_count_or_close_on(self):
        h = self.home("hB")
        steps = self.plan(h)
        self.assertEqual(apply.planned(steps), len(apply.runnable(steps)))
        self.assertFalse([s for s in apply.runnable(steps) if s["n"] == 3])
        ok = [{"n": n, "state": "ok", "command": None, "line": "run"} for n in (1, 2, 4, 5, 6)]
        held = {"n": 3, "state": "todo", "command": None, "line": "run"}
        me = types.SimpleNamespace(say=lambda *w: "setup")
        self.assertEqual(cli.Command._closing(me, ok + [held], []), ("hint.setup.rest", {}))


class OwnBytesTest(Base):
    """The callers the brief does not name keep their bytes for a tool whose kind is `own`; the
    values below are the pin's (43e902e), read in the same homes."""

    def own(self, placed):
        h = self.home("hF")
        if placed:
            h.commands()
            h.file(os.path.join(h.home, ".local", "bin", "agentik-" + T),
                   "#!/bin/sh\nVERSION=0.13.0\nTREE=%s/t\n" % h.home + RAN.split("\n", 1)[1])
        return h

    def test_own_bare(self):
        h = self.own(False)
        code, out, err = self.cli(h, T)
        self.assertEqual((code, err.splitlines()[0]), (3, "FAIL  %s is a plugin with no command" % T))
        steps = self.plan(h)
        self.assertEqual([(s["n"], s["state"], s["subject"], s["detail"], s["command"]) for s in self.of(steps)], [
            (3, "ok", U, "installed at version 0.13.0", None),
            (4, "ok", "~/.local/bin/agentik-" + T, "the plugin ships no command, so there is nothing to place", None),
            (7, "ok", "agentik-" + T, "the plugin ships no command, so it has no doctor to run", None)])
        with inside(h.cwd):
            self.assertEqual(tools.installed(self.env(h)), [T])

    def test_own_placed(self):
        h = self.own(True)
        code, out, err = self.cli(h, T)
        self.assertEqual((code, err.splitlines()), (2, ["FAIL  %s is a tool, not a verb" % T,
                                                       "next: ~/.local/bin/agentik-%s --help" % T]))
        w = os.path.join(h.home, ".local", "bin", "agentik-" + T)
        steps = self.plan(h)
        self.assertEqual([(s["n"], s["state"], s["detail"], s["command"]) for s in self.of(steps)], [
            (3, "ok", "installed at version 0.13.0", None),
            (4, "ok", "at version 0.13.0, the same as the plugin", None),
            (7, "todo", "setup would check the plugin with its doctor", w + " doctor")])
        for verb in ("config", "doctor", "status"):
            code, out, err = self.cli(h, verb, "--json")
            self.assertEqual(code, 0, err)
        self.assertEqual(h.ran(), [w + " describe --json", w + " doctor --json", w + " doctor",
                                   w + " describe --json"])


def relink(path, target):
    os.remove(path)
    os.symlink(target, path)


class ReviewOneTest(Base):
    """Review 1's four findings, each red at 295b86f."""

    def setup_ran(self, h, cwd=None):
        """`ran.log` after `setup --dry-run`, then after `setup --yes`, in the temp HOME."""
        code, out, err = self.cli(h, "setup", "--dry-run", T, cwd=cwd)
        self.assertEqual(code, 0, err)
        dry = h.ran()
        p = subprocess.run([str(LAUNCHER), "setup", "--yes", T], capture_output=True, text=True,
                           env=self.env(h), cwd=cwd or h.cwd, stdin=subprocess.DEVNULL, timeout=120)
        return dry, h.ran(), p

    def no_command(self, h, cwd=None):
        steps = self.plan(h, cwd=cwd)
        self.assertEqual(self.one(steps, 4)["mid"], "setup.launcher.none")
        dry, yes, p = self.setup_ran(h, cwd)
        self.assertEqual((dry, yes), ([], []), p.stderr)

    # F1: a source's command that is a link out of its root is no command
    def test_f1_a_line_naming_the_fork_whose_command_links_into_the_marketplaces_root(self):
        h = self.home("hB")
        cmds = h.commands()
        h.user_file("sources:\n  %s: %s\n" % (T, F))
        relink(cmds[F], cmds[U])
        self.no_command(h)

    def test_f1_a_line_naming_the_own_plugin_whose_command_links_into_the_fork(self):
        h = self.home("hB")
        cmds = h.commands()
        h.user_file("sources:\n  %s: %s\n" % (T, U))
        relink(cmds[U], cmds[F])
        self.no_command(h)

    def test_f1_a_folder_source_whose_command_links_into_an_installed_root(self):
        h = self.home("hF")
        cmds = h.commands()
        fork = os.path.join(h.home, "forks", T)
        os.makedirs(os.path.join(fork, ".claude-plugin"))
        with open(os.path.join(fork, ".claude-plugin", "plugin.json"), "w") as fh:
            json.dump({"name": T, "version": "0.12.6"}, fh)
        os.makedirs(os.path.join(fork, "bin"))
        os.symlink(cmds[U], os.path.join(fork, "bin", "agentik-" + T))
        h.user_file("sources:\n  %s: ~/forks/%s\n" % (T, T))
        self.assertEqual(self.one(self.plan(h), 3)["subject"], "~/forks/" + T)
        self.no_command(h)

    def test_f1_an_own_tool_whose_command_links_into_another_root(self):
        h = self.home("pB")
        h.commands()
        os.remove(os.path.join(h.home, ".local", "bin", "agentik-" + T))
        project = os.path.join(h.table[U][0]["installPath"], "bin", "agentik-" + T)
        relink(os.path.join(h.table[U][1]["installPath"], "bin", "agentik-" + T), project)
        self.no_command(h)

    # F2: a file that is W, by a link to it or a folder linked to W's, is W
    def test_f2_a_link_to_w_is_w_and_a_stale_launcher_is_behind(self):
        for form in ("file", "folder"):
            h = self.home("hF", folder="hF-" + form)
            h.commands()
            w = h.launcher(os.path.join(".local", "bin"), "0.12.0")
            if form == "file":
                os.makedirs(os.path.join(h.home, "bin"))
                os.symlink(w, os.path.join(h.home, "bin", "agentik-" + T))
            else:
                os.symlink(os.path.join(h.home, ".local", "bin"), os.path.join(h.home, "bin"))
            s4 = self.one(self.plan(h), 4)
            self.assertEqual((s4["mid"], s4["values"]), ("setup.launcher.behind",
                                                         {"have": "0.12.0", "want": "0.13.0"}), form)
            self.assertEqual(s4["command"], h.cmd + " install-cli", form)

    # F3: the held row counts plugins, not entries
    def test_f3_one_plugin_installed_twice_is_not_two_plugins(self):
        h = self.home("pB")
        rows = self.of(self.plan(h, cwd=os.path.join(h.project, "sub")))
        self.assertEqual([(s["state"], s["command"], s["mid"]) for s in rows],
                         [("todo", None, "setup.plugin.held.twice")])
        self.assertNotIn("2 plugins", rows[0]["detail"])
        self.assertIn(U, rows[0]["detail"])

    # F4: a source with no string version names none and calls nothing the same
    def test_f4_a_source_with_no_string_version(self):
        for given, placed in ((None, None), (7, "7"), (None, "0.12.6")):
            h = self.home("hD", folder="hD-%s-%s" % (given, placed))
            if given is None:
                del h.table[F][0]["version"]
            else:
                h.table[F][0]["version"] = given
            h.write()
            if placed:
                h.launcher(os.path.join(".local", "bin"), placed)
            else:
                h.file(os.path.join(h.home, ".local", "bin", "agentik-" + T), "#!/bin/sh\nTREE=/t\nexit 0\n")
            steps = self.plan(h)
            self.assertEqual(self.one(steps, 3)["mid"], "setup.plugin.source.none")
            s4 = self.one(steps, 4)
            self.assertEqual((s4["state"], s4["mid"], s4["command"]), ("ok", "setup.launcher.noversion", None),
                             (given, placed))
            self.assertNotRegex(s4["detail"], r"None|same|behind|\b7\b|0\.12\.6")


if __name__ == "__main__":
    unittest.main()
