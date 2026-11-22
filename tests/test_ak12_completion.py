"""Row ak12-polish: `completion zsh|bash`, its callback `completion words`, and the suite's skill.

`quill` and `scribe` are made up. Each run is the suite's launcher, or the door copied beside it,
in a temp HOME whose PATH is a temp bin, then /usr/bin:/bin. The temp bin holds the two tools, each
a launcher that appends to a marker file when it runs, and recorders under the names `ps`, `git`,
`gh` and `claude`, which append to the same file. The describes are written in the temp cache as
the suite writes them. The shells run as `/bin/bash --norc --noprofile` and `zsh -f`, with no
terminal; a test that needs a shell this machine lacks is skipped and says so. Nothing here reads
the live home or writes outside its temp folder."""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "suite"
LAUNCHER = PLUGIN / "bin" / "agentik-suite"
LIB = PLUGIN / "lib"
SKILL = PLUGIN / "skills" / "suite" / "SKILL.md"
BASH = "/bin/bash"
ZSH = shutil.which("zsh") or "/bin/zsh"
LOG = '#!/bin/sh\necho "$0 $*" >> "%s"\nexit 0\n'

sys.path.insert(0, str(LIB))
from agentik_suite import cli, completion, tools  # noqa: E402

BASH_DRIVER = r"""source "$1"
t() {
    COMP_WORDS=("$@")
    COMP_CWORD=$((${#COMP_WORDS[@]} - 1))
    _agentik
    printf '%s\n' "[${COMP_WORDS[*]}]" "${COMPREPLY[@]}"
}
t agentik ""
t agentik se
t agentik setup --d
t agentik quill ""
COMP_WORDS=(agentik se --json)
COMP_CWORD=1
_agentik
printf '%s\n' "[mid]" "${COMPREPLY[@]}"
t agentik zzz ""
printf '%s\n' "[complete]"
complete -p agentik agentik-suite
"""

ZSH_DRIVER = r"""eval "$(<$1)"
print -r -- "[comps] ${_comps[agentik]} ${_comps[agentik-suite]}"
_describe() { local x; for x in "${(@P)4}"; do print -r -- "${x%%:*}"; done }
_files() { print -r -- "<files>" }
t() {
    words=("$@")
    CURRENT=${#words}
    print -r -- "[$*]"
    _agentik
}
t agentik ""
t agentik se
t agentik setup --d
t agentik quill ""
words=(agentik se --json)
CURRENT=2
print -r -- "[mid]"
_agentik
t agentik zzz ""
"""

HOSTILE = "%s $(touch {m}) `touch {m}`\tafter a tab\nafter a newline \x1b[31mred\x1b[0m"


def answer(tool, summary="A made-up tool.", verbs=()):
    return {"schema": "agentik.describe/1", "ok": True, "tool": tool, "version": "0.1.0",
            "summary": summary, "repo": "acme/" + tool, "plugin": tool + "@acme-tools", "needs": [],
            "verbs": [{"name": n, "summary": s, "top": False} for n, s in verbs], "reads": []}


def split(out):
    """{label: [names]} of a driver's output, each label a `[...]` line."""
    found, at = {}, None
    for line in out.splitlines():
        if line.startswith("[") and line.endswith("]") or line.startswith("[comps]"):
            at = line
            found[at] = []
        elif at is not None:
            found[at].append(line)
    return found


