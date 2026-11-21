"""Row sc12-picker: the picker as a component (design/23 section 4a). The screens are checked
through the pure `layout`, the keys through the parser and the key handler, and the doors off a
full terminal in a child process on a pipe or a pty. The terminal's modes and the signals are
`scripts/pick-probe`'s, run by hand; here only its shape. Every name is made up."""
import ast
import io
import os
import pty
import re
import select
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "plugins" / "suite" / "lib"
PACKAGE = LIB / "agentik_suite"
PROBE = ROOT / "scripts" / "pick-probe"
sys.path.insert(0, str(LIB))

from agentik_suite import catalogue, pick, term  # noqa: E402

EXTRA = {"t.plugins": "Which plugins does setup install?", "t.effort": "How hard does the model think?",
         "t.key": "Which key?", "t.run": "Run these {count} commands now?", "t.yes": "Run them",
         "t.no": "Don't run anything",
         "t.typed": "Run these {count} commands now? y for yes, n or Enter for no."}
# The four reads the brief allows outside pick.py, each by file and function; a later row
# moves each onto pick.
ALLOWED = {("apply.py", "_before"), ("issue.py", "_ask"), ("remove.py", "Remove.ask"),
           ("update.py", "Update.ask")}
READ = re.compile(r"\binput\(|stdin\.readline|termios")


def a_term(env=None):
    messages = dict(catalogue.load())
    messages.update(EXTRA)
    return term.Term(env=env or {"LANG": "en_US.UTF-8"}, out=io.StringIO(), err=io.StringIO(),
                     messages=messages)


def plugins(least=1):
    def check(text):
        return "" if re.fullmatch("[a-z][a-z0-9-]*", text) else "%s is not a plugin's name" % text
    return {"id": "plugins", "tab": "Plugins", "prompt": "t.plugins", "kind": "many",
            "least": least, "default": ["session", "decisions", "relay"],
            "options": [{"value": v, "label": v, "note": n} for v, n in (
                ("session", "Profiles, the budget and the charter for a sitting"),
                ("decisions", "One ledger per repo, and the questions put to its owner"),
                ("agents", "Every agent on this machine, and helpers on a local model"),
                ("relay", "Queued runs, one child per worktree"),
                ("respeak", "Agent output as a narrative for a named reader"))],
            "other": {"label": "other", "note": "a plugin's name, typed", "check": check}}


def keys28():
    return {"id": "key", "tab": "Key", "prompt": "t.key", "kind": "one", "filter": True,
            "noun": "keys", "options": [{"value": "k%02d" % i, "label": "tool.part.key%02d" % i,
                                         "note": "What key %d does, said at some length here." % i}
                                        for i in range(28)] +
            [{"value": "effort", "label": "session.effort", "note": "How hard the model thinks."}]}


def effort():
    return {"id": "effort", "tab": "Effort", "prompt": "t.effort", "kind": "one", "default": "medium",
            "options": [{"value": v, "label": v, "note": v + " thought"} for v in
                        ("low", "medium", "high", "xhigh", "max")]}


def shown(t, lines, cols):
    plain = term.Term(env={}, out=io.StringIO(), err=io.StringIO(), messages=t.messages)
    return [pick._painted(plain, segs, cols - 1, "…") for segs in lines]


def press(handler, *keys):
    got = (False, None)
    for k in keys:
        got = handler(*k) if isinstance(k, tuple) else handler("text", k)
    return got


def feed(handler, data, utf8=True):
    """Every byte through the parser, as the loop does once the 50 ms wait is over."""
    buf = data
    while buf:
        event, used = pick.parse(buf, True, utf8)
        buf = buf[used:]
        if event[0] != "none":
            handler(*event)


def child(code, stdin=None, env=None, tty=False):
    """A child Python running `code` with the package on its path: (exit, stdout, stderr)."""
    env = dict(env or {}, PATH="/usr/bin:/bin", LANG="en_US.UTF-8")
    head = "import sys; sys.path.insert(0, %r)\n" % str(LIB)
    if not tty:
        p = subprocess.run([sys.executable, "-I", "-c", head + code], input=stdin or b"",
                           capture_output=True, env=env, timeout=30)
        return p.returncode, p.stdout, p.stderr
    master, slave = pty.openpty()
    p = subprocess.Popen([sys.executable, "-I", "-c", head + code], stdin=slave, stdout=subprocess.PIPE,
                         stderr=slave, env=env)
    os.close(slave)
    seen = b""

    def drain(wait):
        got = b""
        while select.select([master], [], [], wait)[0]:
            try:
                chunk = os.read(master, 4096)
            except OSError:
                break
            if not chunk:
                break
            got += chunk
            wait = 0.2
        return got
    if stdin:
        seen += drain(5)  # the question shows first: a line typed ahead is dropped by design
        os.write(master, stdin)
    out = p.communicate(timeout=30)[0]
    seen += drain(0.2)
    os.close(master)
    return p.returncode, out, seen


