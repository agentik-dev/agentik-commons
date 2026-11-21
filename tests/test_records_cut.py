"""Packet rc0-records-cut: `scripts/records-cut --repo <clone> --holder <repo> [--go]` moves a
repo's working records to `<holder>/repos/<the clone's folder name>/`, removes them in one
commit that declares `records: out`, and sets `agentik.records` (hq design/28; GUIDE §12).
Every repo here is a temp repo with made-up names; `--go` runs only on them, and no test reads
the live private list, home or git config."""
import contextlib
import hashlib
import importlib.util
import io
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "records-cut"
SCANNER = ROOT / "scripts" / "hygiene"
RESOLVER = ROOT / "scripts" / "agentik_records.py"
ENV = "AGENTIK_HYGIENE_PRIVATE"
MAIL = "t" + "@x.invalid"  # split, so no line of this file is an address
EXECUTABLE = "history/tools/tally.sh"
RECORDS = {
    "history/sittings/2026-01-01-1.md": "# a charter\n",
    EXECUTABLE: "#!/bin/sh\necho one\n",
    "design/packets/p1.md": "# a packet\n",
    "bugs/x.md": "a bug\n",
    "HANDOFF.md": "# Handoff\n",
    "NICE_TO_HAVE.md": "# Nice to have\n",
    "OPEN-QUESTIONS.md": "# Questions\n",
    "relay/queue.yaml": "rows: []\n",
    ".hygiene-live": "# no chain runs here\n",
}
KEEP = {"README.md": "# widget\n", "design/notes.md": "notes\n", "docs/HANDOFF.md": "no record\n",
        "relay/other.yaml": "x: 1\n", ".hygiene-allow": "# made-up rows: none\n"}
NAMES = ["history/", "design/packets/", "bugs/", "HANDOFF.md", "NICE_TO_HAVE.md",
         "OPEN-QUESTIONS.md", "relay/queue.yaml", ".hygiene-live"]


def setUpModule():
    global HOME_DIR, QUIET
    HOME_DIR = tempfile.TemporaryDirectory()
    private = os.path.join(HOME_DIR.name, "private.tsv")
    Path(private).write_text("private\tzorbla[x]-ops\n")
    QUIET = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    QUIET.update({"HOME": HOME_DIR.name, "XDG_CONFIG_HOME": os.path.join(HOME_DIR.name, "c"),
                  "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                  "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": MAIL,
                  "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": MAIL, ENV: private})


def tearDownModule():
    HOME_DIR.cleanup()


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), *args], check=check, capture_output=True,
                          text=True, env=QUIET).stdout.strip()


