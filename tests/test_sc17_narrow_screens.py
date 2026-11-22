"""Packet sc17-narrow-screens: the screens sc0's probe found red at 50 columns, mended.

Each run is the plugin's launcher in a temp HOME (test_agentik_suite's `Home`) with a stub
`claude`; nothing here starts the real `claude` or writes outside its temp folder."""
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import Home  # noqa: E402
from agentik_suite import apply, term  # noqa: E402

SGR = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07|\r")

# a `claude` whose every call prints a coloured line and a title sequence, then fails
LOUD = r"""#!/usr/bin/python3
import sys
print("\x1b[32mgreen words\x1b[0m and plain", flush=True)
print("\x1b]0;a made-up title\x07after the title", flush=True)
print("\x1b]2;another title\x1b\\after the second", flush=True)
sys.exit(1)
"""


class CleanTest(unittest.TestCase):
    """R9: a whole CSI and a whole OSC sequence go; a lone control byte as before."""

    def test_csi_goes_whole(self):
        self.assertEqual(term.clean("\x1b[32mgreen\x1b[0m"), "green")
        self.assertEqual(term.clean("a\x1b[1;31mb\x1b[2Kc"), "abc")
        self.assertEqual(term.clean("\x1b[?25lhidden"), "hidden")

    def test_osc_goes_whole(self):
        self.assertEqual(term.clean("\x1b]0;a title\x07after"), "after")
        self.assertEqual(term.clean("\x1b]8;;http://x.example\x1b\\link\x1b]8;;\x1b\\"), "link")

    def test_a_lone_control_byte_as_before(self):
        self.assertEqual(term.clean("a\x07b\x00c\x7fd"), "abcd")
        self.assertEqual(term.clean("a\x1bb"), "ab")
        self.assertEqual(term.clean("a\tb\nc"), "a b c")

    def test_a_line_with_no_escape_is_unchanged(self):
        for line in ("plain words, 3 of them", "~/.local/bin/agentik doctor", "[32m as typed ]0;"):
            self.assertEqual(term.clean(line), line)


class TailTest(Home):
    """Acceptance 4: a failed command's tail shows its words, no escape left over."""

    def test_a_failed_commands_tail_is_clean(self):
        self.stub("claude", LOUD)
        code, out, err = self.run_cli("setup", "--yes", COLUMNS="80")
        self.assertNotEqual(code, 0)
        text = out + err
        self.assertIn("green words and plain", text)
        self.assertIn("after the title", text)
        self.assertIn("after the second", text)
        for left in ("[32m", "[0m", "]0;", "]2;", "\x1b", "\x07"):
            self.assertNotIn(left, text)


class Narrow(Home):
    """A screen on a pty of `cols` columns, as its lines, colour taken off."""

    def rows(self, *args, cols=80, **more):
        code, text = self.run_pty(*args, cols=cols, **more)
        return code, [SGR.sub("", line) for line in text.splitlines()]

    def widest(self, rows):
        return max(term.columns(r) for r in rows)


class TitleTest(Narrow):
    """R1: the title's words go under the name and version where the three do not fit."""

    def test_at_50_the_words_go_on_the_next_line(self):
        for words in ([], ["help"]):
            code, rows = self.rows(*words, cols=50)
            self.assertEqual(code, 0, rows)
            self.assertRegex(rows[0], r"^agentik-suite \S+$")
            self.assertEqual(rows[1], "one command for the agentik tools")

    def test_at_80_the_title_is_one_line(self):
        for words in ([], ["help"]):
            code, rows = self.rows(*words, cols=80)
            self.assertRegex(rows[0], r"^agentik-suite \S+   one command for the agentik tools$")

    def test_off_a_terminal_one_line(self):
        code, out, err = self.run_cli(COLUMNS="40")
        self.assertRegex(out.splitlines()[0], r"^agentik-suite \S+   one command for the agentik tools$")


SUMMARY = "Show each tool's keys, then one tool's, then one key and how to change it."


