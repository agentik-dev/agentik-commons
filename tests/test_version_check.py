"""scripts/plugin-version-check (GUIDE §7): `since` is the last first-parent commit
that changed plugin.json's version (the file's first commit when it never changed),
the files under plugin/ changed since, committed or not, exit 1 with one line each,
a bump in flight passes, and usage, no work tree or no readable version exit 2.
Every repo is built in a temp dir with git config isolated; nothing reads the network."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "plugin-version-check"
MANIFEST = "plugin/.claude-plugin/plugin.json"
# a clean git: no user or system config, a fixed identity, no GIT_* from the caller
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
ENV.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
           GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
           GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")


def check(cwd, *args, env=None):
    p = subprocess.run([str(SCRIPT), *args], capture_output=True, text=True, cwd=cwd,
                       env=dict(ENV, **(env or {})))
    return p.returncode, p.stdout, p.stderr


class VersionCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.join(self.tmp.name, "a plugin repo")
        os.mkdir(self.repo)
        self.git("init", "-q", "-b", "main")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        p = subprocess.run(["git", "-C", self.repo, *args], capture_output=True, text=True,
                           env=ENV, check=True)
        return p.stdout.strip()

    def write(self, path, text):
        full = Path(self.repo, path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(text)

    def manifest(self, version, description="a plugin"):
        self.write(MANIFEST, json.dumps({"name": "x", "version": version,
                                         "description": description}) + "\n")

    def commit(self, *paths, message="c"):
        self.git("add", "--", *(paths or ["."]))
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def json(self, *args):
        code, out, err = check(self.repo, "--json", *args)
        return code, json.loads(out), err

    def released(self):
        """plugin.json at 1.0.0 with one file, then a bump to 1.1.0; the bump's sha."""
        self.manifest("1.0.0")
        self.write("plugin/skills/a.md", "a\n")
        self.commit()
        self.manifest("1.1.0")
        return self.commit()

    def test_unchanged_since_the_bump_exits_zero(self):
        bump = self.released()
        self.write("README.md", "outside plugin/\n")
        self.commit()
        code, out, err = check(self.repo)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(len(out.splitlines()), 1)
        self.assertIn("1.1.0", out)
        self.assertEqual(self.json(), (0, {"version": "1.1.0", "since": bump, "changed": []}, ""))

    def test_a_change_after_the_bump_exits_one_naming_each_file(self):
        bump = self.released()
        self.write("plugin/skills/a.md", "a, changed\n")
        self.write("plugin/hooks/run", "#!/bin/sh\n")
        self.commit()
        code, out, err = check(self.repo)
        self.assertEqual((code, out), (1, ""))
        lines = err.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("plugin-version-check: plugin/hooks/run: "))
        self.assertIn(bump[:12], lines[1])
        code, data, err = self.json()
        self.assertEqual((code, err), (1, ""))
        self.assertEqual(data, {"version": "1.1.0", "since": bump,
                                "changed": ["plugin/hooks/run", "plugin/skills/a.md"]})

    def test_since_is_the_last_version_change_not_the_last_touch(self):
        bump = self.released()
        self.manifest("1.1.0", description="reworded, the version kept")
        self.commit()
        code, data, _ = self.json()
        self.assertEqual((code, data["since"], data["changed"]), (1, bump, [MANIFEST]))
        self.manifest("1.2.0", description="reworded, the version kept")
        again = self.commit()
        self.assertEqual(self.json()[:2], (0, {"version": "1.2.0", "since": again, "changed": []}))

    def test_since_is_the_first_commit_when_the_version_never_changed(self):
        self.write("README.md", "before the plugin\n")
        self.commit()
        self.manifest("0.1.0")
        first = self.commit()
        self.manifest("0.1.0", description="the same version")
        self.write("plugin/skills/b.md", "b\n")
        self.commit()
        code, data, _ = self.json()
        self.assertEqual((code, data["since"]), (1, first))
        self.assertEqual(data["changed"], [MANIFEST, "plugin/skills/b.md"])

    def test_since_follows_the_first_parent_line(self):
        self.manifest("1.0.0")
        self.write("plugin/a.md", "a\n")
        self.commit()
        # a bump made on a branch and merged: the merge moves main's version
        self.git("checkout", "-q", "-b", "bump")
        self.manifest("2.0.0")
        self.commit()
        self.git("checkout", "-q", "main")
        self.write("plugin/a.md", "a, changed on main before the merge\n")
        self.commit()
        self.git("merge", "-q", "--no-ff", "-m", "merge bump", "bump")
        merge = self.git("rev-parse", "HEAD")
        self.assertEqual(self.json()[:2], (0, {"version": "2.0.0", "since": merge, "changed": []}))
        # a change made on a branch cut before a bump on main, merged after it
        self.git("checkout", "-q", "-b", "late", "HEAD")
        self.write("plugin/late.md", "late\n")
        self.commit()
        self.git("checkout", "-q", "main")
        self.manifest("2.1.0")
        bump = self.commit()
        self.git("merge", "-q", "--no-ff", "-m", "merge late", "late")
        code, data, _ = self.json()
        self.assertEqual((code, data["since"], data["changed"]), (1, bump, ["plugin/late.md"]))

    def test_uncommitted_changes_count_and_ignored_files_do_not(self):
        self.released()
        self.write(".gitignore", "*.log\n")
        self.write("plugin/c.md", "c\n")
        self.commit(".gitignore", "plugin/c.md")
        self.manifest("1.2.0")
        bump = self.commit()
        self.write("plugin/skills/a.md", "a, unstaged\n")
        self.write("plugin/c.md", "c, staged\n")
        self.git("add", "plugin/c.md")
        self.write("plugin/new/deep/b c.md", "untracked, a space in its name\n")
        self.write("plugin/debug.log", "ignored\n")
        self.write("notes.md", "outside plugin/\n")
        code, data, _ = self.json()
        self.assertEqual((code, data["since"]), (1, bump))
        self.assertEqual(data["changed"], ["plugin/c.md", "plugin/new/deep/b c.md",
                                           "plugin/skills/a.md"])

    def test_a_rename_names_both_paths(self):
        self.released()
        self.git("mv", "plugin/skills/a.md", "plugin/skills/z.md")
        self.assertEqual(self.json()[1]["changed"], ["plugin/skills/a.md", "plugin/skills/z.md"])
        self.commit()
        self.assertEqual(self.json()[1]["changed"], ["plugin/skills/a.md", "plugin/skills/z.md"])

    def test_a_bump_in_flight_passes(self):
        self.released()
        self.write("plugin/skills/a.md", "a, changed\n")
        self.commit()
        self.write("plugin/skills/b.md", "b, uncommitted\n")
        self.assertEqual(self.json()[0], 1)
        self.manifest("1.2.0")
        code, out, err = check(self.repo)
        self.assertEqual((code, err), (0, ""))
        self.assertIn("uncommitted", out)
        self.assertEqual(self.json(), (0, {"version": "1.2.0", "since": None, "changed": []}, ""))
        # a repo with no commit yet holds its first version in flight
        fresh = os.path.join(self.tmp.name, "fresh")
        subprocess.run(["git", "init", "-q", fresh], check=True, env=ENV)
        Path(fresh, "plugin", ".claude-plugin").mkdir(parents=True)
        Path(fresh, MANIFEST).write_text('{"version": "0.0.1"}\n')
        self.assertEqual(check(fresh, "--json")[:2],
                         (0, '{"version": "0.0.1", "since": null, "changed": []}\n'))

    def test_repo_flag_names_the_checkout(self):
        bump = self.released()
        code, out, _ = check(self.tmp.name, "--repo", self.repo, "--json")
        self.assertEqual((code, json.loads(out)["since"]), (0, bump))

    def test_exit_two(self):
        self.released()
        for args in (("--bogus",), ("--json", "--json"), ("--repo",), ("x",),
                     ("--repo", "a", "--repo", "b"), ("--repo", "--json")):
            code, out, err = check(self.repo, *args)
            self.assertEqual((code, out), (2, ""), args)
            self.assertTrue(err.startswith("usage: "), args)
        self.assertEqual(check(self.repo, "--help")[0], 0)
        self.assertEqual(check(self.repo, "--repo", os.path.join(self.tmp.name, "nosuch"))[0], 2)
        # not a git work tree, though it holds a plugin.json
        plain = os.path.join(self.tmp.name, "plain")
        Path(plain, "plugin", ".claude-plugin").mkdir(parents=True)
        Path(plain, MANIFEST).write_text('{"version": "1.0.0"}\n')
        # (the ceiling keeps git from finding a repo above the temp dir)
        code, out, err = check(plain, env={
            "GIT_CEILING_DIRECTORIES": os.path.realpath(self.tmp.name)})
        self.assertEqual((code, out), (2, ""))
        self.assertIn("work tree", err)
        # no plugin.json, a file that is not JSON, a version that is not a string
        for text in (None, "{", '{"version": 1}\n', "[]\n"):
            if text is None:
                os.remove(Path(self.repo, MANIFEST))
            else:
                self.write(MANIFEST, text)
            code, out, err = check(self.repo, "--json")
            self.assertEqual((code, out), (2, ""), text)
            self.assertEqual(len(err.splitlines()), 1, text)

    def test_shape(self):
        self.assertTrue(SCRIPT.read_text().startswith("#!/usr/bin/env python3\n"))
        self.assertTrue(os.access(SCRIPT, os.X_OK))


