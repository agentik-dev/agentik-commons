"""Row sc6-config: `config` in three steps, each ending on a command that runs (packet
design/packets/sc6-config.md, R1 to R9, acceptance 1 to 4). Each test starts the suite in a temp
HOME under an env of exactly HOME, PATH and XDG_CACHE_HOME, with a made-up tool, `loom`, of 24
keys in five groups and three lone keys; four keys are changed, one of them at a line the tool
does not give, so the suite finds it in the file (R5). The pty is opened with the standard library
and sized before the suite starts; no test reads the live home or the real terminal's size."""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_sc3_table import LAUNCHER, pty_run  # noqa: E402

ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
TOOL = "loom"
KEYS = ["mode", "speed", "voice",
        "ink.colour", "ink.weight", "ink.flow", "ink.dry",
        "page.width", "page.height", "page.margin", "page.gutter", "page.bleed",
        "spool.size", "spool.wind", "spool.tension", "spool.brake",
        "weave.warp", "weave.weft", "weave.twill", "weave.satin", "weave.plain", "weave.density",
        "feed.rate", "feed.pause"]
USER_FILE = "mode: fast\nink:\n  colour: black\n  weight: bold\npage:\n  width: 90\n"

STUB = """#!/usr/bin/python3
import json, os, sys
home = os.environ["HOME"]
user = os.path.join(home, ".config", "loom", "config.yaml")
repo = os.path.join(home, "work", ".claude", "agentik", "config.yaml")
KEYS = %(keys)r
SET = {"mode": ("fast", "user", user, 1), "ink.weight": ("bold", "user", user, 4),
       "page.width": ("90", "user", user, None), "weave.twill": ("tight", "repo", repo, 3)}
CHANGE = {"mode": {"kind": "command", "command": "agentik-loom set mode <value>"},
          "ink.weight": {"kind": "edit", "path": user, "block": "ink:\\n  weight: bold"},
          "voice": {"kind": "launch", "command": "loom --voice <voice>"},
          "feed.rate": {"kind": "fixed", "note": None}}
def s(key):
    value, layer, path, line = SET.get(key, ("d-" + key, "default", None, None))
    values = [{"layer": "default", "value": "d-" + key}]
    if layer != "default":
        values.append({"layer": layer, "value": value, "path": path, "line": line})
    change = dict({"kind": "command", "command": "agentik-loom set %%s <value>" %% key, "path": None,
                   "block": None, "note": None}, **CHANGE.get(key, {}))
    return {"key": key, "value": value, "default": "d-" + key, "type": "string",
            "choices": ["fast", "slow"] if key == "mode" else None,
            "summary": "The %%s of the loom." %% key,
            "source": {"layer": layer, "path": path, "line": line},
            "change": change, "live": key != "voice", "values": values}
args = sys.argv[1:]
if args == ["describe", "--json"]:
    print(json.dumps({"schema": "agentik.describe/1", "ok": True, "tool": "loom", "version": "1.0.0",
        "summary": "A made-up tool.", "repo": "example/loom", "plugin": "loom@agentik", "needs": [],
        "verbs": [{"name": "set", "summary": "Set one.", "top": True}],
        "reads": [{"kind": "config", "name": "settings", "argv": ["describe", "config", "--json"]}]}))
elif args[:3] == ["describe", "config", "--json"]:
    rows = [s(k) for k in KEYS]
    if args[3:]:
        rows = [r for r in rows if r["key"] == args[3]]
    print(json.dumps({"schema": "agentik.config/1", "ok": True, "tool": "loom", "settings": rows,
        "layers": [{"name": "default", "path": None, "present": True, "travels": False},
                   {"name": "user", "path": user, "present": True, "travels": True},
                   {"name": "repo", "path": repo, "present": True, "travels": False}],
        "warnings": [{"path": user, "line": 9, "key": "inq.weight", "reason": "unknown"}]}))
elif args[:1] == ["doctor"]:
    sys.exit(0)
else:
    sys.exit(2)
"""