class SummaryTest(Narrow):
    """R2: `help <verb>`'s sentence wraps at the window's width on a terminal."""

    def test_at_50_it_wraps(self):
        code, rows = self.rows("help", "config", cols=50)
        self.assertEqual(code, 0, rows)
        at = rows.index("Show each tool's keys, then one tool's, then one")
        self.assertEqual(" ".join(rows[at:at + 2]), SUMMARY)
        self.assertLessEqual(self.widest(rows[at:at + 2]), 50)

    def test_at_80_and_off_a_terminal_one_line(self):
        code, rows = self.rows("help", "config", cols=80)
        self.assertEqual(rows[1], SUMMARY)
        code, out, err = self.run_cli("help", "config", COLUMNS="40")
        self.assertEqual(out.splitlines()[1], SUMMARY)



def probe():
    """scripts/screen-probe as a module, for its made-up tool `loom` and its file."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "screen-probe")
    loader = SourceFileLoader("screen_probe", path)
    module = module_from_spec(spec_from_loader("screen_probe", loader))
    sys.dont_write_bytecode, was = True, sys.dont_write_bytecode
    try:
        loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = was
    return module


class ConfigTitleTest(Narrow):
    """R4: `config <tool>`'s head line wraps at the window's width."""

    def setUp(self):
        Narrow.setUp(self)
        p = probe()
        self.stub("agentik-loom", p.LOOM)
        os.makedirs(os.path.join(self.home, ".config", "loom"))
        with open(os.path.join(self.home, ".config", "loom", "config.yaml"), "w") as fh:
            fh.write(p.LOOM_FILE)

    def test_at_50_it_wraps(self):
        code, rows = self.rows("config", "loom", cols=50)
        self.assertEqual(code, 0, rows)
        self.assertEqual(" ".join(rows[:2]),
                         "loom: 24 keys, 3 changed (*). Layers, lowest first: default, user.")
        self.assertLessEqual(self.widest(rows[:2]), 50)
        self.assertEqual(rows[2], "")

    def test_at_80_one_line(self):
        code, rows = self.rows("config", "loom", cols=80)
        self.assertEqual(rows[:2], ["loom: 24 keys, 3 changed (*). Layers, lowest first: default, user.", ""])



class Fake(io.StringIO):
    """A stream that answers isatty, as sc3's table tests have it."""

    def isatty(self):
        return True

    @property
    def encoding(self):
        return "utf-8"

    def fileno(self):
        raise io.UnsupportedOperation("fileno")


ADD = 'add to your shell profile: export PATH="$HOME/.local/bin:$PATH"'
PROFILE = 'export PATH="$HOME/.local/bin:$PATH"'
WHY = "The line below mends this terminal; the line marked add mends each new one."


class CloseTest(unittest.TestCase):
    """R5: doctor's profile row keeps its label and puts its command under it where the two do
    not fit; the sentence above `next:` wraps; at 80 both read as before."""

    def drawn(self, cols, tty=True):
        out, err = Fake(), Fake()
        if not tty:
            out.isatty = err.isatty = lambda: False
        t = term.Term(env={"COLUMNS": str(cols), "NO_COLOR": "1"}, out=out, err=err)
        t.table([("warn", ["path", "not on PATH: ~/.local/bin"], ADD)], indent=4)
        apply.path_close(t, PROFILE)
        return out.getvalue().splitlines(), err.getvalue().splitlines()

    def test_at_50_the_label_keeps_its_line_and_the_command_goes_under(self):
        out, err = self.drawn(50)
        self.assertEqual(out[1:], ["        add to your shell profile:", "        " + PROFILE])
        self.assertEqual(" ".join(err[:-1]), WHY)
        self.assertLessEqual(max(term.columns(r) for r in out + err), 50)
        self.assertEqual(err[-1], "next: " + PROFILE)

    def test_at_80_as_before(self):
        out, err = self.drawn(80)
        self.assertEqual(out[1:], [" " * 13 + ADD])
        self.assertEqual(err, [WHY, "next: " + PROFILE])

    def test_off_a_terminal_one_line_each(self):
        out, err = self.drawn(40, tty=False)
        self.assertEqual(len(out), 2)
        self.assertEqual(err[0], WHY)



CAUSE = "relay has no command here yet, and installs its own by the line on this page:"


