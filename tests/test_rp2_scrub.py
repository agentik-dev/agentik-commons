"""The reporter's layer 1 (packet rp2-scrub): `scrub.py` takes what is private out of a free value
before it is a draft, and `detect` is the check `send` runs on the bytes.

Every hostile line is assembled at run time from parts, with the made-up marker `zqv` in each
private place, so the scanner's scan of this tree counts nothing new. A machine is made by hand
(`scrub.build`); the one test of `machine` runs in a temp home with a stub `git` and a made-up
private list. Nothing here reads the real home, login or private list, or writes outside a temp
folder."""
import ast
import base64
import os
import random
import re
import string
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "plugins" / "suite" / "lib"
MODULE = LIB / "agentik_suite" / "scrub.py"
sys.path.insert(0, str(LIB))

from agentik_suite import scrub  # noqa: E402  (at the pin: an ImportError, every line red)

MARK = "zqv"
AT = "@"
USERS = "/" + "Us" + "ers"
HOME = USERS + "/zqvuser"
DASHED = "-" + "Us" + "ers-zqvuser"
LOGIN = "zqvlogin"
PUBLIC = {"marketplace": "agentik",
          "tools": {"widget": "acmeorg/agentik-widget", "suite": "acmeorg/agentik-commons"}}
RNG = random.Random(22)
PH = re.compile(r"<(?:path|email|address|private|struck|name|url|site|run)-\d+>"
                r"|<(?:user|host|repo|project|secret)>")


def rand(n, alphabet=string.ascii_letters + string.digits):
    return "".join(RNG.choice(alphabet) for _ in range(n))


def machine(**more):
    kw = {"home": HOME, "logins": (LOGIN,), "hosts": ("zqvhost", "zqvhost.internal")}
    kw.update(more)
    return scrub.build(PUBLIC, **kw)


def placeholders(text):
    return PH.findall(text)


# Line 1: (input, expected) for each case of 4(b).
PCT = "%2F".join(["", "Us" + "ers", "zqvuser", "zqvpct", "x.txt"])
PATHS = [
    ('open "%s/My zqv Folder/a.txt" failed' % HOME, 'open "<path-1>" failed'),
    ("cannot read %s/zqv dir/My zqv File.txt" % HOME, "cannot read <path-1>"),
    ("--config=%s/zqvconf/x.yaml" % HOME, "--config=<path-1>"),
    ("PATH=%s/zqvbin:/usr/bin:/opt/zqvtools/bin" % HOME, "PATH=<path-1>:/usr/bin:<path-2>"),
    ("see zqvdir/zqvfile.txt", "see <path-1>"),
    ("wrote /zqvroot", "wrote <path-1>"),
    ("in %s/code/zqv Big Folder" % HOME, "in <path-1>"),
    ("%s/ZQVDIR/x" % HOME.upper(), "<path-1>"),
    ("/System/Volumes/Data%s/zqvdata" % HOME, "<path-1>"),
    ("read " + PCT, "read <path-1>"),
    ("file://%s/zqvurl/x" % HOME, "file:<path-1>"),
    ("project %s-code-zqvproj" % DASHED, "project <project>"),
    ("project %s" % DASHED, "project <project>"),
]

KEPT = ["~/.local/bin", "~/.local/bin/agentik", "~/.local/bin/agentik-widget",
        "~/.claude/plugins/installed_plugins.json",
        "~/.claude/plugins/cache/agentik/widget/1.2.3",
        "~/.claude/plugins/cache/agentik/widget/1.2.3/bin/run",
        "~/.local/share/agentik-widget/0a1b2c3d4e5f", "~/.local/share/agentik-widget/0a1b2c3d4e5f/lib/x.py",
        "~/.config/agentik", "~/.config/agentik/hygiene-private.tsv", "~/.config/agentik/widget",
        "~/.config/agentik/widget/config.yaml", "~/.cache/agentik", "~/.cache/agentik/widget",
        "~/.local/state/agentik-widget", "/usr/bin", "/usr/bin/git", "/bin/sh", "/usr/sbin",
        "/sbin/ps", "/usr/local/bin/python3", "/opt/homebrew/bin/gh", "/dev/null", "/dev/tty", "/tmp",
        ".claude/agentik/config.yaml", ".claude/settings.json", ".claude/settings.local.json"]
