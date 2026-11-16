"""Packet ak9b-plug-reader: a plugin's word runs, a failed settings read says why, the doctor
names each failing check.

`murmur` is a made-up tool. Lines 1 to 4 and 11 run the launcher of a temp copy of the suite's
plugin whose table holds a row for it, in fk_homes' homes (hD: a fork alone, its command under
its root, off PATH; hB: two sources, a command under each root; hK: no entry, a command on PATH);
the terminal's PATH is `~/.local/bin:/usr/bin:/bin`. Lines 5 to 9 run in row sc10's ready home,
where the suite's own group is well, so the close is the tool's. Line 12 runs `update` in row
ak4a's home. Every tool is a stub that appends its words to `$HOME/ran.log`; no test starts the
real `claude`, reads the real home or writes outside its temp folder."""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fk_homes import build  # noqa: E402
from test_agentik_suite import ESC, LIB, PLUGIN  # noqa: E402
from test_sc10_doctor_checks import MARK, ROW as CHECK_ROW, Checks  # noqa: E402
from agentik_suite import cli, doctor, tools  # noqa: E402

T = "murmur"
SUITE = "agentik-suite"
TABLE_ROW = {"lines": ["agentik murmur doctor"], "user_file": None, "needs": [], "status": []}
PAGE = "https://example.com/murmur#install"
LOG = 'echo "$*" >> "$HOME/ran.log"\n'
MESSAGE = "line 3 of /opt/acme/murmur.yaml does not parse"
REMEDY = "murmur-mend /opt/acme/murmur.yaml"
PLAIN = "next: the FAIL rows above say what failed: mend each, then "
# review 2's F2: a direction mark, a zero-width character, a soft hyphen and a lone surrogate
MARKS = ("\u200e", "\u200f", "\u061c", "\u200b", "\ufeff", "\u00ad", "\ud800")


def described(tool=T, reads=("config", "doctor")):
    argv = {"config": ["config", "--json"], "doctor": ["checks", "--json"]}
    return {"schema": "agentik.describe/1", "ok": True, "tool": tool, "version": "0.1.0",
            "summary": "A made-up tool.", "repo": "acme/murmur", "plugin": "murmur@acme-tools",
            "needs": [], "verbs": [], "reads": [{"kind": k, "name": k, "argv": argv[k]} for k in reads]}


def stub(describe=None, config=None, config_exit=1, checks=None, checks_exit=0, text="murmur doctor",
         sleep=None, doctor_json=None):
    """A command's body: each case prints its answer (a dict, or raw text) and exits; `doctor
    --json` prints `doctor_json` where it is given, else refuses the flag."""
    def emit(answer):
        body = answer if isinstance(answer, str) else json.dumps(answer)
        return "cat <<'EOF'\n%s\nEOF\n" % body

    lines = ["#!/bin/sh", LOG.rstrip("\n"), 'case "$1" in']
    if describe is not None:
        lines.append("describe) %sexit 0;;" % emit(describe))
    if config is not None:
        lines.append("config) %sexit %d;;" % (emit(config), config_exit))
    if checks is not None:
        lines.append("checks) %s%sexit %d;;" % ("sleep %s\n" % sleep if sleep else "",
                                                 checks if isinstance(checks, str) else emit(checks),
                                                 checks_exit))
    if doctor_json is not None:
        lines.append('doctor) if [ "$2" = --json ]; then\n%sexit 0\nfi\necho "%s"; exit 0;;'
                     % (emit(doctor_json), text))
    else:
        lines.append('doctor) [ "$2" = --json ] && exit 2; echo "%s"; exit 0;;' % text)
    lines.append("esac\nexit 0\n")
    return "\n".join(lines)


def config_error(message=MESSAGE, remedy=REMEDY):
    return {"schema": "agentik.config/1", "ok": False, "tool": T,
            "error": {"code": "bad_file", "message": message, "remedy": remedy}}


def doctor_answer(checks, ok=True, schema="agentik.doctor/1"):
    return {"schema": schema, "ok": ok, "failed": sum(c["status"] == "fail" for c in checks),
            "warned": sum(c["status"] == "warn" for c in checks), "checks": checks}


