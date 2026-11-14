"""Row fh13-relay-plan: setup says which command it cannot place and names the tool's page.

`murmur` is a made-up tool whose table row in a temp copy of the suite's plugin holds a `page`;
`plain` is one with none. Each home is fk_homes' in a temp HOME: `h0` empty, `hL` the tool's
`@agentik` plugin with no `bin/`, `hM` that with an executable stub at `~/.local/bin`. The
terminal's PATH is `~/.local/bin:/usr/bin:/bin` and a folder holding a stub `claude` that logs its
words. No test opens the page, starts the real `claude`, or reads the real home; `setup --yes`
runs in a temp HOME only."""
import fcntl
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import termios
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fk_homes import RAN, build  # noqa: E402
from test_agentik_suite import PLUGIN, version  # noqa: E402
from test_sc3_table import plain as unpaint, pty_run  # noqa: E402
from agentik_suite import apply, plan  # noqa: E402

T, P = "murmur", "plain"
PAGE = "https://example.com/murmur#install"
SUITE = "agentik-suite"
ROW = {"lines": ["agentik murmur doctor"], "user_file": None, "needs": [], "status": []}
PAGE_LINE = "its page has the line: %s" % PAGE
LAUNCHER_PAGE = "not placed, and not setup's to place: murmur installs its own command"
DOCTOR_PAGE = "not checked: its command is not installed yet"
CLOSE = "next: step 4 names the page with the install line for murmur. Setup has done the rest."
# the pin's words for a tool with no page, measured at 82d634b with the relay in its place
PIN = {"h0": ("setup.launcher.wait", "setup.doctor.wait"),
       "hL": ("setup.launcher.none", "setup.doctor.nocmd"),
       "hM": ("setup.launcher.none", "setup.doctor.nocmd")}


class Base(unittest.TestCase):
    page = PAGE

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = os.path.realpath(tmp.name)
        self.root = os.path.join(self.tmp, "suite")
        shutil.copytree(str(PLUGIN), self.root, ignore=shutil.ignore_patterns("__pycache__"))
        self.lib = os.path.join(self.root, "lib")
        self.launcher = os.path.join(self.root, "bin", SUITE)
        path = os.path.join(self.lib, "fallback.json")
        with open(path) as fh:
            table = json.load(fh)
        table[T] = dict(ROW, page=self.page)
        table[P] = dict(ROW, lines=["agentik plain doctor"])
        with open(path, "w") as fh:
            json.dump(table, fh)

    def home(self, name, tool=T):
        self.count = getattr(self, "count", 0) + 1
        path = os.path.join(self.tmp, "%s%d" % (name, self.count))  # no tool's name in the path
        os.mkdir(path)
        h = build(name, path, tool)
        h.stubs = os.path.join(path, "stubs")
        h.file(os.path.join(h.stubs, "claude"), RAN)
        return h

    def bindir(self, h):
        return os.path.join(h.home, ".local", "bin")

    def env(self, h, path=None, **more):
        search = path or os.pathsep.join([self.bindir(h), "/usr/bin", "/bin", h.stubs])
        return dict({"HOME": h.home, "PATH": search, "XDG_CACHE_HOME": os.path.join(h.home, "cache")}, **more)

    def cli(self, h, *args, path=None):
        p = subprocess.run([self.launcher] + list(args), capture_output=True, text=True,
                           env=self.env(h, path), cwd=h.home, timeout=120, stdin=subprocess.DEVNULL)
        return p.returncode, p.stdout, p.stderr

    def plan(self, h, tool=T, path=None):
        """The steps in process and through `setup --dry-run --json`, checked to agree."""
        old = os.getcwd()
        os.chdir(h.home)
        try:
            steps = plan.build([tool], self.env(h, path), self.lib, SUITE, version())
        finally:
            os.chdir(old)
        code, out, err = self.cli(h, "setup", "--dry-run", "--json", tool, path=path)
        self.assertEqual(code, 0, err)
        dry = json.loads(out)["steps"]
        self.assertEqual([(s["n"], s["state"], s["subject"], s["command"]) for s in steps],
                         [(s["n"], s["state"], s["subject"], s["command"]) for s in dry])
        for s, d in zip(steps, dry):
            s["detail"] = d["detail"]
            self.assertEqual(s.get("page"), d.get("page"))
        return steps

    def one(self, steps, n, tool=T):
        found = [s for s in steps if s["n"] == n and tool in s["subject"]]
        self.assertEqual(len(found), 1, found)
        return found[0]

    def screen(self, h, tool=T, path=None):
        code, out, err = self.cli(h, "setup", "--dry-run", tool, path=path)
        self.assertEqual(code, 0, err)
        return out, err

    def settle(self, h):
        """Step 5 ok: the suite's launcher at this version and the copy's own door."""
        os.makedirs(self.bindir(h), exist_ok=True)
        h.file(os.path.join(self.bindir(h), SUITE), "#!/bin/sh\nVERSION=%s\nexit 0\n" % version())
        shutil.copy(os.path.join(self.root, "bin", "agentik"), os.path.join(self.bindir(h), "agentik"))


