"""The issue's form (packet rp4-form): written and read back byte for byte, its fingerprint, its
ceiling and the nothing-new check. Every tool here is a made-up name; nothing here writes a file
or reaches the network."""
import ast
import copy
import hashlib
import json
import random
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "plugins" / "suite" / "lib"
MODULE = LIB / "agentik_suite" / "form.py"
GOLDEN = ROOT / "tests" / "fixtures" / "rp4_form_example.md"
sys.path.insert(0, str(LIB))
from agentik_suite import form  # noqa: E402

TOOLS = {"lantern", "harmonics", "ledger", "suite", "door"}
ALPHA = {"alpha": "agentik-alpha"}
FAILING = "doctor: failing: resolved, meter"


def example():
    return {
        "tool": "lantern", "title": FAILING, "ran": "agentik lantern doctor", "exit": 2,
        "happened": FAILING,
        "expected": "doctor passes in a fresh clone of billing-api, before any lantern",
        "versions": ["lantern 2.0.0-alpha.101 (1f3a9c0d2b7e)", "suite 0.6.0", "door 0.2.0"],
        "system": ["Claude Code 2.1.323", "Darwin 27.0.0 arm64", "Python 3.9.6", "at a terminal"],
        "counts": [1, 0, 21], "rows": [["lantern", "fail", "doctor", FAILING]],
        "plugins": ["lantern 2.0.0-alpha.101", "harmonics 0.21.17", "ledger 1.6.3", "suite 0.6.0"],
        "others": 1, "lines": ["no profile resolved for <path-1>", FAILING],
        "version": "2.0.0-alpha.101", "fingerprint": "2bcc624a2914"}


def example_facts():
    return {
        "schema": "agentik.issue-facts/1", "tool": "lantern",
        "versions": [
            {"name": "lantern", "plugin": "2.0.0-alpha.101", "commit": "1f3a9c0d2b7e", "launcher": None},
            {"name": "suite", "plugin": "0.6.0", "commit": None, "launcher": "0.6.0"},
            {"name": "door", "plugin": None, "commit": None, "launcher": "0.2.0"},
            {"name": "harmonics", "plugin": None, "commit": None, "launcher": None}],
        "system": {"os": "Darwin", "release": "27.0.0", "arch": "arm64", "python": "3.9.6",
                   "claude": "2.1.323", "where": "at a terminal"},
        "checks": {"read": True, "rows": [{"tool": "lantern", "status": "fail", "name": "doctor",
                                            "detail": FAILING}],
                   "failed": 1, "warned": 0, "passed": 21},
        "plugins": {"named": [{"name": "lantern", "version": "2.0.0-alpha.101"},
                              {"name": "harmonics", "version": "0.21.17"},
                              {"name": "ledger", "version": "1.6.3"},
                              {"name": "suite", "version": "0.6.0"}], "others": 1},
        "output": {"ran": "agentik lantern doctor", "exit": 2,
                   "lines": ["no profile resolved for <path-1>", FAILING]},
        "words": {"expected": "doctor passes in a fresh clone of billing-api, before any lantern"}}


PIECES = ["`", "``", "```", "````", "`````", "|", "\\|", "\\", "</details>", "<summary>", "@name",
          "#12", "é", "日本", "Ωmega", "straße", " ", "word", "x", "*", "_", "<path-1>", "(empty)",
          "**Ran:**", ", exit 3", "agentik-issue/1 alpha"]
GEN_TOOLS = ["alpha", "beta-two", "gamma", "suite", "door"]


def fence(lines):
    """R3's fence for these lines, counted here and not by the module."""
    return "`" * max([3] + [len(run) + 1 for line in lines for run in re.findall("`+", line)])


def gen_value(rng, lo=0):
    return "".join(rng.choice(PIECES) for _ in range(rng.randint(lo, 6)))


def gen_version(rng):
    v = "%d.%d.%d" % (rng.randint(0, 30), rng.randint(0, 99), rng.randint(0, 999))
    return v + rng.choice(["", "-alpha.%d" % rng.randint(0, 200), "-beta.1", "-rc.2"])


