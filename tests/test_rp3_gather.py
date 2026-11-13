"""The issue's facts (packet rp3-gather): `public.json`, the tools an issue may name, held equal
to the marketplace file, and `gather`, a closed list of typed facts read once. Each run is in
the suite tests' temp HOME, with a stub `claude` that records its argv outside HOME and prints a
version; every tool name here is made up, but the pin of line 1, which reads the repo's own two
files. Nothing here reads the real home or writes outside its temp folders."""
import inspect
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import LIB, ROOT, Home, writes_outside_term  # noqa: E402
from agentik_suite import gather  # noqa: E402

MARKET = "market-x"
PUBLIC = {"marketplace": MARKET, "tools": {"suite": "example-org/kit", "alpha": "example-org/alpha-repo",
                                           "beta": "example-org/beta-repo"}}
OUTSIDE = "quillfeather"  # a tool outside the public table, which no value may name
CLAUDE = '#!/bin/sh\necho "$*" >> "%s"\necho "9.8.7 (Claude Code)"\n'
GIVEN = {"tool": None, "ran": None, "exit": None, "output": None, "expected": None}
SHA = "0123456789abcdef0123456789abcdef01234567"


def check(name, status, detail="all well"):
    return {"name": name, "status": status, "detail": detail, "remedy": None}


def doctor(*groups, schema="agentik.doctor/1"):
    return {"schema": schema, "ok": True, "failed": 0, "warned": 0,
            "tools": [{"name": name, "checks": list(found)} for name, found in groups]}


def repo_of(url):
    path = urlparse(url).path.strip("/")
    return path[:-len(".git")] if path.endswith(".git") else path


class GatherHome(Home):
    def setUp(self):
        Home.setUp(self)
        side = tempfile.TemporaryDirectory()
        self.addCleanup(side.cleanup)
        self.side = os.path.realpath(side.name)
        self.calls = os.path.join(self.side, "calls")
        self.stub("claude", CLAUDE % self.calls)
        self.lib = os.path.join(self.side, "lib")
        os.mkdir(self.lib)
        self.public(PUBLIC)

    def public(self, table):
        with open(os.path.join(self.lib, "public.json"), "w") as fh:
            json.dump(table, fh)

    def installed(self, entries):
        """Claude Code's installed_plugins.json: {key: (version, sha)}."""
        folder = os.path.join(self.home, ".claude", "plugins")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "installed_plugins.json"), "w") as fh:
            json.dump({"version": 2, "plugins": {
                key: [{"scope": "user", "version": ver, "gitCommitSha": sha,
                       "installPath": os.path.join(self.home, "inst", key)}]
                for key, (ver, sha) in entries.items()}}, fh)

    def gather(self, given=None, read=None, calls=("--version",), **more):
        """facts in process, held to line 11: HOME unchanged, the stub's calls exactly `calls`."""
        before = self.snapshot()
        if os.path.exists(self.calls):
            os.remove(self.calls)
        start = time.monotonic()
        found = gather.facts(self.env(**more), self.lib, dict(GIVEN, **(given or {})), lambda: read)
        self.elapsed = time.monotonic() - start
        self.assertEqual(self.snapshot(), before)
        try:
            with open(self.calls) as fh:
                seen = fh.read().splitlines()
        except FileNotFoundError:
            seen = []
        self.assertEqual(seen, list(calls))
        return found