UNKEPT = ["~/.claude/plugins/cache/agentik/zqvprivate/1.0.0", "~/.local/bin/zqvscript",
          "/opt/homebrew/Cellar/zqvformula/1.0", "~/.local/state/zqvroot",
          "~/.local/state/agentik-widget/../zqvroot/x", "%s/.local/bin/zqvrun" % HOME]

TAILS = [
    ("loading %s/zqvdir/a.yaml failed at line 9" % HOME, "loading <path-1> failed at line 9"),
    ("fatal: %s/code/Zqv Red Dog is not a git repository" % HOME,
     "fatal: <path-1> is not a git repository"),
]

FULL_WIDTH = "".join(chr(ord(c) + 0xFEE0) for c in LOGIN)
NAMES = [
    ("user %s ran" % LOGIN, "user <user> ran"),
    ("%s9" % LOGIN, "<user>9"),
    ("%s_x" % LOGIN, "<user>_x"),
    ("uid=501(%s)" % LOGIN, "uid=501(<user>)"),
    ("%s%sbox" % (LOGIN, AT), "<user>%sbox" % AT),
    ("by %s now" % FULL_WIDTH, "by <user> now"),
    ("by zqv​login now", "by <user> now"),
]

LEFT = ["tokens: 4096 of 8192", "input_tokens=1200", "at 12:34:56",
        "agentik.doctor/1 read/write and/or 3/22 checks",
        "see https://github.com/acmeorg/agentik-widget/issues/12",
        "test_" + "_".join(["scrub", "keeps", "the", "tail", "words", "after", "a", "paths"]),
        "commit 3f9a2b7c1d4e", "README.md, setup.sh, main.py"]


def key_block():
    head = "-----BEGIN OPENSSH " + "PRIV" + "ATE KEY-----"
    tail = "-----END OPENSSH " + "PRIV" + "ATE KEY-----"
    body = [base64.b64encode(bytes(RNG.randrange(256) for _ in range(48))).decode() for _ in range(20)]
    body.append(base64.b64encode(b"zqv").decode())
    return [head] + body + [tail]


def secret_lines():
    host = "zqvhost.example"
    quad = ".".join(str(RNG.randrange(11, 200)) for _ in range(4))
    return [
        "remote https://zqv:%s%s%s/zqv/repo.git" % (rand(24), AT, host),
        "remote git%s%s:zqv/repo.git" % (AT, host),
        "db postgres://zqvuser:%s%sdb.zqvhost.internal:5432/zqvdb" % (rand(20), AT),
        "Authorization: Bearer zqv%s" % rand(40),
        "Authorization: Basic %s" % base64.b64encode(("zqv:" + rand(20)).encode()).decode(),
        "password=zqv%s" % rand(12),
        'api_key: "zqv%s"' % rand(30),
        "run --token zqv%s now" % rand(24),
        "Co-authored-by: Zqvfirst Zqvlast <zqvperson%s%s>" % (AT, host),
        "mail zqvperson%%40%s" % host,
        "peer %s up" % quad,
        "peer 2001:db8:85a3::8a2e:370:7334 up",
        "mac a4:83:e7:1b:2c:3d",
        "build zqvbox.corp failed",
    ]


class PathTest(unittest.TestCase):
    """Lines 1 to 3: 4(b)'s cases, the closed list, a path's tail words."""

    def test_line1_each_case(self):
        m = machine()
        for raw, want in PATHS:
            with self.subTest(raw=raw):
                out = scrub.scrub(raw, m)[0]
                self.assertNotIn(MARK, out.lower())
                self.assertEqual(out, want)

    def test_line2_kept_by_name(self):
        m = machine()
        for path in KEPT:
            with self.subTest(path=path):
                self.assertEqual(scrub.scrub("at %s ok" % path, m)[0], "at %s ok" % path)
        for path in UNKEPT:
            with self.subTest(path=path):
                out = scrub.scrub("at %s ok" % path, m)[0]
                self.assertNotIn(MARK, out.lower())
                self.assertEqual(out, "at <path-1> ok")
        out = scrub.scrub("at ~/.local/state/agentik-widget/zqvlog/x.txt", m)[0]
        self.assertEqual(out, "at ~/.local/state/agentik-widget/<path-1>")
        out = scrub.scrub("at %s/.local/bin/agentik" % HOME, m)[0]
        self.assertEqual(out, "at ~/.local/bin/agentik")

    def test_line3_tail_words(self):
        m = machine()
        for raw, want in TAILS:
            with self.subTest(raw=raw):
                out = scrub.scrub(raw, m)[0]
                self.assertEqual(out, want)
                for word in ("Zqv", "Red", "Dog"):
                    self.assertNotIn(word, out)

    def test_one_value_one_placeholder(self):
        m = machine()
        raw = "a %s/zqvx then %s/ZQVX then %s/zqvy" % (HOME, HOME, HOME)
        self.assertEqual(scrub.scrub(raw, m)[0], "a <path-1> then <path-1> then <path-2>")
        out, counts, _ = scrub.scrub("<path-4> and /zqvz", m)
        self.assertEqual(out, "<path-4> and <path-5>")
        self.assertEqual(counts, {"path": 1})


