"""Packet su6-rows-part: `status` draws the rows in flight, each joined to the gate's newest result
for its worktree, and counts what waits on the owner from two reads.

Each run is su2-read's ReadHome with its stand-in `agentik-demo` removed and two stand-ins in its
place, the fallback table's tools that give the gate read and the rows read, each answering from
tests/fixtures/su6 and recording every call. The checkout is a made-up hq, `acme-hq`, named on the command line. Made-up names
only; nothing here writes outside its temp folders.
"""
import json
import os
import subprocess
import sys
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LIB  # noqa: E402
from test_su1_status_check import NOW  # noqa: E402
from test_su2_read import ReadHome, text  # noqa: E402
from agentik_suite import tools  # noqa: E402

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "su6")
WT = "/srv/acme/acme-lamp/.claude/worktrees/kb2-lamp"
GATE_ID = "20261112-101500-0042"
TABLE = json.loads((LIB / "fallback.json").read_text())


def giver(read):
    """The table's tool whose `status` list holds `read`."""
    return next(n for n, row in TABLE.items() if any(r["name"] == read for r in row.get("status") or ()))


GATE, ROWS = giver("gate"), giver("rows")


def fix(name):
    with open(os.path.join(FIX, name)) as fh:
        return json.load(fh)


class RowsHome(ReadHome):
    def setUp(self):
        ReadHome.setUp(self)
        os.unlink(os.path.join(self.stubs, "agentik-demo"))
        self.hq = os.path.join(self.side, "acme-hq")
        os.makedirs(os.path.join(self.hq, ".git"))
        self.write(os.path.join(self.hq, ".claude", "agentik", "config.yaml"), "suite:\n  kind: hq\n")
        self.sess, _ = self.tool(GATE)
        self.dec, _ = self.tool(ROWS)
        self.answer(self.sess, **{
            "gate status --json --repo " + WT: {"file": os.path.join(FIX, "gate-wt.json")},
            "gate status --json": "gate.json",
            "unattended status --json": "unattended-none.json",
            "charter show --json": {"file": os.path.join(FIX, "charter.json")}})
        self.answer(self.dec, **{
            "backlog --json": {"file": os.path.join(FIX, "backlog.json")},
            "rows --json": {"file": os.path.join(FIX, "rows.json")}})

    def rows_answer(self, obj=None, **more):
        a = dict(more)
        if obj is not None:
            a["file"] = self.saved("rows-answer.json", obj)
        self.answer(self.dec, **{"rows --json": a})

    def screen(self, code=0):
        p = subprocess.run([str(LIB.parent / "bin" / "agentik-suite"), "status", "--now", NOW, "--ps", self.ps,
                            self.hq], capture_output=True, text=True, env=self.env(TZ="UTC"), timeout=60,
                           cwd=self.repo)
        self.assertNotIn("Traceback", p.stdout + p.stderr)
        self.assertEqual(p.returncode, code, p.stdout + p.stderr)
        return p.stdout.splitlines()

    def part_lines(self, lines, label):
        """The lines of the part whose label is `label`: its first and each under it."""
        found, inside = [], False
        for line in lines:
            if line[6:].startswith(label + " "):
                inside = True
            elif line[:16].strip():
                inside = False
            if inside:
                found.append(line)
        return found

    def not_read(self, lines):
        return [l for l in lines if l[6:].startswith("not read")]


class RowsPartTest(RowsHome):
    def test_a_two_open_rows_two_lines_one_gate_result(self):
        lines = self.screen()
        part = self.part_lines(lines, "rows")
        self.assertEqual(len(part), 2, lines)
        self.assertIn("kb2-lamp", part[0])
        self.assertIn("S3", part[0])
        self.assertIn("building", part[0])
        self.assertIn("lampctl check", part[0])
        self.assertIn(GATE_ID, part[0])
        self.assertIn("passed", part[0])
        self.assertIn("kb3-fern", part[1])
        self.assertIn("briefed", part[1])
        self.assertIn("history/rows/kb3-fern/brief.md", part[1])
        self.assertNotIn("20261112-", part[1])
        calls = self.logged(GATE)
        self.assertEqual([c for c in calls if "--repo" in c], ["gate status --json --repo " + WT])
        self.assertIn("rows --json --root " + os.path.join(self.hq, "history", "rows"), self.logged(ROWS))

    def test_b_a_closed_row_is_not_drawn(self):
        obj = fix("rows.json")
        moss = dict(obj["rows"][1], row="kb1-moss", state="closed", worktree="/srv/acme/acme-moss/wt")
        done = dict(obj["rows"][1], row="kb0-pebble", state="done")
        obj["rows"] += [moss, done]
        self.rows_answer(obj)
        lines = self.screen()
        part = self.part_lines(lines, "rows")
        self.assertEqual(len(part), 2, lines)
        self.assertFalse([l for l in lines if "kb1-moss" in l or "kb0-pebble" in l])
        self.assertFalse([c for c in self.logged(GATE) if "acme-moss" in c])
        got = self.read(self.hq)["rows"]["rows"]
        self.assertEqual([(r["row"], r["closed"]) for r in got],
                         [("kb2-lamp", False), ("kb3-fern", False), ("kb1-moss", True), ("kb0-pebble", True)])


