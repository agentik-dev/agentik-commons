"""The screen of status (packet su2-screen): one agentik.status/1 object drawn on the grid of R4,
for a terminal and for a pipe. Each test is in process: a Term over two streams it holds, the
terminal one answering isatty with no fileno (so its width is 80), colour off unless the test
says so, TZ=UTC. The objects and screens under fixtures/su2/screen use made-up tools only."""
import copy
import io
import json
import os
import re
import sys
import time
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "plugins" / "suite" / "lib"
FIX = Path(__file__).resolve().parent / "fixtures" / "su2" / "screen"
ESC = "\x1b"
NAMES = ("quiet", "busy", "broken")
PARTS = ("watchers", "sessions", "gate", "backlog", "runs")

sys.path.insert(0, str(LIB))
from agentik_suite import term  # noqa: E402

_TZ = None


def setUpModule():
    global _TZ
    _TZ = os.environ.get("TZ")
    os.environ["TZ"] = "UTC"
    time.tzset()


def tearDownModule():
    if _TZ is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = _TZ
    time.tzset()


def screen_module():
    from agentik_suite import status_screen  # each line fails here at the pin
    return status_screen


def load(name):
    return json.loads((FIX / ("%s.json" % name)).read_text())


def fixture(name, kind):
    return (FIX / ("%s.%s.txt" % (name, kind))).read_text(encoding="utf-8")


class Stream(io.StringIO):
    def __init__(self, tty, encoding="utf-8"):
        super().__init__()
        self._tty, self._encoding = tty, encoding

    def isatty(self):
        return self._tty

    @property
    def encoding(self):
        return self._encoding


def make(tty, env=None, quiet=False, width=None):
    out, err = Stream(tty), Stream(tty)
    t = term.Term(env={"NO_COLOR": "1"} if env is None else env, out=out, err=err, quiet=quiet)
    if width is not None:
        t.out.width = lambda: width
    return t, out, err


def slots(tool="agentik"):
    """The suite's commands as `cmd.slots()` names them where `tool` starts them (row sc2)."""
    return {"status": tool + " status", "doctor": tool + " doctor", "tool": tool}


def draw(obj, tty, tool="agentik", **kw):
    t, out, err = make(tty, **kw)
    screen_module().draw(t, obj, slots(tool))
    t.flush()
    return out.getvalue(), err.getvalue()


def piped(obj, **kw):
    return draw(obj, False, **kw)