class Screens(unittest.TestCase):
    def test_a2_each_key_at_both_widths(self):
        t = a_term()
        sets = [[plugins()], [keys28()], [plugins(), effort(), keys28()]]
        keys = [("down", None), ("down", None), ("up", None), ("pagedown", None), ("end", None),
                ("home", None), ("pageup", None), "j", "k", " ", "e", "f", ("back", None),
                ("clear", None), ("tab", None), ("right", None), ("backtab", None),
                ("left", None), ("enter", None), ("esc", None)]
        for cols in (80, 50):
            for qs in sets:
                st = pick.State(t, qs, utf8=True)
                handler, heights = pick._Ask(st), set()
                for k in keys:
                    try:
                        press(handler, k)
                    except pick.Cancelled:
                        st = pick.State(t, qs, utf8=True)
                        handler = pick._Ask(st)
                    lines, cursor = pick.layout(st, cols, 24)
                    heights.add(len(lines))
                    for line in shown(t, lines, cols):
                        self.assertLessEqual(term.columns(line), cols - 1, (cols, k, line))
                    if cursor:
                        self.assertLess(cursor[0], len(lines))
                        self.assertLess(cursor[1], cols)
                self.assertEqual(len(heights), 1, (cols, [q["id"] for q in qs], heights))

    def test_a2_the_yes_or_no_frames(self):
        t = a_term()
        for cols in (80, 50):
            st = pick.Confirm(t, t.text("t.run", count=2), t.text("t.yes"), t.text("t.no"))
            rest = ["Run these 2 commands now?", "  Run them", "❯ Don't run anything",
                    "↑↓ move  Enter choose  Esc cancel"]
            self.assertEqual(shown(t, pick.layout(st, cols, 24)[0], cols), rest)
            yes = pick._Yes(st)
            self.assertEqual(press(yes, "y"), (False, None))
            self.assertEqual(shown(t, pick.layout(st, cols, 24)[0], cols)[1:3],
                             ["❯ Run them", "  Don't run anything"])
            self.assertEqual(press(yes, ("enter", None)), (True, True))
        ascii_ = pick.Confirm(t, "Q?", "Yes", "No", utf8=False)
        self.assertEqual(shown(t, pick.layout(ascii_, 50, 24)[0], 50)[2:],
                         ["> No", "up/down move  Enter choose  Esc cancel"])

    def test_a2_the_strip_the_review_and_the_marks(self):
        t = a_term()
        st = pick.State(t, [plugins(), effort(), keys28()], utf8=True)
        h = pick._Ask(st)
        press(h, ("tab", None))
        top = shown(t, pick.layout(st, 50, 24)[0], 50)
        self.assertTrue(top[0].startswith(" Plugins ✓  [Effort ✓]"), top[0])
        self.assertIn("❯ (x) medium", "\n".join(top))
        press(h, ("backtab", None), ("backtab", None))
        review = shown(t, pick.layout(st, 50, 24)[0], 50)
        self.assertEqual(review[1], "Check your answers")
        self.assertIn("! not answered", review[4])
        press(h, ("enter", None))
        self.assertEqual(st.tab, 2)
        self.assertEqual(st.error, "Key needs an answer")
        ascii_ = shown(t, pick.layout(pick.State(t, [plugins()], utf8=False), 50, 24)[0], 50)
        self.assertTrue(any(x.startswith("> [x] session") for x in ascii_), ascii_)
        self.assertEqual(shown(t, pick.layout(st, 39, 24)[0], 39), ["! needs 40 columns by 13 rows"])

    def test_a2_a_label_is_cut_in_its_middle(self):
        self.assertEqual(pick.middle("session.budget.turns", 11, "…"), "sessi…turns")
        self.assertEqual(pick.middle("short", 11, "…"), "short")

    def test_filter_and_no_match(self):
        t = a_term()
        st = pick.State(t, [keys28()], utf8=True)
        h = pick._Ask(st)
        press(h, "e", "f", "f")
        lines = shown(t, pick.layout(st, 50, 24)[0], 50)
        self.assertEqual(lines[0], "Which key?  1 of 29 keys")
        self.assertIn("❯ session.effort", "\n".join(lines))
        self.assertEqual(press(h, ("enter", None)), (True, {"key": "effort"}))
        st = pick.State(t, [keys28()], utf8=True)
        h = pick._Ask(st)
        press(h, "z", "z", "z")
        self.assertIn("  no keys match zzz", shown(t, pick.layout(st, 80, 24)[0], 80))
        self.assertEqual(press(h, ("enter", None)), (False, None))
        self.assertEqual(st.error, "no keys match zzz")


