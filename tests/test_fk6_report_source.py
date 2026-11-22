"""Row fk6-report-source: what an issue's draft says of a tool from another source (hq design/25
§3 item 15). End to end through the launcher, as rp6 does, in the homes of fk1 (`fk_homes`) with
the made-up fork `acme` of the narrator's tool (render.json's plugin), laid over rp6's issue home.

1. A draft made in hB, hI and hJ, with `acme` planted in the fork's doctor line, its id and its
   version, holds no `acme` byte, in the text or under --json; the tool's row reads `another source`.
2. `issue new <the tool>` in hA refuses in one line and writes no draft; another tool's draft
   there carries the tool's row as `another source`.
3. A marketplace that is a mirror: the draft is made, each mirrored tool's row `another source`.
4. `render.find` gives the fork's script in hA, and the public one where no fork stands.
5. `drop` cannot remove the Versions line.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fk_homes  # noqa: E402
import test_rp6_issue as rp6  # noqa: E402
from test_agentik_suite import LIB  # noqa: E402

sys.path.insert(0, str(LIB))
from agentik_suite import catalogue, form, plan, render  # noqa: E402

FORK = json.loads((LIB / "render.json").read_text())["plugin"]  # a public tool with a narrator
ACME = b"acme"
PLANTED = "0.12.6-acme.1"
LINE = catalogue.load()["err.issue.source"].replace("`", "") if "err.issue.source" in catalogue.load() else None
# the fork's own doctor: one failing row that names its id and its version
FORK_DOCTOR = r'''#!/usr/bin/python3 -I
import json, sys
if sys.argv[1:] == ["doctor", "--json"]:
    print(json.dumps({"schema": "agentik.doctor/1", "ok": True, "checks": [
        {"name": "acme-sync", "status": "fail", "detail": "%s@acme-tools %s cannot reach acme",
         "remedy": None}]}))
    sys.exit(1)
sys.exit(2)
''' % (FORK, PLANTED)
OUTPUT = ("%s@acme-tools %s: no voice\nmarketplace acme-tools is behind\n%s\n"
          % (FORK, PLANTED, rp6.FAILING))


def versions(data):
    """The Versions line's items, before the system items."""
    line = [l for l in data.decode().split("\n") if l.startswith(form.VERSIONS)][0]
    return line[len(form.VERSIONS):].split(", ")


class ForkHome(rp6.IssueHome):
    """rp6's issue home, its marketplace the public one, with fk1's home `name` for the tool laid
    over it: the fork is `<tool>@acme-tools`, known as a marketplace beside `agentik`."""

    def lay(self, name, version=None):
        h = fk_homes.build(name, self.home, tool=FORK)
        h.table.update({"%s@agentik" % rp6.TOOL: [{"scope": "user", "version": "2.0.0-alpha.101",
                                                   "installPath": os.path.join(self.home, "inst", rp6.TOOL)}],
                        "suite@agentik": [{"scope": "user", "version": "0.6.0",
                                           "installPath": os.path.join(self.home, "inst", "suite")}]})
        if version:
            for e in h.table.get(h.fork, []):
                e["version"] = version
        h.known["acme-tools"] = {"source": {"source": "github", "repo": "acme/acme-tools"}}
        h.write()
        self.h = h
        return h

    def plant(self):
        self.stub("agentik-" + FORK, FORK_DOCTOR)
        with open(os.path.join(self.work, "err.txt"), "w") as fh:
            fh.write(OUTPUT)

    def no_acme(self, *texts):
        for t in texts:
            self.assertNotIn(ACME, t if isinstance(t, bytes) else t.encode())

    def another(self, data, name=FORK):
        items = versions(data)
        self.assertIn("%s another source" % name, items, items)
        self.assertEqual([i for i in items if i.startswith(name + " ")], ["%s another source" % name])


