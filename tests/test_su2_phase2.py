"""Row su2-read, phase 2: the rules main brought (sc4's refusals and hints, sc2's name) over the
full status this branch brings.

The temp home is sc4's (tests/test_sc4_errors.py): the door and `agentik-suite` on PATH, every
tool made up. Each printed `next:` is pasted into `sh -c` with stdin closed."""
import json
import os
import unittest

import test_sc4_errors as sc4
from agentik_suite import catalogue, cli  # noqa: E402

TIME = "2026-11-13T12:00:00Z"


class StatusRefusalTest(sc4.Sc4Home):
    """Each refusal of status is its cause, then `next:` and the line that runs: the line as
    typed less each path that is no folder and less the test hooks."""

    refusal = sc4.Review1Test.refusal

    def cases(self):
        nope = os.path.join(self.home, "nope")
        return [  # (argv, cause, next, error.code)
            (("statu",), "statu is not a verb", "agentik status", "unknown_verb"),
            (("state",), "state is not a verb", "agentik status", "unknown_verb"),
            (("statu", "--check"), "statu is not a verb", "agentik status --check", "unknown_verb"),
            (("status", nope), "%s is not a folder" % nope, "agentik status", "bad_path"),
            (("status", self.home, nope), "%s is not a folder" % nope, "agentik status %s" % self.home,
             "bad_path"),
            (("status", "--now", "soon"), "soon is not an ISO 8601 time, such as %s" % TIME,
             "agentik status", "bad_time"),
            (("status", "--check", "--now=soon"), "soon is not an ISO 8601 time, such as %s" % TIME,
             "agentik status --check", "bad_time"),
            (("status", "--ps", nope), "%s cannot be read as a listing that ps wrote" % nope,
             "agentik status", "bad_listing"),
            (("status", nope, "--now", "soon"), "%s is not a folder" % nope, "agentik status", "bad_path"),
        ]

    def test_each_refusal_names_a_line_that_runs(self):
        for argv, cause, nxt, code_word in self.cases():
            self.refusal(argv, cause, nxt, code_word=code_word)
            self.assertFalse(set(nxt.split()) & set(cli.SKIPS), (argv, nxt))
            self.assert_runs(nxt, argv)
            self.assertFalse(os.path.exists(self.calls), (argv, nxt))  # no claude started

    def test_a_user_file_that_does_not_parse_is_its_fault_alone(self):
        folder = os.path.join(self.home, ".config", "agentik", "suite")
        os.makedirs(folder)
        with open(os.path.join(folder, "config.yaml"), "w") as fh:
            fh.write("watchers: [\n")
        for argv in (("status", "--check"), ("status",)):
            code, out, err = self.run_cli(*argv)
            self.assertEqual((code, out), (2, ""), (argv, err))
            self.assertEqual(len(err.splitlines()), 1, (argv, err))
            self.assertTrue(err.startswith("FAIL  ") and "config.yaml" in err, (argv, err))
            code, out, err = self.run_cli("--json", *argv)
            self.assertIsNone(json.loads(out)["error"]["remedy"], argv)


class StatusNameTest(sc4.Sc4Home):
    """sc2: the suite's commands the screen prints come from `cmd.say`, so through the door here."""

    def test_the_backlog_names_status_by_the_door(self):
        code, out, err = self.pasted("agentik status")  # from HOME, which is no checkout
        self.assertEqual(code, 0, err)
        row = next(line for line in out.splitlines() if line.startswith("note  backlog"))
        self.assertEqual(row, "note  backlog   no checkout here; name one: agentik status PATH")

    def test_every_status_hint_starts_next(self):
        found = catalogue.load()
        hints = [mid for mid in found if mid.startswith("hint.status.") and mid != "hint.status.unchecked"]
        self.assertEqual(len(hints), 5)
        for mid in hints:
            self.assertTrue(found[mid].startswith("next: "), mid)
            self.assertNotIn("{tool}", found[mid], mid)


if __name__ == "__main__":
    unittest.main()
