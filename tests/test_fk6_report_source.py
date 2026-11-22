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
import re
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fk_homes  # noqa: E402
import test_rp6_fix as rp6_fix  # noqa: E402
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


# Build 3, the fix of review 1: R1 to R6 (F1 to F6, F9), each red at the second build's head.

PUBLIC = json.loads((LIB / "public.json").read_text())
EDITOR = '''#!/usr/bin/python3 -I
import sys
path = sys.argv[1]
with open(path) as fh:
    text = fh.read()
with open(path, "w") as fh:
    fh.write(text.replace(%r, %r))
'''


class ReaderTest(rp6.IssueHome):
    """R1 (F1, F2): a plugin file that is a FIFO, or nested past the parser's depth, reads as
    holding nothing, as plan's reader reads it: `issue new` makes its draft, exit 0."""

    def launch(self):
        args = [str(rp6.LAUNCHER), "issue", "new", rp6.TOOL, "--ran", "x", "--exit", "2",
                "--output", "err.txt", "--expected", rp6.EXPECTED]
        try:
            p = subprocess.run(args, capture_output=True, text=True, env=self.env(), timeout=30,
                               cwd=self.work, stdin=subprocess.DEVNULL, start_new_session=True)
        except subprocess.TimeoutExpired:
            self.fail("issue new still running after 30 s")
        return p.returncode, p.stdout, p.stderr

    def test_r1_a_fifo_never_hangs(self):
        for name in ("known_marketplaces.json", "installed_plugins.json"):
            with self.subTest(file=name):
                self.setUp()
                path = os.path.join(self.home, ".claude", "plugins", name)
                os.unlink(path)
                os.mkfifo(path)
                code, out, err = self.launch()
                self.assertEqual(code, 0, err)
                self.assertTrue(self.draft())

    def test_r1_a_deep_file_never_raises(self):
        for name in ("known_marketplaces.json", "installed_plugins.json"):
            with self.subTest(file=name):
                self.setUp()
                with open(os.path.join(self.home, ".claude", "plugins", name), "w") as fh:
                    fh.write("[" * 100000)
                code, out, err = self.new()
                self.assertEqual(code, 0, err)
                self.assertNotIn("Traceback", err)
                self.assertTrue(self.draft())

    def test_r1_the_reader_in_process(self):
        from agentik_suite import scrub
        deep = os.path.join(self.home, "deep.json")
        with open(deep, "w") as fh:
            fh.write("{\"a\":" * 100000)
        fifo = os.path.join(self.home, "fifo.json")
        os.mkfifo(fifo)
        for path in (deep, fifo, self.home, os.path.join(self.home, "absent.json")):
            self.assertIsNone(scrub._json(path), path)
        good = os.path.join(self.home, "good.json")
        with open(good, "w") as fh:
            fh.write('{"version": "1.2.3"}')
        self.assertEqual(scrub._json(good), {"version": "1.2.3"})


def scrubbed(text, sources=(), versions=()):
    from agentik_suite import scrub
    return scrub.scrub(text, scrub.build(PUBLIC, sources=sources, versions=versions))[0]


class VersionTest(ForkHome):
    """R2 (F3): a foreign version is a value only where it holds a letter and a digit and is not
    N.N.N, and it is matched whole."""

    TEXT = "unknown command: lint\nPython 3.11.0 at latest build\n%s\n" % rp6.FAILING

    def third(self, version):
        self.setUp()
        h = self.lay("hF")
        h.table["fmt@tools-co"] = [{"scope": "user", "version": version,
                                    "installPath": os.path.join(self.home, "inst", "fmt")}]
        h.write()
        with open(os.path.join(self.work, "err.txt"), "w") as fh:
            fh.write(self.TEXT)
        code, out, err = self.new()
        self.assertEqual(code, 0, err)
        return self.draft()

    def test_r2_a_word_or_a_number_is_no_value(self):
        plain = self.third("1.2.3")
        self.assertIn(b"unknown command: lint", plain)
        self.assertIn(b"Python 3.11.0 at latest build", plain)
        for version in ("1.0", "latest", "unknown"):
            with self.subTest(version=version):
                self.assertEqual(self.third(version), plain)

    def test_r2_a_named_version_is_matched_whole(self):
        for text in ("at %s now", "at v%s now", "see x/%s/bin now", "ends %s.", "(%s)", "%s:"):
            with self.subTest(text=text):
                got = scrubbed(text % PLANTED, versions=[PLANTED])
                self.assertNotIn("acme", got)
                self.assertIn("<", got)
        for text in ("Python 3.11.0", "build 10.12.6-acme.1x", "x0.12.6-acme.1", "0.12.6-acme.12"):
            with self.subTest(text=text):
                self.assertEqual(scrubbed(text, versions=["1.0", PLANTED]), text)

    def test_r2_still_scrubbed_beside_a_v_and_in_a_path(self):
        self.lay("hB", PLANTED)
        self.plant()
        with open(os.path.join(self.work, "err.txt"), "w") as fh:
            fh.write("ran v%s here\nin cache/x/%s/bin\n%s\n" % (PLANTED, PLANTED, rp6.FAILING))
        code, out, err = self.new()
        self.assertEqual(code, 0, err)
        self.no_acme(self.draft(), out, err)


