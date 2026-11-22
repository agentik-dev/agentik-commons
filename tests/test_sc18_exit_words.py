"""Row sc18-exit-words: the messages that talked of exit codes say what happened instead.

design/23 V9: no message holds `exit` or a code; V11: a child's own last line goes whole on its
own line under the line that names it; V3: the command to run again is the screen's `next:`, last.
A script still reads the code from `--json` (R8). Each home is a temp HOME of another module's
fixture, with a stub `claude` or `gh` that prints a made-up line and gives status 3; no test
starts a real `claude` or `gh`, reads the live home or reaches the network."""
import io
import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_ak4a_update as up  # noqa: E402
from test_screen_probe import probe  # noqa: E402
from agentik_suite import apply, cli  # noqa: E402

WORD = re.compile(r"\bexit", re.I)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # this checkout
AGAIN = re.compile(r"\brun\b.*\bagain\b")
SAID = "the made-up market is closed"
# a `claude` that fails one command, `$1 $2` of it, with SAID or silent, and passes the rest on
WRAP = '#!/bin/sh\nif [ "$1 $2" = "%s" ]; then\n%s  exit %d\nfi\nexec "$(dirname "$0")/claude.real" "$@"\n'


def wrap(h, verb, said=SAID, code=3):
    real = os.path.join(h.bin, "claude.real")
    if not os.path.exists(real):
        os.rename(os.path.join(h.bin, "claude"), real)
    h.file(os.path.join(h.bin, "claude"), WRAP % (verb, ("  echo '%s'\n" % said) if said else "", code))


def in_process(h, argv, result, env=None):
    """argv run in this process, each command's result `result` (setup's execute's shape) and
    nothing run: (status, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(apply, "execute", return_value=dict(result)):
        code = cli.Command(list(argv), env or h.env(), out, err).run()
    return code, out.getvalue(), err.getvalue()


def bare(text):
    """`text` with the paths the harness made taken off: the checkout's root and the temp folder,
    as given and as its real path, under which each fixture's home and work folders lie. A
    folder's name may hold the word or the code, and the test chose none of them."""
    temp = tempfile.gettempdir()
    for path, token in sorted({(ROOT, "<root>"), (os.path.realpath(ROOT), "<root>"),
                               (temp, "<tmp>"), (os.path.realpath(temp), "<tmp>")},
                              key=lambda pt: -len(pt[0])):
        text = text.replace(path, token)
    return text


class Shape:
    """The screen's asserts: no exit word or code, the child's line whole, `next:` last."""

    def clean(self, text, said=SAID, again=None, code=3):
        """The rows of `text`, the harness's paths out (see `bare`)."""
        rows = [r for r in bare(text).splitlines() if r.strip()]
        number = re.compile(r"(?<![\w.])%d(?![\w.])" % code)
        at = [i for i, r in enumerate(rows) if re.search(r"stopped|failed|could not", r)]
        for i, row in enumerate(rows):
            self.assertIsNone(WORD.search(row), text)
            if at and i >= at[0]:  # from the cause on: a step's number above it is no code
                self.assertIsNone(number.search(row), text)
            self.assertIsNone(AGAIN.search(row), text)
        if said:
            self.assertIn(said, [r.strip() for r in rows], text)
        if again:
            self.assertTrue(rows[-1].startswith("next: "), text)
            self.assertIn(again, rows[-1], text)
        return rows

    def pasted(self, rows, env, cwd):
        self.assertEqual(probe.check_paste(rows[-1][len("next: "):].strip(), env, cwd), [], rows[-1])


# ---- family: update -----------------------------------------------------------------------