class NameTest(unittest.TestCase):
    """Lines 4 and 5: machine names, and the names that are public words."""

    def test_line4_login(self):
        m = machine()
        for raw, want in NAMES:
            with self.subTest(raw=raw):
                out = scrub.scrub(raw, m)[0]
                self.assertEqual(out, want)
        out, counts, spans = scrub.scrub("x%sy" % LOGIN, m)
        self.assertEqual(out, "x%sy" % LOGIN)
        self.assertEqual(spans, [(0, len(out), "unsure")])
        self.assertEqual(counts, {"unsure": 1})

    def test_line5_plain_word_logins(self):
        for login in ("user", "path", "host", "git", "claude", "doctor", "widget"):
            with self.subTest(login=login):
                m = scrub.build(PUBLIC, home=HOME, logins=(login,))
                self.assertEqual(scrub.scrub("agentik widget doctor", m)[0], "agentik widget doctor")
                line = "owner %s on box" % login
                self.assertEqual(scrub.scrub(line, m)[0], line)
                self.assertEqual(scrub.scrub(login + AT + "box", m)[0], "<user>" + AT + "box")
                self.assertEqual(scrub.weak(m), ["user"])
        m = scrub.build(PUBLIC, home=HOME, repos=("agentik-widget",))
        self.assertEqual(scrub.scrub("agentik widget doctor", m)[0], "agentik widget doctor")
        self.assertEqual(scrub.scrub("owner agentik-widget on box", m)[0], "owner agentik-widget on box")
        self.assertEqual(scrub.scrub("agentik-widget" + AT + "box", m)[0], "<repo>" + AT + "box")
        self.assertEqual(scrub.weak(m), ["repo"])
        self.assertEqual(scrub.weak(machine()), [])

    def test_host_and_repo(self):
        m = machine(repos=("zqvproj",))
        self.assertEqual(scrub.scrub("on zqvhost in zqvproj", m)[0], "on <host> in <repo>")


class ShapeTest(unittest.TestCase):
    """Lines 6 and 7: the reporter's own shapes, and what they leave alone."""

    def assertClean(self, out):
        self.assertNotIn(MARK, out.lower())
        self.assertIsNone(re.search(r"[A-Za-z0-9+/=_-]{19,}", out), out)

    def test_line6_key_block(self):
        m = machine()
        block = key_block()
        self.assertEqual(len(block), 23)
        for lines in (block, block[3:]):
            out = scrub.scrub("before\n" + "\n".join(lines) + "\nafter", m)[0]
            self.assertEqual(out, "before\n<secret>\nafter")

    def test_line6_secrets_and_names(self):
        m = machine()
        for raw in secret_lines():
            with self.subTest(raw=raw[:12]):
                out = scrub.scrub(raw, m)[0]
                self.assertClean(out)
                self.assertTrue(placeholders(out), out)
        out = scrub.scrub("Co-authored-by: Zqvfirst Zqvlast <zqvp%szqv.example>" % AT, m)[0]
        self.assertEqual(out, "Co-authored-by: <name-1> <email-1>")
        self.assertEqual(scrub.scrub("tokens: 4096 and --token 77", m)[0], "tokens: 4096 and --token 77")

    def test_line6_named_variables(self):
        value = "zqv" + rand(20)
        m = machine(secrets=(value,))
        self.assertEqual(scrub.scrub("got %s back" % value.upper(), m)[0], "got <secret> back")

    def test_line7_left(self):
        m = machine()
        for line in LEFT:
            with self.subTest(line=line):
                self.assertEqual(scrub.scrub(line, m)[0], line)
                self.assertEqual(scrub.detect(line, m), [])