def gen_fields(rng):
    tool = rng.choice(GEN_TOOLS)
    title = gen_value(rng, 1).strip() or "t"
    while len((tool + " " + title).encode()) > 72:
        title = title[:-1].strip() or "t"
    hexes = "".join(rng.choice("0123456789abcdef") for _ in range(12))
    f = {"tool": tool, "title": title, "ran": gen_value(rng), "exit": rng.randint(0, 255),
         "happened": gen_value(rng), "expected": gen_value(rng),
         "versions": [], "system": rng.choice([None, ["Claude Code unreadable", "Linux 6.1 x86_64",
                                                     "Python 3.12.1", "in Claude Code"]]),
         "counts": [rng.randint(0, 5), rng.randint(0, 5), rng.randint(0, 40)],
         "rows": [[rng.choice(GEN_TOOLS), rng.choice(["fail", "warn"]), gen_value(rng), gen_value(rng)]
                  for _ in range(rng.randint(0, 4))],
         "plugins": ["%s %s" % (rng.choice(GEN_TOOLS), gen_version(rng)) for _ in range(rng.randint(0, 3))],
         "others": rng.randint(0, 4),
         "lines": [rng.choice(["```", gen_value(rng), ""]) for _ in range(rng.randint(1, 5))],
         "version": rng.choice([gen_version(rng), "unreadable"]), "fingerprint": hexes}
    for _ in range(rng.randint(1, 3)):
        item = "%s %s" % (rng.choice(GEN_TOOLS), gen_version(rng))
        item += rng.choice(["", " (%s)" % hexes, " (unreadable)"])
        item += rng.choice(["", " launcher " + gen_version(rng)])
        f["versions"].append(item)
    for section in form.SECTIONS:
        if rng.random() < 0.25:
            f = form.drop(f, section)
    return f


