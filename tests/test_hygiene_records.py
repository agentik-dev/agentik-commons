"""Packet rr3-records-guard: scripts/hygiene's judged group `records` (hq design/28 §3 item 10).
A repo that declares its records out (the whole line `records: out` in `.hygiene-allow`) holds
no path under a record name, in its tree or in a range it pushes. Every repo here is a temp
clone with made-up content; no test reads the live private list, home or git config."""
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hygiene"
RESOLVER = ROOT / "scripts" / "agentik_records.py"
ENV = "AGENTIK_HYGIENE_PRIVATE"
PRIVATE = "private\tzorbla[x]-ops\n"
DECLARE = "records: out\n"
MAIL = "t" + "@x.invalid"  # split, so no line of this file is an address
RECORDS = ["history/sittings/2026-01-01-1.md", "history/sessions/NEXT", "design/packets/p.md",
           "HANDOFF.md", "NICE_TO_HAVE.md", "OPEN-QUESTIONS.md", "bugs/b1.md",
           "relay/queue.yaml", ".hygiene-live"]
# C3: the root names compare case-folded, so `Handoff.md` and `History/` are records
FOLDED = ["Handoff.md", "History/sittings/2026-01-01-1.md", "Bugs/b1.md", "Design/Packets/p.md",
          "RELAY/Queue.yaml", ".HYGIENE-LIVE"]
NOT_RECORDS = ["design/notes.md", "docs/HANDOFF.md", "history.md",
               "relay/other.yaml", "design/packets-old/p.md", "sub/history/x.md", "README.md",
               "DECI" + "SIONS.md", "DESIGN.md", ".claude/agentik/config.yaml"]
# rr2 review 1's probe5: near misses that declare nothing, then the lines that declare
NEAR = ["records: out # reason", "records:  out", "  records: out", 'records: "out"',
        "﻿records: out"]
EXACT = ["records: out", "records: out   ", "records: out\r"]


def setUpModule():
    global PRIVATE_DIR, PRIVATE_FILE, QUIET
    PRIVATE_DIR = tempfile.TemporaryDirectory()
    PRIVATE_FILE = os.path.join(PRIVATE_DIR.name, "private.tsv")
    Path(PRIVATE_FILE).write_text(PRIVATE)
    QUIET = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    QUIET.update({"HOME": PRIVATE_DIR.name, "XDG_CONFIG_HOME": os.path.join(PRIVATE_DIR.name, "c"),
                  "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                  "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": MAIL,
                  "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": MAIL, ENV: PRIVATE_FILE})


def tearDownModule():
    PRIVATE_DIR.cleanup()


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True,
                          text=True, env=QUIET).stdout.strip()


def run(repo, *args, private=True):
    env = dict(QUIET)
    if not private:
        env[ENV] = os.path.join(PRIVATE_DIR.name, "absent.tsv")
    p = subprocess.run([str(SCRIPT), "--repo", repo, *args], capture_output=True, text=True,
                       env=env)
    return p.returncode, p.stdout, p.stderr


def resolver_state(repo):
    spec = importlib.util.spec_from_file_location("agentik_records_rr3", RESOLVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with mock.patch.dict(os.environ, QUIET, clear=True):
        return module.resolve(repo)["state"]


class Repo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.realpath(self.tmp.name)
        git(self.repo, "init", "-q", "-b", "main")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, files):
        for rel, text in files.items():
            path = Path(self.repo, rel)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text if isinstance(text, bytes) else text.encode("utf-8"))

    def commit(self, files, message="work", delete=()):
        self.write(files)
        for rel in delete:
            git(self.repo, "rm", "-q", rel)
        if files:
            git(self.repo, "add", "--", *files)
        git(self.repo, "commit", "-q", "--allow-empty", "-m", message)
        return git(self.repo, "rev-parse", "HEAD")[:12]

    def scan(self, *args, code=None, private=True):
        got, out, err = run(self.repo, "--json", *args, private=private)
        if code is not None:
            self.assertEqual(got, code, err)
        return got, (json.loads(out) if out else None), err

    def records(self, d):
        return sorted(f["path"] for f in d["files"] if f["group"] == "records")