class FixedPointTest(unittest.TestCase):
    """Line 8: scrub is its own fixed point, and detect finds nothing in what it gives."""

    def corpus(self):
        lines = [raw for raw, _ in PATHS + TAILS + NAMES] + LEFT + secret_lines()
        lines += ["at %s ok" % p for p in KEPT + UNKEPT] + ["\n".join(key_block())]
        return lines

    def check(self, m, x):
        once = scrub.scrub(x, m)[0]
        self.assertEqual(scrub.scrub(once, m)[0], once, repr(x))
        self.assertEqual(scrub.detect(once, m), [], repr(x))

    def test_line8_corpus(self):
        for m in (machine(), scrub.build(PUBLIC, home=HOME, logins=("user",))):
            for x in self.corpus():
                self.check(m, x)

    def test_line8_glued(self):
        pieces = []
        for line in self.corpus():
            pieces += line.split(" ")
        rng = random.Random(1113)
        seps = [" ", "", "/", "\n", ":", "=", '"', " ", " "]
        machines = (machine(), scrub.build(PUBLIC, home=HOME, logins=("user", "git")))
        for n in range(3000):
            parts = [rng.choice(pieces) for _ in range(rng.randint(2, 7))]
            x = parts[0]
            for p in parts[1:]:
                x += rng.choice(seps) + p
            self.check(machines[n % 2], x)

    def test_detect_kinds(self):
        m = machine()
        self.assertEqual(scrub.detect("at /zqvroot", m), ["path"])
        self.assertEqual(scrub.detect("plain words", m), [])
        kinds = scrub.detect("a /zqvroot is %s" % LOGIN, m)
        self.assertEqual(kinds, ["path", "user"])
        self.assertTrue(all(MARK not in k for k in kinds))


class CleanTest(unittest.TestCase):
    """Line 9: 4(e)."""

    def test_line9(self):
        m = machine()
        raw = "zqv 50%\rdone 100%\n\x1b[2Kok \x1b[31mred\x1b[0m\tx" + "".join(
            ["​", "‌", "‍", "⁠", "﻿", "‮"]) + "y"
        self.assertEqual(scrub.clean(raw), "zqv 50%\ndone 100%\nok red xy")
        self.assertIn("control", scrub.detect(raw, m))
        self.assertEqual(scrub.clean("a\r\nb c d️e"), "a\nb\nc de")
        self.assertEqual(scrub.clean(FULL_WIDTH), LOGIN)


class StrikeTest(unittest.TestCase):
    """Line 10: the user's own removals."""

    def test_line10(self):
        text = "<path-1> holds the details; Art beside artisan, 1 of 12, path again"
        out, places = scrub.strike(text, ["path", "details", "1", "art"])
        self.assertEqual(out, "<path-1> holds the <struck-2>; <struck-4> beside artisan, "
                              "<struck-3> of 12, <struck-1> again")
        self.assertEqual(places, 4)
        out, _ = scrub.strike("MyPATHway <struck-7>", ["path"], start=2)
        self.assertEqual(out, "My<struck-8>way <struck-7>")
        out, _ = scrub.strike("x", ["path"], start=5)
        self.assertEqual(out, "x")