class OwnerTest(RowsHome):
    def test_c_three_hand_lines_and_two_waiting_rows(self):
        obj = self.read(self.hq)
        self.assertEqual((obj["owner"]["hands"], obj["owner"]["steps"], obj["owner"]["state"]), (3, 2, "ok"))
        part = self.part_lines(self.screen(), "owner")
        self.assertEqual(len(part), 1, part)
        self.assertIn("3 hand lines", part[0])
        self.assertIn("2 build order rows", part[0])
        self.answer(self.sess, **{"charter show --json": {"exit": 1, "err": "no charter\n"}})
        obj = self.read(self.hq)
        self.assertEqual((obj["owner"]["hands"], obj["owner"]["steps"], obj["owner"]["state"]),
                         (None, 2, "partial"))
        self.assertNotIn("owner", obj["not_read"])
        part = self.part_lines(self.screen(), "owner")
        self.assertIn("not counted", part[0])
        self.assertIn("2 build order rows", part[0])


class FailingTest(RowsHome):
    def test_d_the_rows_read_failing(self):
        self.rows_answer(exit=3, err="the rows are locked\n")
        obj = self.read(self.hq)
        self.assertEqual((self.source(obj, "rows")["state"], obj["rows"]["state"]), ("unreadable", "not read"))
        self.assertIn("rows", obj["not_read"])
        lines = self.screen()
        self.assertEqual(self.not_read(lines)[-1].split(None, 2)[-1], "the rows in flight")
        self.assertTrue(self.part_lines(lines, "backlog"))
        self.assertTrue([l for l in self.part_lines(lines, "rows") if "failed" in l])

    def test_e_json_holds_both_parts(self):
        obj = self.read(self.hq)
        self.assertEqual(obj["not_read"], [])
        rows = obj["rows"]
        self.assertEqual(rows["state"], "ok")
        self.assertEqual([(r["row"], r["level"], r["state"], r["worktree"]) for r in rows["rows"]],
                         [("kb2-lamp", "S3", "building", WT), ("kb3-fern", "S2", "briefed", None)])
        self.assertEqual(rows["rows"][0]["gate"], {"id": GATE_ID, "exit": 0, "seconds": 61.5})
        self.assertEqual((rows["rows"][0]["gate_read"], rows["rows"][1]["gate"], rows["rows"][1]["gate_read"]),
                         ("ok", None, None))
        self.assertEqual(rows["rows"][1]["next"], {"text": "history/rows/kb3-fern/brief.md", "command": None})
        self.assertEqual(obj["owner"], {"state": "ok", "hands": 3, "steps": 2})
        names = [s["name"] for s in obj["sources"] if s["state"] == "ok"]
        self.assertIn("rows", names)
        self.assertIn("charter", names)

    def test_f_the_rows_read_past_its_wall(self):
        self.read(self.hq)  # the describe cache
        pids = os.path.join(self.side, "pids")
        self.rows_answer(sleep=10, child=pids)
        real = tools.fallback

        def short(lib):
            table = real(lib)
            for read in table[ROWS]["status"]:
                if read["name"] == "rows":
                    read["wall_s"] = 0.5
            return table
        start = time.monotonic()
        with mock.patch.object(tools, "fallback", short):
            obj = self.compose(text(self.ps), paths=[self.hq])
        self.assertLess(time.monotonic() - start, 2.0)
        src = self.source(obj, "rows")
        self.assertEqual((src["state"], src["ms"], obj["rows"]["state"]), ("timed out", 500, "not read"))
        self.assertIn("rows", obj["not_read"])
        time.sleep(0.1)
        for pid in map(int, text(pids).split()):
            with self.assertRaises(OSError):
                os.kill(pid, 0)
        self.assertGreater([r for r in real(str(LIB))[ROWS]["status"] if r["name"] == "rows"][0]["wall_s"],
                           3.8)


class CapTest(RowsHome):
    def test_seven_open_rows_keep_their_first_lines(self):
        obj = fix("rows.json")
        obj["rows"] = [dict(obj["rows"][1], row="kb%d-pot" % i) for i in range(7)]
        self.rows_answer(obj)
        part = self.part_lines(self.screen(), "rows")
        self.assertEqual(len(part), 5, part)
        self.assertIn("and 3 more", part[-1])


if __name__ == "__main__":
    unittest.main()