class TreeTest(Repo):
    """G1 to G3: the tree scan of a declaring repo."""

    def setUp(self):
        super().setUp()
        self.commit({"README.md": "clean\n", ".hygiene-allow": "# ours\n" + DECLARE}, "base")

    def test_a_declared_tree_with_no_record_is_clean_and_shows_the_group(self):
        _, d, _ = self.scan(code=0)
        self.assertEqual(d["groups"]["records"],
                         {"lines": 0, "files": 0, "outside_lines": 0, "outside_files": 0})

    def test_a_tracked_record_is_a_hit(self):
        self.commit({"HANDOFF.md": "| # | item |\n"})
        _, d, _ = self.scan(code=1)
        self.assertEqual(self.records(d), ["HANDOFF.md"])
        self.assertEqual(d["groups"]["records"]["outside_lines"], 1)

    def test_an_untracked_record_is_a_hit_before_its_commit(self):
        self.write({"history/sittings/2026-01-01-1.md": "# a charter\n"})
        _, d, _ = self.scan(code=1)
        self.assertEqual(self.records(d), ["history/sittings/2026-01-01-1.md"])

    def test_an_ignored_record_is_not_scanned(self):
        self.commit({".gitignore": "history/\n"})
        self.write({"history/x.md": "a\n"})
        self.scan(code=0)

    def test_the_line_removed_in_the_working_file_alone_still_declares(self):
        self.commit({"NICE_TO_HAVE.md": "# Nice\n"})
        self.write({".hygiene-allow": "# ours\n"})
        _, d, _ = self.scan(code=1)
        self.assertEqual(self.records(d), ["NICE_TO_HAVE.md"])

    def test_the_line_added_in_the_working_file_alone_declares(self):
        self.commit({".hygiene-allow": "# ours\n", "bugs/b1.md": "a\n"})
        self.scan(code=0)
        self.write({".hygiene-allow": DECLARE})
        _, d, _ = self.scan(code=1)
        self.assertEqual(self.records(d), ["bugs/b1.md"])

    def test_every_record_name_and_no_other(self):
        self.commit({p: "a\n" for p in RECORDS + NOT_RECORDS})
        _, d, _ = self.scan(code=1)
        self.assertEqual(self.records(d), sorted(RECORDS))
        self.assertEqual(d["groups"]["records"]["lines"], len(RECORDS))

    def test_no_allow_row_for_another_group_excuses_a_record(self):
        self.commit({"OPEN-QUESTIONS.md": "a\n",
                     ".hygiene-allow": DECLARE + "OPEN-QUESTIONS.md: sibling\n"})
        _, d, _ = self.scan(code=1)
        self.assertEqual(self.records(d), ["OPEN-QUESTIONS.md"])

    def test_an_allow_file_named_on_the_line_declares_too(self):
        git(self.repo, "rm", "-q", ".hygiene-allow")
        self.commit({"HANDOFF.md": "a\n"})
        other = os.path.join(PRIVATE_DIR.name, "declare.allow")
        Path(other).write_text(DECLARE)
        self.scan(code=0)
        self.scan("--allow", other, code=1)

    def test_the_other_groups_count_as_before(self):
        self.commit({"HANDOFF.md": "see /Us" + "ers/alice/notes\n"})
        _, d, _ = self.scan(code=1)
        self.assertEqual(d["groups"]["home"]["lines"], 1)
        self.assertEqual(sorted((f["path"], f["group"]) for f in d["files"]),
                         [("HANDOFF.md", "home"), ("HANDOFF.md", "records")])

    def test_the_text_table_names_the_group(self):
        self.commit({"HANDOFF.md": "a\n"})
        code, out, _ = run(self.repo)
        self.assertEqual(code, 1)
        self.assertIn("HANDOFF.md  records  1", out)
        self.assertRegex(out, r"(?m)^records +1 +1$")


class UndeclaredTest(Repo):
    def test_an_undeclared_tree_with_records_has_no_hit_and_no_group(self):
        self.commit({p: "a\n" for p in RECORDS} | {".hygiene-allow": "# none\n"})
        _, d, _ = self.scan(code=0)
        self.assertNotIn("records", d["groups"])
        code, out, _ = run(self.repo)
        self.assertNotIn("records", out)

    def test_no_allow_file_declares_nothing(self):
        self.commit({"HANDOFF.md": "a\n"})
        self.scan(code=0)


