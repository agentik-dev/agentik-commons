"""scripts/readme-top (packet fh3-top-check): a README's top, the lines before its first `## `,
is held to the ten-line form of GUIDE §10. Fixtures are made-up tops for made-up tools."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "readme-top"
LINK = "Part of [agentik](https://github.com/agentik-dev): what each plugin does, and how to leave."
FENCE = "`" * 3


def top(title="# agentik-murmur", block=("claude plugin marketplace add agentik-dev/agentik-commons; "
                                         "claude plugin install murmur@agentik", "murmur --version"),
        use="Use it when a sitting needs a quiet word.", lang="sh", link=LINK, extra=(), blocks=1,
        tail="## Why it exists\n\nBecause.\n"):
    lines = [title, "", "agentik-murmur says a quiet word for you.", ""]
    lines += list(extra)
    if use:
        lines += [use, ""]
    lines += ["Both lines are typed in a terminal:", ""]
    for _ in range(blocks):
        lines += [FENCE + lang]
        lines += list(block)
        lines += [FENCE, ""]
    lines += ["It needs Claude Code.", link, ""]
    return "\n".join(lines) + "\n" + tail


def run(*args, cwd=None):
    p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, text, name="README.md"):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def check(self, text, code, lines, name="README.md"):
        path = self.write(text, name)
        got = run(path)
        self.assertEqual(got, (code, "".join("%s: top: %s\n" % (path, l) for l in lines), ""), text)


class InTheForm(Case):
    def test_plain_top_counts_eight(self):
        self.check(top(), 0, ["8 lines, in the form"])

    def test_img_line_under_the_title_does_not_count(self):
        self.check(top(extra=('<img src="icon.png" width="64" alt="">',)), 0, ["8 lines, in the form"])

    def test_exactly_ten_counted_lines(self):
        self.check(top(extra=("A line of its own.", "Another one.")), 0, ["10 lines, in the form"])

    def test_block_of_a_slash_command(self):
        self.check(top(block=("/plugin install murmur@agentik", "/murmur:hello")), 0, ["8 lines, in the form"])

    def test_fence_opening_with_a_language_word_or_none(self):
        self.check(top(lang="sh"), 0, ["8 lines, in the form"])
        self.check(top(lang=""), 0, ["8 lines, in the form"])

    def test_second_link_to_another_address(self):
        self.check(top(link=LINK + " See [docs](https://example.org/murmur)."), 0, ["8 lines, in the form"])

    def test_no_second_heading_reads_the_file_whole(self):
        self.check(top(tail=""), 0, ["8 lines, in the form"])

    def test_text_after_the_first_heading_is_not_the_top(self):
        self.check(top(tail="## Why\n\n" + "line\n" * 30), 0, ["8 lines, in the form"])


class Findings(Case):
    def test_no_fenced_block(self):
        text = top().replace(FENCE + "sh\n", "").replace(FENCE + "\n", "")
        self.check(text, 1, ["0 fenced blocks; the form has exactly one"])

    def test_block_of_one_line(self):
        self.check(top(block=("claude plugin install murmur@agentik",)), 1,
                   ["the fenced block holds 1 line; the form has exactly two"])

    def test_block_of_three_lines(self):
        self.check(top(block=("a", "b", "c")), 1, ["the fenced block holds 3 lines; the form has exactly two"])

    def test_two_blocks(self):
        self.check(top(blocks=2, block=("one", "two")), 1,
                   ["2 fenced blocks; the form has exactly one"])

    def test_eleven_counted_lines(self):
        self.check(top(extra=("A.", "B.", "C.")), 1,
                   ["11 lines of text before the first ##; the form allows 10"])

    def test_no_use_it_when_line(self):
        self.check(top(use=""), 1, ['no line starts "Use it when"'])

    def test_two_use_it_when_lines(self):
        self.check(top(extra=("Use it when a second one is a fault.",)), 1,
                   ['2 lines start "Use it when"; the form has one'])

    def test_link_only_to_a_longer_address(self):
        link = "Part of [agentik](https://github.com/agentik-dev/agentik-murmur): what it does."
        self.check(top(link=link), 1, ["no link to https://github.com/agentik-dev"])

    def test_three_faults_print_three_lines_in_order(self):
        text = top(extra=("A.", "B.", "C."), use="", link="Part of agentik.")
        self.check(text, 1, ["11 lines of text before the first ##; the form allows 10",
                             'no line starts "Use it when"',
                             "no link to https://github.com/agentik-dev"])

    def test_all_five_in_order(self):
        text = top(extra=("A.", "B.", "C.", "D."), block=("one",), use="", link="Part of agentik.")
        self.check(text, 1, ["13 lines of text before the first ##; the form allows 10",
                             "the fenced block holds 1 line; the form has exactly two",
                             'no line starts "Use it when"',
                             "no link to https://github.com/agentik-dev"])

    def test_two_files_one_in_form(self):
        good = self.write(top(), "a.md")
        bad = self.write(top(use=""), "b.md")
        code, out, err = run(good, bad)
        self.assertEqual((code, err), (1, ""))
        self.assertEqual(out, "%s: top: 8 lines, in the form\n%s: top: no line starts \"Use it when\"\n" % (good, bad))

    def test_no_file_reads_readme_in_the_cwd(self):
        self.write(top())
        self.assertEqual(run(cwd=self.tmp.name), (0, "README.md: top: 8 lines, in the form\n", ""))


class Usage(Case):
    def test_a_path_that_is_no_file(self):
        missing = os.path.join(self.tmp.name, "absent.md")
        code, out, err = run(missing)
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(len(err.splitlines()), 1)
        self.assertIn(missing, err)

    def test_a_directory_and_an_unreadable_file_among_good_ones(self):
        good = self.write(top(use=""), "a.md")
        code, out, err = run(good, self.tmp.name)
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(len(err.splitlines()), 1)

    def test_help_prints_the_usage(self):
        for flag in ("-h", "--help"):
            code, out, err = run(flag)
            self.assertEqual((code, err), (0, ""))
            self.assertIn("Usage: readme-top [FILE...]", out)

    def test_another_flag_is_usage(self):
        code, out, err = run("--json")
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(len(err.splitlines()), 1)


class ThisRepo(unittest.TestCase):
    def test_shape(self):
        self.assertTrue(SCRIPT.read_text().startswith("#!/usr/bin/env python3\n"))
        self.assertTrue(os.access(SCRIPT, os.X_OK))

    def test_this_repos_own_readme_is_in_the_form(self):
        self.assertEqual(run(cwd=str(ROOT)), (0, "README.md: top: 8 lines, in the form\n", ""))

    def test_the_lint_target_runs_it(self):
        lint = (ROOT / "Makefile").read_text().split("\nlint:\n", 1)[1].split("\n\n", 1)[0]
        self.assertIn("\tscripts/readme-top\n", lint + "\n")


if __name__ == "__main__":
    unittest.main()
