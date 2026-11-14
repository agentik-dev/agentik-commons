"""Packet sc10-doctor-checks: doctor shows each failing check by name, folds what is well, and
ends on one command.

Each run is the plugin's launcher in a temp HOME with a minimal env, a stub `claude` that records
its calls, and each tool a stub `agentik-<made-up name>` that counts its starts. The ready HOME
has steps 1 to 6 ok: the marketplace known, the default set installed (folders with no
command), the suite's launcher and the door in ~/.local/bin, that folder on PATH.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import ESC, LAUNCHER, LIB, PLUGIN, ROOT, SYSTEM  # noqa: E402
from test_ak3d_doctor import DoctorHome  # noqa: E402
from agentik_suite import catalogue, cli, doctor, plan  # noqa: E402
import agentik_install  # noqa: E402

MARK = re.compile(r"^(ok|warn|FAIL|note)  +(\S+)  +(.*)$")
ROW = re.compile(r"^    (ok|warn|FAIL|note)  +(\S+)  +(.*)$")
TAIL = "the tail line of the text form"


class Checks(DoctorHome):
    def answer_of(self, name, checks, ok=True):
        return json.dumps({"schema": "agentik.doctor/1", "ok": ok, "tool": name,
                           "failed": sum(c["status"] == "fail" for c in checks),
                           "warned": sum(c["status"] == "warn" for c in checks), "checks": checks})

    def tool(self, name, answer=None, code=0, text="", plain=0, sleep=None):
        """A stub tool: `doctor --json` prints `answer` (None: the flag refused, exit 2) and exits
        `code`; plain `doctor` prints `text` and exits `plain`. Each start appends its words to
        counts/<name>."""
        counts = os.path.join(self.home, "counts")
        os.makedirs(counts, exist_ok=True)
        body = '#!/bin/sh\necho "$*" >> "%s"\n' % os.path.join(counts, name)
        if sleep:
            body += "sleep %s\n" % sleep
        body += 'if [ "$1" = doctor ] && [ "$2" = --json ]; then\n'
        if answer is None:
            body += 'echo "unknown flag: --json" >&2\nexit 2\n'
        else:
            body += "cat <<'EOF'\n%s\nEOF\nexit %d\n" % (answer, code)
        body += 'fi\n[ "$1" = doctor ] || exit 9\n'
        if text:
            body += "cat <<'EOF'\n%s\nEOF\n" % text
        body += "exit %d\n" % plain
        return self.stub("agentik-" + name, body)

    def starts(self, name):
        try:
            with open(os.path.join(self.home, "counts", name)) as fh:
                return fh.read().splitlines()
        except FileNotFoundError:
            return []

    def ok_checks(self, n=3):
        return [{"name": "c%d" % i, "status": "ok", "detail": "check %d holds" % i, "remedy": None}
                for i in range(n)]

    def ready(self):
        """Steps 1 to 6 ok; returns the env's PATH."""
        bindir = self.bindir
        names = plan.default_set(str(LIB))
        self.plugin_files(os.path.join(self.home, ".claude"), {n: "1.0.0" for n in names}, whole=False)
        for n in names:
            os.makedirs(os.path.join(self.home, "inst", n, "1.0.0"), exist_ok=True)
        version = agentik_install.version(str(LIB))
        self.place(bindir, "agentik-suite", "#!/bin/sh\nVERSION=%s\n" % version)
        os.makedirs(bindir, exist_ok=True)
        shutil.copy(str(PLUGIN / "bin" / "agentik"), os.path.join(bindir, "agentik"))
        return "%s:%s:%s" % (bindir, self.stubs, SYSTEM)

    def screen(self, *args, **more):
        code, out, err = self.doctor(*args, read=False, **more)
        self.assertNotIn(ESC, out + err)
        return code, out, err

    def json_of(self, *args, **more):
        code, out, err = self.doctor("--json", *args, read=False, **more)
        return code, out, json.loads(out)

    def rows(self, out):
        return [ROW.match(l).groups() for l in out.splitlines() if ROW.match(l)]