class FixtureTest(unittest.TestCase):
    """Lines 1 to 6: the three states, byte for byte."""

    def test_line1_quiet(self):
        self.assertEqual(draw(load("quiet"), True), (fixture("quiet", "tty"), ""))
        self.assertEqual(piped(load("quiet")), (fixture("quiet", "piped"), ""))

    def test_line2_busy(self):
        self.assertEqual(draw(load("busy"), True), (fixture("busy", "tty"), ""))
        out, err = piped(load("busy"))
        self.assertEqual((out, err), (fixture("busy", "piped"), ""))
        self.assertLess(len(out.encode()), 2048)

    def test_line3_broken(self):
        sentence = fixture("broken", "hint").rstrip("\n")
        out, err = draw(load("broken"), True)
        self.assertEqual(out, fixture("broken", "tty"))
        self.assertEqual(err, "%s\n" % sentence)  # a hint that starts `next:` has no mark (sc4)
        out, err = piped(load("broken"))
        self.assertEqual(out, fixture("broken", "piped"))
        self.assertEqual(err, "%s\n" % sentence)
        for tty in (True, False):
            self.assertEqual(draw(load("broken"), tty, quiet=True)[1], "")

    def test_line4_the_cut(self):
        for width in (80, 60, 200):
            for name in NAMES:
                out, _ = draw(load(name), True, width=width)
                whole = [r[16:] for r in piped(load(name))[0].splitlines()]
                long = [r for r in out.splitlines() if len(r) > width]
                for row in long:  # a fault, a command or a tool's stderr line, never cut
                    self.assertIn(row[13:], whole, (width, row))
                    self.assertNotIn("…", row)
                if width == 80:
                    self.assertEqual(len(long), 2 if name == "broken" else 0, (name, long))
                if width == 200:
                    self.assertNotIn("…", out)
                    self.assertEqual(long, [])
                for row in out.splitlines():
                    if row.endswith("…"):
                        self.assertEqual(len(row), width, row)
                    for cell in re.split(r" {2,}", row[13:])[:-1]:  # a cell cut at a third
                        if cell.endswith("…"):
                            self.assertEqual(len(cell), width // 3, (row, cell))

    def test_line5_bytes_and_colour(self):
        for name in NAMES:
            out, err = piped(load(name), env={})
            self.assertNotIn(ESC, out + err)
            (out + err).encode("ascii")
            out, _ = draw(load(name), True, env={})
            for label in PARTS + ("sources",):
                self.assertIn("\x1b[1m%s\x1b[0m" % label, out, (name, label))
            for mark, sgr in (("✓", "32"), ("!", "33"), ("·", "36")):
                if re.search(r"^%s  " % re.escape(mark), fixture(name, "tty"), re.M):
                    self.assertIn("\x1b[%sm%s\x1b[0m" % (sgr, mark), out, (name, mark))
            out, err = draw(load(name), True, env={"NO_COLOR": "1"})
            self.assertNotIn(ESC, out + err)

    def test_line6_part_by_part(self):
        mod = screen_module()
        for name in NAMES:
            for tty in (True, False):
                t, out, err = make(tty)
                for part in PARTS:
                    mod.part(t, load(name), part, "agentik")
                mod.foot(t, load(name), "agentik")
                t.flush()
                self.assertEqual((out.getvalue(), err.getvalue()), draw(load(name), tty), (name, tty))
        obj = load("broken")
        some = {k: obj[k] for k in ("at", "covers", "watchers", "hand", "sources")}
        t, out, _ = make(False)
        mod.part(t, some, "watchers", "agentik")
        self.assertEqual(out.getvalue(), "".join(fixture("broken", "piped").splitlines(True)[:5]))


def rows(obj):
    return piped(obj)[0].splitlines()


def text(obj):
    return [r[16:] for r in rows(obj)]


class CapTest(unittest.TestCase):
    """Line 7: at most five rows under a part's first."""

    def test_line7_nine_sessions_and_nine_jobs(self):
        obj = load("busy")
        one = obj["sessions"]["live"][0]
        obj["sessions"]["live"] = [dict(one, id="id%d" % i, name="s%d" % i) for i in range(9)]
        got = text(obj)
        i = got.index(next(r for r in got if r.startswith("9 live")))
        self.assertTrue(all(got[i + k].startswith("s%d " % (k - 1)) for k in range(1, 5)), got)
        self.assertEqual(got[i + 5], "and 5 more: agentik crew status")
        self.assertTrue(rows(obj)[i + 6].startswith("ok    gate"))
        job = obj["gate"]["running"][0]
        obj["gate"]["running"] = [dict(job, name="j%d" % i, label="") for i in range(6)]
        obj["gate"]["red"] = [dict(job, name="r%d" % i, exit=1, cut=None) for i in range(1)]
        got = text(obj)
        i = got.index(next(r for r in got if r.startswith("6 running, 2 queued")))
        self.assertEqual([r.split()[0] for r in got[i + 1:i + 5]], ["running"] * 4)
        self.assertEqual(got[i + 5], "and 5 more: agentik bench gate status")
        self.assertTrue(rows(obj)[i + 6].startswith("ok    backlog"))


class WordsTest(unittest.TestCase):
    """Line 8: R9's words the fixtures do not show."""

    def test_no_watcher_declared(self):
        obj = load("quiet")
        obj["watchers"] = []
        self.assertEqual(rows(obj)[0], "note  watchers  none declared")

    def test_a_watcher_not_checked(self):
        obj = load("quiet")
        obj["watchers"][0].update(state="unknown", beat_line=None)
        obj["hand"] = [{"part": "watchers", "kind": "watcher_unknown", "name": "lamp", "remedy": None}]
        self.assertEqual(rows(obj)[0], "warn  watchers  lamp: not checked: ps gave no listing")

    def test_past_window_and_checked_false(self):
        obj = load("quiet")
        obj["sessions"].update(checked=False, past_window=[{"id": "abcdef0123456789", "pid": 7}])
        got = text(obj)
        i = got.index("1 live")
        self.assertEqual(got[i + 1], "abcdef01      live; no turn in the last 30 min")
        self.assertEqual(got[i + 2], "processes not checked: ps gave no listing")

    def test_running_and_no_runner(self):
        obj = load("busy")
        obj["gate"].update(queued=[], runner=None)
        obj["hand"] = [{"part": "gate", "kind": "no_runner", "name": None,
                        "remedy": "agentik bench gate status"}]
        got = rows(obj)
        i = next(k for k, r in enumerate(got) if r.startswith("warn  gate"))
        self.assertEqual(got[i], "warn  gate      3 running and no runner alive; last: flight0127 passed")
        self.assertEqual(got[i + 1], " " * 16 + "see: agentik bench gate status")

    def test_covers(self):
        obj = load("quiet")
        obj["covers"]["rule"] = "none"
        got = rows(obj)
        i = next(k for k, r in enumerate(got) if "backlog" in r)
        self.assertEqual(got[i], "note  backlog   no checkout here; name one: agentik status PATH")
        self.assertTrue(got[i + 1].startswith("ok    runs"))
        obj["covers"]["rule"] = "checkouts"
        obj["backlog"]["checkouts"] = 2
        self.assertIn("3 open steps in 2 checkouts from the user file", text(obj))
        obj["covers"]["rule"] = "args"
        obj["backlog"].update(checkouts=1, open=1)
        self.assertIn("1 open step in 1 checkout named", text(obj))

    def test_a_part_with_no_source(self):
        obj = load("quiet")
        obj["sources"] = [s for s in obj["sources"] if s["name"] != "gate"]
        obj["gate"] = {"state": "not read", "runner": None, "running": [], "queued": [], "red": [],
                       "last": None}
        self.assertIn("note  gate      not read: no tool here gives it", rows(obj))

    def test_not_drawn_and_none_read(self):
        obj = load("quiet")
        obj["sources"][1]["state"] = "not drawn"
        self.assertIn("not drawn: agentik-bench gate", text(obj))
        for s in obj["sources"]:
            s["state"] = "not installed"
        self.assertIn("      sources   no source read", rows(obj))

    def test_a_null_context_and_one_of_each(self):
        obj = load("busy")
        live = obj["sessions"]["live"][0]
        live.update(context=None, turns=1, helpers={"busy": 1})
        obj["sessions"]["live"] = [live]
        obj["backlog"].update(open=1, checkouts=1)
        got = text(obj)
        self.assertIn("acme-hq  ?/1M  1 turn  busy; 1 helper busy", got)
        self.assertIn("1 live, 1 helper busy; 2 ended in the last 30 min", got)
        self.assertIn("1 open step in 1 checkout beside acme-hq (kind: hq)", got)


class HintTest(unittest.TestCase):
    """Line 9: R10's four cases."""

    def test_line9_the_hint(self):
        obj = load("quiet")
        obj["hand"] = [{"part": "runs", "kind": "run_gone", "name": "r1", "remedy": "agentik baton status"}]
        self.assertEqual(piped(obj)[1], "next: agentik baton status\n")
        obj["hand"] = [dict(obj["hand"][0], remedy=None), dict(obj["hand"][0], name="r2", remedy=None)]
        self.assertEqual(piped(obj)[1], "next: 2 need a hand, and no command for them is known\n")
        obj = load("quiet")
        obj["sources"][2]["state"] = "timed out"
        self.assertEqual(piped(obj)[1], "next: agentik doctor\n")
        self.assertEqual(piped(load("quiet"))[1], "")
        self.assertEqual(piped(load("busy"))[1], "")



def columns(text):
    """Screen columns, counted apart from term: a wide character two, a combining mark none."""
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in "WF" else 1
               for c in text)