class PageTest(Base):
    def assert_page(self, steps, out):
        four, seven = self.one(steps, 4), self.one(steps, 7)
        self.assertEqual((four["state"], four["mid"], four["command"], four["line"], four["page"]),
                         ("todo", "setup.launcher.page", None, "page", PAGE))
        self.assertEqual(four["detail"], LAUNCHER_PAGE)
        self.assertEqual((seven["state"], seven["mid"], seven["command"]), ("todo", "setup.doctor.page", None))
        self.assertEqual(seven["detail"], DOCTOR_PAGE)
        self.assertEqual(out.count(PAGE), 1, out)
        self.assertIn(PAGE_LINE, out)
        self.assertNotIn("places the launcher", out)

    def test_1_an_empty_home_names_the_page(self):
        h = self.home("h0")
        out, _ = self.screen(h)
        self.assert_page(self.plan(h), out)

    def test_2_the_plugin_with_no_command_names_the_page_and_reads_no_ok(self):
        h = self.home("hL")
        out, _ = self.screen(h)
        self.assert_page(self.plan(h), out)
        self.assertNotIn("the plugin ships no command", out)

    def test_3_its_own_command_at_w_is_left_as_it_is(self):
        h = self.home("hM")
        steps = self.plan(h)
        where = os.path.join(self.bindir(h), "agentik-" + T)
        four, seven = self.one(steps, 4), self.one(steps, 7)
        self.assertEqual((four["state"], four["mid"], four["command"]), ("ok", "setup.launcher.theirs", None))
        self.assertEqual(four["detail"], "murmur installed its own command, at ~/.local/bin/agentik-murmur; "
                                         "setup leaves it as it is")
        self.assertEqual((seven["state"], seven["command"], seven["line"]), ("todo", "%s doctor" % where, "later"))
        self.assertFalse([s for s in steps if s["command"] and "install-cli" in s["command"] and T in s["command"]])
        out, _ = self.screen(h)
        self.assertIn("yours to run later: %s doctor" % where, out)
        self.assertNotIn(PAGE, out)

    def test_4_the_close_names_the_page_once_nothing_is_left_to_run(self):
        h = self.home("hL")
        _, err = self.screen(h)  # step 5's command is left: the pin's close
        self.assertEqual(err.splitlines()[-1], "next: %s setup murmur" % self.launcher)
        self.settle(h)
        steps = self.plan(h)
        self.assertEqual({s["state"] for s in steps if s["n"] not in (4, 7)}, {"ok"})
        _, err = self.screen(h)
        self.assertEqual(err.splitlines()[-1], CLOSE)
        # before the PATH line's close: the add line stays under its own row
        out, err = self.screen(h, path=os.pathsep.join(["/usr/bin", "/bin", h.stubs]))
        self.assertEqual(err.splitlines()[-1], CLOSE)
        self.assertIn("add to your shell profile:", out)

    def test_4_the_close_joins_each_page_tool_in_the_plans_order(self):
        steps = [plan._step(4, "launcher", "todo", "~/.local/bin/agentik-" + n, "setup.launcher.page",
                            line="page", name=n) for n in ("murmur", "hum")]
        for s in steps:
            s["page"] = PAGE
        self.assertEqual(apply.page_close(steps), ("hint.setup.page", {"names": "murmur, hum"}))
        steps.append(plan._step(5, "suite", "todo", "~/.local/bin/agentik-suite", "setup.suite.missing", "x install-cli"))
        self.assertIsNone(apply.page_close(steps))  # a command left to run: the pin's close

    def test_5_an_applied_run_starts_nothing_for_the_page_and_closes_on_it(self):
        h = self.home("hL")
        code, out, err = self.cli(h, "setup", "--yes", T)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(err.splitlines()[-1], CLOSE)
        self.assertFalse(os.path.lexists(os.path.join(self.bindir(h), "agentik-" + T)))
        self.assertFalse([line for line in h.ran() if T in line], h.ran())
        self.assertFalse([line for line in err.splitlines() if line.startswith("running") and T in line])
        self.assertIn("install-cli", err)  # the suite's own step ran

    def test_6_its_word_refuses_with_the_page(self):
        for name, remedy in (("hL", "config"), ("h0", "setup")):
            h = self.home(name)
            code, out, err = self.cli(h, T, "doctor")
            self.assertEqual(code, 3, err)
            self.assertIn("murmur has no command here yet: it installs its own. Its page has the line: %s" % PAGE, err)
            self.assertEqual(err.splitlines()[-1], "next: %s %s murmur" % (self.launcher, remedy))
            code, out, err = self.cli(h, T, "doctor", "--json")
            self.assertEqual(code, 3)
            got = json.loads(out)["error"]
            self.assertEqual(got["code"], "not_installed")
            self.assertEqual(got["remedy"], "%s %s murmur" % (self.launcher, remedy))

    def test_6_a_plugin_with_no_page_keeps_its_refusal(self):
        h = self.home("hL", P)
        code, out, err = self.cli(h, P, "doctor")
        self.assertEqual(code, 3)
        self.assertIn("plain is a plugin with no command", err)

    def test_7_a_tool_with_no_page_reads_as_at_the_pin(self):
        for name, (four, seven) in PIN.items():
            h = self.home(name, P)
            steps = self.plan(h, P)
            self.assertEqual((self.one(steps, 4, P)["mid"], self.one(steps, 7, P)["mid"]), (four, seven), name)
            self.assertFalse([s for s in steps if "page" in s])
            out, err = self.screen(h, P)
            self.assertNotIn("page", out + err)
            if name != "h0":
                self.assertIn("ok    ~/.local/bin/agentik-plain  the plugin ships no command, so there is "
                              "nothing to place", out)
                self.assertIn("ok    agentik-plain               the plugin ships no command, so it has no "
                              "doctor to run", out)

    def test_9_each_line_to_paste_runs(self):
        homes = [self.home(n) for n in ("h0", "hL", "hM")]
        settled = self.home("hL")
        homes.append(settled)
        self.settle(settled)
        left_out = []
        for h in homes:
            out, err = self.screen(h)
            lines = [re.sub(r"^\s*", "", line) for line in (out + err).splitlines()]
            pasted = [line.split(": ", 1)[1] for line in lines if line.startswith(("next: ", "yours to run later: "))
                      and line != CLOSE]
            left_out += [line for line in lines if line == CLOSE]
            for line in pasted:
                p = subprocess.run(["/bin/sh", "-c", line], capture_output=True, text=True, env=self.env(h),
                                   cwd=h.home, stdin=subprocess.DEVNULL, timeout=120)
                self.assertNotEqual(p.returncode, 127, (line, p.stderr))
        self.assertEqual(left_out, [CLOSE])  # hint.setup.page is no command: the settled home's, left out

    def test_10_the_page_stands_whole_at_60_columns(self):
        h = self.home("hL")
        text = unpaint(pty_run(self.launcher, ["setup", "--dry-run", T], dict(self.env(h), COLUMNS="60"), 60))
        lines = text.replace("\r\n", "\n").split("\n")
        self.assertEqual(sum(line.count(PAGE) for line in lines), 1, text)  # one piece: never cut
        self.assertEqual([line.strip() for line in lines if PAGE in line], [PAGE_LINE], text)  # on its own line, as a command

    def assert_page_row(self, out):
        """Step 4's row of the page and, on the line under it, the page: what the close points to."""
        lines = [line.strip() for line in unpaint(out).splitlines()]
        at = [i for i, line in enumerate(lines) if line.endswith(LAUNCHER_PAGE)]
        self.assertEqual(len(at), 1, out)
        self.assertIn("~/.local/bin/agentik-murmur", lines[at[0]])
        self.assertEqual(lines[at[0] + 1:at[0] + 2], [PAGE_LINE], out)
        self.assertEqual(out.count(PAGE), 1, out)

    def test_f1_nothing_to_do_shows_the_page_above_its_close(self):
        for args in (("setup", T), ("setup", "--yes", T)):  # stdin closed, then a yes
            h = self.home("hL")
            self.settle(h)
            code, out, err = self.cli(h, *args)
            self.assertEqual(code, 0, out + err)
            self.assertIn("Setup has nothing to do", out + err)
            self.assertEqual(err.splitlines()[-1], CLOSE)
            self.assert_page_row(out)
            self.assertFalse(h.ran(), args)

    def test_f1_an_applied_runs_report_keeps_the_page_under_step_4(self):
        h = self.home("hL")
        code, out, err = self.cli(h, "setup", "--yes", T)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(err.splitlines()[-1], CLOSE)
        self.assertIn("The plan, read again after the run:", out)
        self.assert_page_row(out.split("The plan, read again after the run:", 1)[1])

    def off(self, h):
        """The terminal's PATH without ~/.local/bin."""
        return os.pathsep.join(["/usr/bin", "/bin", h.stubs])

    def test_f2_its_own_command_at_w_off_path_is_left_as_it_is(self):
        h = self.home("hM")
        self.settle(h)
        where = os.path.join(self.bindir(h), "agentik-" + T)
        steps = self.plan(h, path=self.off(h))
        four, seven = self.one(steps, 4), self.one(steps, 7)
        self.assertEqual((four["state"], four["mid"], four["command"], four["line"]),
                         ("ok", "setup.launcher.theirs", None, "run"))
        self.assertEqual(four["detail"], "murmur installed its own command, at ~/.local/bin/agentik-murmur; "
                                         "setup leaves it as it is")
        self.assertEqual((seven["state"], seven["mid"], seven["command"], seven["line"]),
                         ("todo", "setup.doctor.todo", "%s doctor" % where, "later"))
        self.assertFalse([s for s in steps if s["line"] == "page" or "page" in s])
        self.assertFalse([s for s in steps if s["command"] and "install-cli" in s["command"] and T in s["command"]])
        out, err = self.screen(h, path=self.off(h))
        self.assertNotIn(PAGE, out + err)
        self.assertIn("yours to run later: %s doctor" % where, out)
        self.assertIn("add to your shell profile:", out)
        path_close = "next: add the line marked add above to your shell profile, then open a new terminal."
        self.assertEqual(err.splitlines()[-1], path_close)
        with open(where) as fh:
            body = fh.read()
        code, out, err = self.cli(h, "setup", "--yes", T, path=self.off(h))
        self.assertEqual(code, 0, out + err)
        self.assertNotIn(PAGE, out + err)  # the report's add line and the pin's close, no page's
        self.assertIn("add to your shell profile:", out + err)
        self.assertEqual(err.splitlines()[-1], "next: ~/.local/bin/agentik doctor checks each plugin.")
        with open(where) as fh:
            self.assertEqual(fh.read(), body)  # setup writes nothing at W
        self.assertFalse([line for line in h.ran() if T in line], h.ran())

    def test_f2_no_file_that_runs_at_w_keeps_the_page(self):
        for kind in ("dangling link", "file that is not executable", "folder"):
            h = self.home("hL")
            self.settle(h)
            where = os.path.join(self.bindir(h), "agentik-" + T)
            if kind == "dangling link":
                os.symlink(os.path.join(h.home, "nowhere"), where)
            elif kind == "folder":
                os.mkdir(where)
            else:
                h.file(where, "#!/bin/sh\nexit 0\n")
                os.chmod(where, 0o644)
            for path in (None, self.off(h)):
                steps = self.plan(h, path=path)
                self.assertEqual((self.one(steps, 4)["mid"], self.one(steps, 7)["mid"]),
                                 ("setup.launcher.page", "setup.doctor.page"), (kind, path))

    def test_r6_a_page_row_is_never_run_nor_counted(self):
        h = self.home("hL")
        steps = self.plan(h)
        four = self.one(steps, 4)
        self.assertNotIn(four, apply.runnable(steps))
        self.settle(h)
        self.assertEqual(apply.planned(self.plan(h)), 0)


class NotAPageTest(Base):
    """Line 8: a `page` that is not an https string, or that holds whitespace or a control
    character, is read as absent."""

    def assert_no_page(self, page):
        self.page = page
        self.setUp()
        for name, (four, seven) in PIN.items():
            h = self.home(name)
            steps = self.plan(h)
            self.assertEqual((self.one(steps, 4)["mid"], self.one(steps, 7)["mid"]), (four, seven), (page, name))
            self.assertFalse([s for s in steps if "page" in s])

    def test_8_a_number_a_list_or_another_scheme_is_no_page(self):
        for page in (7, [PAGE], "http://example.com/murmur", ""):
            self.assert_no_page(page)

    def test_8_whitespace_or_a_control_character_is_no_page(self):
        for page in ("https://example.com/a b", "https://example.com/murmur\nnext: touch x",
                     "https://example.com/\tx", "https://example.com/\x1b[2J", "https://example.com/\x00",
                     "https://example.com/\x07", "https://example.com/" + chr(0x202E) + "x",
                     "https://example.com/" + chr(0xA0) + "x"):
            self.assert_no_page(page)


if __name__ == "__main__":
    unittest.main()
