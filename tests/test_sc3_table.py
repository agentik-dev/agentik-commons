"""Row sc3-table: a table is laid out to the terminal's width, and `COLUMNS` is read (packet
design/packets/sc3-table.md, R1 to R10, acceptance 1 to 9). Lines 1 to 6 draw through
`Term.table` on a fake stream that answers isatty, its width given by `COLUMNS`; no test reads the
real terminal's size. Lines 7 and 8 start the suite in a temp HOME under an env of exactly HOME,
PATH and XDG_CACHE_HOME, with a made-up tool of 24 keys, one of whose values is a sentence of 180
characters; the pty is opened with the standard library and sized before the suite starts."""
import fcntl
import io
import os
import pty
import re
import select
import struct
import subprocess
import sys
import tempfile
import termios
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "plugins" / "suite" / "lib"
LAUNCHER = ROOT / "plugins" / "suite" / "bin" / "agentik-suite"
sys.path.insert(0, str(LIB))
from agentik_suite import term  # noqa: E402

ESC = "\x1b"
ANSI = re.compile(r"\x1b\[[0-9;]*m")
TOOL = "quill"
WORDS = ["lantern%02d" % i for i in range(17)]
SENTENCE = (" ".join(WORDS) + " " + "z" * 200)[:180]  # 180 characters, words apart by one space

STUB = """#!/usr/bin/python3
import json, os, sys
home = os.environ["HOME"]
user = os.path.join(home, ".config", "quill", "config.yaml")
def s(i):
    key = "k%%02d" %% i
    value = %(sentence)r if i == 5 else "v%%d" %% i
    return {"key": key, "value": value, "default": "v%%d" %% i, "type": "string", "choices": None,
            "summary": "The %%s of each line." %% key,
            "source": {"layer": "default", "path": None, "line": None},
            "change": {"kind": "command", "command": "agentik-quill set %%s VALUE" %% key, "path": None,
                       "block": None, "note": None},
            "live": True, "values": [{"layer": "default", "value": "v%%d" %% i}]}
args = sys.argv[1:]
if args == ["describe", "--json"]:
    print(json.dumps({"schema": "agentik.describe/1", "ok": True, "tool": "quill", "version": "1.0.0",
        "summary": "A made-up tool.", "repo": "example/quill", "plugin": "quill@agentik", "needs": [],
        "verbs": [{"name": "set", "summary": "Set one.", "top": True}],
        "reads": [{"kind": "config", "name": "settings", "argv": ["describe", "config", "--json"]}]}))
elif args[:3] == ["describe", "config", "--json"]:
    rows = [s(i) for i in range(24)]
    if args[3:]:
        rows = [r for r in rows if r["key"] == args[3]]
    print(json.dumps({"schema": "agentik.config/1", "ok": True, "tool": "quill", "settings": rows,
        "layers": [{"name": "default", "path": None, "present": True, "travels": False},
                   {"name": "user", "path": user, "present": False, "travels": True}]}))
elif args[:1] == ["doctor"]:
    sys.exit(0)
else:
    sys.exit(2)
"""

SCREENS = [[], ["help"], ["help", "issue"], ["config"], ["config", TOOL], ["config", TOOL + ".k05"],
           ["doctor"], ["setup", "--dry-run"], ["status", "--check"]]


def stub_home(home):
    """The temp HOME's stub folder and the env of exactly HOME, PATH and XDG_CACHE_HOME."""
    stubs = os.path.join(home, "stubs")
    os.makedirs(stubs, exist_ok=True)
    script = os.path.join(home, "quill.py")
    with open(script, "w") as fh:
        fh.write(STUB % {"sentence": SENTENCE})
    for name, body in (("agentik-" + TOOL, '#!/bin/sh\nexec /usr/bin/python3 -B "%s" "$@"\n' % script),
                       ("claude", "#!/bin/sh\nexit 0\n")):
        path = os.path.join(stubs, name)
        with open(path, "w") as fh:
            fh.write(body)
        os.chmod(path, 0o755)
    return {"HOME": home, "PATH": "%s:/usr/bin:/bin" % stubs, "XDG_CACHE_HOME": os.path.join(home, "cache")}