def tty(obj, width=80):
    return draw(obj, True, width=width)[0].splitlines()


def part_rows(lines, label, lead=16):
    """The rows of one part: its first row, found by its label, and the rows under it."""
    i = next(k for k, r in enumerate(lines) if r[lead - 10:lead].rstrip() == label)
    j = next((k for k in range(i + 1, len(lines)) if lines[k][:lead].strip()), len(lines))
    return lines[i:j]


class CleanTest(unittest.TestCase):
    """R1-F5 and R1-F7: the cleaner drops line and direction controls; a tab or a break is a space."""

    def test_r1f5_line_and_direction_controls(self):
        self.assertEqual(term.clean("a\u2028b\u2029c\u202ad\u202ee\u2066f\u2069g\x1bh"), "abcdefgh")
        obj = load("quiet")
        obj["watchers"][0]["beat_line"] = "lamp ok\u2028ok    gate      spoofed row\u202eRLO"
        for tty_ in (True, False):
            out = draw(obj, tty_, width=200)[0]
            self.assertEqual(len(out.splitlines()), len(draw(load("quiet"), tty_, width=200)[0].splitlines()))
            self.assertNotIn("\u202e", out)
            self.assertNotIn("\u2028", out)

    def test_r1f7_a_tab_or_a_break_is_one_space(self):
        self.assertEqual(term.clean("first line\nsecond line\tcol"), "first line second line col")
        self.assertEqual(term.clean("a\r\nb\rc\x0bd\x0ce\x85f"), "a b c d e f")
        obj = load("broken")
        obj["sources"][0]["stderr"] = "first line\nsecond line\tcol"
        self.assertIn("first line second line col", text(obj))