class GoldenTest(unittest.TestCase):
    """Line 1: the design's example, its tool a made-up name of the same length."""

    def test_the_example_is_the_golden_file(self):
        golden = GOLDEN.read_bytes()
        self.assertEqual(len(golden), 801)
        self.assertEqual(form.build(example()), golden)
        self.assertEqual(form.parse(golden, TOOLS), example())

    def test_the_example_fingerprint_is_its_subject(self):
        subject = form.subject("lantern", "agentik lantern doctor", 2, [], {"lantern": "agentik-lantern"})
        self.assertEqual(form.fingerprint("lantern", subject), example()["fingerprint"])

    def test_draft_from_facts_is_the_example(self):
        got = form.draft(example_facts(), "lantern", form.title("doctor", FAILING), FAILING, "2bcc624a2914")
        self.assertEqual(got, example())

    def test_no_tool_name_here_in_the_module_or_the_golden_file(self):
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        tools = [p["name"] for p in market["plugins"] if p["name"] != "suite"]
        pattern = re.compile(r"\b(?:%s)\b" % "|".join(map(re.escape, tools)), re.I)
        for path in (MODULE, Path(__file__), GOLDEN):
            hit = pattern.search(path.read_text())
            self.assertIsNone(hit, "%s names %s" % (path.name, hit and hit.group(0)))

    def test_imports_hashlib_and_re_alone(self):
        mods = set()
        for node in ast.walk(ast.parse(MODULE.read_text())):
            if isinstance(node, ast.Import):
                mods |= {a.name for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                mods.add(node.module)
        self.assertEqual(mods, {"hashlib", "re"})


class RoundTripTest(unittest.TestCase):
    """Line 2: 200 seeded field sets read back and write again to the same bytes."""

    def test_200_field_sets(self):
        rng = random.Random(4)
        tools = set(GEN_TOOLS)
        for i in range(200):
            f = gen_fields(rng)
            with self.subTest(i=i):
                data = form.build(f)
                self.assertTrue(data.endswith(b"\n") and not data.endswith(b"\n\n"))
                self.assertEqual(form.parse(data, tools), f)
                self.assertEqual(form.build(form.parse(data, tools)), data)

    def test_a_line_break_in_a_single_line_value_is_a_value_error(self):
        for key in ("title", "ran", "happened", "expected"):
            for brk in ("\n", "\r", " "):
                f = example()
                f[key] = "a" + brk + "b"
                with self.subTest(key=key, brk=repr(brk)), self.assertRaises(ValueError):
                    form.build(f)
        f = example()
        f["rows"][0][3] = "a\nb"
        with self.assertRaises(ValueError):
            form.build(f)

    def test_an_empty_free_value_is_a_fixed_word_outside_a_span(self):
        f = example()
        f["happened"] = ""
        data = form.build(f)
        self.assertIn(b"\n**Happened:** " + form.EMPTY.encode() + b"\n", data)
        self.assertEqual(form.parse(data, TOOLS), f)

    def test_a_backtick_at_an_edge_is_padded_and_a_pipe_in_a_cell_escaped(self):
        f = example()
        f["happened"] = "`x"
        f["rows"][0][3] = "a|b"
        data = form.build(f).decode()
        self.assertIn("**Happened:** `` `x ``\n", data)
        self.assertIn("| `a\\|b` |", data)
        self.assertEqual(form.parse(data.encode(), TOOLS), f)


class DropTest(unittest.TestCase):
    """Line 3: each of the five sections dropped, alone and all at once."""
    MARKS = {"checks": ["| tool |", "|---|", "Diagnosis: 1 failed"], "plugins": ["Plugins:"],
             "system": ["Claude Code", "Python 3.9.6", "at a terminal"],
             "output": ["**Ran:**", "Last lines:", "no profile resolved"], "words": ["**Expected:**"]}

    def test_each_alone(self):
        for section, marks in self.MARKS.items():
            f = form.drop(example(), section)
            data = form.build(f).decode()
            with self.subTest(section=section):
                for mark in marks:
                    self.assertNotIn(mark, data)
                self.assertEqual(form.parse(data.encode(), TOOLS), f)

    def test_all_at_once(self):
        f = form.drop(example(), *self.MARKS)
        data = form.build(f).decode()
        for marks in self.MARKS.values():
            for mark in marks:
                self.assertNotIn(mark, data)
        self.assertNotIn("<details>", data)
        self.assertEqual(data.count("\n"), 6)
        self.assertEqual(form.parse(data.encode(), TOOLS), f)


class NotTheFormTest(unittest.TestCase):
    """Line 4: each raising NotTheForm with its line."""

    def assertLine(self, data, line):
        with self.assertRaises(form.NotTheForm) as cm:
            form.parse(data if isinstance(data, bytes) else data.encode(), TOOLS)
        self.assertEqual(cm.exception.line, line, str(cm.exception))

    def test_each(self):
        g = GOLDEN.read_text()
        marker = g.splitlines()[-1]
        self.assertLine("lantern something broke\n\nit failed when I ran it\n", 3)
        self.assertLine(g.replace("**Happened:**", "**Occurred:**"), 4)
        self.assertLine(g.replace("| lantern | fail |", "| zephyr | fail |"), 12)
        self.assertLine(g.replace(marker, marker.replace("lantern", "harmonics")), 24)
        self.assertLine(g.replace("**Happened:** `%s`" % FAILING, "**Happened:** " + FAILING), 4)
        self.assertLine(g.replace("**Happened:** `%s`" % FAILING, "**Happened:** `%s` and more" % FAILING), 4)
        self.assertLine(g + marker + "\n", 25)
        self.assertLine(g + "thanks\n", 25)
        self.assertLine(g + "\n", 25)
        self.assertLine(g[:-1], 24)
        self.assertLine(b"\xff\n", 1)

    def test_a_value_the_writer_refuses_stops_on_its_own_line(self):
        g = GOLDEN.read_text()
        self.assertLine(g.replace(", exit 2\n", ", exit 999\n"), 3)
        self.assertLine(g.replace(", exit 2\n", ", exit 256\n"), 3)
        named = "lantern 2.0.0-alpha.101 (1f3a9c0d2b7e), suite 0.6.0, door 0.2.0, "
        self.assertIn(named, g.splitlines()[5])
        self.assertLine(g.replace(named, ""), 6)
        words = form.build(form.drop(example(), "words")).decode()
        self.assertTrue(words.splitlines()[4].startswith("**Versions:** "))
        self.assertLine(words.replace(named, ""), 5)

    def test_a_fence_closed_early_by_a_shorter_run(self):
        f = example()
        f["lines"] = ["a", "```", "b"]
        text = form.build(f).decode()
        self.assertIn("\n````\na\n```\nb\n````\n", text)
        lines = text.split("\n")
        early = text.replace("\n````\n", "\n```\n")
        self.assertLine(early, lines.index("b") + 1)


class FreeTest(unittest.TestCase):
    """Line 5: free lists each free value once, in order, on its line; put changes it alone."""

    def check(self, f):
        listed = form.free(f)
        keys = [k for k, _, _ in listed]
        self.assertEqual(len(keys), len(set(keys)))
        want = ["title", "ran", "happened", "expected"]
        want += ["rows.%d.%s" % (i, w) for i in range(len(f["rows"] or [])) for w in ("name", "detail")]
        want += ["lines"]
        self.assertEqual(keys, [k for k in want if k in keys])
        old = form.build(f).decode().split("\n")
        lines = [line for _, line, _ in listed]
        self.assertEqual(lines, sorted(lines))
        for key, line, value in listed:
            fences = ()
            if key == "lines":
                span = len(f["lines"])
                self.assertEqual(old[line - 1:line - 1 + span], f["lines"])
                news = ["\n".join(text for _ in f["lines"]) for text in ("q", "a ``` b", "````")]
                fences = (line - 2, line - 1 + span)
            else:
                self.assertIn(value.replace("|", "\\|") if key.startswith("rows") else value, old[line - 1])
                news, span = ["q"], 1
            for new_value in news:
                g = form.put(f, key, new_value)
                new = form.build(g).decode().split("\n")
                self.assertEqual(len(new), len(old), key)
                # R3: the fence is three backticks or one longer than the lines' longest run, so new
                # lines may change the two fence lines around them, and no other byte.
                for i in fences:
                    self.assertEqual(old[i], fence(f["lines"]))
                    self.assertEqual(new[i], fence(g["lines"]))
                for i, (a, b) in enumerate(zip(old, new)):
                    if not line - 1 <= i < line - 1 + span and i not in fences:
                        self.assertEqual(a, b, "%s changed line %d" % (key, i + 1))
                self.assertNotEqual(old, new, key)
                self.assertEqual(form.free(g)[keys.index(key)][2], new_value)

    def test_three_backticks_in_the_lines_change_the_two_fences_and_nothing_else(self):
        old = form.build(example()).decode().split("\n")
        new = form.build(form.put(example(), "lines", "a ``` b\nc")).decode().split("\n")
        changed = {i + 1: (a, b) for i, (a, b) in enumerate(zip(old, new)) if a != b}
        self.assertEqual(len(new), len(old))
        self.assertEqual(changed, {17: ("```", "````"), 18: ("no profile resolved for <path-1>", "a ``` b"),
                                   19: (FAILING, "c"), 20: ("```", "````")})

    def test_the_example(self):
        self.check(example())
        self.assertEqual([(k, n) for k, n, _ in form.free(example())],
                         [("title", 1), ("ran", 3), ("happened", 4), ("expected", 5),
                          ("rows.0.name", 12), ("rows.0.detail", 12), ("lines", 18)])

    def test_generated(self):
        rng = random.Random(5)
        for i in range(40):
            f = gen_fields(rng)
            with self.subTest(i=i):
                self.check(f)

    def test_put_leaves_its_argument(self):
        f = example()
        g = form.put(f, "rows.0.detail", "x")
        self.assertEqual(f, example())
        self.assertEqual(g["rows"][0][3], "x")


class FingerprintTest(unittest.TestCase):
    """Lines 6 and 7: the subject and the fingerprint."""

    def test_the_brief_values(self):
        self.assertEqual(form.fingerprint("alpha", "ran:alpha:doctor:2"), "71c680c682c0")
        self.assertEqual(form.subject("alpha", "agentik alpha doctor --json", 2, [], ALPHA), "ran:alpha:doctor:2")
        self.assertEqual(form.subject("alpha", "agentik-alpha doctor", 2, [], ALPHA), "ran:alpha:doctor:2")
        for cmd in ("make check", "agentik beta doctor", "alpha doctor", "agentik"):
            self.assertEqual(form.subject("alpha", cmd, 1, [], ALPHA), "ran:other:1", cmd)
        self.assertEqual(form.fingerprint("alpha", "ran:other:1"), "c46cab703536")
        row = ["alpha", "fail", "doctor", FAILING]
        got = form.subject("alpha", None, None, [row], ALPHA)
        self.assertEqual(got, "check:alpha:doctor:doctor failing resolved meter")
        self.assertEqual(form.fingerprint("alpha", got), "276969ee989b")

    def test_two_rows_two_fingerprints_and_flags_one(self):
        one = ["alpha", "fail", "doctor", "doctor: failing: resolved"]
        two = ["alpha", "fail", "doctor", "doctor: failing: meter"]
        fp = [form.fingerprint("alpha", form.subject("alpha", None, None, [r], ALPHA)) for r in (one, two)]
        self.assertNotEqual(fp[0], fp[1])
        a = form.subject("alpha", "agentik alpha doctor --json", 2, [], ALPHA)
        b = form.subject("alpha", "agentik alpha doctor --verbose --strict", 2, [], ALPHA)
        self.assertEqual(form.fingerprint("alpha", a), form.fingerprint("alpha", b))

    def test_no_free_word_is_hashed(self):
        digits = "1" * 30
        for after in ("Kestrel", digits, "build" + digits):
            self.assertEqual(form.subject("alpha", "agentik alpha doctor " + after, 2, [], ALPHA),
                             "ran:alpha:doctor:2")
        for verb in ("Doctor", digits, "a" * 21, "doc_tor"):
            self.assertEqual(form.subject("alpha", "agentik alpha " + verb, 2, [], ALPHA), "ran:alpha::2")
        self.assertEqual(form.subject("alpha", "agentik-alpha " + "a" * 20, 2, [], ALPHA),
                         "ran:alpha:" + "a" * 20 + ":2")

    def test_a_check_subject_takes_eight_words_and_drops_digits(self):
        row = ["alpha", "warn", "probe2", "one two three four 55 five six seven eight nine"]
        self.assertEqual(form.subject("alpha", None, None, [["beta", "fail", "x", "y"], row], ALPHA),
                         "check:alpha:probe:one two three four five six seven eight")

    def test_a_word_holding_a_digit_is_dropped_whole(self):
        def check(detail):
            return form.subject("alpha", None, None, [["alpha", "fail", "cache", detail]], ALPHA)

        lock = {check("stale lock 3f9a2c held"), check("stale lock 7be41d held")}
        temp = {check("cannot open tmpqwk2x9 for write"), check("cannot open tmpzrt0b1 for write")}
        self.assertEqual(lock, {"check:alpha:cache:stale lock held"})
        self.assertEqual(temp, {"check:alpha:cache:cannot open for write"})
        self.assertEqual(sorted(form.fingerprint("alpha", s) for s in lock | temp),
                         ["40487b9950b9", "ea168b2327fe"])
        self.assertEqual(check("a1 one two three x9y four five six seven eight nine"),
                         "check:alpha:cache:one two three four five six seven eight")

    def test_twelve_hex(self):
        got = form.fingerprint("alpha", "ran:other:0")
        self.assertRegex(got, r"^[0-9a-f]{12}$")
        want = hashlib.sha256(b"agentik-issue/1 alpha ran:other:0").hexdigest()[:12]
        self.assertEqual(got, want)


class FitTest(unittest.TestCase):
    """Line 8: the ceiling."""

    def big(self):
        f = example()
        f["plugins"] = ["plugin-%02d 10.20.30-alpha.40" % i for i in range(80)]
        f["rows"] += [["lantern", "warn", "probe-%d" % i, "w" * 180] for i in range(10)]
        f["lines"] = ["%02d " % i + "x" * 196 for i in range(20)]
        return f

    def test_nine_kb_comes_under(self):
        f = self.big()
        self.assertGreater(len(form.build(f)), 9000)
        got, went = form.fit(f)
        self.assertLessEqual(len(form.build(got)), 4096)
        self.assertEqual([w for w, _ in went], ["plugins", "warn", "lines"])
        self.assertEqual(went[0][1], 80)
        self.assertEqual(went[1][1], 10)
        self.assertIsNone(got["plugins"])
        self.assertEqual(got["rows"], example()["rows"])
        self.assertEqual(got["lines"], f["lines"][went[2][1]:])
        self.assertEqual(f, self.big())
        shorter, _ = form.fit(f, len(form.build(got)) + 200)
        self.assertEqual(shorter["lines"][-len(got["lines"]):], got["lines"])

    def test_plugins_alone_when_enough(self):
        f = self.big()
        f["rows"], f["lines"] = example()["rows"], f["lines"][:10]
        got, went = form.fit(f)
        self.assertEqual(went, [("plugins", 80)])
        self.assertEqual(got["rows"], f["rows"])

    def test_still_over_after_the_three_drops_went_says_so(self):
        f = example()
        f["rows"] = [["lantern", "fail", "n" * 60, "d" * 200] for _ in range(12)]
        f["expected"], f["ran"] = "e" * 600, "agentik lantern doctor " + "r" * 177
        f["lines"] = ["l" * 200 for _ in range(20)]
        got, went = form.fit(f)
        size = len(form.build(got))
        self.assertGreater(size, 4096)
        self.assertEqual(went, [("plugins", 4), ("lines", 20), ("over", size)])
        self.assertIsNone(got["plugins"])
        self.assertIsNone(got["lines"])
        self.assertEqual(got["rows"], f["rows"])
        bare = form.drop(example(), "plugins", "output")
        bare["expected"] = "e" * 4096
        got, went = form.fit(bare)
        self.assertEqual((got, went), (bare, [("over", len(form.build(bare)))]))
        self.assertEqual(form.fit(bare, len(form.build(bare))), (bare, []))

    def test_under_the_ceiling_as_it_was(self):
        self.assertEqual(form.fit(example()), (example(), []))


class NothingNewTest(unittest.TestCase):
    """Line 9: twelve planted renders."""

    def fields(self):
        f = example()
        f["expected"] = "doctor passes in a fresh clone of <struck-1>, before any lantern"
        return f

    def render(self, happened="", expected=None):
        f = self.fields()
        return {"happened": f["happened"] + happened,
                "expected": f["expected"] if expected is None else expected}

    def test_two_pass(self):
        f = self.fields()
        clean = {"happened": FAILING + ", so the run stops.",
                 "expected": "doctor passes in a fresh clone of <struck-1> before any lantern runs."}
        self.assertEqual(form.nothing_new(clean, f), [])
        self.assertEqual(form.added(clean, f), ["so", "the", "run", "stops", "runs"])
        same = {"happened": f["happened"], "expected": f["expected"]}
        self.assertEqual(form.nothing_new(same, f), [])
        self.assertEqual(form.added(same, f), [])

    def test_seven_planted_words_miss(self):
        f = self.fields()
        planted = {"path": (" under /opt/kestrel/bin", "/opt/kestrel/bin"),
                   "opener": (". Kestrel broke it.", "Kestrel"),
                   "script": (" in the lаntern", "lаntern"),
                   "digit": (" on build42", "build42"),
                   "name": (" while Marisol watched", "Marisol"),
                   "hyphen": (" in north-wing", "north-wing"),
                   "at": (" ping @orbit", "@orbit")}
        for kind, (text, word) in planted.items():
            with self.subTest(kind=kind):
                self.assertEqual(form.nothing_new(self.render(text), f), [("word", word)])

    def test_a_dropped_placeholder_and_dropped_error_text_miss(self):
        f = self.fields()
        got = form.nothing_new(self.render(expected="doctor passes in a fresh clone"), f)
        self.assertEqual(got, [("placeholder", "<struck-1>")])
        got = form.nothing_new({"happened": "doctor fails on resolved and meter", "expected": f["expected"]}, f)
        self.assertEqual(got, [("happened", f["happened"])])

    def test_a_lowercase_paraphrase_of_a_path_passes(self):
        f = self.fields()
        f["happened"] = "no profile resolved for <path-1>"
        render = {"happened": "no profile resolved for <path-1>, the projects folder under home",
                  "expected": f["expected"]}
        self.assertEqual(form.nothing_new(render, f), [])
        self.assertEqual(form.added(render, f), ["the", "projects", "folder", "under", "home"])


class TitleTest(unittest.TestCase):
    """Line 10 and R5: 72 bytes for the line, cut on a character's edge, the verb said once."""

    def test_a_four_byte_letter_at_the_cut(self):
        long = "a" * 60 + "\U0001d400" * 35
        self.assertEqual(len(long.encode()), 200)
        for pad in range(4):
            f = form.draft(example_facts(), "lantern", "b" * pad + long, FAILING, "2bcc624a2914")
            line = form.build(f).split(b"\n")[0]
            with self.subTest(pad=pad):
                self.assertLessEqual(len(line), 72)
                self.assertGreater(len(line), 68)
                line.decode("utf-8")

    def test_the_verb_once(self):
        self.assertEqual(form.title("doctor", FAILING), FAILING)
        self.assertEqual(form.title("doctor", "no profile"), "doctor: no profile")
        self.assertEqual(form.title("doc", "doctor fails"), "doc: doctor fails")
        self.assertEqual(form.title(None, "no profile"), "no profile")


class GatherJoinTest(unittest.TestCase):
    """Phase 2: `draft` over the versions and plugins rp3's `gather` gives, read from a table in
    memory and a PATH of nothing, so no file is read; every value it can give builds a form."""

    PUBLIC = {"marketplace": "agentik", "tools": {"lantern": "made-up/lantern", "suite": "made-up/suite"}}

    def facts(self, table):
        from agentik_suite import gather
        f = example_facts()
        f["versions"] = gather.versions({"PATH": ""}, self.PUBLIC, table, [])
        f["plugins"] = gather.plugins(self.PUBLIC, table)
        return f

    def built(self, table):
        f = form.draft(self.facts(table), "lantern", "lantern: doctor fails", FAILING, "2bcc624a2914")
        data = form.build(f)
        self.assertEqual(form.build(form.parse(data, TOOLS)), data)
        return form.parse(data, TOOLS)

    def test_a_plugin_of_no_version_reads_unreadable(self):
        for entry in ({}, {"version": None}, []):
            got = self.built({"lantern@agentik": entry, "suite@agentik": {"version": "0.6.9"}})
            self.assertEqual(got["plugins"], ["lantern unreadable", "suite 0.6.9"])

    def test_no_version_shown_names_the_tool_unreadable(self):
        got = self.built({})
        self.assertEqual(got["versions"], ["lantern unreadable"])
        self.assertEqual(got["version"], "unreadable")

    def test_every_value_gather_gives_builds(self):
        values = [None, "1.2.3", "1.2", "0.6.9-alpha.3", 7]
        commits = [None, "ABCDEF0123456789", "zz", 12]
        for v in values:
            for c in commits:
                for w in values:
                    entry = {} if v is None else {"version": v}
                    if c is not None:
                        entry["gitCommitSha"] = c
                    self.built({"lantern@agentik": entry, "suite@agentik": {"version": w}, "other@x": {}})


if __name__ == "__main__":
    unittest.main()