def write(repo, files):
    for rel, text in files.items():
        path = Path(repo, rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def commit(repo, message="work", push=True):
    git(repo, "add", "--", ".")
    git(repo, "commit", "-q", "-m", message)
    if push:
        git(repo, "push", "-q")


def load(name, path):
    spec = importlib.util.spec_from_loader(name, SourceFileLoader(name, str(path)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve(repo):
    module = load("agentik_records_rc0", RESOLVER)
    with mock.patch.dict(os.environ, QUIET, clear=True):
        return module.resolve(repo)


def run(*args):
    p = subprocess.run([str(SCRIPT), *args], capture_output=True, text=True, env=QUIET)
    return p.returncode, p.stdout, p.stderr


def snapshot(*folders):
    """Every file and folder under `folders`, .git included, with size, mode and mtime, and
    each repo's status: what a run that writes nothing leaves as it found."""
    seen = []
    for folder in folders:
        for base, dirs, names in os.walk(folder):
            for name in sorted(dirs + names):
                st = os.lstat(os.path.join(base, name))
                seen.append((os.path.join(base, name), st.st_size, st.st_mode, st.st_mtime_ns))
        if os.path.isdir(os.path.join(folder, ".git")):
            seen.append(git(folder, "--no-optional-locks", "status", "--porcelain",
                            "--untracked-files=all"))
    return sorted(seen, key=str)


def refusals(err):
    return [line for line in err.splitlines() if line.startswith("records-cut: refused: ")]


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmps = []
        self.fresh()

    def fresh(self, folder="widget"):
        """A clone level with its upstream, holding every record name, and a holder repo."""
        tmp = tempfile.TemporaryDirectory()
        self.tmps.append(tmp)
        self.top = os.path.realpath(tmp.name)
        self.origin = os.path.join(self.top, "remotes", "widget.git")
        self.clone = os.path.join(self.top, "work", folder)
        self.holder = os.path.join(self.top, "work", "records-holder")
        os.makedirs(os.path.dirname(self.origin))
        git(self.top, "init", "-q", "--bare", "-b", "main", self.origin)
        git(self.top, "clone", "-q", self.origin, self.clone)
        git(self.clone, "symbolic-ref", "HEAD", "refs/heads/main")
        write(self.clone, dict(KEEP, **RECORDS))
        os.makedirs(os.path.join(self.clone, "scripts"))
        shutil.copyfile(SCANNER, os.path.join(self.clone, "scripts", "hygiene"))
        for rel in (EXECUTABLE, "scripts/hygiene"):
            os.chmod(os.path.join(self.clone, rel), 0o755)
        git(self.clone, "add", "--", ".")
        git(self.clone, "commit", "-q", "-m", "start")
        git(self.clone, "push", "-q", "-u", "origin", "main")
        git(self.top, "init", "-q", "-b", "main", self.holder)
        write(self.holder, {"README.md": "# holder\n"})
        commit(self.holder, push=False)
        self.dest = os.path.join(self.holder, "repos", folder)

    def tearDown(self):
        for tmp in self.tmps:
            for base, dirs, _ in os.walk(tmp.name):
                for name in dirs:
                    os.chmod(os.path.join(base, name), 0o755)
            tmp.cleanup()

    def args(self, go=False, repo=None, holder=None):
        return ["--repo", repo or self.clone, "--holder", holder or self.holder] + (
            ["--go"] if go else [])


class DryRunTest(Fixture):
    def test_dry_run_lists_and_writes_nothing(self):
        before = snapshot(self.clone, self.holder)
        code, out, err = run(*self.args())
        self.assertEqual(code, 0, err)
        self.assertEqual(err, "")
        for rel in RECORDS:
            self.assertIn(rel, out)
        for name in NAMES:
            self.assertTrue(any(line.split()[:1] == [name] for line in out.splitlines()), name)
        for rel in KEEP:
            if rel != ".hygiene-allow":
                self.assertNotIn(rel, out)
        self.assertIn(self.dest, out)
        self.assertIn("9 files", out)
        self.assertIn("plan", out)
        self.assertEqual(snapshot(self.clone, self.holder), before)

    def test_a_branch_without_a_record_commit_is_no_refusal(self):
        git(self.clone, "checkout", "-q", "-b", "topic")
        git(self.clone, "rm", "-q", "bugs/x.md")
        write(self.clone, {"README.md": "# widget, changed\n"})
        commit(self.clone, push=False)
        git(self.clone, "checkout", "-q", "main")
        code, out, err = run(*self.args())
        self.assertEqual(code, 0, err)


class GoTest(Fixture):
    def test_go_moves_commits_and_sets_the_key(self):
        head = git(self.clone, "rev-parse", "HEAD")
        holder_head = git(self.holder, "rev-parse", "HEAD")
        remote = git(self.origin, "rev-parse", "main")
        branches = git(self.clone, "for-each-ref", "refs/heads", "refs/tags", "refs/remotes")
        code, out, err = run(*self.args(go=True))
        self.assertEqual(code, 0, err + out)
        for rel, text in RECORDS.items():
            path = os.path.join(self.dest, rel)
            self.assertEqual(Path(path).read_text(), text)
            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode),
                             0o755 if rel == EXECUTABLE else 0o644, rel)
            self.assertFalse(os.path.lexists(os.path.join(self.clone, rel)), rel)
        self.assertEqual(git(self.holder, "ls-files", "repos"), "")
        status = git(self.holder, "status", "--porcelain", "--untracked-files=all").splitlines()
        self.assertEqual(sorted(status), sorted("?? repos/widget/" + rel for rel in RECORDS))
        self.assertEqual(git(self.holder, "rev-parse", "HEAD"), holder_head)
        self.assertEqual(git(self.clone, "rev-parse", "HEAD^"), head)
        changes = git(self.clone, "diff", "--name-status", "--no-renames", "HEAD^", "HEAD")
        self.assertEqual(sorted(changes.splitlines()),
                         sorted(["D\t" + rel for rel in RECORDS] + ["M\t.hygiene-allow"]))
        self.assertEqual(git(self.clone, "show", "HEAD:.hygiene-allow"),
                         KEEP[".hygiene-allow"] + "records: out")
        message = git(self.clone, "log", "-1", "--format=%B")
        self.assertEqual(len(message.splitlines()), 1)
        self.assertNotIn("holder", message)
        self.assertEqual(git(self.clone, "status", "--porcelain"), "")
        self.assertEqual(git(self.clone, "config", "--local", "--get", "agentik.records"),
                         self.dest)
        found = resolve(self.clone)
        self.assertEqual((found["state"], found["records"]), ("out", self.dest))
        self.assertEqual(git(self.origin, "rev-parse", "main"), remote)
        self.assertEqual(git(self.clone, "for-each-ref", "refs/remotes", "refs/tags"),
                         "\n".join(l for l in branches.splitlines() if "refs/heads" not in l))
        self.assertIn("git -C %s add -- repos/widget" % self.holder, out)
        self.assertLess(out.index("git -C %s push" % self.clone),
                        out.index("git -C %s push" % self.holder))
        again, _, err = run(*self.args(go=True))
        self.assertEqual(again, 2)
        self.assertIn("agentik.records is already set", err)
        self.assertIn("already declares", err)

    def test_an_absent_allow_file_is_created(self):
        git(self.clone, "rm", "-q", ".hygiene-allow")
        commit(self.clone)
        code, out, err = run(*self.args(go=True))
        self.assertEqual(code, 0, err + out)
        self.assertEqual(git(self.clone, "show", "HEAD:.hygiene-allow"), "records: out")
        changes = git(self.clone, "diff", "--name-status", "HEAD^", "HEAD").splitlines()
        self.assertIn("A\t.hygiene-allow", changes)

    def test_the_clones_scanner_after_the_move(self):
        code, out, err = run(*self.args(go=True))
        self.assertEqual(code, 0, err + out)
        scanner = os.path.join(self.clone, "scripts", "hygiene")

        def scan(*more):
            return subprocess.run([scanner, "--repo", self.clone, *more], capture_output=True,
                                  text=True, env=QUIET).returncode
        self.assertEqual((scan(), scan("--commits", "HEAD^..HEAD")), (0, 0))
        git(self.clone, "checkout", "HEAD^", "--", "HANDOFF.md")
        commit(self.clone, push=False)
        self.assertEqual((scan(), scan("--commits", "HEAD^..HEAD")), (1, 1))


class FolderNameTest(Fixture):
    def test_the_folder_name_not_the_remotes(self):
        self.fresh(folder="gadget-local")
        code, out, err = run(*self.args(go=True))
        self.assertEqual(code, 0, err + out)
        self.assertTrue(os.path.isfile(os.path.join(self.holder, "repos", "gadget-local",
                                                    "HANDOFF.md")))
        self.assertFalse(os.path.exists(os.path.join(self.holder, "repos", "widget")))
        found = resolve(self.clone)
        self.assertEqual((found["state"], found["records"]), ("out", self.dest))


class NamesTest(unittest.TestCase):
    def test_the_names_are_the_scanners(self):
        cut = load("records_cut_rc0", SCRIPT)
        scanner = load("hygiene_rc0", SCANNER)
        self.assertEqual(cut.RECORD_DIRS, scanner.RECORD_DIRS)
        self.assertEqual(cut.RECORD_FILES, scanner.RECORD_FILES)
        for path in list(RECORDS) + list(KEEP) + ["History/x.md", "Design/Packets/p.md",
                                                   "handoff.md", ".HYGIENE-LIVE", "sub/bugs/x"]:
            self.assertEqual(cut.is_record(path), scanner.is_record(path), path)


class RefusalTest(Fixture):
    def worktree(self, name, *flags):
        path = os.path.join(self.top, "work", name)
        git(self.clone, "worktree", "add", "-q", *flags, path)
        return path

    def cases(self):
        """(name, a setup that answers (repo, holder) or None for the fixture's, the words)"""
        def plain():
            path = os.path.join(self.top, "plain")
            os.makedirs(path)
            return path

        def topic():
            git(self.clone, "checkout", "-q", "-b", "topic")
            write(self.clone, {"HANDOFF.md": "# Handoff, changed\n"})
            commit(self.clone, push=False)
            git(self.clone, "checkout", "-q", "main")

        def detached():
            path = self.worktree("side", "--detach")
            write(path, {"history/sittings/2026-01-02-1.md": "# another\n"})
            commit(path, push=False)

        def link_dir():
            git(self.clone, "rm", "-q", "-r", "history")
            write(self.clone, {"elsewhere/a.md": "a\n"})
            os.symlink("elsewhere", os.path.join(self.clone, "history"))
            commit(self.clone)

        def stray():
            write(self.holder, {"repos/widget/stray.md": "x\n"})
            with open(os.path.join(self.holder, ".git", "info", "exclude"), "a") as fh:
                fh.write("repos/widget/stray.md\n")

        def holder_dirty():
            write(self.holder, {"repos/widget/old.md": "x\n"})
            commit(self.holder, push=False)
            shutil.rmtree(os.path.join(self.holder, "repos"))

        def allow(text):
            def setup():
                write(self.clone, {".hygiene-allow": KEEP[".hygiene-allow"] + text})
                commit(self.clone)
            return setup

        def no_record():
            git(self.clone, "rm", "-q", "-r", "--", *RECORDS)
            commit(self.clone)

        def no_scanner():
            git(self.clone, "rm", "-q", "scripts/hygiene")
            commit(self.clone)

        def link_repos(inside):
            def setup():
                target = os.path.join(self.clone if inside else self.top, "public")
                os.makedirs(target)
                os.symlink(target, os.path.join(self.holder, "repos"))
            return setup

        def holder_ignores(pattern):
            def setup():
                write(self.holder, {".gitignore": pattern + "\n"})
                commit(self.holder, push=False)
            return setup

        def flagged(flag):
            def setup():
                git(self.clone, "update-index", flag, "HANDOFF.md")
                write(self.clone, {"HANDOFF.md": "# Handoff, an edit git status hides\n"})
            return setup

        def allow_ignored(text):
            def setup():
                git(self.clone, "rm", "-q", "--", ".hygiene-allow")
                write(self.clone, {".gitignore": ".hygiene-allow\n"})
                commit(self.clone)
                if text is not None:
                    write(self.clone, {".hygiene-allow": text})
            return setup

        def allow_hidden_edit():
            git(self.clone, "update-index", "--assume-unchanged", ".hygiene-allow")
            write(self.clone, {".hygiene-allow": "docs/*.md: host   # an edit git status hides\n"})

        def other_pushes(branch):
            def setup():
                other = os.path.join(self.top, "work", "other")
                git(self.top, "clone", "-q", self.origin, other)
                if branch:
                    git(other, "checkout", "-q", "-b", branch)
                write(other, {"history/sittings/2026-01-03-1.md": "# a later charter\n"})
                commit(other, push=False)
                git(other, "push", "-q", "origin", "HEAD")
                git(self.clone, "fetch", "-q")
            return setup

        def submodule():
            sub = os.path.join(self.top, "sub")
            git(self.top, "init", "-q", "-b", "main", sub)
            write(sub, {"c.md": "# a charter in the submodule\n"})
            commit(sub, push=False)
            git(self.clone, "rm", "-q", "-r", "history")
            commit(self.clone, push=False)
            git(self.clone, "-c", "protocol.file.allow=always", "submodule", "add", "-q", sub,
                "history")
            commit(self.clone)

        return [
            ("a worktree", lambda: (self.worktree("wt", "-b", "side"), None), "not a main checkout"),
            ("a bare repo", lambda: (self.origin, None), "not a main checkout"),
            ("no repo", lambda: (plain(), None), "no git repo"),
            ("a modified file", lambda: write(self.clone, {"README.md": "x\n"}), "dirty"),
            ("an untracked file", lambda: write(self.clone, {"notes.txt": "x\n"}), "dirty"),
            ("ahead", lambda: (write(self.clone, {"README.md": "x\n"}),
                               commit(self.clone, push=False)) and None, "ahead of its upstream"),
            ("no upstream", lambda: git(self.clone, "branch", "--unset-upstream") and None,
             "no upstream"),
            ("a branch", topic, "branch topic"),
            ("a detached worktree", detached, "worktree " + os.path.join(self.top, "work", "side")),
            ("a symlinked record", lambda: (os.symlink("x.md", os.path.join(self.clone, "bugs", "l.md")),
                                            commit(self.clone)) and None, "symlink"),
            ("a symlink holding records", link_dir, "symlink"),
            ("a destination not empty", stray, "not empty"),
            ("a holder no repo", lambda: (None, plain()), "the holder is no git repo"),
            ("the holder is the clone", lambda: (None, self.clone), "is the clone"),
            ("a holder sharing the git folder", lambda: (None, self.worktree("wt", "-b", "other")),
             "shares the clone's git folder"),
            ("a holder dirty under the destination", holder_dirty, "dirty under"),
            ("a holder that declares", lambda: (write(self.holder, {".hygiene-allow": "records: out\n"}),
                                               commit(self.holder, push=False)) and None,
             "declares records: out itself"),
            ("the key set", lambda: git(self.clone, "config", "--local", "agentik.records",
                                        os.path.join(self.top, "x")) and None,
             "agentik.records is already set"),
            ("already declared", allow("records: out\n"), "already declares"),
            ("a records row", allow("HANDOFF.md: records\n"), "records row"),
            ("no record", no_record, "no record found"),
            ("no scanner", no_scanner, "scripts/hygiene"),
            # review 1, F1: a symlink above the destination, into the clone or out of every repo
            ("repos a symlink into the clone", link_repos(True), "a symlink in the destination's path"),
            ("repos a symlink out of the holder", link_repos(False),
             "a symlink in the destination's path"),
            # F2: a destination path the holder's ignore rules match
            ("the holder ignores a record's name", holder_ignores("*.sh"),
             "the holder ignores 1 destination paths"),
            ("the holder ignores repos/", holder_ignores("repos/"), "the holder ignores 9"),
            # F3: a record whose edit the index hides from git status
            ("an assume-unchanged record", flagged("--assume-unchanged"), "assume-unchanged"),
            ("a skip-worktree record", flagged("--skip-worktree"), "skip-worktree"),
            # F4: a .hygiene-allow that is not HEAD's is never overwritten
            ("an ignored allow file not at HEAD", allow_ignored("docs/*.md: host   # mine\n"),
             "not at HEAD"),
            ("an allow file the clone ignores", allow_ignored(None), "the clone ignores it"),
            ("an allow file edited past HEAD", allow_hidden_edit, "differs from HEAD's"),
            # F5 and L3: an upstream past HEAD, and a remote-tracking branch with a record commit
            ("behind its upstream", other_pushes(None), "1 commits behind its upstream origin/main"),
            ("a remote branch", other_pushes("feat"), "remote branch origin/feat"),
            # L4: a holder whose commit would go to the clone's own remote
            ("a holder sharing the clone's remote", lambda: git(
                self.holder, "remote", "add", "origin", self.origin) and None, "republish"),
            ("a holder sharing it in another spelling", lambda: git(
                self.holder, "remote", "add", "pub", "file://" + self.origin + "/") and None,
             "republish"),
            # L7: a submodule at a record name, refused as a symlink is
            ("a submodule at a record name", submodule, "a symlink or a submodule"),
        ]

    def test_each_refusal_alone(self):
        names = [case[0] for case in self.cases()]
        for index, name in enumerate(names):
            with self.subTest(name):
                self.fresh()
                _, setup, words = self.cases()[index]
                got = setup() or (None, None)
                repo, holder = got if isinstance(got, tuple) else (None, None)
                before = snapshot(self.top)
                for go in (False, True):
                    code, out, err = run(*self.args(go=go, repo=repo, holder=holder))
                    self.assertEqual(code, 2, out + err)
                    self.assertEqual(len(refusals(err)), 1, err)
                    self.assertIn(words, refusals(err)[0])
                self.assertEqual(snapshot(self.top), before)

    def test_three_refusals_at_once(self):
        write(self.clone, {"notes.txt": "x\n"})
        git(self.clone, "config", "--local", "agentik.records", os.path.join(self.top, "x"))
        write(self.holder, {".hygiene-allow": "records: out\n"})
        commit(self.holder, push=False)
        before = snapshot(self.top)
        code, out, err = run(*self.args(go=True))
        self.assertEqual(code, 2, out + err)
        said = "\n".join(refusals(err))
        self.assertEqual(len(refusals(err)), 3, err)
        for words in ("dirty", "agentik.records is already set", "declares records: out itself"):
            self.assertIn(words, said)
        self.assertEqual(snapshot(self.top), before)


def work_tree(folder):
    """The files under `folder` but its .git, with size, mode and mtime, its folders with their
    mode, then its HEAD, its index's bytes and its status: what a refused move leaves in the
    holder (a folder the copy wrote in and the index lock its `git add --dry-run` takes and drops
    move a folder's mtime, and nothing else)."""
    seen = []
    for base, dirs, names in os.walk(folder):
        dirs[:] = [d for d in dirs if not (base == folder and d == ".git")]
        for name in sorted(dirs + names):
            st = os.lstat(os.path.join(base, name))
            seen.append((os.path.join(base, name), st.st_mode) if stat.S_ISDIR(st.st_mode) else
                        (os.path.join(base, name), st.st_size, st.st_mode, st.st_mtime_ns))
    seen.append(git(folder, "rev-parse", "HEAD"))
    seen.append(hashlib.sha256(Path(folder, ".git", "index").read_bytes()).hexdigest())
    seen.append(git(folder, "--no-optional-locks", "status", "--porcelain", "--untracked-files=all",
                    "--ignored"))
    return seen


class HolderTakesTest(Fixture):
    """Review 2, F1 to F4: under --go, after the copy and before the clone changes, the holder's
    own `git add --dry-run` of the printed path must take every copy; else the copies go back."""

    def cases(self):
        """(name, a setup, the refusal's words, whether the dry run sees it)"""
        def ignore_file(text, force):
            def setup():
                write(self.clone, {"history/.gitignore": text})
                git(self.clone, "add", *(["-f"] if force else []), "--", "history/.gitignore")
                commit(self.clone)
            return setup

        def nested():
            git(self.top, "clone", "-q", self.origin, os.path.join(self.holder, "repos"))

        def submodule():
            os.makedirs(self.dest)
            git(self.holder, "update-index", "--add", "--cacheinfo",
                "160000,%s,repos/widget" % git(self.holder, "rev-parse", "HEAD"))
            git(self.holder, "commit", "-q", "-m", "a submodule at the destination")

        def sparse():
            write(self.holder, {"docs/d.md": "d\n"})
            commit(self.holder, push=False)
            git(self.holder, "sparse-checkout", "set", "--cone", "docs")

        return [
            ("an ignore file among the records, force-added", ignore_file("*\n", True),
             "the ignore rule repos/widget/history/.gitignore:1:* matches it", False),
            ("an ignore file among the records", ignore_file("*.sh\n", False),
             "repos/widget/" + EXECUTABLE, False),
            ("a nested repo at repos", nested, "not the holder's", True),
            ("a submodule at the destination", submodule, "tracks a submodule here", True),
            ("a sparse checkout without repos", sparse, "outside the holder's sparse checkout", True),
        ]

    def each(self, check):
        for index, case in enumerate(self.cases()):
            with self.subTest(case[0]):
                self.fresh()
                name, setup, words, seen = self.cases()[index]
                setup()
                check(words, seen)

    def unchanged(self, before):
        self.assertEqual((snapshot(self.clone), work_tree(self.holder)), before)
        self.assertEqual(git(self.clone, "config", "--local", "--get", "agentik.records",
                             check=False), "")

    def test_go_refuses_and_takes_the_copies_back(self):
        def check(words, seen):
            before = snapshot(self.clone), work_tree(self.holder)
            code, out, err = run(*self.args(go=True))
            self.assertEqual(code, 2, out + err)
            self.assertEqual(len(refusals(err)), 1, err)
            self.assertIn(words, refusals(err)[0])
            self.unchanged(before)
        self.each(check)

    def test_the_dry_run_makes_the_checks_it_can(self):
        def check(words, seen):
            before = snapshot(self.clone), work_tree(self.holder)
            code, out, err = run(*self.args())
            if seen:
                self.assertEqual(code, 2, out + err)
                self.assertIn(words, refusals(err)[0])
            else:
                self.assertEqual(code, 0, out + err)
                self.assertIn("add --dry-run -- repos/widget exits 0 and names each copy", out)
            self.unchanged(before)
        self.each(check)

    def test_the_proof_after_the_copy_alone(self):
        """With every check of the destination before the copy silenced, the proof alone refuses."""
        def check(words, seen):
            before = snapshot(self.clone), work_tree(self.holder)
            cut = load("records_cut_rc0_proof", SCRIPT)
            real = cut.survey_destination
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(cut, "survey_destination",
                                   lambda s, refuse, trees: real(s, lambda *a: None, trees)), \
                    mock.patch.dict(os.environ, QUIET, clear=True), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = cut.main(["records-cut"] + self.args(go=True))
            self.assertEqual(code, 2, out.getvalue() + err.getvalue())
            said = refusals(err.getvalue())
            self.assertEqual(len(said), 1, err.getvalue())
            self.assertIn("the holder's add would not take it", said[0])
            self.assertIn("nothing changed in " + self.clone, said[0])
            self.unchanged(before)
        self.each(check)


class RemoteSpellingTest(Fixture):
    """Review 2, F5: one remote in two spellings is one remote; build 2's cases stay refused."""

    def test_one_remote_in_any_spelling(self):
        same = [
            ("git@forge.invalid:o/widget.git", "https://forge.invalid/o/widget", None),
            ("git@forge.invalid:o/widget.git", "ssh://git@forge.invalid/o/widget.git", None),
            ("https://forge.invalid/o/widget", "https://user@forge.invalid/o/widget", None),
            ("ssh://git@Forge.Invalid:22/o/widget", "git@forge.invalid:o/widget/", None),
            ("git@forge.invalid:o/widget.git", "git@forge.invalid:o/widget", None),
            ("https://forge.invalid/o/widget.git", "https://forge.invalid/o/widget/", None),
            ("https://forge.invalid/o/widget", "https://forge.invalid/o/widget.git/", None),
            ("https://forge.invalid/o/widget", "https://forge.invalid/o/private",
             ("remote.origin.pushurl", "https://forge.invalid/o/widget.git")),
            ("https://forge.invalid/o/widget", "fg:o/widget",
             ("url.https://forge.invalid/.insteadOf", "fg:")),
            ("https://forge.invalid/o/widget", "fg:o/widget",
             ("url.https://forge.invalid/.pushInsteadOf", "fg:")),
        ]
        other = [("https://forge.invalid/o/widget", "https://forge.invalid/o/private", None),
                 ("git@forge.invalid:o/widget", "git@other.invalid:o/widget", None)]
        for mine, theirs, extra in same + other:
            with self.subTest((mine, theirs, extra)):
                self.fresh()
                git(self.clone, "config", "remote.origin.url", mine)
                git(self.holder, "remote", "add", "origin", theirs)
                if extra:
                    git(self.holder, "config", *extra)
                code, out, err = run(*self.args())
                if (mine, theirs, extra) in other:
                    self.assertEqual(code, 0, out + err)
                else:
                    self.assertEqual(code, 2, out + err)
                    self.assertEqual(len(refusals(err)), 1, err)
                    self.assertIn("republish", refusals(err)[0])
        with self.subTest("file:// through a symlink"):
            self.fresh()
            os.symlink(os.path.dirname(self.origin), os.path.join(self.top, "rl"))
            git(self.holder, "remote", "add", "origin",
                "file://" + os.path.join(self.top, "rl", "widget.git") + "/")
            code, out, err = run(*self.args())
            self.assertEqual(code, 2, out + err)
            self.assertIn("republish", refusals(err)[0])


class LineEndTest(Fixture):
    """Review 2, L3: a .hygiene-allow that git says is HEAD's moves, whatever its line ends."""

    def test_a_crlf_checkout_moves(self):
        for how in ("attribute", "autocrlf"):
            with self.subTest(how):
                self.fresh()
                if how == "attribute":
                    write(self.clone, {".gitattributes": ".hygiene-allow text eol=crlf\n"})
                    commit(self.clone)
                else:
                    git(self.clone, "config", "core.autocrlf", "true")
                os.unlink(os.path.join(self.clone, ".hygiene-allow"))
                git(self.clone, "checkout", "-q", "--", ".hygiene-allow")
                self.assertIn(b"\r\n", Path(self.clone, ".hygiene-allow").read_bytes())
                self.assertEqual(git(self.clone, "status", "--porcelain"), "")
                code, out, err = run(*self.args(go=True))
                self.assertEqual(code, 0, out + err)
                self.assertEqual(git(self.clone, "show", "HEAD:.hygiene-allow"),
                                 KEEP[".hygiene-allow"] + "records: out")
                self.assertEqual(git(self.clone, "status", "--porcelain"), "")


class FailedStepTest(Fixture):
    def test_a_failed_step(self):
        head = git(self.clone, "rev-parse", "HEAD")
        with self.subTest("a read-only destination after the first copy"):
            cut = load("records_cut_rc0_step", SCRIPT)
            real = cut.copy_one
            calls = []

            def first_then_lock(*args):
                real(*args)
                calls.append(args)
                if len(calls) == 1:
                    os.chmod(self.dest, 0o555)
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(cut, "copy_one", first_then_lock), \
                    mock.patch.dict(os.environ, QUIET, clear=True), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = cut.main(["records-cut"] + self.args(go=True))
            self.assertEqual(code, 1, err.getvalue())
            self.assertIn("records-cut: failed: ", err.getvalue())
            self.assertIn("1 of 9", err.getvalue())
            self.assertIn(self.dest, err.getvalue())
            self.assertEqual(git(self.clone, "rev-parse", "HEAD"), head)
            self.assertEqual(git(self.clone, "status", "--porcelain"), "")
            self.assertEqual(git(self.clone, "config", "--local", "--get", "agentik.records",
                                 check=False), "")
            os.chmod(self.dest, 0o755)
        with self.subTest("a commit hook that refuses"):
            self.fresh()
            head = git(self.clone, "rev-parse", "HEAD")
            hook = os.path.join(self.clone, ".git", "hooks", "pre-commit")
            Path(hook).write_text("#!/bin/sh\nexit 1\n")
            os.chmod(hook, 0o755)
            code, out, err = run(*self.args(go=True))
            self.assertEqual(code, 1, out + err)
            self.assertIn("records-cut: failed: ", err)
            self.assertIn("commit", err)
            self.assertIn("9 of 9", err)
            self.assertIn("undo", err)
            self.assertEqual(git(self.clone, "rev-parse", "HEAD"), head)
            self.assertEqual(git(self.clone, "config", "--local", "--get", "agentik.records",
                                 check=False), "")
            for rel, text in RECORDS.items():
                self.assertEqual(Path(self.dest, rel).read_text(), text)


if __name__ == "__main__":
    unittest.main()
