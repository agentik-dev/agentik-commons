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
                fh.write("repos/\n")

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
