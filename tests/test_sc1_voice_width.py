"""Packet sc1-voice-sweep R4: the catalogue's width and tense, held for the ids it owns.

The voice scanner's budgets are four fixed keys and hold neither a width nor a list of ids, so
the width of design/23 V1 is this test's. It reads the catalogue as text, on the standard
library: a message is at most 76 characters before its values (backticks dropped, each
placeholder counted as written, which is the strict reading), holds none of V4's words, and at
most one of V10's. The ids left out are the ones other rows own, each by prefix, and the one
that is a prompt to a model; a row that lands takes its prefix off OTHERS_OWN."""
import re
import unittest
from pathlib import Path

CATALOGUE = Path(__file__).resolve().parents[1] / "plugins/suite/lib/agentik_suite/messages.md"
WIDTH = 76
# sc8: setup.*, err.setup.*, hint.setup.*; sc10: doctor.*, hint.doctor.*; sc4: the errors of
# design/23 section 7's table; sc11: install.done; sc12: the Pick section.
OTHERS_OWN = ("setup.", "err.setup.", "hint.setup.", "doctor.", "hint.doctor.", "err.verb", "err.flag",
              "err.extra", "err.next", "install.done", "pick.", "err.pick", "hint.pick")
PROMPTS = ("issue.render.contract",)


def messages():
    out = []
    for line in CATALOGUE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"- `([^`]+)`: (.*)$", line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def owned():
    return [(i, t) for i, t in messages() if not i.startswith(OTHERS_OWN) and i not in PROMPTS]


class VoiceWidthTest(unittest.TestCase):
    def test_the_catalogue_is_read(self):
        self.assertGreater(len(owned()), 400)

    def test_width(self):
        over = ["%s (%d)" % (i, len(t.replace("`", ""))) for i, t in owned() if len(t.replace("`", "")) > WIDTH]
        self.assertEqual(over, [])

    def test_the_present(self):
        bad = [i for i, t in owned() if re.search(r"this version|a later version|\bwould\b", t, re.I)]
        self.assertEqual(bad, [])

    def test_one_reason(self):
        bad = [i for i, t in owned() if len(re.findall(r"\b(since|so|because)\b", t, re.I)) > 1]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