QZ = re.compile(rb"(?<![A-Za-z0-9_])qz(?![A-Za-z0-9_])")


class ShortTest(ForkHome):
    """R3 (F4): a marketplace name under three characters is scrubbed as a whole word only."""

    def test_r3_a_two_letter_marketplace(self):
        h = self.lay("hB", "0.12.6-qz.1")
        h.table = {k.replace("acme-tools", "qz"): v for k, v in h.table.items()}
        h.known = {k.replace("acme-tools", "qz"): v for k, v in h.known.items()}
        h.write()
        with open(os.path.join(self.work, "err.txt"), "w") as fh:
            fh.write("marketplace qz is behind\n%s@qz 0.12.6-qz.1 no voice\nqzar and aqz stay\n%s\n"
                     % (FORK, rp6.FAILING))
        for more in ((), ("--json",)):
            with self.subTest(more=more):
                code, out, err = self.new(*more)
                self.assertEqual(code, 0, err)
                with open(os.path.join(self.draft_dir(), "draft.json"), "rb") as fh:
                    meta = fh.read()
                for blob in (self.draft(), meta, out.encode(), err.encode()):
                    self.assertIsNone(QZ.search(blob), blob[-400:])
                self.assertIn(b"qzar and aqz stay", self.draft())

    def test_r3_the_rule_in_process(self):
        self.assertEqual(scrubbed("marketplace qz is behind", sources=["qz"]),
                         "marketplace <source-1> is behind")
        self.assertEqual(scrubbed("at x@qz.", sources=["qz"]), "at x@<source-1>.")
        for text in ("qzar", "aqz", "qz-x", "x.qz", "qz_1", "qz9"):
            with self.subTest(text=text):
                self.assertEqual(scrubbed(text, sources=["qz"]), text)


class EditTest(ForkHome):
    """R4 (F5): `issue edit` refuses a text that removes a tool's `another source` row or gives
    that tool a version; the draft stays as it was."""

    pty_word = rp6_fix.FixHome.pty_word

    def edit(self, old, new):
        editor = os.path.join(self.stubs, "edit-stub")
        with open(editor, "w") as fh:
            fh.write(EDITOR % (old, new))
        os.chmod(editor, 0o755)
        return self.pty_word("edit", EDITOR=editor)

    def test_r4_the_row_holds_against_edit(self):
        line = (catalogue.load().get("err.issue.edit.source") or "?").replace("`", "").replace("{tool}", FORK)
        row = "%s another source" % FORK
        for new in ("", "%s 0.12.6" % FORK, "%s 0.12.6, %s" % (FORK, row)):
            with self.subTest(new=new):
                self.setUp()
                self.lay("hB")
                self.assertEqual(self.new()[0], 0)
                before = self.draft()
                old = (", " + row) if not new else row
                self.assertIn(old.encode(), before)
                code, screen, out = self.edit(old, new)
                self.assertEqual(code, 1, screen)
                shown = " ".join(re.sub(r"\x1b\[[0-9;]*m", "", screen).replace("`", "").split())
                self.assertTrue(shown.endswith(" " + line), screen)  # the one line, wrapped at the pty's width
                self.assertNotIn("next:", shown)
                self.assertEqual(self.draft(), before)
        code, screen, out = self.edit(rp6.EXPECTED, "doctor passes in a fresh clone, every time")
        self.assertEqual(code, 0, screen)
        self.assertIn(b"every time", self.draft())
        self.another(self.draft())

    def test_r4_a_draft_with_no_such_row_edits_as_before(self):
        self.lay("hF")
        self.assertEqual(self.new()[0], 0)
        self.assertNotIn(b"another source", self.draft())
        item = [i for i in versions(self.draft()) if i.startswith(rp6.TOOL + " ")][0]
        code, screen, out = self.edit(item + ", ", "")
        self.assertEqual(code, 0, screen)
        self.assertNotIn(item.encode() + b",", self.draft())


class RidingTest(ForkHome):
    def out(self, text):
        with open(os.path.join(self.work, "err.txt"), "w") as fh:
            fh.write(text + "\n" + rp6.FAILING + "\n")

    def test_r5_a_user_file_id_gives_its_marketplace(self):
        h = self.lay("hF")
        h.user_file("sources:\n  %s: %s@acme-tools\n" % (FORK, FORK))
        h.known.pop("acme-tools", None)
        h.write()
        self.out("marketplace acme-tools is behind")
        code, out, err = self.new()
        self.assertEqual(code, 0, err)
        self.no_acme(self.draft(), out, err)

    def test_r6_a_public_word_only_after_an_at(self):
        h = self.lay("hB", "0.12.6")
        h.table = {k.replace("acme-tools", "suite"): v for k, v in h.table.items()}
        h.known = {k.replace("acme-tools", "suite"): v for k, v in h.known.items()}
        h.write()
        self.out("listed suite@agentik and %s@agentik, and %s@suite" % (rp6.TOOL, FORK))
        code, out, err = self.new()
        self.assertEqual(code, 0, err)
        data = self.draft()
        self.assertIn(b"listed suite@agentik and %s@agentik, and " % rp6.TOOL.encode(), data)
        self.assertNotIn(("%s@suite" % FORK).encode(), data)


if __name__ == "__main__":
    unittest.main()
