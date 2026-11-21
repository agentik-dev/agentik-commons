"""Packet rr7-way-in: a repo with a regular file LICENSE at its root gets CONTRIBUTING.md and
SECURITY.md from commons' templates/, listed like any copy; one with none gets neither, as at
the pin; commons carries its own two, equal to the templates."""
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts" / "sync"
PAGES = ("CONTRIBUTING.md", "SECURITY.md")
SCRIPTS = ["scripts/agentik", "scripts/hygiene", "scripts/recordlint", "scripts/readme-top",
           "scripts/bounded", "scripts/plugin-version-check", "scripts/plugin-description-bytes"]
PLUGIN = ["plugin/lib/agentik_install.py", "plugin/lib/agentik_records.py",
          "plugin/lib/agentik_term/__init__.py", "plugin/lib/agentik_term/term.py",
          "plugin/lib/agentik_term/catalogue.py", "plugin/bin/agentik-x", "plugin/bin/agentik"]


def run(*args):
    p = subprocess.run([str(SYNC), *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def template(page):
    return Path(ROOT, "templates", page).read_bytes()


def listed(repo):
    rows = Path(repo, "scripts", "vendored.sha256").read_text().splitlines()
    return [r.split("  ", 1)[1] for r in rows]


class WayInTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = os.path.realpath(self.tmp.name)

    def repo(self, name, licence="file", plugin=None):
        """A made-up checkout: licence is "file", "none", "folder" or "symlink"; plugin is
        None, "lib" (a plugin/lib/ naming the tool x) or "bare" (a plugin/ with no lib/)."""
        repo = os.path.join(self.base, name)
        os.mkdir(repo)
        subprocess.run(["git", "-C", repo, "init", "-q"], check=True)
        lic = Path(repo, "LICENSE")
        if licence == "file":
            lic.write_text("A made-up licence.\n")
        elif licence == "folder":
            lic.mkdir()
        elif licence == "symlink":
            Path(repo, "COPYING").write_text("A made-up licence.\n")
            lic.symlink_to("COPYING")
        if plugin:
            manifest = Path(repo, "plugin", ".claude-plugin", "plugin.json")
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"name": "x", "version": "1.2.3"}))
            if plugin == "lib":
                Path(repo, "plugin", "lib").mkdir()
        return repo

    def test_a_licensed_target_gets_both_pages(self):
        for plugin, rest in ((None, []), ("lib", PLUGIN), ("bare", [])):
            with self.subTest(plugin=plugin):
                repo = self.repo("tool %s" % plugin, plugin=plugin)
                code, out, err = run(repo)
                self.assertEqual((code, err), (0, ""))
                rows = Path(repo, "scripts", "vendored.sha256").read_text().splitlines()
                for page in PAGES:
                    placed = Path(repo, page)
                    self.assertEqual(placed.read_bytes(), template(page), page)
                    self.assertEqual(placed.stat().st_mode & 0o777, 0o644, page)
                    self.assertIn("%s  %s" % (hashlib.sha256(template(page)).hexdigest(), page), rows)
                self.assertEqual(listed(repo), [*SCRIPTS, *PAGES, *rest])
                self.assertEqual(subprocess.run(["shasum", "-a", "256", "-c", "scripts/vendored.sha256"],
                                                capture_output=True, cwd=repo).returncode, 0)
                # nothing else at the root, no scratch file left
                top = {".git", "LICENSE", "scripts", *PAGES} | ({"plugin"} if plugin else set())
                self.assertEqual(set(os.listdir(repo)), top)
                self.assertEqual(run("--check", repo), (0, "sync: %s: every copy is commons'\n" % repo, ""))

    def test_check_says_behind_a_page(self):
        repo = self.repo("tool repo", plugin="lib")
        self.assertEqual(run(repo)[0], 0)
        Path(repo, "CONTRIBUTING.md").unlink()
        self.assertEqual(run("--check", repo), (1, "behind CONTRIBUTING.md\n", ""))
        self.assertEqual(run(repo)[0], 0)
        sec = Path(repo, "SECURITY.md")
        sec.write_bytes(sec.read_bytes() + b"Write to a made-up address.\n")
        self.assertEqual(run("--check", repo), (1, "behind SECURITY.md\n", ""))
        Path(repo, "CONTRIBUTING.md").unlink()
        self.assertEqual(run("--check", repo), (1, "behind CONTRIBUTING.md\nbehind SECURITY.md\n", ""))
        self.assertEqual(run(repo)[0], 0)
        Path(repo, "SECURITY.md").chmod(0o755)
        self.assertEqual(run("--check", repo), (1, "behind SECURITY.md\n", ""))
        self.assertEqual(run(repo)[0], 0)
        self.assertEqual(run("--check", repo)[0], 0)

    def test_no_licence_is_the_pins(self):
        for licence in ("none", "folder", "symlink"):
            for plugin, rest in ((None, []), ("lib", PLUGIN)):
                with self.subTest(licence=licence, plugin=plugin):
                    repo = self.repo("tool %s %s" % (licence, plugin), licence=licence, plugin=plugin)
                    code, out, err = run(repo)
                    self.assertEqual((code, err), (0, ""))
                    for page in PAGES:
                        self.assertFalse(os.path.lexists(os.path.join(repo, page)), page)
                    self.assertEqual(listed(repo), [*SCRIPTS, *rest])
                    self.assertEqual(run("--check", repo), (0, "sync: %s: every copy is commons'\n" % repo, ""))
                    # a page placed by hand is the repo's own, never read
                    Path(repo, "SECURITY.md").write_text("A made-up page of its own.\n")
                    self.assertEqual(run("--check", repo)[0], 0)

    def test_commons_own_pages_are_the_templates(self):
        for page in PAGES:
            self.assertEqual(Path(ROOT, page).read_bytes(), template(page), page)

    def test_the_templates_name_nothing(self):
        for page in PAGES:
            text = template(page).decode("utf-8")
            with self.subTest(page=page):
                self.assertTrue(text.endswith("\n") and not text.endswith("\n\n"))
                for word in ("@", "http", "agentik", "github", "www.", ".com", "mailto"):
                    self.assertNotIn(word, text.lower())
        self.assertIn("private report form", template("SECURITY.md").decode())
        self.assertIn("The way in is an issue.", template("CONTRIBUTING.md").decode())
        # placed at a tool's root, the pages need no allow row: commons' scanner on a checkout
        # that holds only them, its private list a made-up one, finds nothing
        repo = self.repo("scanned", licence="none")
        for page in PAGES:
            Path(repo, page).write_bytes(template(page))
        private = Path(self.base, "private.tsv")
        private.write_text("person\tMadeup Ownername\n")
        env = dict(os.environ, AGENTIK_HYGIENE_PRIVATE=str(private))
        p = subprocess.run([str(ROOT / "scripts" / "hygiene"), "--require-private"], cwd=repo,
                           capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("hits outside allowlist: 0", p.stdout)


if __name__ == "__main__":
    unittest.main()