class BadRowTest(Repo):
    """G1, G2: a row naming `records`, and an `out` line that is not the declaration."""

    def bad(self, text, private=True):
        self.commit({".hygiene-allow": text, "README.md": "a\n"})
        code, out, err = run(self.repo, private=private)
        self.assertEqual((code, out), (2, ""), err)
        self.assertIn(".hygiene-allow:", err)
        self.assertIn("bad entry", err)

    def test_a_records_row_is_a_bad_entry(self):
        self.bad("HANDOFF.md: records\n")

    def test_a_records_row_among_groups_is_a_bad_entry(self):
        self.bad(DECLARE + "history/*: sibling,records\n")

    def test_a_records_row_without_the_private_list_is_a_bad_entry(self):
        self.bad("HANDOFF.md: records\n", private=False)

    def test_an_out_row_on_a_path_is_a_bad_entry(self):
        self.bad("docs/*.md: out\n")

    def test_an_out_row_without_the_private_list_is_a_bad_entry(self):
        self.bad("records:  out\n", private=False)

    def test_a_range_tip_with_a_records_row_is_a_bad_entry(self):
        self.commit({".hygiene-allow": "HANDOFF.md: records\n"})
        code, out, err = run(self.repo, "--commits", "HEAD")
        self.assertEqual(code, 2, err)
        self.assertIn("bad entry", err)


class ProbeTest(unittest.TestCase):
    """probe5's lines through both readers: the resolver and the scanner give one answer."""

    def answers(self, line):
        with tempfile.TemporaryDirectory() as tmp:
            repo = os.path.realpath(tmp)
            git(repo, "init", "-q", "-b", "main")
            Path(repo, ".hygiene-allow").write_bytes((line + "\n").encode("utf-8"))
            Path(repo, "HANDOFF.md").write_text("a\n")
            git(repo, "add", "--", ".hygiene-allow", "HANDOFF.md")
            git(repo, "commit", "-q", "-m", "base")
            state = resolver_state(repo)
            code, out, err = run(repo, "--json")
        scanner = "refused" if code == 2 else (
            "declared" if "records" in json.loads(out)["groups"] else "undeclared")
        return state, scanner

    def test_near_misses_declare_nothing_in_either_reader(self):
        for line in NEAR:
            with self.subTest(line=line):
                self.assertEqual(self.answers(line), ("own", "refused"))

    def test_the_whole_line_declares_in_both(self):
        for line in EXACT:
            with self.subTest(line=line):
                self.assertEqual(self.answers(line), ("unset", "declared"))

    def test_the_two_rules_agree_line_by_line(self):
        loader = SourceFileLoader("hygiene_rr3", str(SCRIPT))
        hygiene = importlib.util.module_from_spec(importlib.util.spec_from_loader("hygiene_rr3", loader))
        loader.exec_module(hygiene)
        spec = importlib.util.spec_from_file_location("agentik_records_rr3b", RESOLVER)
        resolver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(resolver)
        (path, line), = resolver.DECLARED
        self.assertEqual((path, line), (hygiene.ALLOW_FILE, hygiene.DECLARATION))
        for text in NEAR + EXACT + ["# c\n" + DECLARE, "a: sibling\r\nrecords: out\r\n"]:
            with self.subTest(text=text):
                rows = any(r.rstrip() == line for r in text.splitlines())
                self.assertEqual(hygiene.declares(text), rows)


