"""Row sc7-config-find: `config <word>`, where the word is no tool's name, searches every key
(packet design/packets/sc7-config-find.md, R1 to R5, acceptance 1, 3 and 4). Each test starts the
suite in a temp HOME under an env of exactly HOME, PATH and XDG_CACHE_HOME, with two made-up tools:
`loom` (row sc6's fixture, whose key `spool.tension` holds the word in a segment) and `quill`, whose
key `nib.grip` holds it in its summary only, a summary past 80 columns. No test reads the live home
or the real terminal's size."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_sc3_table import LAUNCHER, draw, pty_run  # noqa: E402
from agentik_suite import term  # noqa: E402  (test_sc3_table puts the suite's lib on the path)
from test_sc6_config import ANSI, loom_home  # noqa: E402

LONG = ("How much tension the nib keeps against the page while it writes, in a made-up unit, "
        "a summary that runs well past eighty columns.")
QUILL = """#!/usr/bin/python3
import json, sys
args = sys.argv[1:]
ROWS = %(rows)r
if args == ["describe", "--json"]:
    print(json.dumps({"schema": "agentik.describe/1", "ok": True, "tool": "quill", "version": "2.0.0",
        "summary": "Another made-up tool.", "repo": "example/quill", "plugin": "quill@agentik",
        "needs": [], "verbs": [],
        "reads": [{"kind": "config", "name": "settings", "argv": ["describe", "config", "--json"]}]}))
elif args[:3] == ["describe", "config", "--json"]:
    rows = [{"key": k, "value": v, "default": v, "type": "string", "choices": None, "summary": s,
             "source": {"layer": "default", "path": None, "line": None},
             "change": {"kind": "fixed", "note": None, "command": None, "path": None, "block": None},
             "live": True, "values": [{"layer": "default", "value": v}]} for k, v, s in ROWS]
    if args[3:]:
        rows = [r for r in rows if r["key"] == args[3]]
    print(json.dumps({"schema": "agentik.config/1", "ok": True, "tool": "quill", "settings": rows,
        "layers": [{"name": "default", "path": None, "present": True, "travels": False}],
        "warnings": []}))
else:
    sys.exit(2)
