"""The `agentik` marketplace (agentik-r1 5.2): the committed file passes
scripts/marketplace-check, each broken shape exits 1, usage exits 2, and
`make local-marketplace` writes the same entries with file:// urls into a
scratch folder, plus an overlay's further entries, which `--local` holds to the
five's shape. Every overlay is the test's own; nothing reads the network."""
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
        self.assertEqual(sorted(p["name"] for p in self.data["plugins"]), TOOLS)
        for p in self.data["plugins"]:
            self.assertEqual(p["source"], {
                "source": "git-subdir", "path": "plugin",
                "url": "https://github.com/agentik-dev/agentik-%s.git" % p["name"]})
            self.assertLess(len(p["description"]), 200)

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
        data = copy.deepcopy(self.data)
        for p in data["plugins"]:
            p["source"]["url"] = Path("/code dir", "agentik-" + p["name"]).as_uri()
        path = self.write(data)
        self.assertEqual(check("--local", path)[0], 0)
        self.assertEqual(check(path)[0], 1)
        data["plugins"][0]["source"]["url"] = "file://host/x/agentik-" + data["plugins"][0]["name"]
        self.assertEqual(check("--local", self.write(data))[0], 1)

    def test_local_takes_a_well_formed_extra_entry(self):
        data = copy.deepcopy(self.data)
        for p in data["plugins"]:
            p["source"]["url"] = Path("/code dir", "agentik-" + p["name"]).as_uri()
        data["plugins"].append({
            "name": "extra", "description": "A made-up plugin.", "version": "0.1.0",
            "source": {"source": "git-subdir", "path": "plugin",
                       "url": Path("/code dir", "agentik-extra").as_uri()}})
        code, out, err = check("--local", self.write(data))
        self.assertEqual((code, err), (0, ""))
        self.assertTrue(out.endswith(", 6 plugins, valid\n"), out)
        self.assertEqual(check(self.write(data))[0], 1)  # the published file: the five only
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
        # today's output, byte for byte: the published file with file:// urls
        expected = copy.deepcopy(self.data)
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
        self.assertEqual(plugins, self.data["plugins"] + [extra])  # the five unchanged

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


if __name__ == "__main__":
    unittest.main()
