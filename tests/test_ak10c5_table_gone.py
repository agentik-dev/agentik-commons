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
from test_ak4_remove import Remove  # noqa: E402
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

    def test_f1_a_second_tool_that_names_run_hides_no_live_run(self):
        """Every tool whose describe names `run`, then every one that names `unattended`, in name
        order: a tool that sorts first and says none live hides no live run (review 1 F1)."""
        h = self.two_behind()
        runner_stubs(h)
        h.ps("4242 /opt/tools/relay run --row r1\n")
        stand_in(h, "agents", [["run", ["status", "--json"]]])
        code, out, err = h.run("update", "--dry-run")
        self.assertEqual(code, 2, out + err)
        self.assertIn("held install: a relay run is live (pid 4242)", err)

    def test_f1_a_second_tool_that_names_unattended_hides_no_live_run(self):
        h = self.two_behind()
        runner_stubs(h, "echo '{\"id\": \"u1\"}'")
        stand_in(h, "decisions", [["unattended", ["unattended", "--json"]]], "echo null")
        code, out, err = h.run("update", "--dry-run")
        self.assertEqual(code, 2, out + err)
        self.assertIn("held install: an unattended run is live", err)


def stand_in(h, name, reads, body="exit 2"):
    """A stand-in `agentik-<name>` whose describe names the status `reads` ([name, argv])."""
    answer = {"schema": "agentik.describe/1", "ok": True, "tool": name, "version": "1.0.0",
              "summary": "A stand-in.", "repo": "example-org/" + name, "plugin": None, "needs": [],
              "verbs": [], "reads": [{"kind": "status", "name": n, "argv": a} for n, a in reads]}
    h.file(os.path.join(h.bin, "agentik-" + name),
           "#!/bin/sh\nif [ \"$1 $2\" = 'describe --json' ]; then echo '%s'; exit 0; fi\n%s\n"
           % (json.dumps(answer), body))


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


    def test_l1_a_describe_that_timed_out_is_no_answer_in_that_time(self):
        """A describe past the wall: the doctor's row says it gave no answer in that time and names
        no update; R7's row is for a tool that answered no describe (review 1 L1)."""
        h = self.two_behind()
        runner_stubs(h)
        p = os.path.join(h.bin, "agentik-relay")
        with open(p) as fh:
            body = fh.read()
        h.file(p, body.replace("then echo", "then sleep 4; echo"))
        code, out, err = h.run("doctor", "--json")
        self.assertNotIn("Traceback", err)
        group = [g for g in json.loads(out)["tools"] if g["name"] == "relay"][0]
        rows = [c for c in group["checks"] if c["name"] == "describe"]
        self.assertEqual([(c["status"], c["remedy"]) for c in rows], [("warn", None)], rows)
        self.assertIn("gave no answer in 2 s", rows[0]["detail"])
        self.assertNotIn("update", rows[0]["detail"])


# tool x's runner, answering describe and its config read as a tool that says what it has
X_RUNNER = """import json, os, sys
a = sys.argv[1:]
if a == ["describe", "--json"]:
    print(json.dumps({"schema": "agentik.describe/1", "ok": True, "tool": "x", "version": "1.0.0",
                      "summary": "A stand-in.", "repo": "example-org/x", "plugin": "x@agentik",
                      "needs": [], "verbs": [],
                      "reads": [{"kind": "config", "name": "config", "argv": ["config", "--json"]}]}))
elif a == ["config", "--json"]:
    print(json.dumps({"schema": "agentik.config/1", "ok": True, "settings": [], "layers": [
        {"name": "user", "path": os.path.join(os.environ["HOME"], ".x-user", "settings.yaml")}]}))
else:
    sys.exit(2)
"""


class RemoveKeepTest(Base):
    home, x = Remove.home, Remove.x  # ak4's remove homes, without running its tests here

    def test_a4_the_keep_line_from_describe_config_and_the_guard_without_it(self):
        """remove's keep line names the user file of x's `describe config` (R6); with no answer the
        guard on the two config folders still keeps them, as at the pin."""
        h, _ = self.x()
        h.file(os.path.join(h.tree(), "agentik-x"), X_RUNNER)  # the runner the placed launcher starts
        mine = h.file(os.path.join(h.home, ".x-user", "settings.yaml"), "mine\n")
        code, out, err = h.go("remove", "x", "--dry-run", "--json")
        self.assertEqual(code, 0, out + err)
        keep = [(s["subject"], s["detail"]) for s in json.loads(out)["steps"] if s["id"] == "keep"]
        self.assertIn(("~/.x-user/settings.yaml", "kept: your config"), keep)
        code, out, err = h.go("remove", "x", "--dry-run")
        line = [l for l in out.splitlines() if "~/.x-user/settings.yaml" in l]
        self.assertEqual(len(line), 1, out)
        self.assertIn("kept: your config", line[0])
        code, out, err = h.go("remove", "x", "--yes")
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.isfile(mine))
        h2, _ = self.x(name="h2")  # x's own runner gives no answer: no user file; the guard stands
        cfg = os.path.join(h2.home, ".config")
        code, out, err = h2.go("remove", "--all", "--yes", XDG_CACHE_HOME=cfg, XDG_CONFIG_HOME=cfg)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.isfile(os.path.join(cfg, "agentik", "x", "config.yaml")))
        self.assertNotIn("~/.config/agentik  removed", out)
        self.assertNotIn(".x-user", out)

    def test_f3_with_no_answer_the_guard_holds_wherever_the_homes_point(self):
        """No tool answers; the config home elsewhere and the cache home the default config folder:
        the agentik cache folder is kept, since it reaches the relay's file, as at the pin (F3)."""
        h = self.home()
        for path in (".config/agentik/relay/config.yaml", ".config/agentik/agents/backends.json"):
            h.file(os.path.join(h.home, path), "mine\n")
        env = {"XDG_CONFIG_HOME": os.path.join(h.home, "cfg"), "XDG_CACHE_HOME": os.path.join(h.home, ".config")}
        code, out, err = h.go("remove", "--all", "--dry-run", **env)
        self.assertEqual(code, 0, out + err)
        line = [l for l in out.splitlines() if "~/.config/agentik " in l]
        self.assertEqual(len(line), 1, out)
        self.assertEqual(line[0].split(), "6 ok ~/.config/agentik kept: it reaches ~/.config/agentik/relay/config.yaml,"
                         " which remove keeps, so nothing there is deleted".split())
        code, out, err = h.go("remove", "--all", "--dry-run", "--json", **env)
        cache = [s for s in json.loads(out)["steps"] if s["id"] == "cache"]
        self.assertEqual([s["state"] for s in cache], ["ok"], out)


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
