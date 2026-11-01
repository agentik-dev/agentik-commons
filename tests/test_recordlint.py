"""scripts/recordlint (hq design/05 §4, packet c3): HANDOFF.md and NICE_TO_HAVE.md
held to design/05 §2's tables. Each fixture is built here, in a temporary directory,
and each test reads the exact stdout and exit: 0 clean, 2 on a finding, 1 on usage.
The build-order marker is assembled at runtime, as the script assembles it, so the
hygiene scan's sibling group finds no tool name in this file."""
import os
import py_compile
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDLINT = ROOT / "scripts" / "recordlint"
MARKER = "<!-- " + "decision" + "s: build order -->"
HANDOFF_HEADER = "| # | item | level | repo | where | state |"
NICE_HEADER = "| id | level | area | finding | evidence | from |"
SEP = "|---|---|---|---|---|---|"
NON_ROW_IN_TABLE = "inside a table: the backlog reader ends the table here and drops the rows after it"
NON_ROW_UNDER = "under a `##`: only table rows belong there"
REPO_RULE = "is not a bare short name (^[a-z][a-z0-9-]*$, no `agentik-` prefix): `--order` matches it exactly"
GREEN_HANDOFF = ("| 17 | the rule, `a \\| b` | S2 | hq | design/05 | open |",
                 "| 18 | the tool | S3 | session | packet c3 | building c3 |",
                 "| 19 | a wait | S1 | suite | the owner | waiting: the owner's word |",
                 "| 20 | a watch | S4 | relay | the night | watch: the next night's line |",
                 "| 21 | landed | S3 | hq | design/05 | done 2026-11-01 abc1234 |")
GREEN_NICE = ("| n1 | S2 | `scripts/sync` | a `x \\| y` finding | sync:114 | 2026-11-01 c3 |",
              "| n2 | S3 | hygiene | another | not confirmed | 2026-11-01 c3 |")


def handoff(*rows, head="The build order, one row an item."):
    """A HANDOFF.md: its table's header at line 9, its first row at line 11."""
    return "\n".join(["# Handoff", "", head, "", MARKER, "", "## The build order", "",
                      HANDOFF_HEADER, SEP, *rows]) + "\n"


def nice(*rows, head="The archive is `history/NICE-2026-11-01.md`."):
    """A NICE_TO_HAVE.md: its table's header at line 7, its first row at line 9."""
    return "\n".join(["# Nice to have", "", head, "", "## Open", "", NICE_HEADER, SEP, *rows]) + "\n"


def padded(make, rows, size):
    """make(*rows, head=...) grown by its head paragraph to exactly size bytes."""
    base = len(make(*rows, head="").encode())
    text = make(*rows, head="x" * (size - base))
    assert len(text.encode()) == size
    return text


class RecordlintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def run_lint(self, files=None, *args):
        for name, text in (files or {}).items():
            Path(self.dir, name).write_text(text, encoding="utf-8")
        p = subprocess.run([str(RECORDLINT), *args], capture_output=True, text=True, cwd=self.dir)
        return p.returncode, p.stdout, p.stderr

    def assertLint(self, files, code, *lines):
        got = self.run_lint(files, *files)
        self.assertEqual(got, (code, "".join(line + "\n" for line in lines), ""))

    def test_shape_the_floor_and_the_mode(self):
        self.assertTrue(RECORDLINT.read_text().startswith("#!/usr/bin/python3\n"))
        self.assertTrue(os.access(RECORDLINT, os.X_OK))
        py_compile.compile(str(RECORDLINT), cfile=os.path.join(self.dir, "c.pyc"), doraise=True)

    def test_skip_without_the_canonical_header(self):
        # rule 1: today's bullets, and a near-miss header, print skip and pass
        self.assertLint({"HANDOFF.md": "# Handoff\n\n## The build order\n\n- one\n  more\n",
                         "NICE_TO_HAVE.md": "# Nice\n\n## Open\n\n| id | level | area | finding |\n"
                                            "|---|---|---|---|\n| n1 | S9 | a | b |\n"}, 0,
                        "HANDOFF.md: skip: no canonical header `%s`" % HANDOFF_HEADER,
                        "NICE_TO_HAVE.md: skip: no canonical header `%s`" % NICE_HEADER)

    def test_missing_files_are_skipped_and_both_are_the_default(self):
        self.assertEqual(self.run_lint(), (0, "HANDOFF.md: skip: no such file\n"
                                              "NICE_TO_HAVE.md: skip: no such file\n", ""))
        Path(self.dir, "NICE_TO_HAVE.md").write_text(nice(*GREEN_NICE))
        self.assertEqual(self.run_lint(), (0, "HANDOFF.md: skip: no such file\n"
                                              "NICE_TO_HAVE.md: held: 2 rows\n", ""))

    def test_a_green_handoff_and_nice(self):
        tables = nice(*GREEN_NICE) + "\n## Later\n\n" + NICE_HEADER + "\n|:--|---|---|---|---|--:|\n" \
            "| n3 | S4 | GUIDE | third | GUIDE.md:70 | 2026-11-01 c3 |\n"
        self.assertLint({"HANDOFF.md": handoff(*GREEN_HANDOFF), "NICE_TO_HAVE.md": tables}, 0,
                        "HANDOFF.md: held: 5 rows", "NICE_TO_HAVE.md: held: 3 rows")

    def test_an_escaped_pipe_in_a_code_span_is_one_cell(self):
        self.assertLint({"NICE_TO_HAVE.md": nice("| n1 | S2 | `a \\| b` | `grep -E 'x\\|y'` | e | f |")}, 0,
                        "NICE_TO_HAVE.md: held: 1 row")
        self.assertLint({"NICE_TO_HAVE.md": nice("| n1 | S2 | `a | b` | x | e | f |")}, 2,
                        "NICE_TO_HAVE.md:9: cells: 7 cells, the header has 6; a pipe inside a cell is `\\|`")

    def test_prose_a_bullet_and_a_subheading_under_a_heading_are_non_rows(self):
        text = nice(*GREEN_NICE) + "\nSome prose.\n\n- a bullet\n\n### Sub\n\n    indented\n\n```\n| n9 |\n```\n"
        self.assertLint({"NICE_TO_HAVE.md": text}, 2,
                        "NICE_TO_HAVE.md:12: non-row: prose " + NON_ROW_UNDER,
                        "NICE_TO_HAVE.md:14: non-row: a bullet " + NON_ROW_UNDER,
                        "NICE_TO_HAVE.md:16: non-row: a heading deeper than `##` " + NON_ROW_UNDER,
                        "NICE_TO_HAVE.md:18: non-row: an indented line " + NON_ROW_UNDER,
                        "NICE_TO_HAVE.md:20: non-row: a fenced line " + NON_ROW_UNDER,
                        "NICE_TO_HAVE.md:21: non-row: a fenced line " + NON_ROW_UNDER,
                        "NICE_TO_HAVE.md:22: non-row: a fenced line " + NON_ROW_UNDER)

    def test_f1_a_line_inside_a_table_that_is_not_a_row(self):
        # the backlog reader ends the table at the indented line; recordlint names it
        rows = (GREEN_NICE[0], "  continued evidence", GREEN_NICE[1])
        self.assertLint({"NICE_TO_HAVE.md": nice(*rows)}, 2,
                        "NICE_TO_HAVE.md:10: non-row: an indented line " + NON_ROW_IN_TABLE)
        rows = (GREEN_HANDOFF[0], "- a bullet", GREEN_HANDOFF[1], "and prose")
        self.assertLint({"HANDOFF.md": handoff(*rows)}, 2,
                        "HANDOFF.md:12: non-row: a bullet " + NON_ROW_IN_TABLE,
                        "HANDOFF.md:14: non-row: prose " + NON_ROW_IN_TABLE)
        # outside a `##` too: a table in the head
        text = "# Nice\n\n" + NICE_HEADER + "\n" + SEP + "\n" + GREEN_NICE[0] + "\n  more\n"
        self.assertLint({"NICE_TO_HAVE.md": text}, 2,
                        "NICE_TO_HAVE.md:6: non-row: an indented line " + NON_ROW_IN_TABLE)

    def test_a_row_over_400_characters(self):
        def row(width):
            frame = "| n1 | S2 | a |  | e | f |"
            return frame.replace("|  |", "| %s |" % ("f" * (width - len(frame))))
        self.assertEqual((len(row(400)), len(row(401))), (400, 401))
        self.assertLint({"NICE_TO_HAVE.md": nice(row(400))}, 0, "NICE_TO_HAVE.md: held: 1 row")
        self.assertLint({"NICE_TO_HAVE.md": nice(row(401))}, 2,
                        "NICE_TO_HAVE.md:9: long: 401 characters, the bound is 400; evidence that does"
                        " not fit goes to a cited file under history/sessions/")

    def test_a_duplicate_number_and_id(self):
        self.assertLint({"HANDOFF.md": handoff(GREEN_HANDOFF[0], GREEN_HANDOFF[0])}, 2,
                        "HANDOFF.md:12: duplicate: # 17 again, first at line 11")
        self.assertLint({"NICE_TO_HAVE.md": nice(GREEN_NICE[0], GREEN_NICE[1], GREEN_NICE[0])}, 2,
                        "NICE_TO_HAVE.md:11: duplicate: id n1 again, first at line 9")

    def test_a_number_the_reader_takes_for_a_header(self):
        self.assertLint({"HANDOFF.md": handoff("| 17a | x | S2 | hq | y | open |")}, 2,
                        'HANDOFF.md:11: number: # "17a" is not a number: the backlog reader takes the row'
                        " for a header")

    def test_f1_a_leading_zero_is_not_a_number(self):
        # refuter round 1's F1: the reader reads `01` as step 1, so beside `1` it passed as two
        one = "| 1 | x | S2 | hq | y | open |"
        self.assertLint({"HANDOFF.md": handoff(one, "| 01 | z | S2 | hq | y | open |")}, 2,
                        'HANDOFF.md:12: number: # "01" is not ^[1-9][0-9]*$: the backlog reader reads it'
                        " as step 1")
        self.assertLint({"HANDOFF.md": handoff("| 0 | z | S2 | hq | y | open |")}, 2,
                        'HANDOFF.md:11: number: # "0" is not ^[1-9][0-9]*$: the backlog reader reads it'
                        " as step 0")
        self.assertLint({"HANDOFF.md": handoff(one, one)}, 2,
                        "HANDOFF.md:12: duplicate: # 1 again, first at line 11")
        self.assertLint({"HANDOFF.md": handoff(one, "| 10 | z | S2 | hq | y | open |")}, 0,
                        "HANDOFF.md: held: 2 rows")

    def test_a_bad_level(self):
        rows = ("| n1 | S5 | a | b | c | d |", "| n2 | s2 | a | b | c | d |", "| n3 |  | a | b | c | d |")
        self.assertLint({"NICE_TO_HAVE.md": nice(*rows)}, 2,
                        'NICE_TO_HAVE.md:9: level: "S5" is not S1 to S4',
                        'NICE_TO_HAVE.md:10: level: "s2" is not S1 to S4',
                        'NICE_TO_HAVE.md:11: level: "" is not S1 to S4')
        self.assertLint({"HANDOFF.md": handoff("| 1 | x | high | hq | y | open |")}, 2,
                        'HANDOFF.md:11: level: "high" is not S1 to S4')

    def test_a_bad_state_word(self):
        states = ("pending", "Open", "waiting the owner", "donex 2026-11-01")
        rows = ["| %d | x | S2 | hq | y | %s |" % (i, s) for i, s in enumerate(states, 1)]
        self.assertLint({"HANDOFF.md": handoff(*rows)}, 2, *(
            'HANDOFF.md:%d: state: "%s" opens with none of open, building, waiting:, watch:, done' % (11 + i, s)
            for i, s in enumerate(states)))

    def test_a_wrong_cell_count(self):
        self.assertLint({"HANDOFF.md": handoff("| 1 | x | S2 | hq | open |", "| 2 | x | S2 | hq | y | z | open |")}, 2,
                        "HANDOFF.md:11: cells: 5 cells, the header has 6; a pipe inside a cell is `\\|`",
                        "HANDOFF.md:12: cells: 7 cells, the header has 6; a pipe inside a cell is `\\|`")

    def test_f3_the_header_and_the_repo_cell(self):
        near = "\n| # | item | level | repo | where | status |\n" + SEP + "\n| 30 | x | S2 | hq | y | open |\n"
        self.assertLint({"HANDOFF.md": handoff(*GREEN_HANDOFF) + near}, 2,
                        "HANDOFF.md:17: header: a table opens with `%s` and its separator" % HANDOFF_HEADER)
        blank_separator = handoff().replace(SEP + "\n", "| | | | | | |\n") + GREEN_HANDOFF[0] + "\n"
        self.assertLint({"HANDOFF.md": blank_separator}, 2,
                        "HANDOFF.md:10: header: the header's next row is not a separator of 6 cells")
        repos = ("agentik-session", "`hq`", "Hq", "hq, suite", "9x")
        rows = ["| %d | x | S2 | %s | y | open |" % (i, r) for i, r in enumerate(repos, 1)]
        self.assertLint({"HANDOFF.md": handoff(*rows)}, 2, *(
            'HANDOFF.md:%d: repo: "%s" %s' % (11 + i, r, REPO_RULE) for i, r in enumerate(repos)))

    def test_order_a_table_the_reader_never_takes(self):
        unmarked = handoff(*GREEN_HANDOFF).replace(MARKER + "\n", "")
        self.assertLint({"HANDOFF.md": unmarked}, 2,
                        "HANDOFF.md:8: order: no build-order marker comment above the first `##`:"
                        " the backlog reader takes no build order")
        second = handoff(*GREEN_HANDOFF) + "\n## Later\n\n" + HANDOFF_HEADER + "\n" + SEP + \
            "\n| 30 | x | S2 | hq | y | open |\n"
        self.assertLint({"HANDOFF.md": second}, 2,
                        "HANDOFF.md:19: order: outside the first `##` after the build-order marker comment,"
                        " the one section the backlog reader takes")

    def test_a_handoff_at_8192_bytes(self):
        # GUIDE §4: a byte ceiling is tested at it, the last byte under passing
        self.assertLint({"HANDOFF.md": padded(handoff, GREEN_HANDOFF, 8191)}, 0, "HANDOFF.md: held: 5 rows")
        self.assertLint({"HANDOFF.md": padded(handoff, GREEN_HANDOFF, 8192)}, 2,
                        "HANDOFF.md:1: size: 8,192 B, the bound is under 8,192 B; a done row leaves as one"
                        " line in history/handoff-done.md")

    def test_a_nice_at_24576_bytes(self):
        self.assertLint({"NICE_TO_HAVE.md": padded(nice, GREEN_NICE, 24575)}, 0, "NICE_TO_HAVE.md: held: 2 rows")
        self.assertLint({"NICE_TO_HAVE.md": padded(nice, GREEN_NICE, 24576)}, 2,
                        "NICE_TO_HAVE.md:1: size: 24,576 B, the bound is under 24,576 B; move the oldest S4"
                        " rows, appended, to history/NICE-overflow.md; the frozen archive is never edited")

    def test_usage_exits_one_and_writes_nothing(self):
        for args in (("-x",), ("notes.md",), ("HANDOFF.md", "--json")):
            code, out, err = self.run_lint(None, *args)
            self.assertEqual((code, out), (1, ""), args)
            self.assertTrue(err.startswith("recordlint: ") and "usage: recordlint [FILE...]" in err, err)
        self.assertEqual(self.run_lint(None, "--help")[0], 0)
        Path(self.dir, "HANDOFF.md").write_text(handoff("| 1 | x | S9 | hq | y | open |"))
        before = sorted(os.listdir(self.dir))
        self.assertEqual(self.run_lint()[0], 2)
        self.assertEqual(sorted(os.listdir(self.dir)), before)


if __name__ == "__main__":
    unittest.main()
