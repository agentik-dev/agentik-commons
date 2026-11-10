"""scripts/hygiene --commits <range>: the added lines and the messages of a commit range,
counts only. Every private term here is invented, and every fixture is assembled at
runtime, so this file scans clean under the tree scan itself (packet h1)."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "hygiene"
ENV = "AGENTIK_HYGIENE_PRIVATE"
PRIVATE = "private\tzorbla[x]-ops\nperson\tglimmerwic[k]\nemail\tsnorkelwi[x]\n"
TERM = "the zorbla" + "x-ops mirror"            # the private group
PERSON = "by Glimmer" + "wick"                  # the person group
HOME = "see /Us" + "ers/alice/notes"            # the home group
SIBLING = "load resp" + "eak first"             # the sibling group
OLD_NAME = "agent-" + "relay"                   # the renamed group
MATCHED = ["zorbla" + "x-ops", "glimmer" + "wick", "/us" + "ers/alice"]
TRAILER = "Co-Authored-By: Some One <noreply" + "@example.com>"
GENERIC_MAIL = "noreply" + "@example.com"     # the generic email group
PRIVATE_MAIL = "Snorkel" + "wix"               # a private row of the email group
CHUNK = 1024 * 1024


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


def run(repo, *args, env_extra=None):
    env = dict(os.environ, **GIT_ENV)
    env[ENV] = PRIVATE_FILE
    env.update(env_extra or {})
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

    # The refuter's fold, round 1 (F1, F3, F4, F7, F8, F9).

    def subject_only(self, message):
        # git refuses a message of sign-off lines alone unless told verbatim
        git(self.repo, "commit", "-q", "--allow-empty", "--cleanup=verbatim", "-m", message)
        return git(self.repo, "rev-parse", "HEAD")

    def test_c13_an_untracked_allow_row_blesses_nothing(self):
        self.commit({"x.md": TERM + "\n"})
        Path(self.repo, ".hygiene-allow").write_text("x.md: private\n")  # never committed
        code, d = self.scan()
        self.assertEqual((code, self.outside(d)), (1, {("x.md", "private"): 1}))

    def test_c14_the_allowlist_is_the_range_tips_not_the_checkouts(self):
        git(self.repo, "checkout", "-q", "main")
        self.commit({".hygiene-allow": "x.md: private\n"}, "main allows")
        git(self.repo, "checkout", "-q", "-B", "work", "main")
        self.commit({"x.md": TERM + "\n"}, delete=[".hygiene-allow"])
        git(self.repo, "checkout", "-q", "main")  # the checkout allows, the tip does not
        code, d = self.scan()
        self.assertEqual((code, self.outside(d)), (1, {("x.md", "private"): 1}))
        git(self.repo, "checkout", "-q", "-b", "kept", "work")
        self.commit({".hygiene-allow": "x.md: private\n"}, "the tip allows")
        git(self.repo, "rm", "-q", "--cached", ".hygiene-allow")
        os.unlink(os.path.join(self.repo, ".hygiene-allow"))  # the working tree has none
        code, d = self.scan("main..kept")
        self.assertEqual((code, d["files"]), (0, []))

    def test_c15_a_trailer_skips_the_generic_email_alone_and_only_in_trailer_position(self):
        hits = {self.commit({}, "s\n\nCo-Authored-By: " + PRIVATE_MAIL + " <" + GENERIC_MAIL + ">"),
                self.commit({}, "s\n\nSigned-off-by: " + TERM),
                self.commit({}, "s\n\nSigned-off-by: x " + GENERIC_MAIL + "\n\nlast paragraph"),
                self.subject_only("Signed-off-by: " + GENERIC_MAIL)}
        self.commit({}, "s\n\nbody\n\n" + TRAILER + "\nSigned-off-by: x <" + GENERIC_MAIL + ">")
        code, d = self.scan()
        self.assertEqual(code, 1)
        self.assertEqual(self.outside(d), {("(commit message)", "email"): 3,
                                           ("(commit message)", "private"): 1})
        self.assertEqual(set(d["commits"]["hit"]), {sha[:12] for sha in hits})

    def test_c16_a_replace_ref_or_graft_hides_no_commit(self):
        leak = self.commit({"a.txt": TERM + "\n"}, "leaky")
        tip = self.commit({"a.txt": "c\n"}, "tidy")
        git(self.repo, "checkout", "-q", "-b", "twin", "main")
        twin = self.commit({"a.txt": "harmless\n"}, "leaky")
        git(self.repo, "checkout", "-q", "work")
        git(self.repo, "replace", leak, twin)
        code, d = self.scan()
        self.assertEqual((code, d["commits"]["scanned"]), (1, 2))
        git(self.repo, "replace", "-d", leak)
        git(self.repo, "replace", "--graft", tip, "main")
        code, d = self.scan()
        self.assertEqual((code, d["commits"]), (1, {"scanned": 2, "hit": [leak[:12]]}))

    def test_c17_git_environment_never_redirects_either_scan(self):
        decoy = tempfile.TemporaryDirectory()
        self.addCleanup(decoy.cleanup)
        git(decoy.name, "init", "-q", "-b", "main")
        Path(decoy.name, "README.md").write_text("clean\n")
        git(decoy.name, "add", "README.md")
        git(decoy.name, "commit", "-q", "-m", "decoy")
        self.commit({"x.md": TERM + "\n"})
        env = {"GIT_DIR": os.path.join(decoy.name, ".git"), "GIT_WORK_TREE": decoy.name,
               "GIT_INDEX_FILE": os.path.join(decoy.name, ".git", "index")}
        for args in (("--json", "--commits", "main..work"), ("--json",)):
            code, out, err = run(self.repo, *args, env_extra=env)
            self.assertEqual((code, err), (1, ""), args)
            self.assertIn({"path": "x.md", "group": "private", "lines": 1},
                          json.loads(out)["files"], args)

    def test_c18_the_commits_touching_the_allowlist_are_named(self):
        self.commit({"a.md": "a\n"})
        allow = self.commit({".hygiene-allow": "a.md: person\n"}, "allow")
        self.commit({"b.md": "b\n"})
        code, d = self.scan()
        self.assertEqual((code, d["commits"]["allowlist_changed"]), (0, [allow[:12]]))
        text = run(self.repo, "--commits", "main..work")[1]
        self.assertIn("allowlist changed in the range: " + allow[:12], text.splitlines())
        code, d = self.scan(allow + "..work")
        self.assertNotIn("allowlist_changed", d["commits"])
        self.assertNotIn("allowlist", run(self.repo, "--commits", allow + "..work")[1])

    def test_c19_a_root_commit_is_scanned_whatever_log_showroot_says(self):
        git(self.repo, "config", "log.showRoot", "false")
        git(self.repo, "checkout", "-q", "--orphan", "root")
        git(self.repo, "rm", "-q", "-r", "--cached", ".")
        root = self.commit({"r.md": TERM + "\n"}, "root")
        code, d = self.scan("root")
        self.assertEqual((code, d["commits"]), (1, {"scanned": 1, "hit": [root[:12]]}))

    def test_c20_a_blob_git_cannot_read_is_the_failure_exit(self):
        self.commit({"blob.bin": b"\0\1" + HOME.encode()})
        bindir = tempfile.TemporaryDirectory()
        self.addCleanup(bindir.cleanup)
        fake = Path(bindir.name, "git")
        fake.write_text('#!/bin/sh\ncase " $* " in *" cat-file blob "*) exit 3;; esac\n'
                        'exec "%s" "$@"\n' % shutil.which("git"))
        fake.chmod(0o755)
        path = bindir.name + os.pathsep + os.environ.get("PATH", "")
        code, out, err = run(self.repo, "--commits", "main..work", env_extra={"PATH": path})
        self.assertEqual((code, out), (2, ""))
        self.assertIn("cat-file", err)

    def test_c21_an_external_diff_or_textconv_hides_no_line(self):
        git(self.repo, "config", "diff.external", "/usr/bin/true")
        git(self.repo, "config", "diff.tc.textconv", "/usr/bin/true")
        Path(self.repo, ".git", "info").mkdir(exist_ok=True)
        Path(self.repo, ".git", "info", "attributes").write_text("*.txt diff=tc\n")
        self.commit({"a.txt": TERM + "\n"})
        code, d = self.scan()
        self.assertEqual((code, self.outside(d)), (1, {("a.txt", "private"): 1}))

    def test_c22_a_match_across_a_pieces_cut_is_seen_once(self):
        # the diff's `+` and TERM's "the " put the match's start 3 bytes before the cut
        self.commit({"long.txt": "x" * (CHUNK - 8) + TERM + "\n"})
        code, d = self.scan()
        self.assertEqual((code, self.outside(d), d["oversize"]),
                         (1, {("long.txt", "private"): 1}, 1))

    def test_c23_a_quoted_path_is_unquoted(self):
        self.commit({'q"uote\\d.md': PERSON + "\n"})
        code, d = self.scan()
        self.assertEqual((code, self.outside(d)), (1, {('q"uote\\d.md', "person"): 1}))

    def test_c24_no_allow_row_covers_a_message(self):
        self.commit({".hygiene-allow": "*: person\n"}, "s\n\n" + PERSON)
        code, d = self.scan()
        self.assertEqual((code, self.outside(d)), (1, {("(commit message)", "person"): 1}))


if __name__ == "__main__":
    unittest.main()