class PageTest(Narrow):
    """R6: the cause within 76 characters, the page's address alone under it at the lead."""

    def test_on_a_terminal_and_off_one(self):
        for cols in (80, 50):
            code, rows = self.rows("relay", cols=cols)
            self.assertEqual(code, 3, rows)
            at = [i for i, r in enumerate(rows) if r.startswith("      https://")][0]
            cause = " ".join(r.strip() for r in rows[:at])
            self.assertEqual(cause, "\u2717  " + CAUSE)
            self.assertLessEqual(self.widest(rows[:at]), cols)
            self.assertRegex(rows[at], r"^      https://\S+#install$")
            self.assertRegex(rows[at + 1], r"^next: /\S+ setup relay$")
        code, out, err = self.run_cli("relay")
        lines = err.splitlines()
        self.assertEqual(lines[0], "FAIL  " + CAUSE)
        self.assertRegex(lines[1], r"^      https://\S+#install$")
        self.assertLessEqual(len(CAUSE) - len("relay"), 76)

    def test_json_gives_the_page(self):
        code, out, err = self.run_cli("relay", "--json")
        got = json.loads(out)["error"]
        self.assertEqual(got["message"], CAUSE)
        self.assertRegex(got["page"], r"^https://\S+#install$")



def row(n, sid, state, subject):
    return {"n": n, "id": sid, "state": state, "subject": subject, "values": {}}


class StepFiveTest(unittest.TestCase):
    """R7: step 5's one ok line names the command a person types, not the launcher's file."""

    def test_its_ok_line_names_the_door(self):
        group = [row(5, "suite", "ok", "~/.local/bin/agentik-suite"), row(5, "door", "ok", "~/.local/bin/agentik")]
        self.assertEqual(apply._summary(5, group, door=True), "agentik")
        self.assertEqual(apply._summary(5, group), "agentik-suite, agentik")  # typed by its path (review 1 F1)

    def test_with_no_door_row_the_names_as_before(self):
        self.assertEqual(apply._summary(5, [row(5, "suite", "ok", "~/.local/bin/agentik-suite")]), "agentik-suite")
        group = [row(4, "launcher", "ok", "~/.local/bin/agentik-murmur"), row(4, "launcher", "ok", "/x/agentik-quill")]
        self.assertEqual(apply._summary(4, group), "agentik-murmur, agentik-quill")

    def test_json_keeps_the_launcher(self):
        s = dict(row(5, "suite", "ok", "~/.local/bin/agentik-suite"), detail="", command=None)
        self.assertEqual(apply.step_json(s)["subject"], "~/.local/bin/agentik-suite")


class StepFiveScreenTest(unittest.TestCase):
    """Review 1 F1: the one word `agentik` prints only on the screen typed through the door; a
    plan typed by the launcher's path in an applied home, ~/.local/bin on PATH or off, names the
    launcher and the door as at the pin."""

    @classmethod
    def setUpClass(cls):
        cls.top = os.path.realpath(tempfile.mkdtemp(prefix="sc17-f1-"))
        cls.p = probe()
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        cls.launcher = os.path.realpath(os.path.join(root, "plugins", "suite", "bin", "agentik-suite"))
        cls.homes = cls.p.build_homes(cls.top, cls.launcher, {"applied-off", "applied-on"})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.top, ignore_errors=True)

    def step5(self, label, how):
        h = self.homes[label]
        argv = self.p.argv_of(how, h, ["setup", "--dry-run"], self.launcher)
        rows = self.p.render(argv, h.env(), h.work, "pty80", None)
        got = [r for r in rows if re.match(r"^\s*\S* 5 ", r)]
        self.assertEqual(len(got), 1, rows)
        return got[0]

    def test_by_the_launcher_as_at_the_pin(self):
        for label in ("applied-off", "applied-on"):
            self.assertRegex(self.step5(label, "launcher"), r" 5 agentik +agentik-suite, agentik$", label)

    def test_through_the_door_one_word(self):
        self.assertRegex(self.step5("applied-on", "door"), r" 5 agentik +agentik$")



class EmptyDoctorTest(Narrow):
    """R8: doctor in an empty home is sc10's 8 lines at 80: the plugin row fits one line."""

    def test_eight_lines_at_80(self):
        code, rows = self.rows("doctor", cols=80)
        rows = [r for r in rows if r.strip()]
        self.assertEqual(len(rows), 8, rows)
        plugin = [r for r in rows if " plugin " in r][0]
        self.assertRegex(plugin, r"default set, not installed: \w+, \w+, \w+$")
        self.assertLessEqual(term.columns(plugin), 80)


if __name__ == "__main__":
    unittest.main()