def check(name, status, detail=None, remedy=None):
    return {"name": name, "status": status, "detail": detail or "%s reads %s" % (name, status),
            "remedy": remedy}


# test 9: sc10's path, a fail and a warn with no remedy, a detail past the 300-character cut
NO_READ = [check("c0", "ok"), check("w1", "warn"), check("f1", "fail", " ".join(["word"] * 80)),
           check("n1", "note"), check("c1", "ok")]
# the pin's bytes, from b99f677's suite (`git archive b99f677 plugins/suite tests`) in this home
PIN_9 = (1,
         'FAIL  murmur     1 failed, 1 to look at, 3 ok\n'
         '    warn  w1  w1 reads warn\n'
         '    FAIL  f1  word word word word word word word word word word word word word word word '
         'word word word word word word word word word word word word word word word word word word '
         'word word word word word word word word word word word word word word word word word word '
         'word word word word word word word word word word word word word word word word word word '
         'word word word word word word word word word word word\n'
         'next: agentik murmur doctor\n',
         '[{"detail": "c0 reads ok", "name": "c0", "remedy": null, "status": "ok"}, {"detail": "w1 '
         'reads warn", "name": "w1", "remedy": null, "status": "warn"}, {"detail": "word word word '
         'word word word word word word word word word word word word word word word word word word '
         'word word word word word word word word word word word word word word word word word word '
         'word word word word word word word word word word word word word word word word word word '
         'word word word word word word word word word word word word word word word word word word '
         'word word word word word", "name": "f1", "remedy": null, "status": "fail"}, {"detail": '
         '"n1 reads note", "name": "n1", "remedy": null, "status": "note"}, {"detail": "c1 reads '
         'ok", "name": "c1", "remedy": null, "status": "ok"}]')


class Copy(unittest.TestCase):
    """The suite's plugin copied to a temp folder, its table holding a row for murmur."""
    page = None

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = os.path.realpath(tmp.name)
        self.root = os.path.join(self.tmp, "suite")
        shutil.copytree(str(PLUGIN), self.root, ignore=shutil.ignore_patterns("__pycache__"))
        self.launcher = os.path.join(self.root, "bin", SUITE)
        path = os.path.join(self.root, "lib", "fallback.json")
        with open(path) as fh:
            table = json.load(fh)
        table[T] = dict(TABLE_ROW, page=self.page) if self.page else dict(TABLE_ROW)
        with open(path, "w") as fh:
            json.dump(table, fh)

    def home(self, name):
        self.count = getattr(self, "count", 0) + 1
        path = os.path.join(self.tmp, "%s%d" % (name, self.count))
        os.mkdir(path)
        return build(name, path)

    def cli(self, h, *args, path=None, stdin=None, **more):
        search = path or os.pathsep.join([os.path.join(h.home, ".local", "bin"), "/usr/bin", "/bin"])
        env = dict({"HOME": h.home, "PATH": search, "XDG_CACHE_HOME": os.path.join(h.home, "cache")}, **more)
        p = subprocess.run([self.launcher] + list(args), capture_output=True, text=True, env=env,
                           cwd=h.home, timeout=120, input=stdin if stdin is not None else "")
        return p.returncode, p.stdout, p.stderr


class WordTest(Copy):
    def test_1_a_plugins_word_runs_its_file(self):
        h = self.home("hD")
        h.commands("#!/bin/sh\n" + LOG + "exit 7\n")
        code, out, err = self.cli(h, T, "--flag", "x", "--json")
        self.assertEqual((code, out, err), (7, "", ""))
        self.assertEqual(h.ran(), ["--flag x --json"])

    def test_1_the_same_streams_and_environment(self):
        h = self.home("hD")
        h.commands('#!/bin/sh\nread line\necho "in $line $ACME_TOOL_WORD"\necho "to err" >&2\nexit 4\n')
        code, out, err = self.cli(h, T, "go", stdin="hello\n", ACME_TOOL_WORD="kept")
        self.assertEqual((code, out, err), (4, "in hello kept\n", "to err\n"))

    def test_2_two_sources_and_a_flag_first_keep_the_refusal(self):
        h = self.home("hB")
        h.commands("#!/bin/sh\n" + LOG + "exit 7\n")
        code, out, err = self.cli(h, T, "--flag", "x", "--json")
        self.assertEqual(code, 3, out + err)
        self.assertEqual(h.ran(), [])
        self.assertIn("is a plugin with no command", out + err)
        d = self.home("hD")
        d.commands("#!/bin/sh\n" + LOG + "exit 7\n")
        code, out, err = self.cli(d, "--no-color", T, "go")
        self.assertEqual(code, 3, out + err)
        self.assertEqual(d.ran(), [])


