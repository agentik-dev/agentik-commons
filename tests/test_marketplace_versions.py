"""scripts/marketplace-versions: each marketplace line against its checkout's
plugin.json under AGENTIK_CODE: all matching exits 0, one line per entry that
trails, leads or differs exits 1, an absent checkout is skipped with a note,
--if-complete compares nothing while one is absent, and usage or an unreadable
marketplace exits 2. Every checkout is a temp folder; no real one is read, and
nothing reads the network."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "marketplace-versions"
FILE = ROOT / ".claude-plugin" / "marketplace.json"
BASE = {k: v for k, v in os.environ.items() if k != "AGENTIK_CODE"}


class MarketplaceVersionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.code = os.path.join(self.tmp.name, "code dir")
        os.mkdir(self.code)

    def tearDown(self):
        self.tmp.cleanup()

    def run_it(self, *args, script=SCRIPT, cwd=None, code=True):
        env = dict(BASE, AGENTIK_CODE=self.code) if code else BASE
        p = subprocess.run([str(script), *args], capture_output=True, text=True,
                           cwd=cwd or self.tmp.name, env=env)
        return p.returncode, p.stdout, p.stderr

    def market(self, entries, name="m.json"):
        """A marketplace of {name: version}; its path."""
        path = os.path.join(self.tmp.name, name)
        Path(path).write_text(json.dumps({"name": "agentik", "plugins": [
            {"name": n, "version": v} for n, v in entries.items()]}))
        return path

    def checkout(self, name, version, root=None):
        d = Path(root or self.code, "agentik-" + name, "plugin", ".claude-plugin")
        d.mkdir(parents=True, exist_ok=True)
        if version is not None:
            (d / "plugin.json").write_text(json.dumps({"name": name, "version": version}))

    def test_all_matching_exits_zero(self):
        versions = {"alpha": "1.0.0", "beta": "2.0.0-alpha.18", "gamma": "0.1.3"}
        for n, v in versions.items():
            self.checkout(n, v)
        code, out, err = self.run_it(self.market(versions))
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(len(out.splitlines()), 1)
        self.assertIn("3 compared", out)
        self.assertEqual(self.run_it("--if-complete", self.market(versions))[:3:2], (0, ""))

    def test_each_trailing_leading_or_differing_entry_is_one_line(self):
        cases = {  # name: (the marketplace line, plugin.json, the verb)
            "alpha": ("1.0.0", "1.1.0", "trails"),
            "beta": ("2.0.0-alpha.9", "2.0.0-alpha.10", "trails"),  # numeric, not lexical
            "gamma": ("2.0.0", "2.0.0-alpha.3", "leads"),  # a release leads its alphas
            "delta": ("1.0.0+b1", "1.0.0+b2", "differs from"),
            "epsilon": ("v1", "1.0.0", "differs from"),
            "zeta": ("3.1.4", "3.1.4", None),
        }
        for n, (_, plugin, _) in cases.items():
            self.checkout(n, plugin)
        path = self.market({n: line for n, (line, _, _) in cases.items()})
        code, out, err = self.run_it(path)
        self.assertEqual((code, out), (1, ""))
        lines = err.splitlines()
        self.assertEqual(len(lines), 5)
        for line, (n, (mline, plugin, verb)) in zip(lines, cases.items()):
            self.assertEqual(line, "marketplace-versions: %s: %s: the marketplace line %s %s "
                             "plugin.json's %s" % (path, n, mline, verb, plugin))

    def test_an_absent_checkout_is_skipped_with_a_note(self):
        self.checkout("alpha", "1.0.0")
        path = self.market({"alpha": "1.0.0", "beta": "9.9.9"})
        code, out, err = self.run_it(path)
        self.assertEqual(code, 0)
        self.assertIn("1 compared", out)
        self.assertIn("1 skipped", out)
        self.assertEqual(len(err.splitlines()), 1)
        self.assertIn("beta: no checkout at", err)
        self.assertIn("skipped", err)
        # the compare still runs on the present ones
        self.checkout("alpha", "1.0.1")
        self.assertEqual(self.run_it(path)[0], 1)

    def test_if_complete_compares_only_when_every_checkout_is_present(self):
        self.checkout("alpha", "1.0.1")
        path = self.market({"alpha": "1.0.0", "beta": "2.0.0"})
        code, out, err = self.run_it("--if-complete", path)
        self.assertEqual((code, out), (0, ""))
        self.assertEqual(len(err.splitlines()), 1)
        self.assertIn("1 of 2 checkouts absent", err)
        self.assertIn("not compared", err)
        self.checkout("beta", "2.0.0")
        code, out, err = self.run_it("--if-complete", path)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("alpha: the marketplace line 1.0.0 trails", err)

    def test_a_present_checkout_without_a_version_exits_one(self):
        for text in (None, "{", '{"version": 2}', "[]"):
            shutil.rmtree(os.path.join(self.code, "agentik-alpha"), ignore_errors=True)
            self.checkout("alpha", None)
            if text is not None:
                Path(self.code, "agentik-alpha", "plugin", ".claude-plugin",
                     "plugin.json").write_text(text)
            code, out, err = self.run_it(self.market({"alpha": "1.0.0"}))
            self.assertEqual((code, out), (1, ""), text)
            self.assertIn("holds no readable version", err, text)

    def test_an_entry_with_no_valid_name_or_version_exits_one(self):
        self.checkout("alpha", "1.0.0")
        Path(self.code, "x").mkdir()
        for entry in ({"name": "../x", "version": "1.0.0"}, {"version": "1.0.0"}, "alpha",
                      {"name": "alpha"}, {"name": "alpha", "version": 1}):
            path = os.path.join(self.tmp.name, "bad.json")
            Path(path).write_text(json.dumps({"plugins": [entry]}))
            code, out, err = self.run_it(path)
            self.assertEqual((code, out, len(err.splitlines())), (1, "", 1), entry)

    def test_usage_and_an_unreadable_marketplace_exit_two(self):
        path = self.market({"alpha": "1.0.0"})
        for args in (("--bogus",), (path, path), ("--if-complete", "--if-complete", path),
                     (os.path.join(self.tmp.name, "missing.json"),)):
            code, out, _ = self.run_it(*args)
            self.assertEqual((code, out), (2, ""), args)
        for text in ("{", "[]", '{"plugins": {}}'):
            Path(path).write_text(text)
            self.assertEqual(self.run_it(path)[:2], (2, ""), text)
        self.assertEqual(self.run_it("--help")[0], 0)

    def test_code_defaults_to_the_parent_folder_of_the_repo(self):
        # a copy of this repo's script in a temp commons, beside a temp checkout
        commons = Path(self.tmp.name, "commons")
        (commons / "scripts").mkdir(parents=True)
        (commons / ".claude-plugin").mkdir()
        shutil.copy2(SCRIPT, commons / "scripts" / "marketplace-versions")
        (commons / ".claude-plugin" / "marketplace.json").write_text(
            json.dumps({"plugins": [{"name": "alpha", "version": "1.0.0"}]}))
        self.checkout("alpha", "1.0.0", root=self.tmp.name)
        code, out, err = self.run_it(script=commons / "scripts" / "marketplace-versions",
                                     cwd=commons, code=False)
        self.assertEqual((code, err), (0, ""))
        self.assertIn("1 compared", out)

    def test_make_versions_and_the_check_guard(self):
        # temp checkouts at the committed marketplace's versions, then one drifted
        for p in json.loads(FILE.read_text())["plugins"]:
            self.checkout(p["name"], p["version"])
        make = ["make", "-s", "-C", str(ROOT), "AGENTIK_CODE=" + self.code]
        p = subprocess.run(make + ["versions"], capture_output=True, text=True, env=BASE)
        self.assertEqual((p.returncode, p.stderr), (0, ""))
        first = json.loads(FILE.read_text())["plugins"][0]
        self.checkout(first["name"], first["version"] + "-1")
        p = subprocess.run(make + ["versions"], capture_output=True, text=True, env=BASE)
        self.assertEqual(p.returncode, 2)  # make's own exit for a failed recipe
        self.assertIn("%s: the marketplace line" % first["name"], p.stderr)
        p = subprocess.run(make + ["-n", "check"], capture_output=True, text=True, env=BASE)
        self.assertIn("scripts/marketplace-versions --if-complete", p.stdout)

    def test_shape(self):
        self.assertTrue(SCRIPT.read_text().startswith("#!/usr/bin/env python3\n"))
        self.assertTrue(os.access(SCRIPT, os.X_OK))


if __name__ == "__main__":
    unittest.main()
