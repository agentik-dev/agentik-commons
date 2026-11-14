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
     "agentik describe --json", 2, "needs_json"),
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
        p = subprocess.run(["sh", "-c", command], cwd=self.home, env=self.env(),
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
        return p.returncode


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
            self.assertNotEqual(self.paste(nxt), 127, (argv, nxt))

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