A1, A2, A3 = "1.0.0-alpha.1", "1.0.0-alpha.2", "1.0.0-alpha.3"
ABOVE = "; above %s at the merge base with main\n"
NO_BASE = "; no merge base with main, the branch's own changes not read\n"


def pin_line(version, since):
    return ("plugin-version-check: version %s, set at %s; nothing under plugin/ changed since\n"
            % (version, since[:12]))


def branch_line(path, base, base_version, version):
    return ("plugin-version-check: %s: changed on this branch since its merge base with main "
            "(%s, version %s); version %s is not above it: bump plugin.json's version\n"
            % (path, base[:12], base_version, version))


class BranchReadTest(unittest.TestCase):
    """The second read (packet c7): the paths under plugin/ that differ from HEAD's merge
    base with main, the manifest aside, need a version above the merge base's."""
    setUp, tearDown = VersionCheckTest.setUp, VersionCheckTest.tearDown
    git, write, manifest = VersionCheckTest.git, VersionCheckTest.write, VersionCheckTest.manifest
    commit, json = VersionCheckTest.commit, VersionCheckTest.json

    def fault(self):
        """main at alpha.1; `row` adds plugin/lib/row.py and never bumps; main adds a file
        and bumps to alpha.2; `row` merges main. (row's tip, main's head)."""
        self.manifest(A1)
        self.write("plugin/a.md", "a\n")
        self.commit()
        self.git("checkout", "-q", "-b", "row")
        self.write("plugin/lib/row.py", "row\n")
        self.commit()
        self.git("checkout", "-q", "main")
        self.write("plugin/other.md", "other\n")
        self.manifest(A2)
        main = self.commit()
        self.git("checkout", "-q", "row")
        self.git("merge", "-q", "--no-edit", "main")
        return self.git("rev-parse", "HEAD"), main

    def test_1_the_faults_branch_exits_one_naming_both_versions(self):
        tip, main = self.fault()
        self.assertEqual(check(self.repo), (1, "", branch_line("plugin/lib/row.py", main, A2, A2)))
        code, data, err = self.json()
        self.assertEqual((code, err), (1, ""))
        self.assertEqual(data, {"version": A2, "since": tip, "changed": [], "base": {
            "ref": "refs/heads/main", "merge_base": main, "version": A2,
            "changed": ["plugin/lib/row.py"]}})

    def test_2_a_version_above_mains_passes_with_the_clause(self):
        tip, main = self.fault()
        self.manifest(A3)
        code, out, err = check(self.repo)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "plugin-version-check: version %s is uncommitted; the bump in "
                              "flight covers every change under plugin/" % A3 + ABOVE % A2)
        self.assertEqual(self.json()[1]["base"]["changed"], ["plugin/lib/row.py"])
        bump = self.commit()
        self.assertEqual(check(self.repo), (0, pin_line(A3, bump)[:-1] + ABOVE % A2, ""))
        self.assertEqual(self.json(), (0, {"version": A3, "since": bump, "changed": [], "base": {
            "ref": "refs/heads/main", "merge_base": main, "version": A2,
            "changed": ["plugin/lib/row.py"]}}, ""))
        # precedence, not text: a release is above its pre-releases, numbers by number
        for version, code in (("1.0.0", 0), ("1.0.0-alpha.10", 0), ("1.0.0-beta", 0),
                              ("1.0.0-alpha.2.0", 0), ("1.0.0-alpha.2", 1),
                              ("1.0.0-alpha.2+b7", 1), ("1.0.0-alpha.1", 1), ("0.9.9", 1)):
            self.manifest(version)
            self.assertEqual(check(self.repo)[0], code, version)

    def test_3_main_after_the_landing_exits_one_as_at_the_pin(self):
        tip, main = self.fault()
        self.git("checkout", "-q", "main")
        self.git("merge", "-q", "--no-ff", "-m", "land row", "row")
        self.assertEqual(check(self.repo), (1, "", (
            "plugin-version-check: plugin/lib/row.py: changed since %s set version %s; "
            "bump plugin.json's version\n" % (main[:12], A2))))
        self.assertNotIn("base", self.json()[1])

    def test_4_a_branch_behind_main_bumped_above_its_merge_base_passes(self):
        self.manifest(A1)
        self.write("plugin/a.md", "a\n")
        base = self.commit()
        self.git("checkout", "-q", "-b", "behind")
        self.write("plugin/lib/row.py", "row\n")
        self.manifest(A2)
        bump = self.commit()
        self.git("checkout", "-q", "main")
        self.write("plugin/other.md", "other\n")
        self.manifest("1.0.0-alpha.9")
        self.commit()
        self.git("checkout", "-q", "behind")
        self.assertEqual(check(self.repo), (0, pin_line(A2, bump)[:-1] + ABOVE % A1, ""))
        self.assertEqual(self.json()[1]["base"]["merge_base"], base)

    def test_5_a_branch_changing_nothing_under_plugin_merging_a_bumped_main(self):
        self.manifest(A1)
        self.write("plugin/a.md", "a\n")
        self.commit()
        self.git("checkout", "-q", "-b", "docs")
        self.write("README.md", "outside plugin/\n")
        self.commit()
        self.git("checkout", "-q", "main")
        self.manifest(A2)
        self.commit()
        self.git("checkout", "-q", "docs")
        self.git("merge", "-q", "--no-edit", "main")
        merge = self.git("rev-parse", "HEAD")
        self.assertEqual(check(self.repo), (0, pin_line(A2, merge), ""))

    def test_6_main_and_detached_at_main_read_as_the_pin_and_a_tip_as_its_branch(self):
        tip, main = self.fault()
        self.git("checkout", "-q", "main")
        for where in ("main", "detached at main's head"):
            self.assertEqual(check(self.repo), (0, pin_line(A2, main), ""), where)
            self.assertEqual(check(self.repo, "--json")[:2], (0, json.dumps(
                {"version": A2, "since": main, "changed": []}) + "\n"), where)
            self.git("checkout", "-q", "--detach", "main")
        self.git("checkout", "-q", "--detach", tip)
        self.assertEqual(check(self.repo), (1, "", branch_line("plugin/lib/row.py", main, A2, A2)))

    def test_7_no_main_an_orphan_and_a_shallow_clone_skip_the_read(self):
        tip, main = self.fault()
        # a shallow clone of the branch alone, and one that holds main's tip too
        for extra in ([], ["--no-single-branch"]):
            clone = os.path.join(self.tmp.name, "shallow%d" % len(extra))
            subprocess.run(["git", "clone", "-q", "--depth", "1", *extra, "--branch", "row",
                            "file://" + self.repo, clone], check=True, env=ENV,
                           capture_output=True)
            self.assertEqual(check(clone), (0, pin_line(A2, tip)[:-1] + NO_BASE, ""), extra)
            self.assertIsNone(json.loads(check(clone, "--json")[1])["base"])
        # an orphan branch beside main: today's read's exit, 0 then 1
        self.git("checkout", "-q", "--orphan", "lone")
        root = self.commit()
        self.assertEqual(check(self.repo), (0, pin_line(A2, root)[:-1] + NO_BASE, ""))
        self.assertIsNone(self.json()[1]["base"])
        self.write("plugin/lib/lone.py", "lone\n")
        code, out, err = check(self.repo)
        self.assertEqual((code, out, len(err.splitlines())), (1, "", 1))
        # a repo whose only branch is trunk: 1 as today, then a bump in flight
        self.git("branch", "-q", "-m", "trunk")
        self.git("branch", "-q", "-D", "main", "row")
        self.assertEqual(check(self.repo)[:2], (1, ""))
        self.manifest(A3)
        self.assertEqual(check(self.repo), (0, "plugin-version-check: version %s is "
                         "uncommitted; the bump in flight covers every change under plugin/"
                         % A3 + NO_BASE, ""))

    def test_8_no_manifest_at_the_merge_base_reads_as_below_any_version(self):
        self.write("README.md", "no plugin yet\n")
        base = self.commit()
        self.git("checkout", "-q", "-b", "new")
        self.manifest("0.0.1")
        self.write("plugin/a.md", "a\n")
        first = self.commit()
        self.assertEqual(check(self.repo), (0, pin_line("0.0.1", first), ""))
        self.assertEqual(self.json()[1]["base"], {"ref": "refs/heads/main", "merge_base": base,
                                                  "version": None, "changed": ["plugin/a.md"]})

    def test_9_a_version_that_cannot_be_ordered_exits_two(self):
        tip, main = self.fault()
        for version in ("2", "v1.0.0", "1.0.0-01", "1.0"):
            self.manifest(version)
            code, out, err = check(self.repo)
            self.assertEqual((code, out), (2, ""), version)
            self.assertEqual(len(err.splitlines()), 1, version)
            self.assertIn("version %s " % version, err)
            self.assertIn(A2, err)
        # the merge base's side: main at "1.0", a branch that changes plugin/
        self.git("checkout", "-q", "-f", "main")
        self.manifest("1.0")
        self.assertEqual(check(self.repo)[0], 0)  # no path listed: today's read alone
        self.commit()
        self.git("checkout", "-q", "-b", "odd")
        self.write("plugin/b.md", "b\n")
        self.manifest("1.1.0")
        self.commit()
        code, out, err = check(self.repo)
        self.assertEqual((code, out, len(err.splitlines())), (2, "", 1))
        self.assertIn("version 1.0 ", err)

    def test_10_origin_main_serves_when_main_is_absent(self):
        tip, main = self.fault()
        self.git("update-ref", "refs/remotes/origin/main", main)
        self.git("branch", "-q", "-D", "main")
        code, data, _ = self.json()
        self.assertEqual((code, data["base"]["ref"], data["base"]["merge_base"]),
                         (1, "refs/remotes/origin/main", main))


