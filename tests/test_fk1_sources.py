"""Row fk1-sources: one finder says what stands for a tool and which file runs, and `agentik-suite
describe sources --json [TOOL]` gives its answer. Each home is fk_homes' in a temp HOME; the read
starts no process; made-up names."""
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fk_homes import HOMES, T, build  # noqa: E402
from test_agentik_suite import LAUNCHER, LIB  # noqa: E402

U, F = T + "@agentik", T + "@acme-tools"
# home: kind, standing id, found, declared line, runs (which file, of)
EXPECT = {
    "hA": ("plugin", F, True, None, None), "hE": ("plugin", F, True, None, None),
    "hC": ("plugin", F, True, None, ("link", "source")),
    "hD": ("plugin", F, True, None, ("cmd", "source")), "pA": ("plugin", F, True, None, ("cmd", "source")),
    "hJ": ("plugin", F, True, 2, ("cmd", "source")),
    "hF": ("own", U, True, None, None), "pB": ("own", U, True, None, ("launch", "placed")),
    "hB": ("undecided", None, False, None, None), "hH": ("undecided", None, False, None, None),
    "hI": ("undecided", None, False, None, ("launch", "placed")),
    "pC": ("undecided", None, False, None, ("launch", "placed")),
    "hG": ("absent", None, False, None, None), "hK": ("absent", None, False, None, ("launch", "unknown")),
}
FIVE = ("5", "[x, y]", "./fork", "~other/fork", "$HOME/fork")


def sources():
    if str(LIB) not in sys.path:
        sys.path.insert(0, str(LIB))
    from agentik_suite import sources as mod
    return mod


class FkTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = os.path.realpath(tmp.name)

    def home(self, name):
        path = os.path.join(self.tmp, name)
        os.mkdir(path)
        return build(name, path)

    def row(self, h, tool=T, cwd=None, **env):
        return sources().read(h.env(**env), cwd or h.cwd, [tool], more=False)[0]

    def cli(self, h, *args, cwd=None, argv=None, **env):
        p = subprocess.run((argv or [str(LAUNCHER)]) + list(args), capture_output=True, text=True,
                           env=h.env(**env), cwd=cwd or h.cwd, timeout=60)
        return p.returncode, p.stdout, p.stderr

    def check(self, name, h, row, path=None):
        kind, standing, found, line, runs = EXPECT[name]
        self.assertEqual(row["tool"], T)
        self.assertEqual(row["kind"], kind, name)
        self.assertEqual(row["plugin"], standing, name)
        self.assertEqual(row["found"], found, name)
        self.assertEqual((row["declared"] or {}).get("line"), line, name)
        if runs is None:
            self.assertIsNone(row["runs"], name)
        else:
            self.assertEqual(row["runs"]["path"], getattr(h, runs[0]), name)
            self.assertEqual(row["runs"]["of"], runs[1], name)

    # line 1
    def test_1_each_home_at_the_terminal(self):
        for name in HOMES:
            h = self.home(name)
            row = self.row(h)
            self.check(name, h, row)
            self.assertIsNone(row["passed_over"], name)
            if row["runs"] and row["runs"]["of"] == "source":
                self.assertEqual(row["runs"]["version"], row["version"], name)
        paint = self.row(self.home_j(), "paint")
        self.assertEqual((paint["kind"], paint["found"], paint["declared"]["line"], paint["runs"]),
                         ("folder", False, 3, None))
        self.assertEqual(paint["root"], os.path.join(self.tmp, "hJ-cli", "src", "paint-fork", "plugin"))

    def test_1_the_launchers_version_and_a_fork_at_a_prerelease(self):
        h = self.home("pC")
        self.assertEqual(self.row(h)["runs"]["version"], "0.12.6")
        h = self.home("hE")
        self.assertEqual(self.row(h)["version"], "0.12.6-acme.1")

    # line 2
    def test_2_every_roots_bin_on_path(self):
        for name in HOMES:
            h = self.home(name)
            row = self.row(h, PATH=h.terminal(*h.bins()))
            if name == "hB":
                self.assertIsNone(row["runs"])
                self.assertEqual(row["passed_over"], {"path": h.own_cmd, "of": U})
            else:
                self.check(name, h, row)
                self.assertIsNone(row["passed_over"], name)

    # line 3
    def test_3_a_projects_entry(self):
        h = self.home("pB")
        row = self.row(h, cwd=os.path.join(h.project, "sub"))
        self.assertEqual(row["kind"], "undecided")
        self.assertEqual(len(row["seen"]), 2)
        self.assertEqual(sorted(s["scope"] for s in row["seen"]), ["project", "user"])
        row = self.row(h)
        self.assertEqual(row["version"], "0.13.0")
        self.assertEqual(row["seen"], [])

    def test_r6_a_link_does_not_walk_the_roots_file_out_of_its_root(self):
        h = self.home("hD")
        outside = h.file(os.path.join(h.home, "elsewhere", "agentik-" + T), "#!/bin/sh\nexit 0\n")
        os.remove(h.cmd)
        os.symlink(outside, h.cmd)
        row = self.row(h)
        self.assertEqual((row["kind"], row["runs"]), ("plugin", None))

    def test_r4_an_entry_with_no_scope_is_the_users_own(self):
        h = self.home("hF")
        del h.table[U][0]["scope"]
        h.write()
        row = self.row(h)
        self.assertEqual((row["kind"], row["plugin"], row["found"]), ("own", U, True))

    def test_r4_the_read_starts_no_process_and_never_imports_tools(self):
        h = self.home("hI")
        # every way to start a process, os.posix_spawn, os.system and os.exec* too (review 1, note 3)
        names = ["fork", "system", "posix_spawn", "posix_spawnp", "execl", "execle", "execlp",
                 "execlpe", "execv", "execve", "execvp", "execvpe"]
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch("subprocess.Popen", side_effect=AssertionError("a process")))
            for name in names:
                if hasattr(os, name):
                    stack.enter_context(mock.patch("os." + name, side_effect=AssertionError("os." + name)))
            self.assertEqual(self.row(h)["kind"], "undecided")
        p = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, %r); "
                            "from agentik_suite import sources; "
                            "print('agentik_suite.tools' in sys.modules)" % str(LIB)],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.stdout.strip(), "False", p.stderr)

    def test_r5_a_line_that_does_not_resolve_stands_unfound(self):
        h = self.home("hF")
        h.user_file("sources:\n  %s: %s\n" % (T, F))
        row = self.row(h)
        self.assertEqual((row["kind"], row["plugin"], row["found"], row["root"]), ("plugin", F, False, None))
        self.assertEqual([s["plugin"] for s in row["seen"]], [U])
        h.user_file("sources:\n  %s: other@acme-tools\n" % T)
        self.assertEqual(self.row(h)["found"], False)
        h.user_file("sources:\n  %s: %s\n" % (T, U))
        row = self.row(h)
        self.assertEqual((row["kind"], row["found"], row["seen"]), ("own", True, []))

    def test_r5_a_folder_stands_when_its_manifest_reads(self):
        h = self.home("hG")
        h.user_file("sources:\n  %s: ~/.claude/plugins/cache/acme-tools/%s/0.12.6\n" % (T, T))
        row = self.row(h)
        self.assertEqual((row["kind"], row["plugin"], row["found"], row["version"]),
                         ("folder", None, True, "0.12.6"))

    # R8
    def test_r8_mirror_in_four_forms(self):
        h = self.home("hF")
        forms = [({"source": "github", "repo": "agentik-dev/agentik-commons"}, False),
                 ({"source": "git", "url": "https://github.com/Agentik-Dev/agentik-commons.git"}, False),
                 ({"source": "git", "url": "git" + "@github.com:agentik-dev/agentik-commons"}, False),
                 ({"source": "directory", "path": "/srv/mirror/agentik-commons"}, True)]
        for source, mirror in forms:
            h.known = {"agentik": {"source": source}}
            h.write()
            self.assertEqual(self.row(h)["mirror"], mirror, source)
        h = self.home("hA")
        h.known = {"agentik": {"source": {"source": "directory", "path": "/srv/mirror"}}}
        h.write()
        self.assertFalse(self.row(h)["mirror"])

    # line 4
    def test_4_describe_sources_in_each_home(self):
        for name in HOMES:
            h = self.home(name)
            code, out, err = self.cli(h, "describe", "sources", "--json", T)
            self.assertEqual(code, 0, name + err)
            body = json.loads(out)
            self.assertEqual((body["schema"], body["ok"]), ("agentik.sources/1", True))
            self.assertEqual(len(body["tools"]), 1)
            self.check(name, h, body["tools"][0])
        code, out, err = self.cli(self.home_j(), "describe", "sources", "--json")
        self.assertEqual(code, 0, err)
        tools = [r["tool"] for r in json.loads(out)["tools"]]
        self.assertIn(T, tools)
        self.assertIn("paint", tools)
        self.assertNotIn("suite", tools)

    def home_j(self):
        path = os.path.join(self.tmp, "hJ-cli")
        os.mkdir(path)
        return build("hJ", path)

    def test_4_a_user_file_outside_the_subset_exits_two(self):
        h = self.home("hF")
        h.user_file("sources:\n\t%s: x\n" % T)
        code, out, err = self.cli(h, "describe", "sources", "--json")
        self.assertEqual(code, 2)

    # line 5
    def test_5_describe_config_warns(self):
        h = self.home("hJ")
        code, out, err = self.cli(h, "describe", "config", "--json", cwd=h.repo)
        self.assertEqual(code, 0, err)
        body = json.loads(out)
        warned = [(w["key"], w["reason"]) for w in body["warnings"]]
        self.assertIn(("suite.sources", "ignored"), warned)
        ign = [w for w in body["warnings"] if w["reason"] == "ignored"][0]
        self.assertEqual((ign["path"], ign["line"]),
                         (os.path.join(h.repo, ".claude", "agentik", "config.yaml"), 2))
        self.assertNotIn("unknown", [r for k, r in warned if k.endswith("sources")])
        line = [s for s in body["settings"] if s["key"] == "sources." + T]
        self.assertEqual(len(line), 1)
        self.assertEqual((line[0]["source"]["line"], line[0]["default"], line[0]["value"]), (2, U, F))
        self.assertEqual(line[0]["change"]["block"], "sources:\n  %s: <id or folder>" % T)
        h.user_file("sources:\n  suite: /x/plugin\n" + "".join("  t%d: %s\n" % (i, v) for i, v in enumerate(FIVE)))
        body = json.loads(self.cli(h, "describe", "config", "--json")[1])
        warned = [(w["key"], w["reason"]) for w in body["warnings"]]
        self.assertIn(("sources.suite", "self"), warned)
        for i in range(len(FIVE)):
            self.assertIn(("sources.t%d" % i, "value"), warned)
        keys = [s["key"] for s in body["settings"]]
        self.assertNotIn("sources.suite", keys)
        self.assertIn("sources.t4", keys)
        row = self.row(h, "t2")
        self.assertEqual((row["found"], row["declared"]["line"]), (False, 5))

    def test_5_a_relative_config_home_ignores_the_block(self):
        h = self.home("hJ")
        h.user_file("sources:\n  %s: %s\n" % (T, F), base=os.path.join(h.home, "cfg"))
        code, out, err = self.cli(h, "describe", "config", "--json", XDG_CONFIG_HOME="cfg")
        self.assertEqual(code, 0, err)
        warned = [(w["key"], w["reason"]) for w in json.loads(out)["warnings"]]
        self.assertIn(("sources", "relative"), warned)
        code, out, err = self.cli(h, "describe", "sources", "--json", T, XDG_CONFIG_HOME="cfg")
        self.assertIsNone(json.loads(out)["tools"][0]["declared"])

    # line 6
    def test_6_the_read_under_an_empty_path(self):
        empty = os.path.join(self.tmp, "empty")
        os.mkdir(empty)
        for name in HOMES:
            h = self.home(name)
            want = json.loads(self.cli(h, "describe", "sources", "--json", T)[1])["tools"]
            code, out, err = self.cli(h, "describe", "sources", "--json", T, PATH=empty,
                                      argv=["/usr/bin/python3", str(LIB / "agentik-suite")])
            self.assertEqual(code, 0, name + err)
            got = json.loads(out)["tools"]
            # every field but `runs`, which the PATH moves (review 1, note 2)
            self.assertEqual([{k: v for k, v in r.items() if k != "runs"} for r in got],
                             [{k: v for k, v in r.items() if k != "runs"} for r in want], name)


if __name__ == "__main__":
    unittest.main()
