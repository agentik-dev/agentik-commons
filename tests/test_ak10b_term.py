"""Packet ak10b-term: scripts/sync places the writer `term` and its catalogue in a tool as the
package plugin/lib/agentik_term/ (byte-equal copies, listed in scripts/vendored.sha256) and seeds
the tool's own messages.md once, with each id term.py names and commons' text for it.

Every tree here is a temp git checkout with a made-up tool; no real tool repo is synced.
"""
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts" / "sync"
SUITE_LIB = ROOT / "plugins" / "suite" / "lib"
WRITER = SUITE_LIB / "agentik_suite"
PKG = "plugin/lib/agentik_term"
COPIES = ["scripts/agentik", "scripts/hygiene", "scripts/recordlint", "scripts/readme-top",
          "scripts/bounded", "scripts/plugin-version-check", "scripts/plugin-description-bytes"]
SOURCES = {"scripts/agentik": "bin/agentik"}
PYTHON = "/usr/bin/python3" if os.access("/usr/bin/python3", os.X_OK) else sys.executable


def run_sync(repo, sync=SYNC):
    p = subprocess.run([str(sync), str(repo)], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def verify(repo):
    p = subprocess.run(["shasum", "-a", "256", "-c", "scripts/vendored.sha256"],
                       capture_output=True, text=True, cwd=repo)
    return p.returncode, p.stdout


def items(path):
    """{id: the whole line} of a catalogue's items, as catalogue.ITEM reads them."""
    found = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("- `") and "`: " in line:
            found[line[3:line.index("`: ")]] = line
    return found


def named_ids():
    """Each message id term.py names itself: a string given first to text, line, hint or error."""
    tree = ast.parse((WRITER / "term.py").read_text(encoding="utf-8"))
    return {node.args[0].value for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("text", "line", "hint", "error") and node.args
            and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)}


def seed_problems(seed):
    """What the seed lacks or holds wrong against term.py's ids and commons' messages.md."""
    have, commons = items(seed), items(WRITER / "messages.md")
    out = []
    for mid in sorted(named_ids()):
        if mid not in have:
            out.append("%s: not in the seed" % mid)
        elif have[mid] != commons.get(mid):
            out.append("%s: %r, commons has %r" % (mid, have[mid], commons.get(mid)))
    return out


