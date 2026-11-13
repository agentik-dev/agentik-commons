"""Row sm1-setup-ask: setup's question counts what a yes runs, names its answers, and defaults to no.

Each run is the plugin's launcher in a temp HOME, on a pty or off one, with the ak3-setup stubs:
`claude` records each call, and the made-up plugins `alpha` and `beta` ship a launcher whose
install-cli places itself. Three plans: fresh (five commands, two of them step 4's, run after step
3 installs), two (the marketplace and the door, with step 7's doctors shown) and one (the
marketplace alone). Nothing here starts the real `claude` or writes outside its temp folder."""
import os
import re
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_ak3_setup import LAUNCHER, SetupHome  # noqa: E402

ANSI = re.compile(r"\x1b\[[0-9;]*m")
WOULD = "would run: "
LATER = "yours to run later: "
DECLINED = "since the answer was not yes"
NEEDS_YES = "since it cannot ask you here"


def screen(text):
    """The lines as a reader sees them: no colour, no carriage return, each stripped."""
    return [l.strip() for l in ANSI.sub("", text).replace("\r", "").splitlines()]


def labelled(text, label):
    return [l[len(label):] for l in screen(text) if l.startswith(label)]


class AskTest(SetupHome):
    @property
    def known(self):
        return os.path.join(self.home, ".claude", "plugins", "known_marketplaces.json")

    def plan_of_two(self):
        """Steps 3 and 4 ok for both plugins, the marketplace unknown and the door not placed."""
        self.installed("alpha", "beta")
        for name in ("alpha", "beta"):
            self.place("agentik-" + name, "1.0.0")
        os.remove(self.known)

    def plan_of_one(self):
        """The marketplace alone is left: the door placed at a version newer than this one's."""
        self.installed("alpha")
        self.place("agentik-alpha", "1.0.0")
        self.place("agentik", "9.0.0")
        os.remove(self.known)

    def ran(self, text):
        return labelled(text, "ran: ")

    def assert_labels_hold(self, text, ran):
        """R1, R2 and acceptance 5: what a yes runs is under `would run:`, and nothing else is."""
        lines = screen(text)
        self.assertFalse([l for l in lines if l.startswith("run: ")], text)
        self.assertNotIn("Answer y or n", text)
        would = labelled(text, WOULD)
        self.assertTrue(would, text)
        commands = [r.rsplit(", ", 1)[0] for r in ran]
        for line in would:
            self.assertIn(line, commands, "a would-run line a yes left unrun")
        for line in labelled(text, LATER):
            self.assertNotIn(line, commands, "a line a yes ran sits under the later label")
        return would

    # ---- R1 to R3, acceptance 1, 3 and 5 ----------------------------------------------------

    def test_a1_enter_runs_nothing_and_declines(self):
        before = self.snapshot()
        code, text = self.answer_on_pty("", "setup", "alpha", "beta")
        self.assertEqual(code, 2, text)
        self.assertIn(DECLINED, text)
        self.assertIn("Run these 5 commands now?", text)
        self.assertEqual(self.recorded(), [])
        self.assertEqual(self.snapshot(), before)

    def test_a3_a5_the_fresh_plan_counts_five_and_runs_five(self):
        code, text = self.answer_on_pty("y", "setup", "alpha", "beta")
        self.assertEqual(code, 0, text)
        self.assertIn("Run these 5 commands now?", text)
        ran = self.ran(text)
        self.assertEqual(len(ran), 5, text)
        would = self.assert_labels_hold(text, ran)
        self.assertEqual(len(would), 3, text)  # step 4's two are run once step 3 installs

    def test_a3_a5_r2_the_plan_of_two_shows_the_doctors_as_the_readers(self):
        self.plan_of_two()
        code, text = self.answer_on_pty("yes", "setup", "alpha", "beta")
        self.assertEqual(code, 0, text)
        self.assertIn("Run these 2 commands now?", text)
        ran = self.ran(text)
        self.assertEqual(len(ran), 2, text)
        self.assert_labels_hold(text, ran)
        later = labelled(text, LATER)
        self.assertEqual([l.split()[-1] for l in later], ["doctor", "doctor"], text)

    def test_a3_the_plan_of_one(self):
        self.plan_of_one()
        code, text = self.answer_on_pty("y", "setup", "alpha")
        self.assertEqual(code, 0, text)
        self.assertIn("Run this 1 command now?", text)
        self.assertEqual(len(self.ran(text)), 1, text)
        self.assert_labels_hold(text, self.ran(text))

    def test_r3_the_question_names_its_answers_and_its_default(self):
        self.plan_of_one()
        code, text = self.answer_on_pty("n", "setup", "alpha")
        lines = screen(text)
        at = [i for i, l in enumerate(lines) if l.startswith("Run this 1 command now?")]
        self.assertEqual(len(at), 1, text)
        both = " ".join(lines[at[0]:at[0] + 2])
        for word in ("y", "n", "Enter"):
            self.assertRegex(both, r"(^|\W)%s(\W|$)" % word)
        self.assertNotIn("run:", lines[at[0]])

    # ---- R4, acceptance 2 and 4 -------------------------------------------------------------

    def test_a2_the_answers(self):
        self.plan_of_one()
        for answer, yes in (("y", True), ("Y", True), ("yes", True), (" YES ", True),
                            ("n", False), ("no", False), ("run", False), ("x", False), ("", False)):
            if os.path.exists(self.calls):
                os.remove(self.calls)
            if os.path.exists(self.known):
                os.remove(self.known)
            code, text = self.answer_on_pty(answer, "setup", "alpha")
            self.assertEqual((code, len(self.recorded())), (0, 1) if yes else (2, 0), (answer, text))
            if not yes:
                self.assertIn(DECLINED, text)
                self.assertFalse(os.path.exists(self.known), answer)

    def test_a4_off_a_terminal_as_at_the_pin(self):
        self.plan_of_one()
        before = self.snapshot()
        piped = subprocess.run([str(LAUNCHER), "setup", "alpha"], input="y\n", capture_output=True,
                               text=True, env=self.env(), timeout=60)
        closed = subprocess.run(["/bin/sh", "-c", 'exec "$0" setup alpha 0<&-', str(LAUNCHER)],
                                capture_output=True, text=True, env=self.env(), timeout=60)
        for p in (piped, closed):
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertIn(NEEDS_YES, p.stderr)
            self.assertIn("setup --yes", p.stderr)
        self.assertEqual(self.recorded(), [])
        self.assertEqual(self.snapshot(), before)
        code, out, err = self.run_cli("setup", "--yes", "alpha")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(len(self.recorded()), 1)
        self.assertNotIn("now?", out + err)

    # ---- R5, acceptance 6 -------------------------------------------------------------------

    def test_a6_the_closing_hint_names_the_door(self):
        self.plan_of_one()
        code, out, err = self.run_cli("setup", "--yes", "alpha")
        self.assertEqual(code, 0, out + err)
        self.assertIn("next: agentik doctor checks each plugin.", err.splitlines()[-1])
        code, out, err = self.run_cli("setup", "alpha")  # nothing to do, the door in place
        self.assertEqual(code, 0, out + err)
        self.assertIn("next: agentik doctor", err.splitlines()[-1])

    def test_a6_a_door_not_ours_keeps_the_suites_name(self):
        self.plan_of_one()
        os.remove(os.path.join(self.bindir, "agentik"))
        os.symlink("/nonexistent/agentik", os.path.join(self.bindir, "agentik"))  # a link: left alone
        code, out, err = self.run_cli("setup", "--yes", "alpha")
        self.assertEqual(code, 0, out + err)
        self.assertIn("next: agentik-suite doctor", err.splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