class Keys(unittest.TestCase):
    def test_a3_escape_forms_leave_the_filter_empty(self):
        t = a_term()
        forms = [b"\x1b\x1b[A", b"\x1b[[A", b"\x1b]11;rgb:0000/0000/0000\x07",
                 b"\x1b]11;rgb:0000/0000/0000\x1b\\", b"\x1bP1$r0m\x1b\\", b"\x1b[M !!",
                 b"\x1b_x\x1b\\", b"\x1b^x\x07", b"\x1bOP", b"\x1b[1;5A", b"\x1bx"]
        for form in forms:
            st = pick.State(t, [keys28()], utf8=True)
            feed(pick._Ask(st), form)
            self.assertEqual(st.qs[0].filter, "", form)

    def test_a3_a_split_sequence_waits(self):
        self.assertEqual(pick.parse(b"\x1b[", False, True), (None, 0))
        self.assertEqual(pick.parse(b"\x1b[A", False, True), (("up", None), 3))
        self.assertEqual(pick.parse(b"\x1b", True, True), (("esc", None), 1))
        self.assertEqual(pick.parse(b"\x1b[200~", False, True), (("paste_on", None), 6))
        self.assertEqual(pick.parse("é".encode(), False, True), (("text", "é"), 2))
        self.assertEqual(pick.parse("é".encode("latin-1"), False, False), (("text", "é"), 1))

    def test_f1_a_run_of_esc_is_one_esc(self):
        self.assertEqual(pick.parse(b"\x1b\x1b\x1b", True, True), (("esc", None), 3))
        self.assertEqual(pick.parse(b"\x1b" * 1100, True, True), (("esc", None), 1100))
        self.assertEqual(pick.parse(b"\x1b\x1b", False, True), (None, 0))  # an Alt prefix, perhaps
        event, used = pick.parse(b"\x1b" * 1100, False, True)  # held: no wait for an end
        self.assertEqual(event, ("esc", None))
        self.assertEqual(pick.parse(b"\x1b\x1b[A", False, True), (("none", None), 4))
        st = pick.Confirm(a_term(), "Q?", "Yes", "No")
        feed(pick._Yes(st), b"\x1b" * 1100)
        self.assertEqual(st.focus, 1)
        st = pick.State(a_term(), [keys28()], utf8=True)
        with self.assertRaises(pick.Cancelled):
            feed(pick._Ask(st), b"\x1b\x1b\x1b")