class MachineTest(unittest.TestCase):
    """Line 11, and `machine`'s reads in a temp home."""

    TERMS = ("zqvalpha", "zqvbeta.example", "zqv-gamma")

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = os.path.realpath(tmp.name)
        stubs = os.path.join(self.home, "stubs")
        os.mkdir(stubs)
        git = os.path.join(stubs, "git")
        with open(git, "w") as fh:
            fh.write('#!/bin/sh\ncase "$*" in\n*user.name*) echo "Zqvfirst Zqvsecond";;\n'
                     '*user.email*) echo "zqvmail%szqvmail.example";;\nesac\n' % AT)
        os.chmod(git, 0o755)
        self.repo = os.path.join(self.home, "work", "zqvcheckout")
        os.makedirs(os.path.join(self.repo, ".git"))
        os.makedirs(os.path.join(self.repo, "sub"))
        conf = os.path.join(self.home, ".config", "agentik", "suite")
        os.makedirs(conf)
        with open(os.path.join(conf, "config.yaml"), "w") as fh:
            fh.write("checkouts:\n  - ~/elsewhere/zqvother\n")
        self.private = os.path.join(self.home, "private.tsv")
        with open(self.private, "w") as fh:
            fh.write("person\tzqvalpha\ndomain\tzqvbeta\\.example\nprivate\tzqv-gamma\n")
        self.env = {"HOME": self.home, "USER": LOGIN, "PATH": stubs + ":/usr/bin:/bin",
                    "XDG_CONFIG_HOME": os.path.join(self.home, ".config"),
                    "AGENTIK_HYGIENE_PRIVATE": self.private, "ZQV_API_TOKEN": "zqv" + rand(16),
                    "ZQV_SHORT_KEY": "short"}

    def test_reads(self):
        m = scrub.machine(self.env, os.path.join(self.repo, "sub"), PUBLIC, logins=("zqvextra",))
        text = ("%s and zqvextra on %s/zqvf in zqvcheckout and zqvother; Zqvfirst Zqvsecond "
                "zqvmail%szqvmail.example %s; short stays") % (
                    LOGIN, self.home, AT, self.env["ZQV_API_TOKEN"])
        out = scrub.scrub(text, m)[0]
        self.assertNotIn(MARK, out.lower(), out)
        self.assertIn("short stays", out)
        self.assertEqual(scrub.detect(out, m), [])

    def test_line11_no_private_term(self):
        m = scrub.machine(self.env, self.repo, PUBLIC)
        self.assertNotIn("zqv", repr(m.get("private")))
        text = "met zqvalpha at zqvbeta.example on zqv-gamma; ZQVALPHA again"
        out, counts, spans = scrub.scrub(text, m)
        kinds = scrub.detect(text, m)
        struck = scrub.strike(out, ["met"])
        for term in self.TERMS:
            for value in (out, counts, spans, kinds, struck, scrub.weak(m)):
                self.assertNotIn(term, repr(value).lower())
        self.assertEqual(out, "met <private-1> at <private-2> on <private-3>; <private-1> again")

    def test_line11_unreadable(self):
        with open(self.private, "wb") as fh:
            fh.write(b"person\tzqvalpha\n\xff\xfe zqvbeta\n")
        with self.assertRaises(scrub.PrivateUnreadable) as caught:
            scrub.machine(self.env, self.repo, PUBLIC)
        with open(self.private, "w") as fh:
            fh.write("person\tzqvalpha\nno tab zqvbeta here\n")
        with self.assertRaises(scrub.PrivateUnreadable) as caught2:
            scrub.machine(self.env, self.repo, PUBLIC)
        for exc in (caught.exception, caught2.exception):
            for term in self.TERMS + ("zqvbeta",):
                self.assertNotIn(term, str(exc))
                self.assertNotIn(term, repr(exc.args))

    def test_no_list(self):
        env = dict(self.env, AGENTIK_HYGIENE_PRIVATE=os.path.join(self.home, "absent.tsv"))
        self.assertEqual(scrub.machine(env, self.repo, PUBLIC)["private"], "none")


