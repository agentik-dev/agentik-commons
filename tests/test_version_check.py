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


if __name__ == "__main__":
    unittest.main()