def pty_run(launcher, args, env, cols):
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, cols, 0, 0))
    p = subprocess.Popen([str(launcher), *args], stdin=slave, stdout=slave, stderr=slave, env=env,
                         close_fds=True)
    os.close(slave)
    chunks = []
    try:
        while True:
            ready, _, _ = select.select([master], [], [], 30)
            if not ready:
                break
            try:
                data = os.read(master, 65536)
            except OSError:
                break
            if not data:
                break
            chunks.append(data)
    finally:
        os.close(master)
    p.wait(timeout=30)
    return b"".join(chunks).decode("utf-8", "replace")


class Fake(io.StringIO):
    def __init__(self, tty=True):
        io.StringIO.__init__(self)
        self.tty = tty

    def isatty(self):
        return self.tty

    @property
    def encoding(self):
        return "utf-8"

    def fileno(self):  # never a real descriptor: the terminal's size is always mocked or absent
        raise io.UnsupportedOperation("fileno")


def draw(rows, width=None, tty=True, colour=False, own=None, indent=2, **env):
    """The lines one table writes on a fake stream; `own` is the terminal's own size, mocked."""
    if width is not None:
        env["COLUMNS"] = str(width)
    if not colour:
        env.setdefault("NO_COLOR", "1")
    out = Fake(tty)
    t = term.Term(env=env, out=out, err=Fake(tty))
    if own is None:
        t.table(rows, indent=indent)
    else:
        with mock.patch.object(term.os, "get_terminal_size", lambda fd: os.terminal_size((own, 24))), \
                mock.patch.object(Fake, "fileno", lambda self: 99):
            t.table(rows, indent=indent)
    return out.getvalue().split("\n")[:-1]


def plain(line):
    return ANSI.sub("", line)


