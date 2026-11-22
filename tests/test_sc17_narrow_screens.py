"""Packet sc17-narrow-screens: the screens sc0's probe found red at 50 columns, mended.

Each run is the plugin's launcher in a temp HOME (test_agentik_suite's `Home`) with a stub
`claude`; nothing here starts the real `claude` or writes outside its temp folder."""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import Home  # noqa: E402
from agentik_suite import term  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