class LeadTest(Copy):
    page = PAGE

    def test_11_a_tool_with_a_page_runs_the_file_the_finder_names(self):
        h = self.home("hL")
        h.file(os.path.join(h.root(h.own, "0.9.0"), "bin", "agentik-" + T), "#!/bin/sh\n" + LOG + "exit 5\n")
        code, out, err = self.cli(h, T, "doctor", path="/usr/bin:/bin")
        self.assertEqual((code, out, err), (5, "", ""))
        self.assertEqual(h.ran(), ["doctor"])
        for name in ("hL", "hM"):  # no file the finder names: ~/.local/bin is off PATH
            bare = self.home(name)
            code, out, err = self.cli(bare, T, "doctor", path="/usr/bin:/bin")
            self.assertEqual(code, 3, out + err)
            self.assertIn("has no command here yet: it installs its own", err)
            self.assertEqual(bare.ran(), [])


class NameTest(Copy):
    def test_3_an_answer_under_another_name_does_not_count(self):
        for answer, reason, words in ((described("other"), "other", "answers under another tool's name"),
                                      ("not an answer", "unread", "gave no answer that reads")):
            h = self.home("hK")
            h.file(h.launch, stub(describe=answer))
            path = h.terminal()
            code, out, err = self.cli(h, "config", T, path=path)
            self.assertEqual(code, 0, out + err)
            self.assertIn(words, out + err)
            code, out, err = self.cli(h, "config", path=path)
            self.assertIn(words, out, err)
            code, out, err = self.cli(h, "config", "--json", path=path)
            row = [r for r in json.loads(out)["tools"] if r["name"] == T][0]
            self.assertEqual((row["state"], row.get("reason")), ("unreadable", reason))

    def test_4_a_failed_settings_read_says_why(self):
        h = self.home("hD")
        h.commands(stub(describe=described(), config=config_error()))
        code, out, err = self.cli(h, "config")
        line = [l for l in out.splitlines() if T in l][0]
        self.assertIn("reading its keys failed", line)
        code, out, err = self.cli(h, "config", T)
        self.assertEqual(code, 0, out + err)
        self.assertIn("murmur answers, but reading its keys failed: " + MESSAGE, out + err)
        self.assertEqual((out + err).splitlines()[-1], "next: " + REMEDY)
        code, out, err = self.cli(h, "config", T + ".key")
        self.assertNotEqual(code, 0)
        self.assertIn("murmur.key cannot be read: " + MESSAGE + "\n", err)  # sc4: the command is next's
        self.assertRegex(err.splitlines()[-1], r"^next: .*config murmur$")
        code, out, err = self.cli(h, "config", "--json")
        row = [r for r in json.loads(out)["tools"] if r["name"] == T][0]
        self.assertEqual(row["read"], "error")
        self.assertEqual(row["error"], {"code": "bad_file", "message": MESSAGE, "remedy": REMEDY})
        bare = self.home("hD")
        bare.commands(stub(describe=described(), config=config_error(remedy=None), config_exit=0))
        code, out, err = self.cli(bare, "config", T)
        self.assertIn("reading its keys failed: " + MESSAGE, out + err)
        self.assertNotIn("next: " + REMEDY, out + err)
        self.assertFalse([l for l in (out + err).splitlines() if l.startswith("next: murmur")])

    def test_8_a_message_and_a_detail_print_on_one_line(self):
        h = self.home("hD")
        h.commands(stub(describe=described(), config=config_error(message="red \x1b[31mpart\nsecond")))
        code, out, err = self.cli(h, "config", T)
        self.assertNotIn(ESC, out + err)
        self.assertIn("reading its keys failed: red [31mpart second", out + err)
        code, out, err = self.cli(h, "config", "--json")
        row = [r for r in json.loads(out)["tools"] if r["name"] == T][0]
        self.assertEqual(row["error"]["message"], "red [31mpart second")
        long = self.home("hD")
        long.commands(stub(describe=described(), config=config_error(message="x" * 400)))
        code, out, err = self.cli(long, "config", "--json")
        row = [r for r in json.loads(out)["tools"] if r["name"] == T][0]
        self.assertEqual(len(row["error"]["message"]), 300)

    def test_13_a_remedy_that_answers_or_removes_stands_on_its_own_line(self):
        """Review 1's lead 1, ruled as sc5's R8: no `next:` offers a `--yes`, a `-y` or a remove."""
        for remedy in ("murmur config --reset --yes", "murmur config --reset -y", "murmur remove all"):
            h = self.home("hD")
            h.commands(stub(describe=described(), config=config_error(remedy=remedy)))
            code, out, err = self.cli(h, "config", T)
            self.assertEqual(code, 0, out + err)
            lines = (out + err).splitlines()
            self.assertIn(remedy, [l.strip() for l in lines], out + err)
            self.assertFalse([l for l in lines if l.startswith("next:") and remedy in l], out + err)
            self.assertRegex(lines[-1], r"^next: \S*agentik\S* config murmur$")

    def test_14_a_remedy_with_a_control_byte_is_no_remedy(self):
        """Review 1's lead 2: no second line of the tool's joins a line a person pastes."""
        for remedy in ("mend \x1b]52;c;ZWNobyBoaQ==\x07 x\nrm -rf ~", "mend x\nrm -rf ~", "mend\rrm -rf ~",
                       "mend\x00 x"):
            h = self.home("hD")
            h.commands(stub(describe=described(), config=config_error(remedy=remedy)))
            code, out, err = self.cli(h, "config", T)
            self.assertEqual(code, 0, out + err)
            self.assertIn("reading its keys failed: " + MESSAGE, out + err)
            self.assertNotIn("mend", out + err)
            self.assertRegex((out + err).splitlines()[-1], r"^next: \S*agentik\S* config$")
            code, out, err = self.cli(h, "config", "--json")
            row = [r for r in json.loads(out)["tools"] if r["name"] == T][0]
            self.assertEqual(row["error"], {"code": "bad_file", "message": MESSAGE, "remedy": None})

    def test_15_a_tool_that_is_no_string_is_unread(self):
        for tool in (None, 5, [T]):
            h = self.home("hK")
            h.file(h.launch, stub(describe=described(tool)))
            path = h.terminal()
            code, out, err = self.cli(h, "config", "--json", path=path)
            row = [r for r in json.loads(out)["tools"] if r["name"] == T][0]
            self.assertEqual((row["state"], row.get("reason")), ("unreadable", "unread"), tool)
            code, out, err = self.cli(h, "config", T, path=path)
            self.assertIn("gave no answer that reads", out + err)

    def no_remedy(self, remedy):
        """`config T` closes as for a null remedy, and `config --json` carries none."""
        h = self.home("hD")
        h.commands(stub(describe=described(), config=config_error(remedy=remedy)))
        code, out, err = self.cli(h, "config", T)
        self.assertEqual(code, 0, out + err)
        self.assertIn("reading its keys failed: " + MESSAGE, out + err)
        self.assertNotIn("murmur prune", out + err)
        self.assertNotIn("mend", out + err)
        self.assertRegex((out + err).splitlines()[-1], r"^next: \S*agentik\S* config$")
        code, out, err = self.cli(h, "config", "--json")
        row = [r for r in json.loads(out)["tools"] if r["name"] == T][0]
        self.assertEqual(row["error"], {"code": "bad_file", "message": MESSAGE, "remedy": None})

    def test_17_a_remedy_past_the_cap_is_no_remedy(self):
        """Review 2's F3: a remedy is never cut; past the cap, its outer spaces gone, it is none."""
        head, tail = "murmur prune ~/.cache/murmur/", " --dry-run"
        long = head + "a" * (tools.LINE_CAP + 1 - len(head) - len(tail)) + tail
        self.assertEqual(len(long), tools.LINE_CAP + 1)
        self.no_remedy(long)
        self.no_remedy("  " + long + "  ")
        at_cap = long[:len(head)] + long[len(head) + 1:]
        self.assertEqual(len(at_cap), tools.LINE_CAP)
        for remedy, whole in ((at_cap, at_cap), ("  " + at_cap + " ", at_cap),
                              ("  murmur-mend /opt/acme/murmur.yaml  ", REMEDY)):
            h = self.home("hD")
            h.commands(stub(describe=described(), config=config_error(remedy=remedy)))
            code, out, err = self.cli(h, "config", T)
            self.assertEqual(code, 0, out + err)
            self.assertEqual((out + err).splitlines()[-1], "next: " + whole)
            code, out, err = self.cli(h, "config", "--json")
            row = [r for r in json.loads(out)["tools"] if r["name"] == T][0]
            self.assertEqual(row["error"]["remedy"], whole)

    def test_18_a_remedy_with_a_mark_that_cannot_be_seen_is_no_remedy(self):
        """Review 2's F2: a character of category Cf or Cs makes no remedy on R4's path."""
        for mark in MARKS:
            self.no_remedy("mend %sx" % mark)