class ReadyTest(Checks):
    def test_a1_all_well_is_one_line_a_group(self):
        path = self.ready()
        for n in ("murmur", "paint", "quill"):
            self.tool(n, self.answer_of(n, self.ok_checks()))
        code, out, err = self.screen(PATH=path)
        self.assertEqual((code, err), (0, ""), out)
        lines = out.splitlines()
        self.assertEqual(lines[-1], "This machine is set up.")
        _, _, obj = self.json_of(PATH=path)
        self.assertEqual(len(lines) - 1, len(obj["tools"]), out)
        for line in lines[:-1]:
            m = MARK.match(line)
            self.assertTrue(m, line)
            self.assertIn(m.group(1), ("ok", "note"), line)
        for n in ("murmur", "paint", "quill"):
            self.assertIn(("ok", n, "3 checks"), [MARK.match(l).groups() for l in lines[:-1]])
        self.assertNotIn("run:", out)

    def stub_root(self, code, fail=True):
        detail = "the root %s/work/site has 34 changed paths" % self.home
        checks = self.ok_checks(2) + [{"name": "root", "status": "fail" if fail else "warn",
                                       "detail": detail, "remedy": None}]
        self.tool("murmur", self.answer_of("murmur", checks), code=code,
                  text="murmur doctor\nline two\n" + TAIL, plain=code)
        return detail

    def test_a3_a_fail_check_under_exit_0(self):
        path = self.ready()
        detail = self.stub_root(0)
        code, out, err = self.screen(PATH=path)
        self.assertEqual(code, 1, out + err)
        self.assertIn(("FAIL", "root", detail.replace(self.home, "~")), self.rows(out))
        self.assertNotIn(TAIL, out + err)
        self.assertEqual(err.splitlines()[-1], "note  next: agentik murmur doctor")
        code, raw, obj = self.json_of(PATH=path)
        self.assertEqual(code, 1)
        root = [c for g in obj["tools"] if g["name"] == "murmur" for c in g["checks"]]
        self.assertEqual([c["detail"] for c in root if c["name"] == "root"], [detail])
        self.assertEqual(self.starts("murmur"), ["doctor --json"] * 2)

    def test_a4_exit_2_with_no_fail_check(self):
        path = self.ready()
        self.stub_root(2, fail=False)
        code, out, err = self.screen(PATH=path)
        self.assertEqual(code, 0, out + err)
        self.assertNotIn(TAIL, out + err)
        self.assertNotIn("FAIL", out)

    def test_a5_two_warns_of_one_name(self):
        path = self.ready()
        warns = [{"name": "backend", "status": "warn", "detail": "backend %s is not answering" % w,
                  "remedy": None} for w in ("one", "two")]
        self.tool("murmur", self.answer_of("murmur", self.ok_checks(2) + warns), code=1)
        code, out, err = self.screen(PATH=path)
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual([r for r in self.rows(out) if r[1] == "backend"],
                         [("warn", "backend", "backend one is not answering"),
                          ("warn", "backend", "backend two is not answering")])
        group = [MARK.match(l).groups() for l in out.splitlines() if MARK.match(l)]
        self.assertIn(("warn", "murmur", "2 to look at, 2 ok"), group)

    def test_a6_the_second_round(self):
        path = self.ready()
        self.stub_root(0)
        self.tool("paint", json.dumps({"ok": True, "checks": []}), text="all fine")
        self.tool("quill", None, text="all fine")
        self.tool("rune", None, text="rune: one failed\nmore", plain=1)
        self.tool("sable", None, plain=1)
        code, raw, obj = self.json_of(PATH=path)
        got = {g["name"]: [(c["name"], c["status"], c["detail"]) for c in g["checks"]] for g in obj["tools"]}
        self.assertEqual(got["paint"], [("doctor", "ok", "its doctor passed")])
        self.assertEqual(got["quill"], [("doctor", "ok", "its doctor passed")])
        self.assertEqual(got["rune"], [("doctor", "fail", "its doctor failed")])
        self.assertEqual(got["sable"], [("doctor", "fail", "its doctor failed, and printed nothing")])
        for n in ("paint", "quill", "rune", "sable"):
            self.assertEqual(self.starts(n), ["doctor --json", "doctor"], n)
        self.assertEqual(self.starts("murmur"), ["doctor --json"])
        code, out, err = self.screen(PATH=path)
        self.assertNotIn("rune: one failed", out + err)
        group = {MARK.match(l).group(2): MARK.match(l).groups() for l in out.splitlines() if MARK.match(l)}
        self.assertEqual(group["sable"], ("FAIL", "sable", "its doctor failed, and printed nothing"))
        self.assertEqual(group["paint"], ("ok", "paint", "its doctor passed"))

    def test_a1_ok_false_is_one_fail_check(self):
        path = self.ready()
        self.tool("murmur", json.dumps({"schema": "agentik.doctor/1", "ok": False, "tool": "murmur",
                                        "error": {"code": "bad_file", "message": "a tab in the indent",
                                                  "remedy": "agentik murmur config"}}), code=2)
        code, raw, obj = self.json_of(PATH=path)
        got = [g["checks"] for g in obj["tools"] if g["name"] == "murmur"][0]
        self.assertEqual(got, [{"name": "doctor", "status": "fail", "detail": "a tab in the indent",
                                "remedy": "agentik murmur config"}])
        self.assertEqual(code, 1)

    def test_a7_fix_and_slash_lines(self):
        path = self.ready()
        checks = self.ok_checks(1) + [
            {"name": "launcher", "status": "fail", "detail": "the launcher is behind",
             "remedy": "/murmur:install-cli"},
            {"name": "cli", "status": "warn", "detail": "the command is behind",
             "remedy": "agentik murmur install-cli"}]
        self.tool("murmur", self.answer_of("murmur", checks), code=1)
        code, out, err = self.screen(PATH=path)
        lines = out.splitlines()
        at = [i for i, l in enumerate(lines) if ROW.match(l) and ROW.match(l).group(2) == "cli"][0]
        self.assertEqual(lines[at + 1].strip(), "fix: agentik murmur install-cli")
        self.assertEqual(lines[at + 1].index("fix:"), lines[at].index("the command"))
        at = [i for i, l in enumerate(lines) if ROW.match(l) and ROW.match(l).group(2) == "launcher"][0]
        self.assertEqual(lines[at + 1].strip(), "in Claude Code: /murmur:install-cli")
        self.assertNotIn("/murmur", err)
        self.assertEqual(err.splitlines()[-1], "note  next: agentik murmur doctor")
        self.assertNotIn("run:", out + err)
        code, out, err = self.screen()  # an empty HOME
        self.assertNotIn("run:", out + err)

    def test_a8_all_shows_every_check(self):
        path = self.ready()
        for n in ("paint", "quill"):
            self.tool(n, self.answer_of(n, self.ok_checks()))
        self.stub_root(0)
        for env in ({"PATH": path}, {}):
            code, raw, obj = self.json_of(**env)
            code2, raw2, obj2 = self.json_of("--all", **env)
            self.assertEqual(raw, raw2)
            every = [c for g in obj["tools"] for c in g["checks"]]
            self.assertEqual((obj["failed"], obj["warned"]),
                             (sum(c["status"] == "fail" for c in every),
                              sum(c["status"] == "warn" for c in every)))
            code, out, err = self.screen("--all", **env)
            rows = self.rows(out)
            self.assertEqual(len(rows), len(every), out)
            self.assertEqual([r[1] for r in rows], [c["name"].split(" ")[0] for c in every])
            self.assertEqual(sum(1 for l in out.splitlines() if MARK.match(l)), len(obj["tools"]))