"""
ROWS = [("nib.grip", "firm", LONG), ("ink", "blue", "The ink it writes with."),
        ("Spool", "none", "A key whose name is cased.")]
DEAF = '#!/bin/sh\nexit 1\n'  # a tool whose describe fails: it does not answer


def stub(home, name, body):
    path = os.path.join(home, "stubs", "agentik-" + name)
    with open(path, "w") as fh:
        fh.write(body)
    os.chmod(path, 0o755)


class Search(unittest.TestCase):
    def setUp(self):
        self._home = tempfile.TemporaryDirectory()
        self.home = os.path.realpath(self._home.name)
        self.env = loom_home(self.home)
        script = os.path.join(self.home, "quill.py")
        with open(script, "w") as fh:
            fh.write(QUILL % {"rows": ROWS})
        stub(self.home, "quill", '#!/bin/sh\nexec /usr/bin/python3 -B "%s" "$@"\n' % script)

    def tearDown(self):
        self._home.cleanup()

    def pty(self, *args, cols=80):
        return ANSI.sub("", pty_run(LAUNCHER, list(args), self.env, cols)).replace("\r", "")

    def pipe(self, *args):
        return subprocess.run([str(LAUNCHER), *args], env=self.env, capture_output=True, text=True,
                              cwd=self.home, timeout=60)

    def next_line(self, text):
        found = [line for line in text.splitlines() if line.startswith("next: ")]
        self.assertEqual(len(found), 1, text)
        return found[0][len("next: "):]

    def runs(self, line):
        ran = subprocess.run(["/bin/sh", "-c", line], env=self.env, capture_output=True, text=True,
                             cwd="/", stdin=subprocess.DEVNULL, timeout=60)
        self.assertEqual(ran.returncode, 0, (line, ran.stderr))

    def rows(self, out):
        return [line.split()[0] for line in out.splitlines() if line.startswith("  ") and "." in line.split()[0]]

    # ---- acceptance -----------------------------------------------------------------------

    def test_a1_a_word_lists_the_key_and_the_summary_that_hold_it_and_no_other(self):
        p = self.pipe("config", "tension")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.rows(p.stdout), ["loom.spool.tension", "quill.nib.grip"], p.stdout)
        self.assertEqual(p.stdout.splitlines()[0], "Keys that match tension: 2.")
        in_pipe = self.next_line(p.stderr)
        self.assertTrue(in_pipe.endswith(" config loom.spool.tension"), in_pipe)
        self.assertEqual(self.next_line(self.pty("config", "tension")), in_pipe)
        self.runs(in_pipe)

    def test_a3_a_long_summary_is_cut_on_a_pty_and_whole_in_a_pipe(self):
        shown = self.pty("config", "tension").splitlines()
        grip = [line for line in shown if "quill.nib.grip" in line]
        self.assertEqual(len(grip), 1, "\n".join(shown))
        self.assertTrue(grip[0].endswith("…"), grip[0])
        self.assertLessEqual(len(grip[0]), 80)
        self.assertIn("firm", grip[0])  # the value is never cut
        self.assertTrue(all(len(line) <= 80 for line in shown if not line.startswith("next: ")), shown)
        p = self.pipe("config", "tension")
        self.assertIn("quill.nib.grip", p.stdout)
        self.assertIn(LONG, p.stdout)
        self.assertNotIn("…", p.stdout)

    def test_a4_a_tool_name_wins_and_no_match_keeps_the_refusal(self):
        p = self.pipe("config", "loom")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(p.stdout.startswith("loom: 24 keys, 4 changed (*)."), p.stdout)
        p = self.pipe("config", "zzzq")
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")
        self.assertTrue(p.stderr.startswith("FAIL  zzzq is not a tool here\nnext: "), p.stderr)
        self.runs(self.next_line(p.stderr))

    # ---- the rulings ----------------------------------------------------------------------

    def test_r1_case_folded_segments_and_summary_words_only(self):
        p = self.pipe("config", "SPOOL")  # loom's spool group, and quill's key `Spool`
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.rows(p.stdout), ["loom.spool.size", "loom.spool.wind", "loom.spool.tension",
                                               "loom.spool.brake", "quill.Spool"], p.stdout)
        p = self.pipe("config", "tens")  # a word, not a part of one
        self.assertEqual(p.returncode, 2, p.stdout)

    def test_r3_no_match_names_the_near_key(self):
        p = self.pipe("config", "tensoin")
        self.assertEqual(p.returncode, 2)
        self.assertTrue(p.stderr.startswith("FAIL  tensoin is not a tool here\n"), p.stderr)
        nxt = self.next_line(p.stderr)
        self.assertTrue(nxt.endswith(" config loom.spool.tension"), nxt)
        self.runs(nxt)
        self.assertTrue(self.next_line(self.pipe("config", "quil").stderr).endswith(" config quill"))

    def test_r4_a_dotted_path_whose_tool_is_unknown_is_no_search(self):
        for args in (("config", "tension.x"), ("config", "tension", "x")):
            p = self.pipe(*args)
            self.assertEqual((p.returncode, p.stdout), (2, ""), p.stdout)
            self.assertTrue(p.stderr.startswith("FAIL  tension is not a tool here\n"), p.stderr)

    def test_r2_a_tool_that_did_not_answer_is_one_line(self):
        stub(self.home, "deaf", DEAF)
        p = self.pipe("config", "tension")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual([line for line in p.stdout.splitlines() if "deaf" in line],
                         ["warn  deaf did not answer, so its keys are not in this list"])
        p = self.pipe("config", "zzzq")
        self.assertEqual(p.returncode, 2)
        self.assertIn("warn  deaf did not answer, so its keys are not in this list\n", p.stderr)
        self.assertIn("FAIL  zzzq is not a tool here\n", p.stderr)

    def test_r2_json_lists_the_matches(self):
        import json
        p = self.pipe("config", "tension", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        obj = json.loads(p.stdout)
        self.assertEqual((obj["word"], [(m["tool"], m["key"]) for m in obj["matches"]], obj["silent"]),
                         ("tension", [("loom", "spool.tension"), ("quill", "nib.grip")], []))
        self.assertEqual(obj["matches"][1]["summary"], LONG)


class CutRoom(unittest.TestCase):
    """Review 1's F1 and F2: the cut cell on a terminal at 40, 64 and 80 columns. It is cut only
    where it does not fit, from where the row's text really ends, and no line passes the width."""

    FITS = "A long value without spaces."  # 28 columns: whole under its row at every width here
    LONG = "The turns this sitting is metered against, a summary that fits nowhere on a row."

    def row(self, key, value, summary):
        return (None, [term.name(key), value, term.cut(summary)], None)

    def assertWithin(self, lines, width):
        for line in lines:
            self.assertLessEqual(term.columns(line), width, (width, line, lines))

    def test_f1_a_summary_that_fits_under_its_row_has_no_mark(self):
        for width in (40, 64, 80):
            third = width // 3  # a key and a value of a third each leave the summary under 24 columns
            lines = draw([self.row("k" * third, "v" * third, self.FITS)], width)
            self.assertEqual(lines[1:], [" " * 6 + self.FITS], (width, lines))
            self.assertWithin(lines, width)

    def test_f1_a_summary_that_does_not_fit_under_its_row_is_cut_to_the_width(self):
        for width in (40, 64, 80):
            third = width // 3
            lines = draw([self.row("k" * third, "v" * third, self.LONG)], width)
            self.assertEqual(len(lines), 2, lines)
            self.assertTrue(lines[1].endswith("…"), lines)
            self.assertEqual(term.columns(lines[1]), width, lines)

    def test_f2_a_key_past_a_third_pushes_the_row_and_the_cut_follows_it(self):
        key = "session.ceilings.turns"  # 22 columns: past a third of 64, and of 40
        for width in (40, 64, 80):
            lines = draw([self.row(key, "400", self.LONG), self.row("a.b", "1", self.LONG)], width)
            self.assertWithin(lines, width)
            first = lines[0]
            self.assertTrue(first.startswith("  " + key + "  400"), lines)
            self.assertEqual(sum(self.LONG[:8] in line for line in lines), 2, lines)
            self.assertTrue(all("…" in line for line in lines if self.LONG[:8] in line), lines)
        lines = draw([self.row(key, "400", self.LONG)], 64)  # acceptance 2's shape: 31 columns in, 33 left
        self.assertEqual(term.columns(lines[0]), 64, lines)
        self.assertEqual(len(lines), 1, lines)

    def test_f2_a_value_past_a_third_pushes_the_row_and_the_cut_follows_it(self):
        for width, value in ((40, "x" * 20), (64, "~/.local/state/example/turns.log"), (80, "y" * 32)):
            lines = draw([self.row("log.turns", value, self.LONG)], width)
            self.assertWithin(lines, width)
            self.assertIn(value, lines[0])
            self.assertTrue(lines[-1].endswith("…"), lines)

    def test_f2_a_room_under_24_columns_puts_the_summary_under_the_row(self):
        for width, key, value in ((40, "session.ceilings.turns", "400"), (64, "k" * 21, "v" * 25),
                                  (80, "k" * 30, "v" * 22)):
            lines = draw([self.row(key, value, self.LONG)], width)
            self.assertEqual(len(lines), 2, (width, lines))
            self.assertNotIn("…", lines[0])
            self.assertTrue(lines[1].startswith(" " * 6 + self.LONG[:10]), lines)
            self.assertWithin(lines, width)


if __name__ == "__main__":
    unittest.main()
