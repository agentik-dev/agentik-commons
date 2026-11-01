"""The `agentik` marketplace (agentik-r1 5.2): the committed file passes
scripts/marketplace-check, each broken shape exits 1, usage exits 2, and
`make local-marketplace` writes the same entries with file:// urls into a
scratch folder, less the `suite` entry, plus an overlay's further entries, which
`--local` holds to the five's shape. The published file holds the five tools and
suite (hq design/04 section 5), suite on commons' own url and `plugins/suite`.
Every overlay is the test's own; nothing reads the network."""
import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "marketplace-check"
FILE = ROOT / ".claude-plugin" / "marketplace.json"
TOOLS = ["agents", "decisions", "relay", "respeak", "session"]
SIX = sorted(TOOLS + ["suite"])
SUITE_SOURCE = {"source": "git-subdir", "path": "plugins/suite",
                "url": "https://github.com/agentik-dev/agentik-commons.git"}


def check(*args, cwd=ROOT):
    p = subprocess.run([str(CHECK), *args], capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


class MarketplaceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = json.loads(FILE.read_text())

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, data, name="m.json"):
        path = os.path.join(self.tmp.name, name)
        Path(path).write_text(data if isinstance(data, str) else json.dumps(data))
        return path

    def test_committed_file_is_valid(self):
        code, out, err = check()
        self.assertEqual((code, err), (0, ""))
        self.assertIn("valid", out)
        self.assertEqual(self.data["name"], "agentik")
        self.assertEqual(sorted(p["name"] for p in self.data["plugins"]), SIX)
        self.assertEqual(self.data["plugins"][-1]["name"], "suite")  # after the five
        for p in self.data["plugins"]:
            self.assertEqual(p["source"], SUITE_SOURCE if p["name"] == "suite" else {
                "source": "git-subdir", "path": "plugin",
                "url": "https://github.com/agentik-dev/agentik-%s.git" % p["name"]})
            self.assertLess(len(p["description"]), 200)
        self.assertTrue(out.endswith(", 6 plugins, valid\n"), out)

    def on_file_urls(self):
        """The five, on file:// urls, as `make local-marketplace` writes them."""
        data = copy.deepcopy(self.data)
        data["plugins"] = [p for p in data["plugins"] if p["name"] != "suite"]
        for p in data["plugins"]:
            p["source"]["url"] = Path("/code dir", "agentik-" + p["name"]).as_uri()
        return data

    def test_the_suite_entry_each_break_is_one_line(self):
        at = len(self.data["plugins"]) - 1
        suite = lambda d: d["plugins"][at]
        cases = {
            "missing": (lambda d: d["plugins"].pop(at), "plugins lacks suite"),
            "url": (lambda d: suite(d)["source"].update(
                url="https://github.com/agentik-dev/agentik-suite.git"),
                "plugins[5] (suite): source.url is not the public url for agentik-commons"),
            "path": (lambda d: suite(d)["source"].update(path="plugin"),
                     "plugins[5] (suite): source.path is not 'plugins/suite'"),
            "version": (lambda d: suite(d).update(version="0.1"),
                        "plugins[5] (suite): version is not semver"),
        }
        for name, (mutate, line) in cases.items():
            code, out, err = self.broken(mutate)
            self.assertEqual((code, out), (1, ""), name)
            self.assertEqual(len(err.splitlines()), 1, (name, err))
            self.assertTrue(err.rstrip("\n").endswith(": " + line), (name, err))
        # under --local suite is absent; present, it is one line, the rest valid
        data = self.on_file_urls()
        code, out, err = check("--local", self.write(data))
        self.assertEqual((code, err), (0, ""))
        self.assertTrue(out.endswith(", 5 plugins, valid\n"), out)
        entry = copy.deepcopy(self.data["plugins"][at])
        entry["source"]["url"] = Path("/code dir", "agentik-suite").as_uri()
        data["plugins"].append(entry)
        code, out, err = check("--local", self.write(data))
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(len(err.splitlines()), 1, err)
        self.assertTrue(err.rstrip("\n").endswith(
            ": plugins[5] (suite): suite is in a local file; this Mac installs the tools by name"), err)

    def broken(self, mutate):
        data = copy.deepcopy(self.data)
        mutate(data)
        return check(self.write(data))

    def test_each_broken_shape_exits_one(self):
        cases = {
            "name": lambda d: d.update(name="agentik-dev"),
            "owner": lambda d: d.pop("owner"),
            "four": lambda d: d["plugins"].pop(),
            "six": lambda d: d["plugins"].append(copy.deepcopy(d["plugins"][0])),
            "dup": lambda d: d["plugins"][1].update(name=d["plugins"][0]["name"]),
            "unknown": lambda d: d["plugins"][0].update(name="nosuch"),
            "kind": lambda d: d["plugins"][0]["source"].update(source="github"),
            "url": lambda d: d["plugins"][0]["source"].update(
                url=d["plugins"][1]["source"]["url"]),
            "http": lambda d: d["plugins"][0]["source"].update(
                url=d["plugins"][0]["source"]["url"].replace("https:", "http:")),
            "file": lambda d: d["plugins"][0]["source"].update(url="file:///x/agentik-session"),
            "path": lambda d: d["plugins"][0]["source"].update(path="."),
            "string": lambda d: d["plugins"][0].update(source="./plugin"),
            "version": lambda d: d["plugins"][0].update(version="1.2"),
            "noversion": lambda d: d["plugins"][0].pop("version"),
            "list": lambda d: d.update(plugins={}),
        }
        for name, mutate in cases.items():
            code, out, err = self.broken(mutate)
            self.assertEqual((code, out), (1, ""), name)
            self.assertTrue(err.startswith("marketplace-check: "), name)
        self.assertEqual(check(self.write("{"))[0], 1)
        self.assertEqual(check(self.write("[]"))[0], 1)

    def test_local_wants_file_urls(self):
        self.assertEqual(check("--local", str(FILE))[0], 1)
        data = self.on_file_urls()
        path = self.write(data)
        self.assertEqual(check("--local", path)[0], 0)
        self.assertEqual(check(path)[0], 1)
        data["plugins"][0]["source"]["url"] = "file://host/x/agentik-" + data["plugins"][0]["name"]
        self.assertEqual(check("--local", self.write(data))[0], 1)

    def test_local_takes_a_well_formed_extra_entry(self):
        data = self.on_file_urls()
        data["plugins"].append({
            "name": "extra", "description": "A made-up plugin.", "version": "0.1.0",
            "source": {"source": "git-subdir", "path": "plugin",
                       "url": Path("/code dir", "agentik-extra").as_uri()}})
        code, out, err = check("--local", self.write(data))
        self.assertEqual((code, err), (0, ""))
        self.assertTrue(out.endswith(", 6 plugins, valid\n"), out)
        self.assertEqual(check(self.write(data))[0], 1)  # the published file: the six only
        cases = {
            "https": lambda e: e["source"].update(
                url="https://github.com/agentik-dev/agentik-extra.git"),
            "path": lambda e: e["source"].update(path="."),
            "kind": lambda e: e["source"].update(source="github"),
            "segment": lambda e: e["source"].update(url="file:///code/agentik-other"),
            "version": lambda e: e.update(version="1.2"),
            "name": lambda e: e.update(name="Extra"),
            "repeat": lambda e: (e.update(name="session"), e["source"].update(
                url="file:///code/agentik-session")),
        }
        for name, mutate in cases.items():
            broken = copy.deepcopy(data)
            mutate(broken["plugins"][-1])
            code, out, err = check("--local", self.write(broken))
            self.assertEqual((code, out), (1, ""), name)
            self.assertTrue(err.startswith("marketplace-check: "), name)
        del data["plugins"][0]  # the five are still required
        self.assertEqual(check("--local", self.write(data))[0], 1)

    def test_usage_exits_two(self):
        for args in (("--bogus",), ("a", "b"), ("--local", "--local"),
                     (os.path.join(self.tmp.name, "missing.json"),)):
            code, out, _ = check(*args)
            self.assertEqual((code, out), (2, ""), args)
        self.assertEqual(check("--help")[0], 0)
        merge = subprocess.run([str(ROOT / "scripts" / "local-marketplace"), "a", "b", "c"],
                               capture_output=True, text=True)
        self.assertEqual((merge.returncode, merge.stdout), (2, ""))

    def make_local(self, overlay):
        """`make local-marketplace` with every input under the temp dir, the
        owner's overlay never among them."""
        out = os.path.join(self.tmp.name, "market")
        code_dir = os.path.join(self.tmp.name, "code")
        p = subprocess.run(["make", "-s", "-C", str(ROOT), "local-marketplace",
                            "AGENTIK_MARKETPLACE_DIR=" + out, "AGENTIK_CODE=" + code_dir,
                            "AGENTIK_MARKETPLACE_OVERLAY=" + overlay],
                           capture_output=True, text=True)
        return p, Path(out, ".claude-plugin", "marketplace.json"), code_dir

    def test_make_local_marketplace_absent_overlay(self):
        p, path, code_dir = self.make_local(os.path.join(self.tmp.name, "none.json"))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(p.stdout.endswith(", 5 plugins, valid\n"), p.stdout)
        written = json.loads(path.read_text())
        urls = {p["name"]: p["source"]["url"] for p in written["plugins"]}
        self.assertEqual(urls, {t: Path(code_dir, "agentik-" + t).as_uri() for t in TOOLS})
        # today's output, byte for byte: the published file, less suite, with file:// urls
        expected = copy.deepcopy(self.data)
        expected["plugins"] = [p for p in expected["plugins"] if p["name"] != "suite"]
        for p in expected["plugins"]:
            p["source"]["url"] = urls[p["name"]]
        self.assertEqual(path.read_bytes(), (json.dumps(expected, indent=2) + "\n").encode())

    def test_make_local_marketplace_overlay_adds_extra(self):
        extra = {"name": "extra", "source": {
                     "source": "git-subdir", "path": "plugin",
                     "url": "https://github.com/agentik-dev/agentik-extra.git"},
                 "description": "A made-up plugin whose repo is not public.",
                 "version": "0.1.0"}
        p, path, code_dir = self.make_local(self.write({"plugins": [extra]}, "overlay.json"))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(p.stdout.endswith(", 6 plugins, valid\n"), p.stdout)
        plugins = json.loads(path.read_text())["plugins"]
        self.assertEqual(len(plugins), 6)
        self.assertEqual(plugins[5]["source"]["url"], Path(code_dir, "agentik-extra").as_uri())
        for p in plugins:
            p["source"]["url"] = "https://github.com/agentik-dev/agentik-%s.git" % p["name"]
        five = [p for p in self.data["plugins"] if p["name"] != "suite"]
        self.assertEqual(plugins, five + [extra])  # the five unchanged, suite left out

    def test_make_local_marketplace_bad_overlay_fails(self):
        p, path, _ = self.make_local(os.path.join(self.tmp.name, "none.json"))
        self.assertEqual(p.returncode, 0, p.stderr)
        before = path.read_bytes()
        os.mkdir(os.path.join(self.tmp.name, "dir.json"))
        unwritten = {
            "not JSON": self.write("{", "o1.json"),
            "no plugins": self.write({"plugin": []}, "o2.json"),
            "a list": self.write([], "o3.json"),
            "plugins an object": self.write({"plugins": {}}, "o4.json"),
            "unreadable": os.path.join(self.tmp.name, "dir.json"),
        }
        for name, overlay in unwritten.items():
            p, _, _ = self.make_local(overlay)
            self.assertNotEqual(p.returncode, 0, name)
            self.assertIn("local-marketplace: ", p.stderr, name)
            self.assertEqual(path.read_bytes(), before, name)  # nothing new written
        session = next(e for e in self.data["plugins"] if e["name"] == "session")
        p, _, _ = self.make_local(self.write({"plugins": [session]}, "o5.json"))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("plugin name session appears 2 times", p.stderr)

    def test_overlay_nan_refused(self):
        extra = {"name": "extra", "description": "@", "version": "0.1.0",
                 "source": {"source": "git-subdir", "path": "plugin",
                            "url": "https://github.com/agentik-dev/agentik-extra.git"}}
        described = json.dumps(self.data["plugins"][0]["description"])
        for constant in ("NaN", "Infinity", "-Infinity"):
            text = json.dumps({"plugins": [extra]}).replace('"@"', constant)
            p, path, _ = self.make_local(self.write(text, "overlay.json"))
            self.assertNotEqual(p.returncode, 0, constant)
            self.assertIn("local-marketplace: ", p.stderr, constant)
            self.assertIn("not JSON", p.stderr, constant)
            self.assertFalse(path.parent.exists(), constant)  # no folder made
            published = json.dumps(self.data).replace(described, constant, 1)
            code, out, err = check(self.write(published))
            self.assertEqual((code, out), (1, ""), constant)
            self.assertIn("not JSON", err, constant)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root reads a mode-000 folder")
    def test_overlay_in_an_unreadable_folder_refused(self):
        locked = os.path.join(self.tmp.name, "locked")
        os.mkdir(locked)
        extra = {"name": "extra", "description": "A made-up plugin.", "version": "0.1.0",
                 "source": {"source": "git-subdir", "path": "plugin",
                            "url": "https://github.com/agentik-dev/agentik-extra.git"}}
        overlay = self.write({"plugins": [extra]}, os.path.join("locked", "overlay.json"))
        os.chmod(locked, 0)
        try:
            p, path, _ = self.make_local(overlay)
        finally:
            os.chmod(locked, 0o755)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("local-marketplace: cannot read ", p.stderr)
        self.assertFalse(path.parent.exists())  # no folder made


if __name__ == "__main__":
    unittest.main()