class EmptyTest(Checks):
    def test_a2_an_empty_home(self):
        code, out, err = self.screen()
        self.assertEqual(code, 0, out + err)
        lines = out.splitlines() + err.splitlines()
        self.assertLessEqual(len(lines), 8, "\n".join(lines))
        self.assertEqual(len(set(lines)), len(lines), "\n".join(lines))
        last = lines[-1]
        self.assertTrue(last.startswith("note  next: "), last)
        command = last[len("note  next: "):]
        self.assertEqual(command, "%s setup" % LAUNCHER)
        p = subprocess.run(["sh", "-c", command], stdin=subprocess.DEVNULL, capture_output=True,
                           env=self.env(), cwd=str(ROOT), timeout=60)
        self.assertNotEqual(p.returncode, 127)


class VoiceTest(unittest.TestCase):
    def test_a9_the_doctor_section(self):
        with open(os.path.join(str(LIB), "agentik_suite", "messages.md"), encoding="utf-8") as fh:
            text = fh.read()
        section = text.split("\n## Doctor\n", 1)[1].split("\n## ", 1)[0]
        items = [catalogue.ITEM.match(l) for l in section.splitlines() if l.startswith("- ")]
        self.assertTrue(items)
        for m in items:
            words = catalogue.LONE.sub(r"\1", m.group(2))
            for bad in ("exit", "would", "run:", "{code}"):
                self.assertNotIn(bad, words, m.group(1))
            self.assertLessEqual(len(catalogue.SLOT.sub("", words)), 76, m.group(1))
        ids = [m.group(1) for m in items]
        for gone in ("doctor.title", "doctor.group", "doctor.run", "doctor.tool.ok", "hint.doctor.done",
                     "hint.doctor.setup", "hint.doctor.fail", "hint.doctor.warn"):
            self.assertNotIn(gone, ids)


class BoundTest(Checks):
    def test_a10_two_rounds_inside_one_deadline(self):
        self.tool("slow", None, sleep=10)
        self.tool("late", None)  # round 1 refused, so round 2: then it sleeps
        late = os.path.join(self.stubs, "agentik-late")
        with open(late) as fh:
            body = fh.read()
        with open(late, "w") as fh:
            fh.write(body.replace('[ "$1" = doctor ] || exit 9\n', '[ "$1" = doctor ] || exit 9\nsleep 10\n'))
        self.tool("murmur", self.answer_of("murmur", self.ok_checks()))
        saved = doctor.DEADLINE
        doctor.DEADLINE = 1.0
        self.addCleanup(setattr, doctor, "DEADLINE", saved)
        out, err = io.StringIO(), io.StringIO()
        start = time.monotonic()
        code = cli.Command(["doctor", "--json"], self.env(), out, err).run()
        self.assertLess(time.monotonic() - start, 3)
        obj = json.loads(out.getvalue())
        got = {g["name"]: [(c["status"], c["detail"]) for c in g["checks"]] for g in obj["tools"]}
        slow = doctor.DEADLINE
        self.assertEqual(got["slow"], [("warn", "its doctor ran past %g s, so it was stopped" % slow)])
        self.assertEqual(got["late"], [("warn", "its doctor ran past %g s, so it was stopped" % slow)])
        self.assertEqual(self.starts("late"), ["doctor --json", "doctor"])
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.calls))
        for n in ("slow", "late", "murmur"):
            self.assertFalse(any("describe" in s for s in self.starts(n)), n)


if __name__ == "__main__":
    unittest.main()