class SameAs(unittest.TestCase):
    def plain(self, qs, lines, command):
        t = a_term()
        old, sys.stdin = sys.stdin, io.StringIO(lines)
        where, pick._where = pick._where, lambda t_: "plain"
        try:
            got = pick.ask(t, qs, command)
        finally:
            sys.stdin, pick._where = old, where
        return got, t.err.raw.getvalue()

    def test_a7_a_typed_value_is_one_word(self):
        q = plugins()
        q["other"]["check"] = lambda text: ""
        got, err = self.plain([q], "1 6\n/tmp/my profile; echo $HOME\n",
                              lambda a: ["agentik", "setup"] + list(a["plugins"]))
        self.assertEqual(got["plugins"], ["session", "/tmp/my profile; echo $HOME"])
        self.assertIsInstance(got["plugins"][1], pick.Other)
        line = err[err.index("same as: "):].rstrip("\n")
        self.assertEqual(line, "same as: agentik setup session '/tmp/my profile; echo $HOME'")
        words = line[len("same as: "):]
        p = subprocess.run(["sh", "-c", "printf '<%s>' " + words], capture_output=True, text=True)
        self.assertEqual(p.stdout, "<agentik><setup><session></tmp/my profile; echo $HOME>")

    def test_a7_a_refused_other_stays_wherever_the_focus_is(self):
        t = a_term()
        st = pick.State(t, [plugins()], utf8=True)
        h = pick._Ask(st)
        press(h, *[("down", None)] * 5)
        self.assertEqual(st.qs[0].row(), "other")
        press(h, *"Bad Name")
        press(h, ("up", None))
        self.assertEqual(press(h, ("enter", None)), (False, None))
        self.assertEqual(st.error, "Bad Name is not a plugin's name")
        self.assertEqual(st.qs[0].row(), "other")
        self.assertIn("! Bad Name is not a plugin's name", shown(t, pick.layout(st, 50, 24)[0], 50))

    def test_a7_least_one_stays_and_refuses_none(self):
        t = a_term()
        st = pick.State(t, [plugins()], utf8=True)
        h = pick._Ask(st)
        press(h, " ", ("down", None), " ", ("down", None), ("down", None), " ")
        self.assertEqual(press(h, ("enter", None)), (False, None))
        self.assertEqual(st.error, "tick at least one")
        with self.assertRaises(pick.Cancelled):
            self.plain([plugins()], "none\nnone\nnone\n", lambda a: ["x"])
        got, err = self.plain([plugins()], "none\n\n", lambda a: ["agentik", "setup"] + a["plugins"])
        self.assertIn("! tick at least one", err)
        self.assertIn("Numbers (1 3, 2-4 or none); Enter keeps 1 2 4:", err)
        self.assertEqual(got["plugins"], ["session", "decisions", "relay"])

    def test_a7_the_plain_prompt_reads_a_name_past_its_window(self):
        old = os.get_terminal_size
        os.get_terminal_size = lambda fd=None: os.terminal_size((80, 5))
        try:
            got, err = self.plain([keys28()], "nope\nsession.effort\n", lambda a: ["agentik", a["key"]])
        finally:
            os.get_terminal_size = old
        self.assertEqual(got, {"key": "effort"})
        self.assertIn("! nope is not one of the names above", err)
        self.assertNotIn("  1  ", err)
        self.assertNotIn("\x1b", err)


class Doors(unittest.TestCase):
    ASK = ("from agentik_suite import pick, term\n"
           "t = term.Term(messages=dict(term.catalogue.load(), q='Which?', y='Yes', n='No', ty='Go? y or n.'))\n"
           "qs = [{'id': 'a', 'prompt': 'q', 'kind': 'one', 'options': [{'value': 'x', 'label': 'x'}]}]\n"
           "try:\n"
           "    %s\n"
           "except pick.NoTerminal:\n"
           "    sys.exit(3)\n")

    def test_a10_no_terminal_writes_no_byte(self):
        for call in ("pick.ask(t, qs, lambda a: ['x'])", "pick.confirm(t, 'q', 'y', 'n', 'ty')"):
            code, out, err = child(self.ASK % call, stdin=b"1\ny\n")
            self.assertEqual((code, out, err), (3, b"", b""), call)
            code, out, seen = child(self.ASK % call, stdin=b"", env={"CI": "1", "TERM": "xterm"}, tty=True)
            self.assertEqual((code, out, seen), (3, b"", b""), call)

    def test_a11_no_termios_still_imports_and_asks_plain(self):
        code = "sys.modules['termios'] = None\n" + (self.ASK % "print(pick.ask(t, qs, lambda a: ['x']))")
        rc, out, seen = child(code, stdin=b"1\n", env={"TERM": "xterm-256color"}, tty=True)
        self.assertEqual((rc, out), (0, b"{'a': 'x'}\n"), seen)
        self.assertIn(b"Number:", seen)
        self.assertNotIn(b"\x1b", seen)

    def test_a9_the_typed_form_reads_one_line(self):
        for env in ({"TERM": "dumb"}, {"TERM": "xterm", "AGENTIK_PLAIN": "1"}):
            rc, out, seen = child(self.ASK % "print(pick.confirm(t, 'q', 'y', 'n', 'ty'))",
                                  stdin=b"  YES \n", env=env, tty=True)
            self.assertEqual((rc, out), (0, b"True\n"), seen)
            self.assertIn(b"Go? y or n.", seen)
            self.assertNotIn(b"\x1b", seen)


