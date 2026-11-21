"""Row ak10c5-table-gone: the suite asks each tool for what its old table held, and the table goes.

A made-up home of test_ak4a_update's, its stand-in tools on the home's own PATH; su6's made-up hq for
the slow rows read. Nothing here reads the live home or starts the real `claude`.
"""
import json
import os
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_su2_read as su2  # noqa: E402
import test_su6_rows_part as su6  # noqa: E402
from test_agentik_suite import LIB  # noqa: E402
from test_ak4a_update import Base, runner_stubs  # noqa: E402
from test_su2_read import text  # noqa: E402
from agentik_suite import plan  # noqa: E402

SILENT = "#!/bin/sh\nexit 2\n"


class SlowRowsTest(su6.RowsHome):
    def test_a2_a_slow_rows_read_is_drawn(self):
        """A `rows` read of 3.8 s whose describe says `wall_s` 6: drawn, not cut (R2)."""
        self.read(self.hq)  # the describe cache
        self.rows_answer(file=os.path.join(su6.FIX, "rows.json"), sleep=3.8)
        start = time.monotonic()
        obj = self.compose(text(self.ps), paths=[self.hq])
        self.assertGreater(time.monotonic() - start, 3.5)
        self.assertEqual(self.source(obj, "rows")["state"], "ok")


class UndrawnTest(su2.ReadHome):
    def test_fork1_a_named_tools_undrawn_read_is_on_no_screen_line(self):
        """The text screen lists a `not drawn` read only for a tool public.json does not name;
        a named tool's is in `--json`'s `sources` with its state, on no line (build 2 fork 1)."""
        for name in ("session", "murmur"):
            answers, _ = self.tool(name)
            reads = (su2.PIN_READS[name] if name == "session" else []) + [
                {"name": "meter", "argv": ["meter", "--json"]}]
            self.described(name, answers, reads)
        obj = self.read()
        undrawn = {(s["tool"], s["name"]) for s in obj["sources"] if s["state"] == "not drawn"}
        self.assertLessEqual({("murmur", "meter"), ("session", "meter"), ("session", "gate")}, undrawn)
        p = subprocess.run([str(LIB.parent / "bin" / "agentik-suite"), "status", "--now", su2.NOW,
                            "--ps", self.ps], capture_output=True, text=True, env=self.env(TZ="UTC"),
                           timeout=60, cwd=self.repo)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("not drawn: agentik-murmur meter", p.stdout)
        self.assertIn("not drawn: agentik-demo weather", p.stdout)
        self.assertNotIn("not drawn: agentik-session", p.stdout)


class HoldTest(Base):
    def test_a3_a_tool_that_does_not_answer_holds_nothing(self):
        """A runner whose file gives no describe: one warn line, no hold (R5)."""
        h = self.two_behind()
        h.file(os.path.join(h.bin, "agentik-relay"), SILENT)
        h.ps("4242 /opt/tools/relay run --row r1\n")
        code, out, err = h.run("update", "--dry-run")
        self.assertEqual(code, 0, out + err)
        said = [l for l in err.splitlines() if "gave no `describe` answer" in l]
        self.assertEqual(len(said), 1, err)
        self.assertTrue(said[0].startswith("warn: ") and "relay" in said[0], said)
        self.assertNotIn("held install", out + err)

    def test_fork2_a_tool_public_json_does_not_list_is_not_named(self):
        """`update.unasked` names only a tool public.json lists; a stand-in it does not list,
        whose file runs and gives no answer, is named nowhere and holds nothing (build 2 fork 2)."""
        h = self.two_behind()
        h.file(os.path.join(h.bin, "agentik-murmur"), SILENT)
        code, out, err = h.run("update", "--dry-run")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("gave no `describe` answer", err)
        self.assertNotIn("held install", out + err)
        h.file(os.path.join(h.bin, "agentik-relay"), SILENT)
        h.file(os.path.join(h.bin, "agentik-respeak"), SILENT)
        code, out, err = h.run("update", "--dry-run")
        said = [l for l in err.splitlines() if "gave no `describe` answer" in l]
        self.assertEqual(len(said), 1, err)
        self.assertIn("relay, respeak", said[0])
        self.assertNotIn("murmur", said[0])

    def test_a3_both_holds_through_describe(self):
        h = self.two_behind()
        runner_stubs(h, "echo '{\"id\": \"u1\"}'")
        code, out, err = h.run("update", "--dry-run")
        self.assertEqual(code, 2, out + err)
        self.assertIn("held install: an unattended run is live", err)
        h.ps("4242 /opt/tools/relay run --row r1\n")
        code, out, err = h.run("update", "--dry-run")
        self.assertEqual(code, 2, out + err)
        self.assertIn("held install: a relay run is live (pid 4242)", err)
        self.assertNotIn("gave no `describe` answer", err)


class SilentToolTest(Base):
    def test_a5_doctor_warns_and_status_and_inbox_hold(self):
        """A tool too old to answer: doctor's one `describe` warn row; status and inbox no part (R7)."""
        h = self.two_behind()
        h.file(os.path.join(h.bin, "agentik-relay"), SILENT)
        code, out, err = h.run("doctor", "--json")
        self.assertNotIn("Traceback", err)
        group = [g for g in json.loads(out)["tools"] if g["name"] == "relay"][0]
        rows = [c for c in group["checks"] if c["name"] == "describe"]
        self.assertEqual([(c["status"], c["remedy"].split()[-2:]) for c in rows], [("warn", ["update", "relay"])])
        code, out, err = h.run("status", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual([s for s in json.loads(out)["sources"] if s["tool"] == "relay"], [])
        repo = os.path.join(os.path.dirname(h.bin), "acme-lamp")
        os.makedirs(os.path.join(repo, ".git"))
        code, out, err = h.run("inbox", repo)  # the silent relay gives no read: the pin's refusal
        self.assertEqual(code, 3, err)
        self.assertIn("no command on PATH gives a read the inbox needs", err)
        self.assertNotIn("Traceback", err)
        self.assertNotIn("relay", out + err)


class PublicTest(unittest.TestCase):
    def test_a6_setup_reads_needs_and_the_page_from_public_json(self):
        """Not installed: the relay's Go and its page, respeak's PyYAML, from public.json (R4)."""
        home = os.path.realpath(os.path.join(os.environ.get("TMPDIR", "/tmp"), "ak10c5-none"))
        env = {"HOME": home, "PATH": "/nowhere"}
        steps = plan.build(["relay", "respeak"], env, str(LIB), "agentik-suite", "0.0.1")
        self.assertEqual(sorted((s["subject"], s["values"]["name"]) for s in steps if s["id"] == "need"),
                         [("Go", "relay"), ("PyYAML", "respeak")])
        pages = [s["page"] for s in steps if s.get("page")]
        self.assertEqual(pages, ["https://github.com/agentik-dev/agentik-relay#install"])

    def test_a6_a_described_need_row(self):
        answer = {"needs": [{"name": "go", "kind": "toolchain", "optional": False},
                            {"name": "PyYAML", "kind": "package", "optional": True},
                            {"name": "git", "kind": "program", "optional": False}]}
        self.assertEqual(plan.needs_of(answer, ["PyYAML"]), ["Go"])
        self.assertEqual(plan.needs_of(None, ["PyYAML"]), ["PyYAML"])


if __name__ == "__main__":
    unittest.main()