class Home(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = os.path.realpath(tmp.name)
        self.home = os.path.join(self.tmp, "home")
        self.bin = os.path.join(self.tmp, "bin")
        self.cache = os.path.join(self.tmp, "cache")
        self.marker = os.path.join(self.tmp, "ran")
        self.mark = os.path.join(self.tmp, "M")
        for d in (self.home, self.bin):
            os.mkdir(d)
        for name in ("agentik-quill", "agentik-scribe", "ps", "git", "gh", "claude"):
            self.file(name, LOG % self.marker)
        self.file("agentik-suite", '#!/bin/sh\nexec "%s" "$@"\n' % LAUNCHER)
        shutil.copy(str(PLUGIN / "bin" / "agentik"), os.path.join(self.bin, "agentik"))
        self.describe("quill", answer("quill", "Writes with a quill.",
                                      [("draw", "Draw a line."), ("ink", "Fill the pen.")]))
        self.describe("scribe", answer("scribe", "Copies the page.", [("copy", "Copy a page.")]))

    def file(self, name, text):
        path = os.path.join(self.bin, name)
        with open(path, "w") as fh:
            fh.write(text)
        os.chmod(path, 0o755)

    def env(self):
        return {"HOME": self.home, "PATH": os.pathsep.join([self.bin, "/usr/bin", "/bin"]),
                "XDG_CACHE_HOME": self.cache, "ZDOTDIR": self.home}

    def describe(self, tool, obj):
        folder = tools.cache_dir(self.env())
        os.makedirs(folder, exist_ok=True)
        stamp = tools._stamp(os.path.join(self.bin, "agentik-" + tool))
        with open(os.path.join(folder, tool + ".json"), "w") as fh:
            json.dump({"stamp": stamp, "answer": obj}, fh)

    def run_(self, *args, door=False):
        exe = os.path.join(self.bin, "agentik") if door else str(LAUNCHER)
        p = subprocess.run([exe] + list(args), capture_output=True, text=True, env=self.env(),
                           cwd=self.home, timeout=60)
        return p.returncode, p.stdout, p.stderr

    def words(self, *line):
        code, out, err = self.run_("completion", "words", "--", *line)
        self.assertEqual((code, err), (0, ""), line)
        return [l.split("\t")[0] for l in out.splitlines()], out

    def shell(self, which, driver):
        exe = BASH if which == "bash" else ZSH
        if not os.access(exe, os.X_OK):
            self.skipTest("no %s on this machine" % exe)
        code, script, _ = self.run_("completion", which)
        self.assertEqual(code, 0)
        paths = []
        for name, text in (("script", script), ("driver", driver)):
            paths.append(os.path.join(self.tmp, "%s.%s" % (name, which)))
            with open(paths[-1], "w") as fh:
                fh.write(text)
        argv = [BASH, "--norc", "--noprofile", paths[1], paths[0]] if which == "bash" \
            else [ZSH, "-f", paths[1], paths[0]]
        p = subprocess.run(argv, capture_output=True, text=True, env=self.env(), cwd=self.home, timeout=120)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return split(p.stdout)


class ScriptsTest(Home):
    def test_1_each_shell_takes_its_script(self):
        for which, exe in (("zsh", ZSH), ("bash", BASH)):
            code, out, err = self.run_("completion", which)
            self.assertEqual((code, err), (0, ""))
            code, js, _ = self.run_("completion", which, "--json")
            self.assertEqual(json.loads(js), {"schema": "agentik.completion/1", "ok": True,
                                              "shell": which, "script": out})
            if not os.access(exe, os.X_OK):
                self.skipTest("no %s on this machine" % exe)
            p = subprocess.run([exe, "-n"], input=out, capture_output=True, text=True, timeout=30)
            self.assertEqual(p.returncode, 0, p.stderr)

    def test_6_r5_r6_the_scripts_words(self):
        for which, text in completion.SCRIPTS.items():
            self.assertNotRegex(text, r"\beval\b|compgen|compopt|mapfile|declare -A|typeset -A")
            self.assertNotRegex(text, r"[^\"]\$(?:line|name|rest)\b", which)  # what came back, quoted
            self.assertIn("2>/dev/null", text)
            self.assertNotIn("\t", text)
        self.assertTrue(completion.ZSH.startswith("#compdef agentik agentik-suite\n"))
        self.assertIn("compdef _agentik agentik agentik-suite\n", completion.ZSH)
        self.assertIn("\ncomplete -o default -F _agentik agentik agentik-suite\n", completion.BASH)


class BashDriverTest(Home):
    def test_2_the_function_against_the_real_command(self):
        got = self.shell("bash", BASH_DRIVER)
        first = got["[agentik ]"]
        self.assertEqual(sorted(first), sorted(list(cli.VERBS) + ["quill", "scribe"]))
        self.assertEqual(got["[agentik se]"], ["setup"])
        self.assertEqual(got["[agentik setup --d]"], ["--dry-run"])
        self.assertEqual(got["[agentik quill ]"], ["draw", "ink"])
        self.assertEqual(got["[mid]"], ["setup"])
        self.assertEqual(got["[agentik zzz ]"], [])
        shown = got["[complete]"]
        self.assertEqual(sorted(shown), ["complete -o default -F _agentik agentik",
                                         "complete -o default -F _agentik agentik-suite"])
        self.assertFalse(os.path.exists(self.marker))


class ZshDriverTest(Home):
    def test_3_the_function_registered_and_driven(self):
        got = self.shell("zsh", ZSH_DRIVER)
        self.assertIn("[comps] _agentik _agentik", got)
        self.assertEqual(sorted(got["[agentik ]"]), sorted(list(cli.VERBS) + ["quill", "scribe"]))
        self.assertEqual(got["[agentik se]"], ["setup"])
        self.assertEqual(got["[agentik setup --d]"], ["--dry-run"])
        self.assertEqual(got["[agentik quill ]"], ["draw", "ink"])
        self.assertEqual(got["[mid]"], ["setup"])
        self.assertEqual(got["[agentik zzz ]"], ["<files>"])
        self.assertFalse(os.path.exists(self.marker))


class NoProcessTest(Home):
    LINES = ([""], ["quill", ""], ["scribe", ""], ["setup", "--"], ["help", ""], ["config", ""],
             ["setup", ""], ["update", ""], ["issue", ""], ["status", "--"])

    def test_4_ten_lines_start_nothing(self):
        for line in self.LINES:
            self.words(*line)
        self.assertFalse(os.path.exists(self.marker), self.marker)

    def test_4_a_stale_or_absent_cache_gives_the_name_alone(self):
        quill = os.path.join(self.bin, "agentik-quill")
        os.utime(quill, ns=(1, 1))  # the stamp no longer matches
        os.unlink(os.path.join(tools.cache_dir(self.env()), "scribe.json"))
        names, out = self.words("")
        self.assertIn("quill\t\n", out + "\n")
        self.assertIn("scribe\t\n", out + "\n")
        for tool in ("quill", "scribe"):
            self.assertEqual(self.words(tool, "")[0], [])
        self.assertFalse(os.path.exists(self.marker))


class HostileTest(Home):
    def test_5_a_describe_is_data(self):
        hostile = HOSTILE.replace("{m}", self.mark)
        self.describe("quill", answer("quill", hostile % "tool", [("a;b", hostile % "verb"),
                                                                 ("draw", hostile % "verb")]))
        for line in ([""], ["quill", ""], ["help", ""]):
            names, out = self.words(*line)
            self.assertNotIn("\x1b", out)
            self.assertNotIn("a;b", names)
            for row in out.splitlines():
                self.assertEqual(row.count("\t"), 1, row)
        self.assertEqual(self.words("quill", "")[0], ["draw"])
        self.shell("bash", BASH_DRIVER)
        self.shell("zsh", ZSH_DRIVER)
        self.assertFalse(os.path.exists(self.mark))

    def test_5_a_summary_is_one_plain_line_of_80_columns(self):
        self.assertEqual(completion.summary("a\tb\nc\x1b[1md"), "a b cd")  # the whole CSI gone (sc17 R9)
        self.assertEqual(completion.summary("x\u200by"), "xy")  # term.clean drops the hidden mark
        self.assertEqual(completion.summary("x\u00ady"), "")  # a format character clean keeps is refused
        self.assertEqual(completion.summary(None), "")
        self.assertEqual(len(completion.summary("w" * 300)), 80)
        self.assertEqual(len(completion.summary("字" * 300)), 40)  # wide: two columns each


class TablesTest(Home):
    def offered(self, *line):
        out = io.StringIO()
        code = cli.Command(["completion", "words", "--"] + list(line), self.env(), out, io.StringIO()).run()
        self.assertEqual(code, 0)
        return [row.split("\t")[0] for row in out.getvalue().splitlines()]

    def test_6_each_verbs_flags_are_its_tables(self):
        for verb in cli.VERBS:
            want = [f[0] for f in cli.FLAGS + cli.VERB_FLAGS.get(verb, ())]
            want += [f for f, (_, owner) in cli.VALUE_FLAGS.items() if owner == verb and f not in cli.HOOKS]
            self.assertEqual(self.offered(verb, "-"), want, verb)
            for flag in want:
                line = [verb, flag] + (["x"] if flag in cli.VALUE_FLAGS else [])
                opts, words = cli.parse(line)[:2]
                self.assertIsNone(cli._flag_fault(opts, words, verb), line)
        self.assertNotIn("--ps", self.offered("status", "--p"))
        self.assertNotIn("--now", self.offered("status", "--n"))

    def test_6_a_flag_on_the_line_is_not_offered_again(self):
        self.assertNotIn("--dry-run", self.offered("setup", "--dry-run", "-"))
        self.assertNotIn("--quiet", self.offered("setup", "-q", "-"))
        self.assertIn("hq", self.offered("init", "--kind", ""))

    def test_6_a_flag_added_later_is_offered(self):
        saved = dict(cli.VERB_FLAGS)
        self.addCleanup(lambda: (cli.VERB_FLAGS.clear(), cli.VERB_FLAGS.update(saved)))
        cli.VERB_FLAGS["doctor"] = cli.DOCTOR_FLAGS + (("--fresh", None, "fresh"),)
        self.assertIn("--fresh", self.offered("doctor", "--"))

    def test_6_each_flag_has_its_message(self):
        messages = cli.term.catalogue.load()
        keys = [k for f in [cli.FLAGS] + list(cli.VERB_FLAGS.values()) for _, _, k in f]
        keys += [k for f, (k, _) in cli.VALUE_FLAGS.items() if f not in cli.HOOKS]
        self.assertEqual([k for k in keys if "flag." + k not in messages], [])


class RefusalsTest(Home):
    def test_7_bare_a_third_shell_and_a_word_more(self):
        for line in (["completion"], ["completion", "fish"], ["completion", "zsh", "more"]):
            code, out, err = self.run_(*line)
            self.assertEqual((code, out), (2, ""), line)
            lines = err.splitlines()
            self.assertEqual(len(lines), 2, err)
            self.assertTrue(lines[1].startswith("next: ") and lines[1].endswith(" help completion"), err)
            code, out, err = self.run_(*line, "--json")
            got = json.loads(out)
            self.assertEqual((code, got["ok"], got["schema"]), (2, False, "agentik.completion/1"))
            self.assertTrue(got["error"]["remedy"].endswith(" help completion"))

    def test_7_the_callback_with_no_word(self):
        for line in (["completion", "words"], ["completion", "words", "--"]):
            self.assertEqual(self.run_(*line), (0, "", ""))
        code, out, _ = self.run_("completion", "words", "--json")
        self.assertEqual(json.loads(out)["words"], [])
        code, out, err = self.run_("completion", "words", "--", "--json", "")
        self.assertEqual((code, err), (0, ""))

    def test_7_the_suite_takes_the_lines(self):
        for line in (["completion", "zsh"], ["completion", "bash"], ["completion", "words", "--", "x"]):
            self.assertFalse(cli.refused(line), line)
        for line in (["completion"], ["completion", "fish"], ["completion", "zsh", "more"]):
            self.assertTrue(cli.refused(line), line)


class SkillTest(unittest.TestCase):
    def test_8_the_skill(self):
        p = subprocess.run([str(ROOT / "scripts" / "plugin-description-bytes"), str(PLUGIN)],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        text = SKILL.read_text()
        head, body = re.match(r"---\n(.*?)\n---\n(.*)\Z", text, re.S).groups()
        self.assertIn("name: suite", head.splitlines())
        description = [l for l in head.splitlines() if l.startswith("description: ")][0]
        self.assertLessEqual(len(description[len("description: "):].encode()), 200)
        self.assertLessEqual(len(body.splitlines()), 60)
        lines = re.findall(r"`(agentik [^`]*)`", body)
        lines += [l.strip() for block in re.findall(r"```\n(.*?)```", body, re.S) for l in block.splitlines()]
        lines = [l for l in lines if l.startswith("agentik ")]
        self.assertTrue(lines)
        for line in lines:
            self.assertFalse(cli.refused(line.split()[1:]), line)
        self.assertIn("issue", body)


class ScreensTest(Home):
    def screen(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        cli.Command(list(argv), self.env(), out, err).run()
        return out.getvalue() + err.getvalue()

    def test_9_the_first_screen_does_not_change(self):
        now = self.screen()
        saved = cli.VERBS
        self.addCleanup(setattr, cli, "VERBS", saved)
        cli.VERBS = tuple(v for v in saved if v != "completion")
        self.assertEqual(self.screen(), now)
        self.assertNotIn("completion", now)

    def test_9_help_lists_the_verb_and_its_lines(self):
        code, out, _ = self.run_("help", "--json")
        self.assertIn("completion", [v["name"] for v in json.loads(out)["verbs"]])
        code, out, _ = self.run_("help", "completion")
        self.assertEqual(code, 0)
        self.assertRegex(out, r'eval "\$\(\S*agentik\S* completion zsh\)"\s+add this line to ~/\.zshrc')
        self.assertRegex(out, r'eval "\$\(\S*agentik\S* completion bash\)"\s+add this line to ~/\.bashrc')


if __name__ == "__main__":
    unittest.main()
