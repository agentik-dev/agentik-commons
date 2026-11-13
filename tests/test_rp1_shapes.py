"""scripts/hygiene's `secret` group knows the token shapes an issue could carry (packet
rp1-shapes), and plugins/suite/lib/agentik_hygiene.py is its byte copy, imported, never run.
Every token here is random and assembled at run time from parts, so no literal in this file is
a token and the scan of this tree stays clean. The scans run in temp repos with a made-up
private list; nothing here writes outside its temp folder."""
import base64
import json
import os
import random
import string
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hygiene"
LIB = ROOT / "plugins" / "suite" / "lib"
COPY = LIB / "agentik_hygiene.py"
ALNUM = string.ascii_letters + string.digits
URLSAFE = ALNUM + "_-"
RNG = random.SystemRandom()


def rand(n, alphabet=ALNUM):
    return "".join(RNG.choice(alphabet) for _ in range(n))


def b64(obj):
    raw = json.dumps(obj, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def jwt_body():
    """A JWT less its first three letters: header, payload and signature, all made up."""
    head = b64({"alg": "HS256", "typ": "JWT"})
    body = b64({"sub": rand(12), "iat": RNG.randrange(10 ** 9, 2 * 10 ** 9)})
    return head[3:] + "." + body + "." + rand(43, URLSAFE)


def shapes():
    """(name, prefix, body): R1's shapes, each prefix split so its letters never sit whole here."""
    gh = [("github " + c, "gh" + c + "_", rand(36)) for c in "ousr"]
    slack = [("slack " + c, "xo" + "x" + c + "-",
              rand(12, string.digits) + "-" + rand(12, string.digits) + "-" + rand(24))
             for c in "baprs"]
    return gh + [("jwt", "ey" + "J", jwt_body())] + slack + [
        ("openai", "s" + "k-", rand(48)),
        ("openai project", "s" + "k-" + "pro" + "j-", rand(120, URLSAFE)),
        ("google", "AI" + "za", rand(35, URLSAFE)),
        ("npm", "np" + "m_", rand(36)),
        ("gitlab", "gl" + "pat-", rand(20, URLSAFE)),
        ("hugging face", "h" + "f_", rand(34, string.ascii_letters)),
    ]


# Twelve lines of prose and code: a prefix's letters inside a longer word, or a short body.
PROSE = [
    "    def test_" + "gh" + "s_tokens_are_scrubbed(self):",
    "the kios" + "k-modeconfigurationsettingsfile is read at start",
    "export np" + "m_config_registry=https://registry.example.test/",
    "set the xo" + "xb-token in the bot's settings",
    "pinned at version gh" + "o_1.2.3 of the action",
    "a gl" + "pat-placeholder stands in the form",
    "uses the h" + "f_transfer-for-downloads switch",
    "the key opens AI" + "zaShortKey123 and stops",
    "header only: " + b64({"alg": "none"}),
    "the s" + "k-pro" + "j-alpha slug names a folder",
    "gh" + "r_ is the prefix of a refresh token",
    "an s" + "k-learn-compatible-estimator-interface",
]


def secret_lines(text):
    """The scanner's `secret` count over one file holding `text`, in a temp repo."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, "repo")
        os.mkdir(repo)
        subprocess.run(["git", "-C", repo, "init", "-q"], check=True, capture_output=True)
        Path(repo, "note.txt").write_text(text)
        private = os.path.join(tmp, "private.tsv")
        Path(private).write_text("domain\tquuxvill[e]\\.example\n")
        env = dict(os.environ, AGENTIK_HYGIENE_PRIVATE=private)
        p = subprocess.run([str(SCRIPT), "--json", "--repo", repo],
                           capture_output=True, text=True, env=env)
        assert p.stderr == "", p.stderr
        return json.loads(p.stdout)["groups"]["secret"]["outside_lines"], p.stdout


class ShapesTest(unittest.TestCase):
    """Acceptance 1 and 2: each shape is one hit, cut short it is none; prose is none."""

    def test_each_shape_is_a_hit_and_short_is_not(self):
        for name, prefix, body in shapes():
            with self.subTest(shape=name):
                token = prefix + body
                count, out = secret_lines("value: " + token + " end\n")
                self.assertEqual(count, 1, name)
                self.assertNotIn(token, out)
                count, _ = secret_lines("value: " + prefix + body[:8] + " end\n")
                self.assertEqual(count, 0, name)

    def test_prose_and_code_are_no_hit(self):
        self.assertEqual(len(PROSE), 12)
        count, _ = secret_lines("\n".join(PROSE) + "\n")
        self.assertEqual(count, 0)


def secret_rx():
    """The scanner's `secret` regex, loaded in-process from scripts/hygiene."""
    loader = SourceFileLoader("hygiene_rp1_fix", str(SCRIPT))
    mod = module_from_spec(spec_from_loader(loader.name, loader))
    keep, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = keep
    return dict(mod.COMPILED)["secret"]


# Where a token sits in a line: (name, before, after). `\\n` is two characters, a JSON
# escape as a transcript holds it; `%3D` is a percent-encoded `=`.
CONTEXTS = [
    ("bare", "value: ", " end"),
    ("json", '{"key": "', '"}'),
    ("bearer", "Authorization: Bearer ", ""),
    ("assign", "TOKEN=", ""),
    ("json escape n", '{"text": "line one\\n', '"}'),
    ("json escape r", '{"text": "line one\\r', '"}'),
    ("json escape t", '{"text": "col one\\t', '"}'),
    ("percent 3D", "https://example.test/cb?token%3D", "&x=1"),
    ("percent 3d", "https://example.test/cb?token%3d", "&x=1"),
    ("underscore", "export my_", ""),
    ("digit", "id 1", ""),
]


class ContextTest(unittest.TestCase):
    """Review 1's R1-F1: each shape counts in every context, and a prefix inside a word
    still does not."""

    def test_each_shape_in_each_context_is_a_hit(self):
        rx = secret_rx()
        lines = []
        for name, prefix, body in shapes():
            for where, before, after in CONTEXTS:
                line = before + prefix + body + after
                lines.append(line)
                with self.subTest(shape=name, context=where):
                    self.assertTrue(rx.search(line), (name, where))
        count, _ = secret_lines("\n".join(lines) + "\n")
        self.assertEqual(count, len(lines))
        self.assertEqual(len(lines), 16 * len(CONTEXTS))

    def test_a_prefix_inside_a_word_is_still_no_hit(self):
        rx = secret_rx()
        words = [
            "the kios" + "k-" + rand(30),
            "the tas" + "k-pro" + "j-" + rand(30, URLSAFE),
            "a wis" + "h" + "f_" + rand(34, string.ascii_letters),
            "the des" + "k-" + rand(24),
        ]
        for line in words:
            with self.subTest(line=line[:12]):
                self.assertIsNone(rx.search(line))


class CopyTest(unittest.TestCase):
    """Acceptance 4 and 5, R4 and R5: the byte copy, imported, never run."""

    def test_copy_is_byte_equal_and_not_executable(self):
        self.assertEqual(COPY.read_bytes(), SCRIPT.read_bytes())
        self.assertEqual(COPY.stat().st_mode & 0o111, 0)

    def test_copy_imports_with_its_names_and_no_stderr(self):
        line = ("import sys; sys.path.insert(0, %r); import agentik_hygiene as h; "
                "print(len(h.COMPILED)); print(callable(h.private_path), callable(h.load_private))"
                % str(LIB))
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        p = subprocess.run(["/usr/bin/python3", "-c", line], capture_output=True, text=True,
                           env=env, cwd=tempfile.gettempdir())
        self.assertEqual((p.returncode, p.stdout, p.stderr), (0, "6\nTrue True\n", ""))

    def test_copy_gives_the_scanners_tables(self):
        sys.path.insert(0, str(LIB))
        keep, sys.dont_write_bytecode = sys.dont_write_bytecode, True
        try:
            import agentik_hygiene as h
        finally:
            sys.path.remove(str(LIB))
            sys.dont_write_bytecode = keep
        self.assertEqual([name for name, _ in h.COMPILED],
                         ["home", "lan", "sibling", "secret", "email", "renamed"])
        token = "gh" + "o_" + rand(36)
        self.assertTrue(dict(h.COMPILED)["secret"].search("x " + token))


if __name__ == "__main__":
    unittest.main()