class RangeTest(Repo):
    """G4: the range scan, read from each end's blob."""

    def setUp(self):
        super().setUp()
        self.commit({"README.md": "clean\n"}, "base")
        git(self.repo, "checkout", "-q", "-b", "work")

    def test_a_range_adding_a_record_under_a_declaring_tip(self):
        sha = self.commit({"history/sittings/2026-01-01-1.md": "a\n"})
        tip = self.commit({".hygiene-allow": DECLARE})
        _, d, _ = self.scan("--commits", "main..work", code=1)
        self.assertEqual(self.records(d), ["history/sittings/2026-01-01-1.md"])
        self.assertEqual(d["commits"]["hit"], [sha])
        self.assertNotIn(tip, d["commits"]["hit"])

    def test_a_modified_record_counts_each_commit(self):
        self.commit({".hygiene-allow": DECLARE, "HANDOFF.md": "a\n"})
        self.commit({"HANDOFF.md": "b\n"})
        _, d, _ = self.scan("--commits", "main..work", code=1)
        self.assertEqual(d["groups"]["records"]["lines"], 2)
        self.assertEqual(len(d["commits"]["hit"]), 2)

    def test_an_empty_record_and_a_mode_change_count(self):
        self.commit({".hygiene-allow": DECLARE, "bugs/b1.md": ""})
        git(self.repo, "update-index", "--chmod=+x", "bugs/b1.md")
        self.commit({})
        _, d, _ = self.scan("--commits", "main..work", code=1)
        self.assertEqual(d["groups"]["records"]["lines"], 2)

    def test_a_removed_record_is_no_hit(self):
        git(self.repo, "checkout", "-q", "main")
        self.commit({"HANDOFF.md": "a\n"})
        git(self.repo, "checkout", "-q", "-B", "work")
        self.commit({".hygiene-allow": DECLARE}, delete=["HANDOFF.md"])
        _, d, _ = self.scan("--commits", "main..work", code=0)
        self.assertEqual(d["groups"]["records"]["lines"], 0)

    def test_a_base_that_declares_and_a_tip_that_does_not(self):
        git(self.repo, "checkout", "-q", "main")
        self.commit({".hygiene-allow": DECLARE})
        git(self.repo, "checkout", "-q", "-B", "work")
        sha = self.commit({"HANDOFF.md": "a\n"})
        tip = self.commit({".hygiene-allow": "# gone\n"})
        _, d, _ = self.scan("--commits", "main..work", code=1)
        self.assertEqual(self.records(d), [".hygiene-allow", "HANDOFF.md"])
        rows = {f["path"]: f["lines"] for f in d["files"] if f["group"] == "records"}
        self.assertEqual(rows[".hygiene-allow"], 1)
        self.assertEqual(sorted(d["commits"]["hit"]), sorted([sha, tip]))

    def test_the_switch_off_alone_is_a_hit(self):
        git(self.repo, "checkout", "-q", "main")
        self.commit({".hygiene-allow": DECLARE})
        git(self.repo, "checkout", "-q", "-B", "work")
        self.commit({".hygiene-allow": "# gone\n"})
        _, d, _ = self.scan("--commits", "main..work", code=1)
        self.assertEqual(self.records(d), [".hygiene-allow"])

    def test_an_undeclared_range_with_records_has_no_hit_and_no_group(self):
        self.commit({"HANDOFF.md": "a\n", "history/x.md": "b\n"})
        _, d, _ = self.scan("--commits", "main..work", code=0)
        self.assertNotIn("records", d["groups"])

    def test_a_range_without_a_base_reads_the_tip(self):
        self.commit({"HANDOFF.md": "a\n", ".hygiene-allow": DECLARE})
        _, d, _ = self.scan("--commits", "work", code=1)
        self.assertEqual(self.records(d), ["HANDOFF.md"])

    def test_the_working_file_does_not_move_a_range(self):
        self.commit({"HANDOFF.md": "a\n"})
        self.write({".hygiene-allow": DECLARE})
        self.scan("--commits", "main..work", code=0)

    def test_an_allow_flag_keeps_the_blobs_declaration(self):
        self.commit({"HANDOFF.md": "a\n", ".hygiene-allow": DECLARE})
        other = os.path.join(PRIVATE_DIR.name, "rows.allow")
        Path(other).write_text("HANDOFF.md: sibling\n")
        self.scan("--commits", "main..work", "--allow", other, code=1)