class PublicTest(unittest.TestCase):
    """Line 1: public.json is the marketplace file's name and each plugin's OWNER/REPO."""

    def test_public_equals_the_marketplace(self):
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        want = {"marketplace": market["name"],
                "tools": {p["name"]: repo_of(p["source"]["url"]) for p in market["plugins"]}}
        self.assertEqual(gather.load_public(str(LIB)), want)

    def test_other_shapes_raise(self):
        bad = [dict(PUBLIC, extra=1), {"marketplace": MARKET, "tools": {"alpha": "a/b/c"}},
               {"marketplace": MARKET}, {"marketplace": MARKET, "tools": {"alpha": "a"}},
               {"marketplace": MARKET, "tools": {"Alpha!": "a/b"}}, [], "x",
               {"marketplace": 3, "tools": {"alpha": "a/b"}}]
        for table in bad:
            with tempfile.TemporaryDirectory() as lib:
                with open(os.path.join(lib, "public.json"), "w") as fh:
                    json.dump(table, fh)
                with self.assertRaises(ValueError, msg=table):
                    gather.load_public(lib)
        with tempfile.TemporaryDirectory() as lib:
            with self.assertRaises(ValueError):
                gather.load_public(lib)


class HygieneTest(unittest.TestCase):
    """Line 2: the scan's sibling count outside the allowlist stays 0, public.json allowed."""

    def test_sibling_outside_is_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = os.path.join(tmp, "private.tsv")
            open(empty, "w").close()
            env = {"HOME": tmp, "PATH": "/usr/bin:/bin", "AGENTIK_HYGIENE_PRIVATE": empty}
            p = subprocess.run([str(ROOT / "scripts" / "hygiene"), "--json"], cwd=str(ROOT),
                               capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(json.loads(p.stdout)["groups"]["sibling"]["outside_lines"], 0, p.stderr)

    def test_the_row_is_needed_and_placed(self):
        import agentik_hygiene
        text = (LIB / "public.json").read_text()
        sibling = dict(agentik_hygiene.COMPILED)["sibling"]
        self.assertTrue(sibling.search(text))
        rows = [l for l in (ROOT / ".hygiene-allow").read_text().splitlines()
                if l and not l.startswith("#")]
        at = rows.index("plugins/suite/lib/fallback.json: sibling")
        self.assertEqual(rows[at + 1], "plugins/suite/lib/public.json: sibling")


class ModuleTest(unittest.TestCase):
    """R1, R3, R6: the module prints nothing, takes no cwd, and names no tool."""

    def test_prints_nothing_and_takes_no_cwd(self):
        path = LIB / "agentik_suite" / "gather.py"
        source = path.read_text()
        self.assertEqual(writes_outside_term(source), [])
        self.assertNotIn(".text(", source)
        self.assertEqual(list(inspect.signature(gather.facts).parameters),
                         ["env", "lib", "given", "read_doctor"])

    def test_no_public_name_here_or_there(self):
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        names = [p["name"] for p in market["plugins"] if p["name"] != "suite"]
        for path in (LIB / "agentik_suite" / "gather.py", os.path.abspath(__file__)):
            with open(path) as fh:
                text = fh.read().lower()
            for name in names:
                self.assertNotRegex(text, r"\b%s\b" % name, path)


class ChecksTest(GatherHome):
    def test_line3_thirty_fails_bound(self):
        fails = [check("fail %d" % i, "fail", "broken %d" % i) for i in range(28)]
        fails.append(check("n" * 300, "fail", "short"))
        fails.append(check("long", "fail", "é" * 2500))
        read = doctor(("suite", [check("warn first", "warn")] + fails + [check("fine", "ok")]),
                      ("alpha", [check("w2", "warn"), check("ok2", "ok"), check("n2", "note")]))
        f = self.gather(read=read)
        rows = f["checks"]["rows"]
        self.assertEqual([r["status"] for r in rows], ["fail"] * 30 + ["warn"] * 2)
        self.assertIn("é" * 2500, [r["detail"] for r in rows])
        b = gather.bound(f)
        self.assertEqual(len(b["checks"]["rows"]), 12)
        self.assertEqual({r["status"] for r in b["checks"]["rows"]}, {"fail"})
        for r in b["checks"]["rows"]:
            self.assertLessEqual(len(r["name"].encode()), 60)
            self.assertLessEqual(len(r["detail"].encode()), 200)
            r["detail"].encode().decode("utf-8")
        alone = dict(f, checks=dict(f["checks"], rows=[r for r in rows if r["name"] == "long"]))
        self.assertEqual(gather.bound(alone)["checks"]["rows"][0]["detail"], "é" * 100)
        named = dict(f, checks=dict(f["checks"], rows=[r for r in rows if r["detail"] == "short"]))
        self.assertEqual(gather.bound(named)["checks"]["rows"][0]["name"], "n" * 60)
        self.assertEqual((b["checks"]["failed"], b["checks"]["warned"], b["checks"]["passed"]),
                         (30, 2, 3))
        self.assertTrue(b["checks"]["read"])

    def test_line4_a_tool_outside_public(self):
        read = doctor(("suite", [check("door", "ok")]),
                      (OUTSIDE, [check("%s broke" % OUTSIDE, "fail", "%s: no" % OUTSIDE),
                                 check("ok", "ok")]),
                      ("alpha", [check("a", "fail")]))
        f = self.gather(read=read, given={"tool": OUTSIDE})
        self.assertNotIn(OUTSIDE, json.dumps(f))
        self.assertEqual((f["checks"]["failed"], f["checks"]["warned"], f["checks"]["passed"]),
                         (1, 0, 3))
        self.assertEqual([r["tool"] for r in f["checks"]["rows"]], ["alpha"])
        self.assertIsNone(f["tool"])

    def test_an_unlisted_key_reaches_nothing(self):
        mark = "unlisted-%d" % random.randrange(10 ** 9)
        read = doctor(("alpha", [dict(check("a", "fail"), extra=mark, remedy=mark)]))
        read["extra"] = mark
        read["tools"][0]["extra"] = mark
        f = self.gather(read=read)
        self.assertNotIn(mark, json.dumps(f))
        self.assertEqual(set(f["checks"]["rows"][0]), {"tool", "status", "name", "detail"})

    def test_line10_no_object_or_another_schema(self):
        self.installed({"alpha@" + MARKET: ("1.2.3", SHA)})
        good = self.gather(read=doctor(("alpha", [check("a", "fail")])))
        for read in (None, doctor(("alpha", [check("a", "fail")]), schema="agentik.doctor/2"),
                     ["x"], {"schema": "agentik.doctor/1", "tools": "x"}):
            f = self.gather(read=read)
            if read is not None and isinstance(read, dict) and read.get("tools") == "x":
                continue
            self.assertFalse(f["checks"]["read"], read)
            self.assertEqual(f["checks"]["rows"], [])
            self.assertEqual({k: v for k, v in f.items() if k != "checks"},
                             {k: v for k, v in good.items() if k != "checks"})


class VersionsTest(GatherHome):
    def test_versions_order_and_types(self):
        self.installed({"suite@" + MARKET: ("0.6.1", SHA), "alpha@" + MARKET: ("1.2.3-rc.4", SHA.upper())})
        self.stub("agentik", "#!/bin/sh\nVERSION=0.6.1\n")
        self.stub("agentik-suite", "#!/bin/sh\nVERSION=0.6.1-alpha.3\n")
        f = self.gather()
        self.assertEqual([v["name"] for v in f["versions"]], ["suite", "door", "alpha", "beta"])
        by = {v["name"]: v for v in f["versions"]}
        self.assertEqual(by["suite"], {"name": "suite", "plugin": "0.6.1", "commit": SHA[:12],
                                       "launcher": "0.6.1-alpha.3"})
        self.assertEqual(by["door"], {"name": "door", "plugin": None, "commit": None, "launcher": "0.6.1"})
        self.assertEqual(by["alpha"]["plugin"], "1.2.3-rc.4")
        self.assertEqual(by["alpha"]["commit"], SHA[:12])
        self.assertEqual(by["beta"], {"name": "beta", "plugin": None, "commit": None, "launcher": None})

    def test_line6_unreadable(self):
        self.installed({"beta@" + MARKET: ("q" * 60, "not-a-sha"), "alpha@" + MARKET: ("1.2.3-feature.1", SHA[:8])})
        self.stub("agentik-alpha", "#!/bin/sh\nVERSION=my-feature-branch\n")
        os.mkdir(os.path.join(self.stubs, "agentik-beta"))  # a folder is no launcher
        f = self.gather()
        by = {v["name"]: v for v in f["versions"]}
        self.assertEqual(by["alpha"]["launcher"], "unreadable")
        self.assertEqual((by["alpha"]["plugin"], by["alpha"]["commit"]), ("unreadable", "unreadable"))
        self.assertEqual((by["beta"]["plugin"], by["beta"]["commit"]), ("unreadable", "unreadable"))
        self.assertIsNone(by["beta"]["launcher"])
        self.assertEqual({p["name"]: p["version"] for p in f["plugins"]["named"]},
                         {"alpha": "unreadable", "beta": "unreadable"})


class PluginsTest(GatherHome):
    def test_line5_outside_counted_never_named(self):
        self.installed({"alpha@" + MARKET: ("1.0.0", SHA), "%s@%s" % (OUTSIDE, MARKET): ("2.0.0", SHA)})
        f = self.gather()
        self.assertEqual(f["plugins"], {"named": [{"name": "alpha", "version": "1.0.0"}], "others": 1})
        self.assertNotIn(OUTSIDE, json.dumps(f))

    def test_another_marketplace_is_not_public(self):
        self.installed({"alpha@elsewhere": ("1.0.0", SHA), "beta@" + MARKET: ("1.0.0", SHA)})
        f = self.gather()
        self.assertEqual(f["plugins"], {"named": [{"name": "beta", "version": "1.0.0"}], "others": 1})
        self.assertNotIn("elsewhere", json.dumps(f))

    def test_twelve_named_at_most(self):
        tools = {"t%02d" % i: "example-org/t%02d" % i for i in range(15)}
        self.public({"marketplace": MARKET, "tools": tools})
        self.installed({"%s@%s" % (t, MARKET): ("1.0.0", SHA) for t in tools})
        f = self.gather()
        self.assertEqual(len(f["plugins"]["named"]), 12)
        self.assertEqual(f["plugins"]["others"], 3)


class PrivacyTest(GatherHome):
    def test_line7_marker_nowhere(self):
        mark = "mk%d" % random.randrange(10 ** 12)
        folder = os.path.join(self.side, "work-" + mark)
        os.mkdir(folder)
        with open(os.path.join(folder, "CLAUDE.md"), "w") as fh:
            fh.write("# %s\n" % mark)
        os.makedirs(os.path.join(self.home, ".claude"), exist_ok=True)
        with open(os.path.join(self.home, ".claude", "settings.json"), "w") as fh:
            json.dump({"env": {"X": mark}, "model": mark}, fh)
        self.installed({"alpha@" + MARKET: ("1.0.0", SHA)})
        here = os.getcwd()
        os.chdir(folder)
        self.addCleanup(os.chdir, here)
        path = "%s:%s:%s" % (self.stubs, os.path.join(self.side, mark), "/usr/bin:/bin")
        f = self.gather(read=doctor(("alpha", [check("a", "fail")])), SOME_VALUE=mark, PATH=path,
                        CLAUDECODE="1", CLAUDE_CODE_SESSION=mark)
        self.assertNotIn(mark, json.dumps(f))
        self.assertEqual(f["system"]["where"], "in Claude Code")


class OutputTest(GatherHome):
    def test_line8_three_mib(self):
        out = os.path.join(self.side, "out.log")
        known = "the known last line"
        with open(out, "wb") as fh:
            row = b"x" * 299 + b"\n"
            for _ in range(3 * 1024 * 1024 // len(row) + 1):
                fh.write(row)
            fh.write(b"\xff\xfe broken bytes\n" + known.encode() + b"\n")
        self.assertGreaterEqual(os.path.getsize(out), 3 * 1024 * 1024)
        f = self.gather(given={"output": out, "ran": "make thing", "exit": 2, "expected": "it works"})
        lines = f["output"]["lines"]
        self.assertEqual(len(lines), 200)
        self.assertEqual(lines[-1], known)
        self.assertIn("�� broken bytes", lines)
        self.assertEqual((f["output"]["ran"], f["output"]["exit"], f["words"]["expected"]),
                         ("make thing", 2, "it works"))
        self.assertNotIn(out, json.dumps(f))
        b = gather.bound(f)
        self.assertEqual(len(b["output"]["lines"]), 20)
        self.assertEqual(b["output"]["lines"][-1], known)
        for line in b["output"]["lines"]:
            self.assertLessEqual(len(line.encode()), 200)

    def test_line8_a_cut_never_inside_a_placeholder(self):
        f = self.gather(given={"ran": "r" * 195 + "<path-12>" + "tail", "expected": "é" * 400})
        f["output"]["lines"] = ["x" * 195 + "<path-12>" + "tail", "y" * 191 + "<path-12>", "€" * 100]
        b = gather.bound(f)
        self.assertEqual(b["output"]["lines"], ["x" * 195, "y" * 191 + "<path-12>", "€" * 66])
        self.assertEqual(b["output"]["ran"], "r" * 195)
        self.assertEqual(b["words"]["expected"], "é" * 300)

    def test_exit_bounds_and_a_missing_file(self):
        for code, want in ((0, 0), (255, 255), (256, None), (-1, None), (True, None), ("2", None)):
            f = self.gather(given={"exit": code, "output": os.path.join(self.side, "none")})
            self.assertEqual(f["output"]["exit"], want, code)
            self.assertEqual(f["output"]["lines"], [])

    def test_map_free_order(self):
        f = self.gather(read=doctor(("alpha", [check("n1", "warn", "d1"), check("n2", "fail", "d2")])),
                        given={"ran": "r", "expected": "e"})
        f["output"]["lines"] = ["l1", "l2"]
        seen = []
        g = gather.map_free(f, lambda v: seen.append(v) or v.upper())
        self.assertEqual(seen, ["n2", "d2", "n1", "d1", "r", "l1", "l2", "e"])
        self.assertEqual(g["checks"]["rows"][0], {"tool": "alpha", "status": "fail", "name": "N2", "detail": "D2"})
        self.assertEqual(g["output"]["lines"], ["L1", "L2"])
        self.assertEqual(f["output"]["lines"], ["l1", "l2"])
        self.assertEqual(g["system"], f["system"])


class SystemTest(GatherHome):
    def test_line9_where_and_claude(self):
        f = self.gather(CLAUDECODE="1")
        self.assertEqual(f["system"]["where"], "in Claude Code")
        self.assertEqual(f["system"]["claude"], "9.8.7")
        f = self.gather()
        self.assertEqual(f["system"]["where"], "at a terminal")
        s = f["system"]
        self.assertIn(s["os"], ("Darwin", "Linux", "other"))
        self.assertIn(s["arch"], ("arm64", "x86_64", "aarch64", "other"))
        self.assertRegex(s["release"], r"\A[0-9.]{1,20}\Z")
        self.assertEqual(s["python"], "%d.%d.%d" % sys.version_info[:3])
        self.assertEqual(f["schema"], "agentik.issue-facts/1")

    def test_line9_no_claude(self):
        os.remove(os.path.join(self.stubs, "claude"))
        f = self.gather(calls=())
        self.assertEqual(f["system"]["claude"], "unreadable")
        self.assertLess(self.elapsed, 6)

    def test_a_slow_claude(self):
        self.stub("claude", '#!/bin/sh\necho "$*" >> "%s"\nsleep 30\n' % self.calls)
        f = self.gather()
        self.assertEqual(f["system"]["claude"], "unreadable")
        self.assertLess(self.elapsed, 6)


if __name__ == "__main__":
    unittest.main()