class UpdateTest(Shape, up.Base):
    def failing(self, said=SAID):
        h = self.two_behind()
        wrap(h, "plugin update", said)
        return h

    def test_r1_a_failed_command_on_a_terminal_at_80(self):
        h = self.failing()
        rows = probe.render([str(up.LAUNCHER), "update", "--yes"], h.env(), h.home, "pty80", None)
        text = "\n".join(rows)
        self.clean(text, again="update")
        self.assertTrue([r for r in rows if "Update stopped: claude plugin update" in r and r.endswith("failed")], text)
        self.pasted([r for r in rows if r.strip()], h.env(), h.home)

    def test_r1_a_silent_command(self):
        h = self.failing(said=None)
        code, out, err = h.run("update", "--yes")
        self.assertEqual(code, 1, err)
        self.clean(out + err, said=None, again="update")
        self.assertIn("failed, and printed nothing", err)

    def test_r8_the_json_keeps_the_code_as_a_number(self):
        h = self.failing()
        code, out, err = h.run("update", "--yes", "--json")
        self.assertEqual(code, 1, err)
        error = json.loads(out)["error"]
        self.assertEqual((error["code"], error["exit"]), ("step_failed", 3))
        self.assertIsInstance(error["remedy"], str)
        self.assertIn(SAID, error["message"])
        self.assertIsNone(WORD.search(bare(error["message"])))

    def test_r1_a_step_that_ran_and_is_still_not_done(self):
        h = self.home()
        h.install("murmur@agentik", "1.1.0")  # its launcher behind it: step 3 runs install-cli
        h.file(os.path.join(h.bindir, "agentik-murmur"), "#!/bin/sh\nVERSION=1.0.0\nTREE=%s\nexit 0\n"
               % os.path.join(h.home, ".local", "share", "agentik-murmur", "1.0.0"))
        code, out, err = in_process(h, ["update", "--yes"], {"exit": 0, "last": "", "why": None, "wall": 120})
        self.assertEqual(code, 1, err)
        rows = self.clean(err, said=None, again="update --dry-run", code=0)
        self.assertTrue([r for r in rows if "ran and is still not done" in r], err)
        code, out, err = in_process(h, ["update", "--yes", "--json"], {"exit": 0, "last": "", "why": None, "wall": 120})
        self.assertEqual(json.loads(out)["error"]["exit"], 0)

    def test_r3_the_wall_and_the_start(self):
        h = self.two_behind()
        for result, words in (({"exit": None, "last": SAID, "why": "wall", "wall": 120}, "ran past 120 s"),
                              ({"exit": None, "last": "", "why": "wall", "wall": 120}, "printed nothing"),
                              ({"exit": None, "last": SAID, "why": "start", "wall": 120}, "could not start")):
            code, out, err = in_process(h, ["update", "--yes"], result)
            self.assertEqual(code, 1, err)
            self.clean(err, said=result["last"], again="update")
            self.assertIn(words, err)


# ---- family: remove -----------------------------------------------------------------------

class RemoveTest(Shape, up.Base):
    def x(self):
        import test_ak4_remove as rm
        h = rm.RHome(os.path.join(self.tmp, "h"), ("murmur", "paint", "x"))
        h.real_tool()
        env = h.env()
        h.under_temp(env)
        return h, env

    def test_r2_a_failed_command_on_a_terminal_at_80(self):
        h, env = self.x()
        wrap(h, "plugin uninstall")
        rows = probe.render([str(up.LAUNCHER), "remove", "x", "--yes"], env, h.home, "pty80", None)
        text = "\n".join(rows)
        self.clean(text, again="remove")
        self.assertTrue([r for r in rows if "Remove stopped: claude plugin uninstall" in r], text)
        self.pasted([r for r in rows if r.strip()], env, h.home)

    def test_r2_a_silent_command_and_the_json(self):
        h, env = self.x()
        wrap(h, "plugin uninstall", said=None)
        code, out, err = h.go("remove", "x", "--yes")
        self.assertEqual(code, 1, err)
        self.clean(out + err, said=None, again="remove")
        self.assertIn("failed, and printed nothing", err)
        wrap(h, "plugin uninstall")
        code, out, err = h.go("remove", "x", "--yes", "--json")
        error = json.loads(out)["error"]
        self.assertEqual((error["code"], error["exit"]), ("step_failed", 3))
        self.assertIn(SAID, error["message"])
        self.assertIsNone(WORD.search(bare(error["message"])))

    def test_r3_the_wall_and_the_start(self):
        h, env = self.x()
        for result, words in (({"exit": None, "last": SAID, "why": "wall", "wall": 120}, "ran past 120 s"),
                              ({"exit": None, "last": "", "why": "wall", "wall": 120}, "printed nothing"),
                              ({"exit": None, "last": SAID, "why": "start", "wall": 120}, "could not start")):
            code, out, err = in_process(h, ["remove", "x", "--yes"], result, env)
            self.assertEqual(code, 1, err)
            self.clean(err, said=result["last"], again="remove")
            self.assertIn(words, err)

    def test_r2_the_marketplace_that_stands(self):
        h, env = self.x()
        os.makedirs(os.path.join(h.plugins, "marketplaces", "agentik"))
        wrap(h, "plugin marketplace", said=None, code=0)
        code, out, err = h.go("remove", "--all", "--yes")
        rows = [r for r in (out + err).splitlines() if "stands:" in r]
        self.assertEqual(len(rows), 1, out + err)
        self.assertIn("ran and left it", rows[0])
        self.assertIsNone(WORD.search(bare(rows[0])))