class DoctorTest(Checks):
    def starts(self, name=T):
        try:
            with open(os.path.join(self.home, "ran.log")) as fh:
                return fh.read().splitlines()
        except FileNotFoundError:
            return []

    def murmur(self, body):
        return self.stub("agentik-" + T, body)

    def group(self, out, name=T):
        """The lines under a group's line, to the next group's."""
        lines, found = out.splitlines(), None
        for i, line in enumerate(lines):
            m = MARK.match(line)
            if m and m.group(2) == name:
                found = i
            elif found is not None and (m or not line.startswith("    ")):
                return lines[found:i]
        return lines[found:] if found is not None else []

    def order(self, remedy=REMEDY):
        return [check("c0", "ok"), check("w1", "warn"), check("f1", "fail", remedy=remedy),
                check("n1", "note"), check("c1", "ok"), check("f2", "fail"), check("c2", "ok")]

    def test_5_each_failing_check_by_name_then_the_rest(self):
        path = self.ready()
        self.murmur(stub(describe=described(reads=("doctor",)), checks=doctor_answer(self.order())))
        code, out, err = self.screen(PATH=path)
        self.assertEqual(code, 1, out + err)
        rows = [CHECK_ROW.match(l).groups() for l in self.group(out) if CHECK_ROW.match(l)]
        self.assertEqual(rows, [("FAIL", "f1", "f1 reads fail"), ("FAIL", "f2", "f2 reads fail"),
                                ("warn", "w1", "w1 reads warn"), ("ok", "doctor", "4 checks read ok")])
        self.assertEqual(err.splitlines()[-1], "next: " + REMEDY)
        code, raw, obj = self.json_of(PATH=path)
        self.assertEqual((code, obj["failed"], obj["warned"]), (1, 2, 1))
        self.assertEqual(self.starts(T), ["describe --json", "checks --json", "checks --json"])

    def test_6_no_remedy_closes_on_the_plain_line(self):
        path = self.ready()
        self.murmur(stub(describe=described(reads=("doctor",)), checks=doctor_answer(self.order(None))))
        code, out, err = self.screen(PATH=path)
        self.assertEqual(code, 1, out + err)
        last = err.splitlines()[-1]
        self.assertTrue(last.startswith(PLAIN), err)
        p = subprocess.run(["/bin/sh", "-c", last[len(PLAIN):]], capture_output=True, text=True,
                           env=self.env(PATH=path), timeout=60)
        self.assertNotEqual(p.returncode, 127, p.stderr)
        one = [check("c0", "ok"), check("f1", "fail")]
        self.murmur(stub(describe=described(reads=("doctor",)), checks=doctor_answer(one)))
        code, out, err = self.screen(PATH=path)
        self.assertEqual(self.group(out)[-1].split(None, 2)[2].strip(), "1 check read ok")

    def test_7_an_answer_that_does_not_count_keeps_the_pins_rows(self):
        bad = doctor_answer([check("c0", "bad")])
        self.stub("agentik-bad", stub(describe=described("bad", ("doctor",)), checks=bad))
        self.stub("agentik-big", stub(describe=described("big", ("doctor",)),
                                      checks="head -c 2097152 /dev/zero | tr '\\0' a\n"))
        self.stub("agentik-slow", stub(describe=described("slow", ("doctor",)),
                                       checks=doctor_answer([check("c0", "ok")]), sleep=10))
        saved = doctor.DEADLINE
        doctor.DEADLINE = 1.0
        self.addCleanup(setattr, doctor, "DEADLINE", saved)
        out, err = io.StringIO(), io.StringIO()
        code = cli.Command(["doctor", "--json"], self.env(), out, err).run()
        self.assertNotIn("Traceback", err.getvalue())
        got = {g["name"]: [(c["status"], c["detail"]) for c in g["checks"]]
               for g in json.loads(out.getvalue())["tools"]}
        unread = [("warn", "its doctor could not start, or printed more than 1 MiB")]
        self.assertEqual((got["bad"], got["big"]), (unread, unread))
        self.assertEqual(got["slow"], [("warn", "its doctor ran past 1 s, so it was stopped")])
        self.assertEqual(code, 0)

    def test_8_a_detail_prints_on_one_line(self):
        path = self.ready()
        checks = [check("f1", "fail", "red \x1b[31mpart\nsecond")]
        self.murmur(stub(describe=described(reads=("doctor",)), checks=doctor_answer(checks)))
        code, out, err = self.screen(PATH=path)
        self.assertIn(("FAIL", "f1", "red [31mpart second"), self.rows(out))

    def no_read(self):
        """(exit, the group's lines and the close, the group's --json) of a tool on sc10's path."""
        code, out, err = self.screen(PATH=self.path)
        lines = self.group(out) + err.splitlines()[-1:]
        _, _, obj = self.json_of(PATH=self.path)
        group = [g for g in obj["tools"] if g["name"] == T][0]
        return code, "\n".join(lines) + "\n", json.dumps(group["checks"], sort_keys=True)

    def test_9_no_doctor_read_keeps_the_pins_bytes(self):
        """Review 1's F1: a tool whose describe names no doctor read, or that answers no describe,
        is read through sc10's `doctor --json` and keeps the pin's rows, order, close and --json,
        as taken at b99f677 in this home (PIN_9)."""
        self.path = self.ready()
        answer = self.answer_of(T, NO_READ)
        self.tool(T, answer)  # no describe: sc10's stub exits 9
        self.assertEqual(self.no_read(), PIN_9)
        self.assertEqual(Checks.starts(self, T)[-2:], ["describe --json", "doctor --json"])  # counts/
        self.murmur(stub(describe=described(reads=("config",)), doctor_json=json.loads(answer)))
        self.assertEqual(self.no_read(), PIN_9)
        self.assertEqual(self.starts(T), ["describe --json", "doctor --json", "doctor --json"])  # cached

    def test_14_a_doctor_remedy_with_a_control_byte_is_no_remedy(self):
        """Review 1's lead 2: a check of R5's read whose remedy holds a control byte or a newline
        has no `fix:` line, and the close names no command of it."""
        path = self.ready()
        bad = "m \x1b]0;x\x07\nrm -rf ~"
        for answer in (doctor_answer([check("c0", "ok"), check("f1", "fail", remedy=bad)]),
                       {"schema": "agentik.doctor/1", "ok": False,
                        "error": {"code": "c", "message": "it broke", "remedy": "mend\nrm -rf ~"}}):
            self.murmur(stub(describe=described(reads=("doctor",)), checks=answer))
            code, out, err = self.screen(PATH=path)
            self.assertEqual(code, 1, out + err)
            self.assertNotIn("rm -rf", out + err)
            self.assertNotIn("fix:", "\n".join(self.group(out)))
            self.assertTrue(err.splitlines()[-1].startswith(PLAIN), err)
            _, _, obj = self.json_of(PATH=path)
            group = [g for g in obj["tools"] if g["name"] == T][0]
            self.assertEqual([c["remedy"] for c in group["checks"] if c["status"] == "fail"], [None])

    def test_16_an_empty_doctor_read_does_not_count(self):
        path = self.ready()
        d = described(reads=("doctor",))
        d["reads"][0]["argv"] = []
        self.murmur(stub(describe=d, checks=doctor_answer([check("f1", "fail")])))
        code, out, err = self.screen(PATH=path)
        self.assertEqual(code, 0, out + err)
        self.assertIn(("ok", T, "its doctor passed"), [MARK.match(l).groups() for l in out.splitlines()
                                                       if MARK.match(l)])
        self.assertEqual(self.starts(T), ["describe --json", "doctor --json", "doctor"])

    def test_18_a_doctor_remedy_with_a_mark_that_cannot_be_seen_is_no_remedy(self):
        """Review 2's F2: a check of R5's read, or its `ok` false answer, whose remedy holds a
        character of category Cf or Cs has no `fix:` line, and the close names no command of it."""
        path = self.ready()
        for mark in MARKS:
            bad = "murmur-mend %sx" % mark  # PLAIN holds "mend each"
            for answer in (doctor_answer([check("c0", "ok"), check("f1", "fail", remedy=bad)]),
                           {"schema": "agentik.doctor/1", "ok": False,
                            "error": {"code": "c", "message": "it broke", "remedy": bad}}):
                self.murmur(stub(describe=described(reads=("doctor",)), checks=answer))
                code, out, err = self.screen(PATH=path)
                self.assertEqual(code, 1, out + err)
                self.assertNotIn("murmur-mend", out + err, ascii(mark))
                self.assertNotIn("fix:", "\n".join(self.group(out)))
                self.assertTrue(err.splitlines()[-1].startswith(PLAIN), err)
                _, _, obj = self.json_of(PATH=path)
                group = [g for g in obj["tools"] if g["name"] == T][0]
                self.assertEqual([c["remedy"] for c in group["checks"] if c["status"] == "fail"], [None])


