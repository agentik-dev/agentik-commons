"""Row sc4-errors: a refusal is the cause and then the command, and `config murmur width` is
`config murmur.width`.

Each run is the suite's launcher in a temp HOME whose PATH holds the door, a wrapper that puts
`agentik-suite` on PATH, a stub `claude`, and a made-up tool `murmur` that answers the config read
with the keys `width` and `paint.colour`; `paint` is a plugin installed with no command, and
`plum` one the marketplace names that is not installed. Every printed `next:` is pasted into
`sh -c` with stdin closed. Every tool and plugin here is made up."""
import io
import json
import os
import re
import subprocess
import sys
import unittest
from unittest import mock

import test_agentik_suite as base
from test_agentik_suite import LAUNCHER, ROOT

LIB = ROOT / "plugins" / "suite" / "lib"
sys.path.insert(0, str(LIB))
from agentik_suite import catalogue, cli  # noqa: E402

ANSI = re.compile(r"\x1b\[[0-9;]*m")
MURMUR = r'''#!/usr/bin/python3
import json, sys
args = sys.argv[1:]
def s(key, value):
    return {"key": key, "value": value, "default": value, "type": "string", "choices": None,
            "summary": "The %s." % key, "source": {"layer": "default", "path": None, "line": None},
            "change": {"kind": "fixed", "command": None, "path": None, "block": None, "note": None},
            "live": True, "values": [{"layer": "default", "value": value}]}
if args == ["describe", "--json"]:
    print(json.dumps({"schema": "agentik.describe/1", "ok": True, "tool": "murmur", "version": "1.0.0",
        "summary": "A made-up tool.", "repo": "example/murmur", "plugin": "murmur@agentik", "needs": [],
        "verbs": [{"name": "list", "summary": "List.", "top": True}],
        "reads": [{"kind": "config", "name": "settings", "argv": ["describe", "config", "--json"]}]}))
elif args[:3] == ["describe", "config", "--json"]:
    rows = [s("width", "80"), s("paint.colour", "dark")]
    if args[3:]:
        rows = [r for r in rows if r["key"] == args[3]]
    print(json.dumps({"schema": "agentik.config/1", "ok": True, "tool": "murmur", "settings": rows,
        "layers": [{"name": "default", "path": None, "present": True, "travels": False}]}))
else:
    sys.exit(0 if args[:1] in (["list"], ["--help"]) else 2)
'''

# R7's table: (argv, cause, next or None, exit, the pin's error.code)
TABLE = [
    (("confg",), "confg is not a verb", "agentik config", 2, "unknown_verb"),
    (("confg", "suite.kind"), "confg is not a verb", "agentik config suite.kind", 2, "unknown_verb"),
    (("murmr",), "murmr is not a tool", "agentik help murmur", 2, "unknown_verb"),
    (("murmr", "list"), "murmr is not a tool", "agentik murmur list", 2, "unknown_verb"),
    (("zzz",), "zzz is not a verb or a tool", "agentik help", 2, "unknown_verb"),
    (("paint",), "paint is a plugin with no command", "agentik config paint", 3, "not_installed"),
    (("plum",), "plum is not installed", "agentik setup plum", 3, "not_installed"),
    (("murmur",), "murmur is a tool, not a verb", "~/stubs/agentik-murmur --help", 2, "unknown_verb"),
    (("config", "--jsno"), "--jsno is not a flag of config", "agentik config --json", 2, "unknown_flag"),
    (("config", "--zzz"), "--zzz is not a flag of config", "agentik help config", 2, "unknown_flag"),
    (("--zzz",), "--zzz is not a flag", "agentik help", 2, "unknown_flag"),
    (("--help", "--version"), "--version takes no verb and no --help", "agentik --version", 2,
     "unknown_flag"),
    (("doctor", "--version"), "--version takes no verb and no --help", "agentik --version", 2,
     "unknown_flag"),
    (("doctor", "extra"), "doctor takes no name; extra is one more", "agentik help doctor", 2,
     "extra_word"),
    (("help", "config", "extra"), "help takes one name; extra is one more", "agentik help help", 2,
     "extra_word"),
    (("config", "--changed", "suite"), "config --changed takes no name; suite is one more",
     "agentik config --changed", 2, "extra_word"),
    (("config", "--changed", "--user-files"), "--changed and --user-files are two answers",
     "agentik config --changed", 2, "two_answers"),
    (("config", "murmr"), "murmr is not a tool here", "agentik config murmur", 2, "unknown_tool"),
    (("config", "murmr", "width"), "murmr is not a tool here", "agentik config murmur.width", 2,
     "unknown_tool"),
    (("config", "zzz"), "zzz is not a tool here", "agentik config", 2, "unknown_tool"),
    (("config", "murmur.widht"), "murmur has no key widht", "agentik config murmur.width", 2,
     "unknown_key"),
    (("config", "murmur", "zzz"), "murmur has no key zzz", "agentik config murmur", 2, "unknown_key"),
    (("config", ".width"), "a tool's name goes before the dot", "agentik config", 2, "unknown_tool"),
    (("config", "murmur."), "a key goes after the dot", "agentik config murmur", 2, "unknown_key"),
    (("config", "paint", "width"), "paint.width cannot be read: paint ships no command",
     "agentik config paint", 2, "no_answer"),
    (("describe",), "describe prints JSON for other tools, so it needs --json",
     "agentik help describe", 2, "needs_json"),  # --json is a flag not typed (review 1)
    (("setup", "Bad_Name"), "Bad_Name is not a plugin name: lowercase letters, digits and dashes",
     "agentik setup --dry-run", 2, "bad_name"),
]