class LayoutTest(unittest.TestCase):
    def test_a1_a_long_sentence_wraps_inside_its_column(self):
        for width in (50, 60, 80, 120):
            lines = draw([("ok", [term.name("tool-a"), SENTENCE, "default"], None)], width)
            for line in lines:
                self.assertLessEqual(term.columns(line), width, (width, line))
            self.assertTrue(lines[0].endswith("  default"), (width, lines))
            words = " ".join(lines).replace("default", "").replace("tool-a", "").split()
            self.assertEqual(words[1:], SENTENCE.split(), width)  # the mark, then each word once
            self.assertGreater(len(lines), 1, width)

    def test_a2_a_path_that_does_not_fit_goes_whole_under_the_row(self):
        p = "/" + "/".join(["folder%02d" % i for i in range(10)])[:89]
        self.assertEqual(len(p), 90)
        lines = draw([("ok", [term.name("tool-a"), term.path(p)], None)], 60)
        self.assertEqual([l for l in lines if p in l], [" " * 6 + p], lines)
        self.assertEqual([l for l in lines if term.columns(l) > 60 and p not in l], [])

    def test_a3_an_after_command_that_does_not_fit_goes_whole_at_the_fixed_indent(self):
        cmd = ("agentik-tool-a set " + "k" * 60)[:70]
        lines = draw([("note", [term.name("tool-a"), "a short cell", "x"], cmd)], 50)
        self.assertEqual([l for l in lines if cmd in l], [" " * 6 + cmd], lines)

    def test_a4_columns_are_counted_by_the_screen_not_by_len(self):
        lines = draw([(None, ["日本語", "x"], None), (None, ["abc", "y"], None),
                      (None, ["ab\u0301c", "z"], None)], 80)
        at = [term.columns(l[:l.index(c)]) for l, c in zip(lines, "xyz")]
        self.assertEqual(at, [2 + 6 + 2] * 3, lines)

    def test_a4_r2_a_zero_width_character_takes_no_column(self):
        self.assertEqual([term.columns(s) for s in ("a\u200bb", "a\u200db", "\ufeffab", "e\u0301", "日")],
                         [2, 2, 2, 1, 2])

    def test_a5_columns_is_read_on_a_terminal(self):
        long = [("ok", [term.name("tool-a"), "word " * 60], None)]
        for env, want in (({"COLUMNS": "60"}, 60), ({}, 120), ({"COLUMNS": ""}, 120), ({"COLUMNS": "0"}, 120),
                          ({"COLUMNS": "abc"}, 120), ({"COLUMNS": "10"}, 40), ({"COLUMNS": "-5"}, 120)):
            lines = draw(long, own=120, **env)
            widest = max(term.columns(l) for l in lines)
            self.assertLessEqual(widest, want, (env, lines))
            self.assertGreater(widest, want - 8, (env, lines))

    def test_a5_r1_off_a_terminal_columns_is_not_read(self):
        rows = [("ok", [term.name("tool-a"), SENTENCE, "default"], "run: x")]
        self.assertEqual(draw(rows, 60, tty=False), draw(rows, tty=False))
        self.assertEqual(len(draw(rows, 60, tty=False)), 2)

    def test_a6_each_line_of_a_wrapped_cell_is_painted_on_its_own(self):
        name = " ".join(["part%02d" % i for i in range(14)])
        rows = [("ok", [term.name(name), "done"], None)]
        lines = draw(rows, 50, colour=True)
        held = [l for l in lines if "part" in l]
        self.assertGreater(len(held), 1, lines)
        for line in held:
            self.assertIn("\x1b[1m", line)
            self.assertTrue(line.rstrip(" ").endswith("\x1b[0m") or "done" in line, line)
            self.assertEqual(line.count("\x1b[") - line.count("\x1b[0m"), line.count("\x1b[0m"), line)
        self.assertIn("✓", lines[0])
        self.assertNotIn(ESC, "".join(draw(rows, 50)))

    def test_r4_a_word_longer_than_its_column_is_whole(self):
        word = "w" * 30
        lines = draw([("ok", [term.name("tool-a"), "short " + word + " end", "last"], None)], 60)
        self.assertEqual([l.strip() for l in lines if word in l], [word], lines)
        self.assertTrue(lines[0].endswith("last"), lines)

    def test_r4_a_last_cell_with_a_word_longer_than_its_room_goes_under_the_row(self):
        word = "/" + "w" * 60
        lines = draw([("ok", [term.name("tool-a"), "a cell", "on " + word + " here"], None)], 60)
        self.assertEqual(lines[0], "  ✓  tool-a  a cell")
        self.assertEqual(lines[1:], [" " * 6 + "on", " " * 6 + word, " " * 6 + "here"])

    def test_r5_a_last_column_of_under_24_puts_a_long_last_cell_under_the_row(self):
        lines = draw([("ok", [term.name("tool-a"), "middle words here and there", "one two three " * 5], None)], 50)
        self.assertNotIn("one", lines[0])
        self.assertIn("middle", lines[0])
        under = [l for l in lines if "one" in l]
        self.assertGreater(len(under), 1, lines)
        for line in under:
            self.assertTrue(line.startswith(" " * 6) and line[6] != " ", lines)
            self.assertLessEqual(term.columns(line), 50)

    def test_r9_off_a_terminal_the_pins_bytes(self):
        out = Fake(False)
        t = term.Term(env={"COLUMNS": "60"}, out=out, err=Fake(False))
        t.table([("ok", ["a", term.name("b"), "x" * 300], None), ("note", ["c", "d", "e"], "run: z")])
        self.assertEqual(out.getvalue(), "  ok    a  b  " + "x" * 300 + "\n  note  c  d  e\n" + " " * 14 + "run: z\n")


class ScreenTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = os.path.realpath(tmp.name)
        self.env = stub_home(self.home)

    def test_a7_a_pipe_ignores_columns(self):
        for args in SCREENS:
            seen = []
            for more in ({}, {"COLUMNS": "60"}):
                p = subprocess.run([str(LAUNCHER), *args], capture_output=True, env=dict(self.env, **more),
                                   timeout=60)
                seen.append((p.returncode, p.stdout, p.stderr))
            self.assertEqual(seen[0], seen[1], args)
            self.assertNotIn(ESC.encode(), seen[0][1] + seen[0][2], args)

    def test_a8_on_a_pty_no_table_line_passes_the_width(self):
        for cols in (60, 80):
            for args in SCREENS:
                text = pty_run(LAUNCHER, args, self.env, cols)
                for line in plain(text).replace("\r\n", "\n").split("\n"):
                    if term.columns(line) <= cols or line[:1] not in " " + "".join(term.GLYPH.values()):
                        continue  # a title, a hint or a usage line starts at the edge: R10's, not a table's
                    held = line.strip()  # a single word or path, or a line that holds a command:
                    moved = re.match("( {6}| {8})[^ ]", line)  # a path or an `after` at the fixed indent
                    self.assertTrue(" " not in held or str(LAUNCHER) in held or moved, (cols, args, line))
                    self.assertNotIn("lantern", line, (cols, args))


if __name__ == "__main__":
    unittest.main()