class DraftTest(ForkHome):
    def test_1_no_acme_byte_and_the_row(self):
        for name in ("hB", "hI", "hJ"):
            with self.subTest(home=name):
                self.lay(name, PLANTED)
                self.plant()
                code, out, err = self.new()
                self.assertEqual(code, 0, err)
                data = self.draft()
                with open(os.path.join(self.draft_dir(), "draft.json"), "rb") as fh:
                    self.no_acme(data, out, err, fh.read())
                self.another(data)
                code, out, err = self.new("--json")
                self.assertEqual(code, 0, err)
                self.no_acme(out, err, self.draft())
                self.another(self.draft())
                self.assertTrue(self.reads_back(self.draft()))


class RefusalTest(ForkHome):
    def test_2_the_fork_refuses_and_another_tool_says_so(self):
        self.lay("hA")
        code, out, err = self.issue("new", FORK, "--ran", "agentik %s doctor" % FORK, "--exit", "2",
                                    "--output", "err.txt", "--expected", rp6.EXPECTED)
        self.assertEqual(code, 1, err)
        self.assertIsNotNone(LINE)
        self.assertEqual(len(err.splitlines()), 1, err)  # one line, no `next:`
        self.assertTrue(err.replace("`", "").rstrip("\n").endswith(" " + LINE.replace("{tool}", FORK)), err)
        self.assertEqual(out, "")
        self.assertFalse(os.path.isdir(self.drafts) and os.listdir(self.drafts))
        code, out, err = self.issue("new", FORK, "--json")
        self.assertEqual(code, 1, err)
        self.assertEqual(json.loads(out)["error"]["code"], "another_source")
        self.assertIsNone(json.loads(out)["error"]["remedy"])
        code, out, err = self.new()
        self.assertEqual(code, 0, err)
        self.another(self.draft())
        self.assertTrue(self.reads_back(self.draft()))


class MirrorTest(rp6.IssueHome):
    def test_3_a_mirror_makes_the_draft(self):
        known = os.path.join(self.home, ".claude", "plugins", "known_marketplaces.json")
        with open(known, "w") as fh:
            json.dump({"agentik": {"source": {"source": "github", "repo": "acme/agentik-commons"}}}, fh)
        code, out, err = self.new()
        self.assertEqual(code, 0, err)
        items = versions(self.draft())
        for name in (rp6.TOOL, "suite"):
            self.assertEqual([i for i in items if i.startswith(name + " ")], ["%s another source" % name])
        self.assertTrue(self.reads_back(self.draft()))
        self.assertIn(" %s unreadable " % rp6.TOOL, self.draft().decode().rstrip("\n").split("\n")[-1] + " ")


class FindTest(ForkHome):
    def script(self, root):
        path = os.path.join(root, rp6_render_script())
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write("#!/bin/sh\nexit 0\n")
        os.chmod(path, 0o755)
        return path

    def test_4_the_narrator_is_the_one_that_stands(self):
        h = self.lay("hA")
        fork = self.script(h.root(h.fork, "0.12.6"))
        self.assertEqual(render.find({"HOME": self.home}, str(LIB)), fork)
        h = self.lay("hF")
        own = self.script(h.root(h.own, "0.13.0"))
        self.assertEqual(render.find({"HOME": self.home}, str(LIB)), own)


def rp6_render_script():
    return json.loads((LIB / "render.json").read_text())["script"]


class DropTest(ForkHome):
    def test_5_drop_cannot_remove_the_versions_row(self):
        self.lay("hB")
        code, out, err = self.new()
        self.assertEqual(code, 0, err)
        before = self.draft()
        code, out, err = self.issue("drop", "versions")
        self.assertEqual(code, 2, out + err)
        self.assertEqual(self.draft(), before)


class SourceTest(unittest.TestCase):
    def test_the_public_source_is_the_plans(self):
        self.assertEqual(fk_homes.SOURCE, plan.SOURCE)


if __name__ == "__main__":
    unittest.main()