class ColumnsTest(unittest.TestCase):
    """R1-F4: a cut and a pad count screen columns."""

    def test_r1f4_wide_and_combining(self):
        obj = load("busy")
        obj["backlog"]["first"]["title"] = "\u5bfc\u5165\u7a0b\u5e8f\u8bfb\u53d6" * 10
        row = next(r for r in tty(obj) if "first:" in r)
        self.assertEqual(columns(row), 80, row)
        self.assertTrue(row.endswith("\u2026"), row)
        obj["backlog"]["first"]["title"] = "e\u0301" * 80
        row = next(r for r in tty(obj) if "first:" in r)
        self.assertEqual(columns(row), 80, row)
        obj = load("busy")
        obj["sessions"]["live"][1]["name"] = "\u6570\u636e\u5e93"
        for lines in (tty(obj), rows(obj)):
            at = {columns(r[:r.index("k/1M") - 3]) for r in part_rows(lines, "sessions", 16 - 3 * (lines[0][0] != "o"))[1:]}
            self.assertEqual(len(at), 1, lines)


class ThirdTest(unittest.TestCase):
    """R1-F6: no column but the last takes more than a third of the width."""

    def test_r1f6_a_long_cell_is_cut_at_a_third(self):
        obj = load("broken")
        obj["gate"]["queued"][0]["label"] = "land the importer fix and the follow-up review round"
        got = part_rows(tty(obj), "gate", 13)
        self.assertTrue(got[-1].endswith("failed"), got)
        self.assertTrue(got[2][13:].startswith("queued  acme-cli: land the import\u2026  "), got)
        for r in got[2:]:
            self.assertLessEqual(columns(re.split(r"\s{2,}", r[13:])[1]), 80 // 3, r)
        obj = load("busy")
        obj["sessions"]["live"][0]["name"] = "s" * 70
        for r in part_rows(tty(obj), "sessions", 13)[1:]:
            self.assertIn(" turns", r)
        self.assertIn("s" * 70, piped(obj)[0])


class GoneTest(unittest.TestCase):
    """R1-F1: a gone run by its tool and its id; a run the object says is alive is never gone."""

    def test_r1f1_an_alive_run_with_a_gone_id(self):
        obj = load("broken")
        gone = obj["runs"]["shown"][0]
        obj["runs"]["shown"] = [dict(gone, by="unattended", source="unattended", pid=5151, alive=True,
                                     row="importer-fix", age_s=40, rows={"landed": 2}), gone]
        self.assertEqual([r[16:] for r in part_rows(rows(obj), "runs")], [
            "unattended 2026-11-13-2: running row importer-fix, its last line 40 s ago; 2 landed",
            "baton 2026-11-13-2: reads running, and its process (pid 4242) is gone",
            "see: agentik baton status",
            "not read: agentik-bench gave no answer in 1 s"])

    def test_r1f1_the_hand_names_the_tool(self):
        obj = load("broken")
        gone = obj["runs"]["shown"][0]
        obj["runs"]["shown"] = [dict(gone, by="unattended", source="unattended", pid=5151), gone]
        obj["hand"][-1]["tool"] = "unattended"
        got = [r[16:] for r in part_rows(rows(obj), "runs")]
        self.assertEqual(got[:3], [
            "unattended 2026-11-13-2: reads running, and its process (pid 5151) is gone",
            "see: agentik baton status",
            "baton 2026-11-13-2: running; 1 green, 1 running"])


class MarkTest(unittest.TestCase):
    """R1-F2: only a part the object says was read whole takes the ok mark."""

    def test_r1f2_an_absent_part(self):
        obj = load("quiet")
        for name in ("sessions", "gate", "backlog", "runs"):
            del obj[name]
        got = piped(obj)
        for name in ("sessions", "gate", "backlog", "runs"):
            self.assertIn("warn  %-8s  not read: the status object holds no %s" % (name, name),
                          got[0].splitlines())

    def test_r1f2_a_missing_or_unknown_state(self):
        obj = load("quiet")
        obj["gate"]["state"] = "broken"
        self.assertIn("warn  gate      unknown: gate reads a state not known here, broken", rows(obj))
        obj["gate"]["state"] = "hand"
        self.assertTrue(part_rows(rows(obj), "gate")[0].startswith("warn  gate"))
        del obj["gate"]["state"]
        self.assertIn("warn  gate      not read: gate holds no state", rows(obj))

    def test_r1f2_a_watcher_not_running(self):
        obj = load("quiet")
        for state in (None, "crashed"):
            obj["watchers"][0]["state"] = state
            self.assertEqual(rows(obj)[0], "warn  watchers  lamp: unknown: its state reads %s" % (state or "?"))
        obj["watchers"][0]["state"] = "missing"
        self.assertTrue(rows(obj)[0].startswith("warn  watchers  lamp: not running since"), rows(obj)[0])
        del obj["watchers"]
        self.assertEqual(rows(obj)[0], "warn  watchers  not read: the status object holds no watchers")


def malformed():
    """The review's malformed objects: each a name, the part it breaks, and the object."""
    cases = []

    def case(name, part, base, change):
        obj = load(base)
        change(obj)
        cases.append((name, part, obj))

    case("since 1e20", "watchers", "broken", lambda o: o["watchers"][0].update(since=1e20))
    case("since a date", "watchers", "broken", lambda o: o["watchers"][0].update(since="2026-11-04"))
    case("at now", "watchers", "broken", lambda o: o.update(at="now"))
    case("context 326k", "sessions", "busy", lambda o: o["sessions"]["live"][0].update(context="326k"))
    case("helpers busy 3", "sessions", "busy", lambda o: o["sessions"]["live"][0].update(helpers={"busy": "3"}))
    case("not_read null", "not read", "broken", lambda o: o.update(not_read=[None]))
    case("not_read a word", "not read", "broken", lambda o: o.update(not_read="owner"))
    case("gate a word", "gate", "broken", lambda o: o.update(gate="ok"))
    case("skipped a word", "backlog", "busy", lambda o: o["backlog"].update(skipped="acme-notes"))
    case("runs shown a word", "runs", "broken", lambda o: o["runs"].update(shown="x"))
    case("live a dict", "sessions", "busy", lambda o: o["sessions"].update(live={"a": 1}))
    case("items a list", "backlog", "busy", lambda o: o["backlog"].update(items=["S3"]))
    case("sources a word", "sources", "quiet", lambda o: o.update(sources="crew"))
    return cases


class GuardTest(unittest.TestCase):
    """R1-F3: each part behind one guard; no traceback on any object."""

    def test_r1f3_a_value_of_the_wrong_kind(self):
        labels = PARTS + ("sources",)
        for name, part, obj in malformed():
            for tty_ in (True, False):
                lead = 13 if tty_ else 16
                out, err = draw(obj, tty_, width=200)
                lines = out.splitlines()
                self.assertEqual([r[lead - 10:lead].strip() for r in lines if r[:lead].strip()
                                  and r[lead - 10:lead].strip() != "not read"], list(labels), (name, out))
                self.assertIn("not read: %s has a value of the wrong kind" % part,
                              [r[lead:] for r in part_rows(lines, part, lead)], (name, out))
                self.assertLessEqual(err.count("\n"), 1, name)
        obj = load("broken")
        obj["hand"].append(None)
        out, _ = piped(obj)
        self.assertIn("warn  runs      baton 2026-11-13-2: reads running, and its process (pid 4242) is gone",
                      out.splitlines())
        for obj in ([], "x", None, {"hand": "x"}, {"sources": [None]}, {"watchers": [None]}):
            out, _ = piped(obj)
            self.assertIn("runs", out)


class NeverCutTest(unittest.TestCase):
    """Line 4: a command's row and a hand's row are never cut on a terminal."""

    def test_line4_command_rows_whole(self):
        long = " --and-a-flag-long-enough-to-pass-any-width-this-test-draws"
        obj = load("broken")
        obj["watchers"][0]["start"] += long
        obj["watchers"].append({"name": "drum" + long, "state": "unknown", "beat_line": None})
        obj["hand"].append({"part": "watchers", "kind": "watcher_unknown", "name": "drum", "remedy": None})
        obj["hand"][2]["remedy"] += long
        obj["hand"][3]["remedy"] += long
        one = obj["gate"]["queued"][0]
        obj["gate"]["queued"] = [dict(one, name="q%d" % i, label="") for i in range(9)]
        obj["sources"][1]["argv"] = ["gate", "status" + long, "--json"]
        for width in (40, 60, 80):
            got = [r[13:] for r in tty(obj, width)]
            for whole in ("start it: lampd watch --every 60" + long,
                          "drum%s: not checked: ps gave no listing" % long,
                          "see: agentik bench gate status" + long,
                          "and 6 more: agentik bench gate status" + long,
                          "see: agentik baton status" + long):
                self.assertIn(whole, got, (width, got))


class DoctorHintTest(unittest.TestCase):
    """Line 9: each state that gave nothing points at doctor."""

    def test_line9_unreadable_and_changed(self):
        for state in ("timed out", "unreadable", "changed"):
            obj = load("quiet")
            obj["sources"][2]["state"] = state
            self.assertEqual(piped(obj)[1], "next: agentik doctor\n", state)


if __name__ == "__main__":
    unittest.main()
