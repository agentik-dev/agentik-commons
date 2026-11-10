"""scripts/hygiene --commits <range>: the added lines and the messages of a commit range,
counts only. Every private term here is invented, and every fixture is assembled at
runtime, so this file scans clean under the tree scan itself (packet h1)."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "hygiene"
ENV = "AGENTIK_HYGIENE_PRIVATE"
PRIVATE = "private\tzorbla[x]-ops\nperson\tglimmerwic[k]\n"
TERM = "the zorbla" + "x-ops mirror"            # the private group
PERSON = "by Glimmer" + "wick"                  # the person group
HOME = "see /Us" + "ers/alice/notes"            # the home group
SIBLING = "load resp" + "eak first"             # the sibling group
OLD_NAME = "agent-" + "relay"                   # the renamed group
MATCHED = ["zorbla" + "x-ops", "glimmer" + "wick", "/us" + "ers/alice"]
TRAILER = "Co-Authored-By: Some One <noreply" + "@example.com>"


def setUpModule():
    global PRIVATE_DIR, PRIVATE_FILE
    PRIVATE_DIR = tempfile.TemporaryDirectory()
    PRIVATE_FILE = os.path.join(PRIVATE_DIR.name, "private.tsv")
    Path(PRIVATE_FILE).write_text(PRIVATE)


def tearDownModule():
    PRIVATE_DIR.cleanup()


MAIL = "t" + "@x.invalid"
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": MAIL,
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": MAIL,
           "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}


def git(repo, *args):
    env = dict(os.environ, **GIT_ENV)
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True,
                          text=True, env=env).stdout.strip()


def run(repo, *args):
    env = dict(os.environ, **GIT_ENV)
    env[ENV] = PRIVATE_FILE
    p = subprocess.run([str(SCRIPT), "--repo", repo, *args], capture_output=True,
                       text=True, env=env)
    return p.returncode, p.stdout, p.stderr


class CommitsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        git(self.repo, "init", "-q", "-b", "main")
        self.commit({"README.md": "clean\n"}, "base")
        git(self.repo, "checkout", "-q", "-b", "work")

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self, files, message="work", delete=()):
        for rel, text in files.items():
            path = Path(self.repo, rel)
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(text, bytes):
                path.write_bytes(text)
            else:
                path.write_text(text)
        for rel in delete:
            git(self.repo, "rm", "-q", rel)
        if files:
            git(self.repo, "add", "--", *files)
        git(self.repo, "commit", "-q", "--allow-empty", "-m", message)
        return git(self.repo, "rev-parse", "HEAD")

    def scan(self, rng="main..work"):
        code, out, err = run(self.repo, "--json", "--commits", rng)
        self.assertEqual(err, "")
        return code, json.loads(out)

    def outside(self, d):
        return {(f["path"], f["group"]): f["lines"] for f in d["files"]}

    def test_c1_a_term_added_then_removed_is_a_hit_while_the_tree_is_clean(self):
        first = self.commit({"notes.md": "a\n" + TERM + "\n"})
        self.commit({"notes.md": "a\n"}, "tidy")
        self.assertEqual(run(self.repo)[0], 0)  # the tree scan sees nothing
        code, d = self.scan()
        self.assertEqual(code, 1)
        self.assertEqual(self.outside(d), {("notes.md", "private"): 1})
        self.assertEqual(d["commits"], {"scanned": 2, "hit": [first[:12]]})

    def test_c2_a_message_is_scanned_its_trailer_and_sibling_are_not(self):
        sha = self.commit({}, "subject\n\n" + PERSON + "\n" + SIBLING + "\n\n" + TRAILER)
        self.commit({}, "plain\n\n" + TRAILER)
        code, d = self.scan()
        self.assertEqual(code, 1)
        self.assertEqual(self.outside(d), {("(commit message)", "person"): 1})
        self.assertEqual(d["commits"]["hit"], [sha[:12]])

    def test_c3_the_heads_allowlist_rules_every_commit(self):
        self.commit({"LICENSE": PERSON + "\n", ".hygiene-allow": "LICENSE: person\n"})
        code, d = self.scan()
        self.assertEqual((code, d["files"]), (0, []))
        self.assertEqual(d["groups"]["person"]["lines"], 1)
        # a row a commit adds and a later one removes blesses nothing
        self.commit({"x.md": TERM + "\n", ".hygiene-allow": "LICENSE: person\nx.md: private\n"})
        self.commit({".hygiene-allow": "LICENSE: person\n"}, "drop the row")
        code, d = self.scan()
        self.assertEqual((code, self.outside(d)), (1, {("x.md", "private"): 1}))

    def test_c4_a_term_only_in_a_removed_line_is_no_hit(self):
        git(self.repo, "checkout", "-q", "main")
        self.commit({"old.md": "keep\n" + TERM + "\n"}, "already public")
        git(self.repo, "checkout", "-q", "work")
        git(self.repo, "reset", "-q", "--hard", "main")
        self.commit({"old.md": "keep\n"}, "remove it")
        code, d = self.scan()
        self.assertEqual((code, d["files"], d["commits"]["scanned"]), (0, [], 1))

    def test_c5_a_term_in_a_file_deleted_later_is_a_hit(self):
        self.commit({"tmp/scratch.txt": TERM + "\n"})
        self.commit({}, "drop", delete=["tmp/scratch.txt"])
        code, d = self.scan()
        self.assertEqual((code, self.outside(d)), (1, {("tmp/scratch.txt", "private"): 1}))

    def test_c6_no_matched_text_is_ever_printed(self):
        self.commit({"a.md": TERM + "\n" + HOME + "\n"}, "m\n\n" + PERSON)
        for args in (("--commits", "main..work"), ("--json", "--commits", "main..work")):
            code, out, err = run(self.repo, *args)
            self.assertEqual(code, 1)
            for token in MATCHED:
                self.assertNotIn(token, (out + err).lower(), args)
        text = run(self.repo, "--commits", "main..work")[1]
        self.assertIn("commits: 1 scanned, 1 with a hit outside the allowlist: ", text)
        self.assertIn("(commit message)  person  1", text.splitlines())

    def test_c7_a_bad_range_is_the_git_failure_exit(self):
        for rng in ("main..nosuchbranch", "nosuch..work"):
            code, out, err = run(self.repo, "--commits", rng)
            self.assertEqual((code, out), (2, ""), rng)
            self.assertIn("git log", err)
        for args in (("--commits",), ("--commits", ""), ("--commits", "--all")):
            self.assertEqual(run(self.repo, *args)[0], 2, args)

    def test_c8_an_empty_range_is_clean(self):
        self.commit({"a.md": TERM + "\n"})
        code, d = self.scan("work..work")
        self.assertEqual((code, d["files"], d["commits"]), (0, [], {"scanned": 0, "hit": []}))

    def test_c9_path_rules_binaries_and_new_paths(self):
        self.commit({"history/sittings/2026-01-01-1.md": SIBLING + "\n",
                     "src/a.py": "# " + OLD_NAME + "\n",
                     "blob.bin": b"\0\1" + HOME.encode() + b"\0" + TERM.encode(),
                     "docs/zorbla" + "x-ops.md": "clean\n"})
        code, d = self.scan()
        hits = self.outside(d)
        self.assertNotIn(("history/sittings/2026-01-01-1.md", "sibling"), hits)
        self.assertNotIn("renamed", d["groups"])  # a live-files group, never on history
        self.assertEqual(hits[("blob.bin", "home")], 1)
        self.assertNotIn(("blob.bin", "private"), hits)  # a binary: home, secret, email only
        self.assertEqual(hits[("docs/zorbla" + "x-ops.md", "private")], 1)  # a new path is a line

    def test_c10_a_merge_scans_its_message_and_never_its_diff_twice(self):
        git(self.repo, "checkout", "-q", "-b", "side")
        self.commit({"s.md": TERM + "\n"})
        git(self.repo, "checkout", "-q", "work")
        self.commit({"w.md": "w\n"})
        git(self.repo, "merge", "-q", "--no-ff", "-m", "merge side\n\n" + PERSON, "side")
        code, d = self.scan()
        self.assertEqual(self.outside(d), {("s.md", "private"): 1,
                                           ("(commit message)", "person"): 1})
        self.assertEqual(d["commits"]["scanned"], 3)

    def test_c11_a_long_line_and_hostile_config_are_still_scanned(self):
        for key, value in (("diff.noprefix", "true"), ("diff.mnemonicPrefix", "true"),
                           ("color.ui", "always"), ("core.quotePath", "true")):
            git(self.repo, "config", key, value)
        self.commit({"big.txt": "x" * (3 * 1024 * 1024) + TERM + "\n",
                     "sp aceé.md": PERSON + "\n"})
        code, d = self.scan()
        self.assertEqual(self.outside(d), {("big.txt", "private"): 1,
                                           ("sp aceé.md", "person"): 1})

    def test_c12_help_names_the_flag(self):
        code, out, err = run(self.repo, "--help")
        self.assertEqual(code, 0)
        self.assertIn("--commits RANGE", out)


if __name__ == "__main__":
    unittest.main()