class Sc4Home(base.Home):
    def setUp(self):
        base.Home.setUp(self)
        self.stub("murmur-impl", MURMUR)
        os.rename(os.path.join(self.stubs, "murmur-impl"), os.path.join(self.stubs, "agentik-murmur"))
        os.symlink(str(ROOT / "bin" / "agentik"), os.path.join(self.stubs, "agentik"))
        self.stub("agentik-suite", '#!/bin/sh\nexec "%s" "$@"\n' % LAUNCHER)
        plugins = os.path.join(self.home, ".claude", "plugins")
        market = os.path.join(self.home, "market")
        os.makedirs(os.path.join(market, ".claude-plugin"))
        os.makedirs(plugins)
        with open(os.path.join(market, ".claude-plugin", "marketplace.json"), "w") as fh:
            json.dump({"plugins": [{"name": "plum", "description": "A made-up plugin."},
                                   {"name": "suite", "description": "The set."}]}, fh)
        with open(os.path.join(plugins, "known_marketplaces.json"), "w") as fh:
            json.dump({"agentik": {"installLocation": market}}, fh)
        with open(os.path.join(plugins, "installed_plugins.json"), "w") as fh:
            json.dump({"plugins": {"paint@agentik": [{}]}}, fh)

    def paste(self, command):
        return self.pasted(command)[0]

    def pasted(self, command):
        p = subprocess.run(["sh", "-c", command], cwd=self.home, env=self.env(),
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
        return p.returncode, p.stdout, p.stderr

    def tree(self):
        """Every file and folder under the temp HOME, with its size and mtime."""
        found = {}
        for top, dirs, files in os.walk(self.home):
            for name in dirs + files:
                full = os.path.join(top, name)
                st = os.lstat(full)
                found[os.path.relpath(full, self.home)] = (st.st_size, st.st_mtime_ns)
        return found

    def assert_runs(self, command, why):
        """A pasted `next:` is not refused: it neither exits 127 nor 2, and prints no FAIL line."""
        code, out, err = self.pasted(command)
        self.assertNotIn(code, (2, 127), (why, command, err))
        self.assertFalse([l for l in err.splitlines() if l.startswith("FAIL")], (why, command, err))

    def assert_writes_nothing(self, command, why):
        before = self.tree()
        self.pasted(command)
        self.assertEqual(self.tree(), before, (why, command))
        self.assertFalse(os.path.exists(self.calls), (why, command))


class PathTest(Sc4Home):
    def test_l1_the_words_after_config_are_one_path(self):
        for spaced, dotted in ((("murmur", "width"), "murmur.width"),
                               (("murmur", "paint", "colour"), "murmur.paint.colour")):
            code, out, err = self.run_cli("config", *spaced)
            self.assertEqual(code, 0, err)
            self.assertEqual((code, out, err), self.run_cli("config", dotted), spaced)
            self.assertNotIn("murmur width", out + err)
            self.assertNotIn("murmur paint", out + err)

    def test_l5_no_tool_within_the_cutoff_is_offered(self):
        code, out, err = self.run_cli("config", "turns")
        self.assertEqual((code, out, err), (2, "", "FAIL  turns is not a tool here\nnext: agentik config\n"))


class TableTest(Sc4Home):
    def test_l2_l4_each_refusal_is_its_cause_then_its_command(self):
        for argv, cause, nxt, exit_code, _ in TABLE:
            code, out, err = self.run_cli(*argv)
            want = "FAIL  %s\n" % cause + ("next: %s\n" % nxt if nxt else "")
            self.assertEqual((code, out, err), (exit_code, "", want), argv)
            if nxt.split()[1:2] == ["setup"] and "--dry-run" not in nxt:
                # setup asks on a terminal; in a pipe it stops at that question and writes nothing
                self.assert_writes_nothing(nxt, argv)
                code, out, err = self.pasted(nxt)
                self.assertRegex(err, r"(?m)^FAIL  .*--yes", (argv, nxt))
            else:
                self.assert_runs(nxt, argv)

    def test_l3_json_gives_the_cause_and_the_command(self):
        for argv, cause, nxt, exit_code, code_word in TABLE:
            if argv == ("describe",):
                continue  # `describe --json` answers
            code, out, err = self.run_cli(*argv, "--json")
            got = json.loads(out)["error"]
            self.assertEqual((code, got["code"]), (exit_code, code_word), argv)
            if nxt.startswith("~/"):
                nxt = self.home + nxt[1:]
            self.assertEqual((got["message"], got["remedy"]), (cause, nxt), argv)

    def test_l2_a_file_that_does_not_parse_has_no_next(self):
        conf = os.path.join(self.home, "conf")
        os.makedirs(os.path.join(conf, "agentik", "suite", "config.yaml"))
        code, out, err = self.run_cli("config", "suite", XDG_CONFIG_HOME=conf)
        self.assertEqual((code, out), (2, ""))
        self.assertRegex(err, r"\AFAIL  [^\n]*config\.yaml cannot be read: a file that cannot be read\n\Z")
        code, out, err = self.run_cli("config", "suite", "--json", XDG_CONFIG_HOME=conf)
        got = json.loads(out)["error"]
        self.assertEqual((code, got["code"], got["remedy"]), (2, "bad_file", None))
        self.assertEqual("FAIL  %s\n" % got["message"], self.run_cli("config", "suite", XDG_CONFIG_HOME=conf)[2])

    def test_l2_a_version_with_no_manifest(self):
        path = os.path.join(str(LIB.parent), ".claude-plugin", "plugin.json")
        for asked in ([], ["--json"]):
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(cli.agentik_install, "version", return_value="0.0.0-unknown"):
                code = cli.Command(["version"] + asked, self.env(), out, err).run()
            cause = "agentik has no version: %s cannot be read" % path
            if asked:
                got = json.loads(out.getvalue())["error"]
                self.assertEqual((code, got["code"], got["message"], got["remedy"]),
                                 (2, "no_version", cause, "claude plugin install suite@agentik"))
            else:
                self.assertEqual((code, err.getvalue()),
                                 (2, "FAIL  %s\nnext: claude plugin install suite@agentik\n" % cause))
        self.assertNotEqual(self.paste("claude plugin install suite@agentik"), 127)


class FormTest(Sc4Home):
    def test_l6_on_a_terminal_the_glyph_then_next(self):
        code, text = self.run_pty("confg")
        lines = ANSI.sub("", text).replace("\r", "").splitlines()
        self.assertEqual(code, 2)
        self.assertEqual(lines[:2], ["✗  confg is not a verb", "next: agentik config"])

    def test_l6_a_hint_in_a_pipe_starts_next(self):
        code, out, err = self.run_cli("help")
        self.assertEqual(code, 0)
        self.assertRegex(err, r"\Anext: [^\n]*\n\Z")

    def test_l7_setup_and_install_keep_one_line(self):
        code, out, err = self.run_cli("install-cli", "--prefix")
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(err, "FAIL  --prefix needs a folder after it, and got none. Run agentik "
                              "install-cli --prefix <folder>, or leave it out for ~/.local.\n")
        code, out, err = self.run_cli("setup")
        lines = err.splitlines()
        self.assertEqual(code, 2, err)
        self.assertTrue(lines and lines[-1].startswith("FAIL  ") and "Run agentik setup" in lines[-1], err)
        self.assertFalse([l for l in lines if l.startswith("next:")], err)


class Review1Test(Sc4Home):
    """Review 1's findings. A mended line is offered only when it would run, and never when it
    does more than the typed line asked."""

    def refusal(self, argv, cause, nxt, exit_code=2, code_word=None, json_too=True):
        code, out, err = self.run_cli(*argv)
        self.assertEqual((code, out, err), (exit_code, "", "FAIL  %s\nnext: %s\n" % (cause, nxt)), argv)
        if not json_too:
            return
        code, out, err = self.run_cli("--json", *argv)  # first: a value flag takes what follows
        got = json.loads(out)["error"]
        want = self.home + nxt[1:] if nxt.startswith("~/") else nxt
        self.assertEqual((code, got["message"], got["remedy"]), (exit_code, cause, want), argv)
        if code_word:
            self.assertEqual(got["code"], code_word, argv)

    def test_f1_a_flag_is_never_mended_into_one_that_skips_a_question(self):
        for argv, cause, nxt in (
                (("setup", "--test"), "--test is not a flag of setup", "agentik help setup"),
                (("setup", "--ask"), "--ask is not a flag of setup", "agentik help setup"),
                (("setup", "--test", "plum"), "--test is not a flag of setup", "agentik help setup"),
                (("install-cli", "--test"), "--test is not a flag of install-cli",
                 "agentik help install-cli"),
                (("setup", "--yes", "--jsno"), "--jsno is not a flag of setup", "agentik help setup")):
            self.refusal(argv, cause, nxt, code_word="unknown_flag")
            self.assert_writes_nothing(nxt, argv)
        self.refusal(("setup", "--dry-rn"), "--dry-rn is not a flag of setup", "agentik setup --dry-run")

    def test_f2_a_word_that_is_no_verb_is_never_mended_into_a_verb_that_writes(self):
        for word in ("uninstall", "stop", "stup"):
            self.refusal((word,), "%s is not a verb" % word, "agentik help", code_word="unknown_verb")
            self.assert_writes_nothing("agentik help", word)
        self.refusal(("set", "suite.kind"), "set is not a verb", "agentik help")

    def test_f3_a_mended_line_that_would_be_refused_is_the_verbs_help(self):
        for argv, cause, nxt in (
                (("statu",), "statu is not a verb", "agentik help status"),
                (("start",), "start is not a verb", "agentik help status"),
                (("state",), "state is not a verb", "agentik help status"),
                (("describe", "x"), "describe prints JSON for other tools, so it needs --json",
                 "agentik help describe"),
                (("doctor", "--jsno", "x"), "--jsno is not a flag of doctor", "agentik help doctor")):
            self.refusal(argv, cause, nxt, json_too=argv[0] != "describe")
            self.assert_runs(nxt, argv)

    def test_f3_a_mended_line_the_door_would_refuse_is_help(self):
        # the door hands on a name first, `help` and at most one name, or `--version` alone
        for argv, cause in ((("help", "--jsno"), "--jsno is not a flag"),
                            (("--jsno", "config"), "--jsno is not a flag of config")):
            nxt = "agentik help config" if "config" in argv else "agentik help"
            self.refusal(argv, cause, nxt, code_word="unknown_flag")
            self.assert_runs(nxt, argv)

    def test_f4_a_value_flag_with_no_value_is_not_mended_into_another(self):
        for argv, cause in ((("status", "--ps"), "--ps is not a flag of status"),
                            (("status", "--check", "--ps"), "--ps is not a flag of status"),
                            (("status", "--pss"), "--pss is not a flag of status")):
            self.refusal(argv, cause, "agentik help status", code_word="unknown_flag")
            self.assert_runs("agentik help status", argv)

    def test_f5_with_no_door_a_mended_tool_is_its_own_file(self):
        os.remove(os.path.join(self.stubs, "agentik"))
        for argv, nxt in ((("murmr",), "~/stubs/agentik-murmur --help"),
                          (("murmr", "list"), "~/stubs/agentik-murmur list"),
                          (("help", "murmr"), "~/stubs/agentik-murmur --help")):
            self.refusal(argv, "murmr is not a tool", nxt, code_word="unknown_verb")
            self.assert_runs(nxt, argv)

    def test_f6_a_plugin_with_no_command_is_a_tool_by_its_name(self):
        self.refusal(("plumm",), "plumm is not a tool", "agentik help plum", code_word="unknown_verb")

    def test_f7_a_hint_that_does_not_start_next(self):
        class Tty(io.StringIO):
            encoding = "utf-8"

            def isatty(self):
                return True

        values = {"name": "murmur", "path": "~/x.json", "status": "agentik status"}
        for err, start in ((Tty(), "·  murmur is not checked"), (io.StringIO(), "next: murmur is not checked")):
            t = base.term.Term(no_color=True, env={}, out=io.StringIO(), err=err)
            t.hint("hint.status.unchecked", **values)
            self.assertTrue(err.getvalue().startswith(start), err.getvalue())
        for err in (Tty(), io.StringIO()):
            t = base.term.Term(no_color=True, env={}, out=io.StringIO(), err=err)
            t.hint("hint.help", setup="agentik setup")
            self.assertTrue(err.getvalue().startswith("next: agentik setup"), err.getvalue())

    def test_f7_each_hint_in_a_pipe_starts_next(self):
        for argv in (("help",), ("help", "config"), ("config",), ("config", "murmur"),
                     ("config", "murmur.width"), ("setup", "--dry-run")):
            code, out, err = self.run_cli(*argv)
            self.assertEqual(code, 0, (argv, err))
            self.assertRegex(err, r"\Anext: [^\n]*\n\Z", argv)
            self.assertNotIn("next: next:", err, argv)

    def test_f8_line_and_direction_controls_never_reach_the_screen(self):
        marks = "  ‪‫‬‭‮⁦⁧⁨⁩"
        for argv in (("‮confg",), ("confg", "x y"), ("confg", "a⁦b c"),
                     ("config", "murmr‭"), ("--zz⁧",)):
            code, out, err = self.run_cli(*argv)
            self.assertEqual((code, out), (2, ""), argv)
            self.assertIn("\nnext: ", err, argv)
            self.assertFalse([c for c in err if c in marks], (argv, err))


class CatalogueTest(unittest.TestCase):
    def test_l8_each_cause_is_short_and_holds_no_command(self):
        text = open(catalogue.PATH, encoding="utf-8").read()
        section = text.split("\n## Errors\n", 1)[1].split("\n## ", 1)[0]
        found = {m.group(1): m.group(2) for m in map(catalogue.ITEM.match, section.splitlines()) if m}
        turned = [mid for mid in found if not mid.startswith("err.status.")]
        self.assertGreaterEqual(len(turned), 22)
        for mid in turned:
            body = found[mid]
            for word in ("Run ", "Mend", "nearest", "exit"):
                self.assertNotIn(word, body, mid)
            self.assertFalse(body.endswith("."), mid)
            bare = catalogue.SLOT.sub("", catalogue.LONE.sub(r"\1", body))
            self.assertLessEqual(len(bare), 76, mid)


if __name__ == "__main__":
    unittest.main()