class TableTest(unittest.TestCase):
    def test_10_the_table_holds_four_rows(self):
        table = tools.fallback(str(LIB))
        self.assertEqual(len(table), 4)
        self.assertTrue(all(row.get("lines") for row in table.values()))


class UpdateTest(unittest.TestCase):
    def test_12_updates_close_is_the_doctors_screen(self):
        from test_ak4a_update import Home
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        h = Home(os.path.join(os.path.realpath(tmp.name), "h"))
        root = h.install("murmur@agentik", "1.0.0")
        h.install("paint@agentik", "2.0.0")
        body = stub(describe=described(reads=("doctor",)),
                    checks=doctor_answer([check("c0", "ok"), check("f1", "fail")]))
        for exe in (os.path.join(root, "bin", "agentik-" + T), os.path.join(h.bindir, "agentik-" + T)):
            with open(exe) as fh:
                head = [l for l in fh.read().splitlines() if l.startswith(("VERSION=", "TREE="))]
            h.file(exe, body.replace("#!/bin/sh\n", "#!/bin/sh\n" + "".join(l + "\n" for l in head), 1))
        code, out, err = h.run("update", "--yes")
        doc_code, doc_out, doc_err = h.run("doctor")
        self.assertIn("FAIL  f1", doc_out)
        self.assertTrue(out.endswith(doc_out), out + "\n----\n" + doc_out)
        # the suite from a checkout closes on its own line, after the doctor's (row up2 R2)
        self.assertEqual(err.splitlines()[-2], doc_err.splitlines()[-1])
        self.assertTrue(err.splitlines()[-1].startswith("next: pull that checkout"), err)


if __name__ == "__main__":
    unittest.main()