# ---- family: inbox ------------------------------------------------------------------------

class InboxTest(Shape, unittest.TestCase):
    def setUp(self):
        import test_in4_inbox as inb
        self.home = type("H", (inb.InboxHome,), {"runTest": lambda s: None})()
        self.home.setUp()
        self.addCleanup(self.home.doCleanups)

    def test_r4_a_read_that_failed(self):
        h = self.home
        h.how("charter", exit=3)
        code, out, err = h.inbox(h.pear, h.quince)
        rows = [r for r in out.splitlines() if "not read" in r]
        self.assertEqual(rows, ["note  not read  charter: agentik-bench charter show --json failed"], out)
        self.clean(out + err, said=None)
        code, out, err = h.inbox("--json", h.pear)
        reads = [r for r in json.loads(out)["reads"] if r["name"] == "charter"]
        self.assertEqual([(r["state"], r["exit"]) for r in reads], [("no_answer", 3)])


# ---- family: issue ------------------------------------------------------------------------

class IssueTest(Shape, unittest.TestCase):
    def fixture(self, module, name):
        mod = __import__(module)
        home = type("H", (getattr(mod, name),), {"runTest": lambda s: None})()
        home.setUp()
        self.addCleanup(home.doCleanups)
        return mod, home

    def test_r5_gh_filed_nothing(self):
        rp5, h = self.fixture("test_rp5_send", "Base")
        h.stub("gh", (rp5.GH % h.gh).replace("sys.exit(code)", "if code:\n    sys.stderr.write(%r)\nsys.exit(code)"
                                    % ("HTTP 422: " + SAID + "\n")))
        h.fixture("issue_create.exit", "3")
        _, result = h.drive(rp5.draft(), b"send\n")
        self.assertEqual(result.get("refusal", [0, 0])[1], "err.issue.send.failed", result)
        code, mid, values = result["refusal"]
        self.assertEqual((code, mid, values["exit"], values["said"]),
                         (1, "err.issue.send.failed", 3, "HTTP 422: " + SAID))
        from agentik_suite import issue
        for argv in (["issue", "send"], ["issue", "send", "--json"]):
            out, err = io.StringIO(), io.StringIO()
            cmd = cli.Command(argv, h.env(), out, err)
            cmd.verb = "issue"
            self.assertEqual(cmd.fail(issue._usage(cmd, "failed", mid, exit_code=code, **values)), 1)
            if "--json" in argv:
                error = json.loads(out.getvalue())["error"]
                self.assertEqual((error["code"], error["exit"]), ("failed", 3))
                self.assertIn("HTTP 422: " + SAID, error["message"])
            else:
                rows = self.clean(err.getvalue(), said="HTTP 422: " + SAID)
                self.assertIn("gh filed nothing; the draft is kept", rows[0])

    def test_r6_the_flag_takes_a_number(self):
        _, h = self.fixture("test_rp6_issue", "IssueHome")
        code, out, err = h.issue("new", "--exit", "300")
        self.assertEqual(code, 2, err)
        self.assertEqual(err.splitlines()[0], "FAIL  --exit takes a number from 0 to 255, not 300")

    def test_r7_the_narrators_script_failed(self):
        _, h = self.fixture("test_rp8_render", "RenderHome")
        h.install()
        h.behave("Happened: one\nExpected: two\n", exit=3)
        code, out, err = h.new("--render")
        self.assertEqual(code, 0, err)
        lines = [r for r in (out + err).splitlines() if "template stands" in r]
        self.assertEqual(lines, ["The narrator's script failed, so the template stands unchanged."], out + err)

    def test_r8_the_json_keeps_the_narrators_code(self):
        """The screen's line lost the code (R7); a script reads it from `--json`'s `render.exit`."""
        _, h = self.fixture("test_rp8_render", "RenderHome")
        h.install()
        h.behave("Happened: one\nExpected: two\n", exit=3)
        code, out, err = h.new("--render", "--json")
        self.assertEqual(code, 0, err)
        said = json.loads(out)["render"]
        self.assertEqual((said["rendered"], said["why"], said["exit"]), (False, "exit", 3), out)
        self.assertIs(type(said["exit"]), int, out)


if __name__ == "__main__":
    unittest.main()