def reads_outside_pick(path, source):
    """Each read of a person outside pick.py that no allow line names: (file, function, line)."""
    tree = ast.parse(source)
    where = {}

    def walk(node, prefix):
        for child_ in ast.iter_child_nodes(node):
            if isinstance(child_, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + child_.name
                for n in range(child_.lineno, getattr(child_, "end_lineno", child_.lineno) + 1):
                    where[n] = name
                walk(child_, name + ".")
            else:
                walk(child_, prefix)
    walk(tree, "")
    hits = []
    for n, line in enumerate(source.splitlines(), 1):
        if READ.search(line.split("#")[0]) and (path, where.get(n, "")) not in ALLOWED:
            hits.append((path, where.get(n, ""), n))
    return hits


class OneReader(unittest.TestCase):
    def test_a12_pick_is_the_one_reader(self):
        for p in sorted(PACKAGE.glob("*.py")):
            if p.name != "pick.py":
                self.assertEqual(reads_outside_pick(p.name, p.read_text()), [], p.name)

    def test_a12_a_planted_read_is_red(self):
        source = (PACKAGE / "config.py").read_text()
        self.assertEqual(reads_outside_pick("config.py", source), [])
        self.assertTrue(reads_outside_pick("config.py", source + "\ndef planted():\n    return input('x')\n"))
        self.assertTrue(reads_outside_pick("apply.py", "def other():\n    import termios\n"))

    def test_the_four_allowed_reads_are_there(self):
        found = set()
        for path, fn in ALLOWED:
            source = (PACKAGE / path).read_text()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and fn.split(".")[-1] == node.name:
                    seg = "\n".join(source.splitlines()[node.lineno - 1:node.end_lineno])
                    if READ.search(seg):
                        found.add((path, fn))
        self.assertEqual(found, ALLOWED)


class Words(unittest.TestCase):
    def test_r9_the_pick_section(self):
        text = (PACKAGE / "messages.md").read_text()
        section = text.split("\n## Pick\n", 1)[1].split("\n## ", 1)[0]
        ids = re.findall(r"^- `(pick\.[a-z.]+)`: (.*)$", section, re.M)
        self.assertLess(len(ids), 30)
        for mid, body in ids:
            self.assertLessEqual(len(re.sub(r"`\{[^}]*\}`", "", body).replace("`", "")), 76, mid)
            self.assertNotIn("!", body, mid)
        used = set(re.findall(r'"(pick\.[a-z.]+)"', (PACKAGE / "pick.py").read_text()))
        self.assertLessEqual(used, {m for m, _ in ids})
        self.assertEqual(used, {m for m, _ in ids})

    def test_r1_clean_drops_the_zero_width_and_direction_controls(self):
        self.assertEqual(term.clean("a​b‏c﻿d‮e⁦f"), "abcdef")

    def test_r1_put_has_no_line_break_and_need_not_wait(self):
        t = a_term()
        t.put("one")
        t.put("two", err=False)
        self.assertEqual((t.err.raw.getvalue(), t.out.raw.getvalue()), ("one", "two"))
        r, w = os.pipe()
        try:
            with os.fdopen(w, "w", closefd=False) as fh:
                s = term._Stream(fh, True)
                left = s.put(b"x" * 200000, wait=False)
                self.assertTrue(0 < len(left) < 200000)
        finally:
            os.close(r)
            os.close(w)

    def test_a_tab_is_at_most_twelve(self):
        q = effort()
        q["tab"] = "a" * 13
        with self.assertRaises(ValueError):
            pick.State(a_term(), [q])


class Probe(unittest.TestCase):
    def test_r10_shape(self):
        self.assertTrue(PROBE.read_text().startswith("#!/usr/bin/env python3\n"))
        self.assertTrue(os.access(PROBE, os.X_OK))
        p = subprocess.run([str(PROBE), "--help"], capture_output=True, text=True, timeout=30)
        self.assertEqual((p.returncode, p.stdout), (0, "usage: pick-probe [--python PATH]\n"))
        for args in (["--bogus"], ["--python"]):
            p = subprocess.run([str(PROBE), *args], capture_output=True, text=True, timeout=30)
            self.assertEqual((p.returncode, p.stdout), (2, ""), args)

    def test_r10_make_never_runs_it(self):
        self.assertNotIn("pick-probe", (ROOT / "Makefile").read_text())


if __name__ == "__main__":
    unittest.main()
