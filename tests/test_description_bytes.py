"""scripts/plugin-description-bytes (packet p1, hq design/09 §2): a plugin's loaded
description bytes, one line per command, skill and agent type, against a ceiling. A
command or skill that sets disable-model-invocation: true is hidden and not counted;
an agent always is; a counted file with no description is an error."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "plugin-description-bytes"


def run(*args, cwd=None):
    p = subprocess.run([str(SCRIPT), *args], capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


class DescriptionBytesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.plugin = Path(self.tmp.name, "plugin")

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, rel, text):
        path = self.plugin / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_d1_hidden_command_listed_not_counted(self):
        self.put("commands/owner.md", "---\ndescription: Only the owner types this one\n"
                 "disable-model-invocation: true\n---\nbody\n")
        self.put("commands/open.md", "---\ndescription: abcdefghij\n"
                 "disable-model-invocation: false\n---\nbody\n")
        code, out, err = run(str(self.plugin))
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out.splitlines(), ["10  command  open", "hidden  command  owner",
                                            "total 10 of 1024 B"])

    def test_d2_agent_counted_folded_quoted_utf8(self):
        self.put("agents/helper.md", "---\nname: helper\ndescription: >\n  one two\n  three\n"
                 "tools: Read\n---\nbody\n")
        self.put("skills/s/SKILL.md", '---\nname: s\ndescription: "a \\"q\\" b"\n---\nbody\n')
        self.put("commands/c.md", "---\ndescription: 'it''s — x'\n---\nbody\n")
        code, out, err = run(str(self.plugin))
        self.assertEqual((code, err), (0, ""))
        # "one two three" 13; 'a "q" b' 7; "it's — x" is 8 characters, 10 bytes
        self.assertEqual(out.splitlines(), ["10  command  c", "7  skill  s", "13  agent  helper",
                                            "total 30 of 1024 B"])

    def test_d3_missing_description_is_an_error(self):
        self.put("agents/bare.md", "---\nname: bare\ntools: Read\n---\nbody\n")
        self.put("commands/none.md", "no frontmatter at all\n")
        code, out, err = run(str(self.plugin))
        self.assertEqual(code, 1)
        self.assertIn("error: %s: no description" % (self.plugin / "agents" / "bare.md"), err)
        self.assertIn("error: %s: no description" % (self.plugin / "commands" / "none.md"), err)
        self.assertEqual(out.splitlines()[-1], "total 0 of 1024 B")

    def test_d4_over_the_ceiling_fails(self):
        self.put("agents/a.md", "---\ndescription: %s\n---\n" % ("x" * 30))
        code, out, err = run("--max", "29", str(self.plugin))
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines()[-1], "total 30 of 29 B")
        self.assertIn("over the 29 B ceiling", err)
        code, out, err = run("--max", "30", str(self.plugin))
        self.assertEqual((code, err), (0, ""))

    def test_d5_hidden_skill_but_never_a_hidden_agent(self):
        self.put("skills/quiet/SKILL.md", "---\nname: quiet\ndescription: >\n  typed only\n"
                 "disable-model-invocation: true\n---\n")
        self.put("agents/loud.md", "---\nname: loud\ndescription: abc\n"
                 "disable-model-invocation: true\n---\n")
        code, out, err = run(str(self.plugin))
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out.splitlines(), ["hidden  skill  quiet", "3  agent  loud",
                                            "total 3 of 1024 B"])

    def test_d6_usage_and_missing_directory_exit_two(self):
        self.assertEqual(run("--max")[0], 2)
        self.assertEqual(run("--max", "ten")[0], 2)
        self.assertEqual(run("a", "b")[0], 2)
        self.assertEqual(run("--json")[0], 2)
        code, out, err = run(str(self.plugin / "absent"))
        self.assertEqual(code, 2)
        self.assertIn("is not a directory", err)

    def test_default_directory_is_plugin(self):
        self.put("commands/c.md", "---\ndescription: abc\n---\n")
        code, out, err = run(cwd=self.tmp.name)
        self.assertEqual((code, out.splitlines()[-1]), (0, "total 3 of 1024 B"))

    def test_continued_plain_value_and_when_to_use(self):
        self.put("skills/w/SKILL.md", "---\nname: w\ndescription: one\n  two\n"
                 "when_to_use: three\n---\n")
        code, out, err = run(str(self.plugin))
        self.assertEqual((code, err), (0, ""))
        # "one two" 7 plus "three" 5
        self.assertEqual(out.splitlines()[0], "12  skill  w")


if __name__ == "__main__":
    unittest.main()
