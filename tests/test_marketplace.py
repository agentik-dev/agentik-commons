"""The `agentik` marketplace (agentik-r1 5.2): the committed file passes
scripts/marketplace-check, each broken shape exits 1, usage exits 2, and
`make local-marketplace` writes the same entries with file:// urls into a
scratch folder. Nothing reads the network."""
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

    def test_usage_exits_two(self):
        for args in (("--bogus",), ("a", "b"), ("--local", "--local"),
                     (os.path.join(self.tmp.name, "missing.json"),)):
            code, out, _ = check(*args)
            self.assertEqual((code, out), (2, ""), args)
        self.assertEqual(check("--help")[0], 0)

    def test_make_local_marketplace(self):
        out = os.path.join(self.tmp.name, "market")
        code_dir = os.path.join(self.tmp.name, "code")
        p = subprocess.run(["make", "-s", "-C", str(ROOT), "local-marketplace",
                            "AGENTIK_MARKETPLACE_DIR=" + out, "AGENTIK_CODE=" + code_dir],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        written = json.loads(Path(out, ".claude-plugin", "marketplace.json").read_text())
        urls = {p["name"]: p["source"]["url"] for p in written["plugins"]}
        self.assertEqual(urls, {t: Path(code_dir, "agentik-" + t).as_uri() for t in TOOLS})
        # the same file otherwise: names, versions, paths and the rest match
        for p in written["plugins"]:
            p["source"]["url"] = "https://github.com/agentik-dev/agentik-%s.git" % p["name"]
        self.assertEqual(written, self.data)


if __name__ == "__main__":
    unittest.main()