def loom_home(home):
    """The temp HOME with `agentik-loom` and a stub `claude` on PATH, the user file written; the
    env of exactly HOME, PATH and XDG_CACHE_HOME."""
    stubs = os.path.join(home, "stubs")
    os.makedirs(stubs, exist_ok=True)
    os.makedirs(os.path.join(home, ".config", "loom"), exist_ok=True)
    with open(os.path.join(home, ".config", "loom", "config.yaml"), "w") as fh:
        fh.write(USER_FILE)
    script = os.path.join(home, "loom.py")
    with open(script, "w") as fh:
        fh.write(STUB % {"keys": KEYS})
    for name, body in (("agentik-" + TOOL, '#!/bin/sh\nexec /usr/bin/python3 -B "%s" "$@"\n' % script),
                       ("claude", "#!/bin/sh\nexit 0\n")):
        path = os.path.join(stubs, name)
        with open(path, "w") as fh:
            fh.write(body)
        os.chmod(path, 0o755)
    return {"HOME": home, "PATH": "%s:/usr/bin:/bin" % stubs, "XDG_CACHE_HOME": os.path.join(home, "cache")}


class Screens(unittest.TestCase):
    def setUp(self):
        self._home = tempfile.TemporaryDirectory()
        self.home = os.path.realpath(self._home.name)
        self.env = loom_home(self.home)

    def tearDown(self):
        self._home.cleanup()

    def pty(self, *args, cols=80):
        return ANSI.sub("", pty_run(LAUNCHER, list(args), self.env, cols)).replace("\r", "")

    def pipe(self, *args, **more):
        return subprocess.run([str(LAUNCHER), *args], env=self.env, capture_output=True, text=True,
                              cwd=self.home, timeout=60, **more)

    def next_line(self, text):
        found = [line for line in text.splitlines() if line.startswith("next: ")]
        self.assertEqual(len(found), 1, text)
        return found[0][len("next: "):]

    # ---- acceptance -----------------------------------------------------------------------

    def test_a1_24_keys_fold_to_20_lines_on_a_pty_and_print_flat_in_a_pipe(self):
        shown = self.pty("config", TOOL).rstrip("\n").split("\n")
        self.assertLessEqual(len(shown), 20, "\n".join(shown))
        # a command is never cut (sc3): the `next:` line, whose launcher is a temp path, may pass 80
        self.assertTrue(all(len(line) <= 80 for line in shown if not line.startswith("next: ")),
                        "\n".join(shown))
        p = self.pipe("config", TOOL)
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = [line for line in p.stdout.splitlines() if line[:3] in ("*  ", "   ")]
        self.assertEqual(sorted(line.split()[1 if line.startswith("*") else 0] for line in rows), sorted(KEYS))

    def test_a2_a_changed_key_shows_its_path_and_line_at_steps_2_and_3(self):
        user = "~/.config/loom/config.yaml"
        for out in (self.pty("config", TOOL), self.pipe("config", TOOL).stdout):
            weight = [line for line in out.splitlines() if " ink.weight " in line]
            self.assertTrue(weight and weight[0].startswith("*"), out)
            self.assertIn(user + ":4", weight[0])
            width = [line for line in out.splitlines() if " page.width " in line]
            self.assertIn(user + ":6", width[0], "the line found in the file (R5)")
        for out in (self.pty("config", TOOL + ".ink.weight"), self.pipe("config", TOOL + ".ink.weight").stdout):
            self.assertRegex(out, r"set in +%s:4 +\(user\)" % re.escape(user))

    def test_a3_each_next_runs_as_printed_and_is_the_same_on_a_pty_and_in_a_pipe(self):
        for args in (["config"], ["config", TOOL]):
            on_pty = self.next_line(self.pty(*args))
            in_pipe = self.next_line(self.pipe(*args).stderr)
            self.assertEqual(on_pty, in_pipe)
            ran = subprocess.run(["/bin/sh", "-c", in_pipe], env=self.env, capture_output=True,
                                 text=True, cwd=self.home, stdin=subprocess.DEVNULL, timeout=60)
            self.assertEqual(ran.returncode, 0, (in_pipe, ran.stderr))
        self.assertTrue(self.next_line(self.pipe("config").stderr).endswith("config " + TOOL))
        self.assertTrue(self.next_line(self.pipe("config", TOOL).stderr).endswith("config loom.mode"))

    def test_a4_the_words_after_config_are_one_path(self):
        a = subprocess.run([str(LAUNCHER), "config", TOOL, "ink.weight"], env=self.env, capture_output=True,
                           cwd=self.home, timeout=60)
        b = subprocess.run([str(LAUNCHER), "config", TOOL + ".ink.weight"], env=self.env,
                           capture_output=True, cwd=self.home, timeout=60)
        self.assertEqual((a.returncode, a.stdout, a.stderr), (b.returncode, b.stdout, b.stderr))

    # ---- the rulings ----------------------------------------------------------------------

    def test_r2_step_1_one_row_a_tool_and_a_mark_only_where_wrong(self):
        p = self.pipe("config")
        lines = p.stdout.splitlines()
        self.assertRegex(lines[0], r"^Keys by tool: 4 of \d+ changed from their defaults\.$")
        loom = [line for line in lines if line.split()[:1] == [TOOL]]
        self.assertTrue(loom, p.stdout)
        self.assertRegex(loom[0], r"^ +loom +24 keys +4 changed +~/\.config/loom/config\.yaml$")
        self.assertNotIn("answers", p.stdout)
        self.assertNotRegex(p.stdout, r"(?m)^ *ok ")
        self.assertNotIn("from a list", p.stdout + p.stderr)

    def test_r3_a_prefix_prints_its_group_flat(self):
        p = self.pipe("config", TOOL + ".weave")
        self.assertEqual(p.returncode, 0, p.stderr)
        names = sorted(w for line in p.stdout.splitlines()[1:] for w in line.split() if w.startswith("weave."))
        self.assertEqual(names, sorted(k for k in KEYS if k.startswith("weave.")))
        self.assertTrue(self.next_line(p.stderr).endswith("config loom.weave.twill"))
        shown = self.pty("config", TOOL + ".weave")
        self.assertIn("weave.density", shown)

    def test_r3_all_prints_every_key_flat_on_a_pty(self):
        shown = self.pty("config", TOOL, "--all")
        for key in KEYS:
            self.assertRegex(shown, r"(?m)^[* ] +%s " % re.escape(key))

    def test_r3_the_title_names_the_layers_and_an_unknown_key_its_line(self):
        out = self.pty("config", TOOL)
        self.assertIn("loom: 24 keys, 4 changed (*). Layers, lowest first: default, user, repo.", out)
        self.assertRegex(out, r"unknown key inq\.weight +~/\.config/loom/config\.yaml:9")
        self.assertRegex(out, r"(?m)^ +weave +6 +warp weft twill\* satin plain density$")

    def test_r4_the_card(self):
        out = self.pipe("config", TOOL + ".mode").stdout
        lines = out.splitlines()
        self.assertRegex(lines[0], r"^loom\.mode = fast +\(default d-mode\)$")
        self.assertEqual(lines[1], "The mode of the loom.")
        self.assertRegex(out, r"layers +default d-mode, user fast")
        self.assertRegex(out, r"choices +fast slow")
        self.assertRegex(out, r"change +agentik-loom set mode <value>")
        self.assertRegex(out, r"applies +now")
        p = self.pipe("config", TOOL + ".mode")
        self.assertNotIn("next:", p.stderr)
        edit = self.pipe("config", TOOL + ".ink.weight").stdout
        self.assertRegex(edit, r"change +edit ~/\.config/loom/config\.yaml:4")
        launch = self.pipe("config", TOOL + ".voice").stdout
        self.assertRegex(launch, r"change +at launch: loom --voice <voice>")
        self.assertRegex(launch, r"applies +at the next start of Claude Code")
        fixed = self.pipe("config", TOOL + ".feed.rate").stdout
        self.assertRegex(fixed, r"change +fixed: no command changes it")


if __name__ == "__main__":
    unittest.main()