class ModuleTest(unittest.TestCase):
    """R1: the module's imports, and it writes to no stream."""

    def test_r1_imports(self):
        tree = ast.parse(MODULE.read_text(), feature_version=(3, 9))
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods |= {a.name for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                mods |= {"." * node.level + (node.module or "") + ":" + a.name for a in node.names}
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotEqual(node.func.id, "print")
        self.assertEqual(mods, {"agentik_hygiene", "os", "re", "subprocess", "unicodedata",
                                ".:settings"})



# Review 1's findings (R1-F1 to R1-F7, and its note on `Authorization:`). Every private piece
# is assembled here at run time; the cases are the review's probes with `zqv` markers.
GH = "https://github.com/acmeorg/agentik-widget"


def token():
    return "gh" + "p_" + rand(36)


def private_rows(*terms):
    return [("client", re.compile(re.escape(t), re.I)) for t in terms]


class Review1Case(unittest.TestCase):
    """What every new case holds: nothing private is left, the scrub is its own fixed point,
    `detect` finds nothing in what it gives, and `detect` and `scrub` agree on the raw line."""

    def closes(self, m, raw, gone=(), keep=()):
        out = scrub.scrub(raw, m)[0]
        self.assertNotIn(MARK, out.lower(), out)
        for word in gone:
            self.assertNotIn(word.lower(), out.lower(), out)
        for word in keep:
            self.assertIn(word, out)
        self.assertEqual(scrub.scrub(out, m)[0], out, repr(raw))
        self.assertEqual(scrub.detect(out, m), [], repr(raw))
        self.assertEqual(scrub.detect(raw, m) == [], out == raw, repr(raw))
        return out


class R1F1Test(Review1Case):
    """R1-F1: of a kept URL only the prefix through the repo's name is sealed; its path, query
    and fragment go through every later step, and `detect` reads them too."""

    def test_r1f1_public_url_tail(self):
        import urllib.parse
        m = machine(private=private_rows("zqvacme"))
        tok = token()
        mail = "zqvperson" + AT + "zqvcorp.example"
        cases = [
            (GH + "/issues?access_token=" + tok, [tok]),
            (GH + "/issues/new?body=%s/code/zqvsecretrepo/x" % HOME, []),
            (GH + "/issues/new?body=" + urllib.parse.quote(HOME + "/code/zqvsecretrepo", safe=""), []),
            (GH + "/issues?q=involves:" + mail, []),
            (GH + "/pulls?q=author:" + LOGIN, []),
            (GH + "#zqvhost", []),
            (GH + "/issues?q=zqvacme", []),
            (GH + "/issues/3);zqvacme", []),
            (GH + "/blob/main/x" + USERS + "/zqvother/code/zqvrepo", []),
        ]
        for raw, gone in cases:
            with self.subTest(raw=raw[len(GH):len(GH) + 14]):
                out = self.closes(m, "see " + raw, gone, keep=["see " + GH])
                self.assertNotEqual(out, "see " + raw)

    def test_r1f1_issue_url_still_kept(self):
        m = machine()
        for raw in (GH + "/issues/12", GH + "/pull/7/files#diff-3", GH + ".git", GH + "/issues?q=is:open"):
            with self.subTest(raw=raw):
                self.assertEqual(scrub.scrub("see %s." % raw, m)[0], "see %s." % raw)
                self.assertEqual(scrub.detect("see %s." % raw, m), [])


class R1F2Test(Review1Case):
    """R1-F2: a kept tree and a schema word are sealed against the path step alone; a version
    takes no letters glued after its numbers."""

    def test_r1f2_kept_tree_tail_read(self):
        m = machine(private=private_rows("zqvacme"))
        cache = "~/.claude/plugins/cache/agentik/widget/"
        share = "%s/.local/share/agentik-widget/0a1b2c3d/" % HOME
        tok = token()
        cases = [
            (cache + "1.2.3/notes/zqvacme-plan.md", [], cache + "1.2.3/notes/"),
            (share + LOGIN + "-notes/x", [], "~/.local/share/agentik-widget/0a1b2c3d/"),
            (share + tok, [tok], "~/.local/share/agentik-widget/0a1b2c3d/"),
            ("agentik-zqvacme/1", [], "agentik-"),
            (cache + "1.0.0/link" + USERS + "/zqvother/code/zqvrepo", [], cache + "1.0.0/link"),
        ]
        for raw, gone, keep in cases:
            with self.subTest(raw=raw[-20:]):
                self.closes(m, "at %s ok" % raw, gone, keep=[keep])

    def test_r1f2_version_takes_no_letters(self):
        m = machine()
        cache = "~/.claude/plugins/cache/agentik/widget/"
        for tail in ("1.0.0-zqvacme/x", "1.0.0zqvacme" + USERS + "/zqvlogin", "1.2.3zqv"):
            with self.subTest(tail=tail):
                out = self.closes(m, "at %s%s ok" % (cache, tail))
                self.assertEqual(out, "at <path-1> ok")
        for kept in ("1.2.3", "1.2.3/bin/run", "3f9a2b7c1d4e", "1.2.3-4"):
            with self.subTest(kept=kept):
                self.assertEqual(scrub.scrub("at %s%s ok" % (cache, kept), m)[0], "at %s%s ok" % (cache, kept))


if __name__ == "__main__":
    unittest.main()