class CrissCrossTest(unittest.TestCase):
    """Review 1 of packet c7: in a criss-cross HEAD has two merge bases with main, and
    `git merge-base` prints the one with the newer commit date. Every base is read, and
    the check is red when any fails, so the result never turns on commit dates."""
    setUp, tearDown = VersionCheckTest.setUp, VersionCheckTest.tearDown
    write, manifest = VersionCheckTest.write, VersionCheckTest.manifest
    commit, json = VersionCheckTest.commit, VersionCheckTest.json
    date = "1700000000 +0000"

    def at(self, t):
        self.date = "%d +0000" % (1700000000 + t)

    def git(self, *args):
        p = subprocess.run(["git", "-C", self.repo, *args], capture_output=True, text=True,
                           env=dict(ENV, GIT_AUTHOR_DATE=self.date,
                                    GIT_COMMITTER_DATE=self.date), check=True)
        return p.stdout.strip()

    def criss(self, b_time, m_time, unbumped=False):
        """main at 1.0.0; `br`'s B1 adds plugin/b.md (with `unbumped`, a later commit adds
        plugin/c.md), never bumping; main's M1 adds plugin/m.md and bumps to 1.1.0, merges
        B1, bumps to 1.2.0; `br` merges M1. The merge bases are B1 and M1, dated b_time and
        m_time. (B1, M1)"""
        self.at(0)
        self.manifest("1.0.0")
        self.write("plugin/a.md", "a\n")
        self.commit()
        self.git("checkout", "-q", "-b", "br")
        self.at(b_time)
        self.write("plugin/b.md", "b\n")
        b1 = self.commit()
        if unbumped:
            self.at(b_time + 1)
            self.write("plugin/c.md", "c\n")
            self.commit()
        self.git("checkout", "-q", "main")
        self.at(m_time)
        self.write("plugin/m.md", "m\n")
        self.manifest("1.1.0")
        m1 = self.commit()
        self.at(30)
        self.git("merge", "-q", "--no-edit", b1)
        self.at(40)
        self.manifest("1.2.0")
        self.commit()
        self.git("checkout", "-q", "br")
        self.at(50)
        self.git("merge", "-q", "--no-edit", m1)
        self.assertEqual(sorted(self.git("merge-base", "--all", "HEAD", "main").split()),
                         sorted([b1, m1]))
        # the date order decides which base git prints first: both orders are run
        self.assertEqual(self.git("merge-base", "HEAD", "main"), b1 if b_time > m_time else m1)
        return b1, m1

    def test_f2_an_unbumped_path_fails_against_the_base_it_is_not_above(self):
        for b_time, m_time in ((20, 10), (10, 20)):
            with self.subTest(b_time=b_time, m_time=m_time):
                self.tearDown(), self.setUp()  # a fresh repo per date order
                b1, m1 = self.criss(b_time, m_time, unbumped=True)
                self.assertEqual(check(self.repo), (1, "", (
                    branch_line("plugin/b.md", m1, "1.1.0", "1.1.0")
                    + branch_line("plugin/c.md", m1, "1.1.0", "1.1.0"))))

    def test_f1_a_criss_cross_without_a_bump_is_red_in_both_date_orders(self):
        for b_time, m_time in ((10, 20), (20, 10)):
            with self.subTest(b_time=b_time, m_time=m_time):
                self.tearDown(), self.setUp()  # a fresh repo per date order
                b1, m1 = self.criss(b_time, m_time)
                self.assertEqual(check(self.repo), (
                    1, "", branch_line("plugin/b.md", m1, "1.1.0", "1.1.0")))

    def test_a_bump_above_both_bases_passes_naming_the_higher(self):
        for b_time, m_time in ((10, 20), (20, 10)):
            with self.subTest(b_time=b_time, m_time=m_time):
                self.tearDown(), self.setUp()  # a fresh repo per date order
                b1, m1 = self.criss(b_time, m_time)
                self.manifest("1.3.0")
                code, out, err = check(self.repo)
                self.assertEqual((code, err), (0, ""))
                self.assertTrue(out.endswith(ABOVE % "1.1.0"), out)
                self.at(60)
                bump = self.commit()
                self.assertEqual(check(self.repo),
                                 (0, pin_line("1.3.0", bump)[:-1] + ABOVE % "1.1.0", ""))
                at_m1 = {"ref": "refs/heads/main", "merge_base": m1, "version": "1.1.0",
                         "changed": ["plugin/b.md"]}
                at_b1 = {"ref": "refs/heads/main", "merge_base": b1, "version": "1.0.0",
                         "changed": ["plugin/m.md"]}
                self.assertEqual(self.json(), (0, {
                    "version": "1.3.0", "since": bump, "changed": [], "base": at_m1,
                    "bases": sorted([at_m1, at_b1], key=lambda b: b["merge_base"])}, ""))


class ReadOnlyTest(unittest.TestCase):
    """Review 1's L2: the check never rewrites `.git/index`, a bump in flight included."""
    setUp, tearDown = VersionCheckTest.setUp, VersionCheckTest.tearDown
    git, write, manifest = VersionCheckTest.git, VersionCheckTest.write, VersionCheckTest.manifest
    commit, json = VersionCheckTest.commit, VersionCheckTest.json
    fault = BranchReadTest.fault

    def test_the_index_is_never_rewritten(self):
        self.fault()
        self.manifest(A3)
        old = 1600000000
        os.utime(os.path.join(self.repo, "plugin", "a.md"), (old, old))  # stat-dirty in the index
        index = Path(self.repo, ".git", "index")
        before = index.read_bytes()
        self.assertEqual(check(self.repo)[0], 0)
        self.assertEqual(index.read_bytes(), before)
        # one merge base: no `bases` key
        self.assertNotIn("bases", self.json()[1])


if __name__ == "__main__":
    unittest.main()