class FixTest(Repo):
    """Review 1's F1 to F5 (brief 2's C1 to C4), each probe a case."""

    def declared_main(self):
        self.commit({"README.md": "a\n", ".hygiene-allow": DECLARE}, "base")
        return git(self.repo, "rev-parse", "HEAD")

    def test_f1_a_symlinked_allow_file_at_a_base_declares_nothing(self):
        Path(self.repo, "rows.txt").write_text("# none\n")
        os.symlink("rows.txt", os.path.join(self.repo, ".hygiene-allow"))
        git(self.repo, "add", "--", "rows.txt", ".hygiene-allow")
        git(self.repo, "commit", "-q", "-m", "base")
        base = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "rm", "-q", ".hygiene-allow")
        self.commit({".hygiene-allow": "# none\n", "HANDOFF.md": "a\n"})
        got, d, err = self.scan("--commits", base + "..HEAD", code=0)
        self.assertEqual(err, "")
        self.assertNotIn("records", d["groups"])

    def test_f1_a_tracked_symlinked_allow_file_in_an_undeclared_tree(self):
        Path(self.repo, "rows.txt").write_text("# none\n")
        os.symlink("rows.txt", os.path.join(self.repo, ".hygiene-allow"))
        self.commit({"rows.txt": "# none\n"})
        git(self.repo, "add", "--", ".hygiene-allow")
        self.commit({"HANDOFF.md": "a\n"})
        got, d, err = self.scan(code=0)
        self.assertEqual(err, "")
        self.assertNotIn("records", d["groups"])

    def test_f1_a_symlink_holding_the_line_declares_nothing(self):
        Path(self.repo, "rows.txt").write_text(DECLARE)
        os.symlink("rows.txt", os.path.join(self.repo, ".hygiene-allow"))
        git(self.repo, "add", "--", "rows.txt", ".hygiene-allow")
        self.commit({"HANDOFF.md": "a\n"})
        self.assertEqual(resolver_state(self.repo), "own")
        _, d, _ = self.scan(code=0)
        self.assertNotIn("records", d["groups"])

    def test_f2_a_record_only_a_merge_adds_is_a_hit(self):
        base = self.declared_main()
        git(self.repo, "checkout", "-q", "-b", "side")
        self.commit({"side.txt": "s\n"})
        git(self.repo, "checkout", "-q", "main")
        self.commit({"m.txt": "m\n"})
        subprocess.run(["git", "-C", self.repo, "merge", "-q", "--no-commit", "side"],
                       capture_output=True, env=QUIET)
        merge = self.commit({"history/notes.md": "notes\n"}, "merge")
        self.commit({}, "drop", delete=["history/notes.md"])
        self.assertIn("history/notes.md", git(self.repo, "ls-tree", "-r", "--name-only", merge))
        _, d, _ = self.scan("--commits", base + "..main", code=1)
        self.assertEqual(self.records(d), ["history/notes.md"])
        self.assertEqual(d["commits"]["hit"], [merge])
        self.scan(code=0)

    def test_f2_a_merge_that_brings_no_record_adds_no_hit(self):
        base = self.declared_main()
        git(self.repo, "checkout", "-q", "-b", "side")
        self.commit({"side.txt": "s\n"})
        git(self.repo, "checkout", "-q", "main")
        self.commit({"m.txt": "m\n"})
        git(self.repo, "merge", "-q", "--no-edit", "side")
        _, d, _ = self.scan("--commits", base + "..main", code=0)
        self.assertEqual(d["groups"]["records"]["lines"], 0)

    def test_f3_a_working_file_not_utf8_beside_an_allow_flag_passes(self):
        self.commit({"README.md": "a\n"})
        self.write({".hygiene-allow": b"# \xff\n"})
        other = os.path.join(PRIVATE_DIR.name, "plain.allow")
        Path(other).write_text("# none\n")
        _, d, err = self.scan("--allow", other, code=0)
        self.assertEqual(err, "")
        self.assertNotIn("records", d["groups"])

    def test_f3_a_declaration_beside_bytes_not_utf8_still_declares(self):
        self.commit({"README.md": "a\n", "HANDOFF.md": "a\n"})
        self.write({".hygiene-allow": b"records: out\n# \xff\n"})
        other = os.path.join(PRIVATE_DIR.name, "plain.allow")
        Path(other).write_text("# none\n")
        _, d, _ = self.scan("--allow", other, code=1)
        self.assertEqual(self.records(d), ["HANDOFF.md"])

    def test_f3_the_rows_read_still_fails_as_at_the_pin(self):
        self.commit({"README.md": "a\n"})
        self.write({".hygiene-allow": b"# \xff\n"})
        got, out, err = run(self.repo)
        self.assertEqual(got, 2)
        self.assertIn("not UTF-8", err)

    def test_f4_a_replace_ref_moves_neither_reader(self):
        self.commit({"README.md": "a\n", ".hygiene-allow": DECLARE, "HANDOFF.md": "a\n"})
        old = git(self.repo, "rev-parse", "HEAD:.hygiene-allow")
        new = subprocess.run(["git", "-C", self.repo, "hash-object", "-w", "--stdin"],
                             input="a: sibling\n", capture_output=True, text=True,
                             env=QUIET, check=True).stdout.strip()
        git(self.repo, "replace", old, new)
        self.assertEqual(resolver_state(self.repo), "unset")
        _, d, _ = self.scan(code=1)
        self.assertEqual(self.records(d), ["HANDOFF.md"])

    def test_f5_root_names_fold_case_in_the_tree(self):
        self.commit({".hygiene-allow": DECLARE})
        self.commit({p: "a\n" for p in FOLDED})
        _, d, _ = self.scan(code=1)
        self.assertEqual(self.records(d), sorted(FOLDED))

    def test_f5_root_names_fold_case_in_a_range(self):
        base = self.declared_main()
        self.commit({p: "a\n" for p in FOLDED})
        _, d, _ = self.scan("--commits", base + "..HEAD", code=1)
        self.assertEqual(self.records(d), sorted(FOLDED))


if __name__ == "__main__":
    unittest.main()