class Tree(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.top = Path(os.path.realpath(self.tmp.name))
        self.repo = self.top / "demo tool"
        self.repo.mkdir()
        subprocess.run(["git", "-C", str(self.repo), "init", "-q"], check=True)
        manifest = self.repo / "plugin" / ".claude-plugin" / "plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"name": "demo", "version": "0.1.0"}))
        self.lib = self.repo / "plugin" / "lib"
        self.lib.mkdir()

    def files(self):
        return {str(p.relative_to(self.repo)) for p in self.repo.rglob("*")
                if ".git" not in p.parts and p.is_file()}


class R5(Tree):
    PROBE = r'''import sys
lib, commons = sys.argv[1], sys.argv[2]
sys.path.insert(0, lib)
assert not any(p == commons or p.startswith(commons + "/") for p in sys.path), sys.path
try:
    import agentik_suite
    raise SystemExit("agentik_suite is importable")
except ImportError:
    pass
from agentik_term import term
assert term.__file__.startswith(lib + "/"), term.__file__
assert term.catalogue.PATH == lib + "/agentik_term/messages.md", term.catalogue.PATH
t = term.Term(env={})
t.line("demo.hello", who="a reader")
t.error("demo.hello", next_="agentik demo doctor", who="a refusal")
'''

    def probe(self):
        home = self.top / "home"
        home.mkdir(exist_ok=True)
        return subprocess.run([PYTHON, "-I", "-c", self.PROBE, str(self.lib), str(ROOT / "plugins")],
                              capture_output=True, text=True, cwd=str(home),
                              env={"HOME": str(home), "PATH": "/usr/bin:/bin"})

    def test_r5_the_writer_works_in_a_made_up_tool(self):
        code, out, err = run_sync(self.repo)
        self.assertEqual((code, err), (0, ""))
        for name in ("term.py", "catalogue.py"):
            self.assertEqual((self.repo / PKG / name).read_bytes(), (WRITER / name).read_bytes(), name)
        self.assertTrue((self.repo / PKG / "__init__.py").is_file())
        code, listed = verify(self.repo)
        self.assertEqual(code, 0, listed)
        for name in ("__init__.py", "term.py", "catalogue.py"):
            self.assertIn("%s/%s: OK" % (PKG, name), listed)
        self.assertNotIn("messages.md", (self.repo / "scripts/vendored.sha256").read_text())
        self.assertIn("lib/agentik_term/__init__.py, lib/agentik_term/term.py, "
                      "lib/agentik_term/catalogue.py", out)
        messages = self.repo / PKG / "messages.md"
        with open(messages, "a", encoding="utf-8") as fh:
            fh.write("- `demo.hello`: hello, `{who}`\n")
        p = self.probe()
        self.assertEqual((p.returncode, p.stdout, p.stderr),
                         (0, "hello, a reader\n", "FAIL  hello, a refusal\nnext: agentik demo doctor\n"))
        # a second sync restores a copy changed by a byte and keeps the tool's own catalogue
        placed = self.repo / PKG / "term.py"
        good = placed.read_bytes()
        placed.write_bytes(good[:-1] + bytes([good[-1] ^ 1]))
        self.assertNotEqual(verify(self.repo)[0], 0)
        kept = messages.read_bytes()
        self.assertEqual(run_sync(self.repo)[0], 0)
        self.assertEqual(placed.read_bytes(), good)
        self.assertEqual(messages.read_bytes(), kept)
        self.assertEqual(verify(self.repo)[0], 0)
        self.assertEqual(self.probe().returncode, 0)


class R4(Tree):
    def test_r4_the_seed_holds_each_id_term_names_with_commons_text(self):
        self.assertIn("err.next", named_ids())
        self.assertEqual(run_sync(self.repo)[0], 0)
        seed = self.repo / PKG / "messages.md"
        self.assertEqual(seed_problems(seed), [])
        lines = seed.read_text(encoding="utf-8").splitlines()
        self.assertTrue(lines[0].startswith("# "), lines[0])
        self.assertEqual(set(items(seed)), named_ids())

    def test_r4_the_check_sees_an_id_taken_out(self):
        self.assertEqual(run_sync(self.repo)[0], 0)
        seed = self.repo / PKG / "messages.md"
        seed.write_text("".join(line for line in seed.read_text(encoding="utf-8").splitlines(True)
                                if not line.startswith("- `err.next`")), encoding="utf-8")
        self.assertEqual(seed_problems(seed), ["err.next: not in the seed"])
        seed.write_text(seed.read_text(encoding="utf-8") + "- `err.next`: next `{command}`\n",
                        encoding="utf-8")
        self.assertEqual(len(seed_problems(seed)), 1)

    def test_r4_a_seed_id_commons_lacks_writes_nothing(self):
        # a copy of commons' sync and its sources, its messages.md lacking err.next
        fake = self.top / "commons copy"
        for rel in ["scripts/sync", "bin/agentik", "scripts/agentik_install.py", "scripts/plugin-launcher",
                    *[c for c in COPIES if c not in SOURCES], "plugins/suite/lib/agentik_suite/term.py",
                    "plugins/suite/lib/agentik_suite/catalogue.py"]:
            (fake / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, fake / rel)
        text = (WRITER / "messages.md").read_text(encoding="utf-8")
        (fake / "plugins/suite/lib/agentik_suite/messages.md").write_text(
            "".join(line for line in text.splitlines(True) if not line.startswith("- `err.next`")),
            encoding="utf-8")
        before = self.files()
        code, out, err = run_sync(self.repo, fake / "scripts" / "sync")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("err.next", err)
        self.assertEqual(self.files(), before)


class R3(Tree):
    def expected(self):
        return "".join("%s  %s\n" % (hashlib.sha256((ROOT / SOURCES.get(c, c)).read_bytes()).hexdigest(), c)
                       for c in COPIES)

    def test_r3_no_plugin_lib_gets_nothing_new(self):
        shutil.rmtree(self.lib)
        code, out, err = run_sync(self.repo)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual((self.repo / "scripts/vendored.sha256").read_text(), self.expected())
        self.assertNotIn("agentik_term", out)
        self.assertFalse(any("agentik_term" in f for f in self.files()))

    def test_r3_no_plugin_at_all_gets_nothing_new(self):
        shutil.rmtree(self.repo / "plugin")
        self.assertEqual(run_sync(self.repo)[0], 0)
        self.assertEqual((self.repo / "scripts/vendored.sha256").read_text(), self.expected())
        self.assertEqual(self.files(), {*COPIES, "scripts/vendored.sha256"})


if __name__ == "__main__":
    unittest.main()
