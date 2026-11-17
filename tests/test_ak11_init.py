"""Row ak11-init: `agentik-suite init --kind hq DIR` writes a fresh coordinating repo, an hq.

Each test runs in test_agentik_suite's `Home`, a temp HOME with a recording `claude` stub, and
writes only in `T`, a second temp folder outside it. The scaffold `S` is the repo's own
`plugins/suite/lib/scaffold/hq`. A test that names the ledger's file or its tool assembles the
name, so no tool's name stands in these tests (packet ak11-init R1, R10)."""
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_suite import ESC, LAUNCHER, LIB, ROOT, Home  # noqa: E402
from agentik_suite import cli  # noqa: E402

S = os.path.join(str(LIB), "scaffold", "hq")
LEDGER = "DECI" + "SIONS.md"
FILES = ["README.md", ".claude/agentik/config.yaml", ".gitignore", "CLAUDE.md", LEDGER, "HANDOFF.md",
         "Makefile", "NICE_TO_HAVE.md", "OPEN-QUESTIONS.md", "history/sittings/.gitkeep",
         "scripts/recordlint", "scripts/recordlint.sha256"]
SHA = {"README.md": "d539d06ccfca113d0ae93653376011b6dec3bea212efaadd258f654b09f43117",
       "CLAUDE.md": "a4aafde9e50a063a2b5102ed6dab85680a7686f0282fa693cfce5e281f66431b",
       LEDGER: "ab59682f0d43b680ec398d66869a917ee5975ffb96fdf462032860b8ee9f0840",
       "OPEN-QUESTIONS.md": "ece4f53f34e21458e1e1b922c90726ff9b1cf44b49bd6e876b640e4292a85751",
       "HANDOFF.md": "1e105e225a2cdc35fd1d8e2b2f76f5983f9698b790d68bf25ed7e16f82a45c3b",
       "NICE_TO_HAVE.md": "73109709839c436ca56400a58d1ae8e299a1f764126083bf0aeabaaadc98415f",
       "Makefile": "d7d4c375b1cc68957cee0266b4e1f2a037cce65d07a45c68b6b1626b992b2e91",
       ".gitignore": "ef0f379da339763579b140de87661351628d8bfd1aa09660850fe61e4ebf755d",
       ".claude/agentik/config.yaml": "78b28cace40194e8bf1b6c06d71c5ecab66a71c9444d77a654a940a747919e79"}
HINT = "next: cd pear-hq && make check, then read README.md there for the steps after it.\n"
ALREADY = "FAIL  pear-hq is already a hq, so init wrote nothing; run make check there\n"
FULL = "FAIL  full is not empty: it holds %s; init needs an empty folder\n"


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def tree(root, skip=(".git",)):
    """{path under root: (sha256, mode)} for every file, the folders in `skip` aside."""
    found = {}
    for here, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not (here == root and d in skip)]
        for name in files:
            path = os.path.join(here, name)
            found[os.path.relpath(path, root)] = (sha(path), stat.S_IMODE(os.lstat(path).st_mode))
    return found


class Stream(io.StringIO):
    encoding = "utf-8"


class ScaffoldTest(unittest.TestCase):
    """R3: the twelve files as the hq's script wrote them; no byte of them changes."""

    def test_r3_the_scaffold_at_its_hashes(self):
        self.assertEqual(sorted(tree(S)), sorted(FILES))
        for name, digest in SHA.items():
            self.assertEqual(sha(os.path.join(S, name)), digest, name)
        with open(os.path.join(S, "scripts", "recordlint"), "rb") as a, \
                open(os.path.join(str(ROOT), "scripts", "recordlint"), "rb") as b:
            self.assertEqual(a.read(), b.read())
        with open(os.path.join(S, "scripts", "recordlint.sha256")) as fh:
            self.assertEqual(fh.read(), "%s  scripts/recordlint\n" % sha(os.path.join(S, "scripts", "recordlint")))
        self.assertEqual(os.path.getsize(os.path.join(S, "history", "sittings", ".gitkeep")), 0)


class InitTest(Home):
    def setUp(self):
        Home.setUp(self)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.T = os.path.realpath(tmp.name)

    def go(self, *args, cwd=None, exe=LAUNCHER, **more):
        p = subprocess.run([str(exe), *args], capture_output=True, text=True, cwd=cwd or self.T,
                           env=self.env(**more), timeout=60)
        return p.returncode, p.stdout, p.stderr

    def inproc(self, *args, env=None):
        out, err = Stream(), Stream()
        code = cli.Command(list(args), dict(env if env is not None else self.env()), out, err).run()
        return code, out.getvalue(), err.getvalue()

    def at(self, *parts):
        return os.path.join(self.T, *parts)

    def git(self, *args):
        return subprocess.run(["git", *args], capture_output=True, text=True, env=self.env(), timeout=30)

    def made(self, name):
        code, out, err = self.go("init", "--kind", "hq", name)
        self.assertEqual(code, 0, err)
        return out, err

    def test_1_a_new_folder_is_an_hq(self):
        out, err = self.made("pear-hq")
        self.assertEqual(out, "pear-hq is now an hq: 12 files, in a new git repository.\n"
                         + "".join("  %s\n" % f for f in FILES))
        self.assertEqual(err, HINT)
        self.assertEqual(stat.S_IMODE(os.stat(self.at("pear-hq")).st_mode), 0o755)
        with open(self.at("pear-hq", ".git", "HEAD")) as fh:
            self.assertEqual(fh.read().strip(), "ref: refs/heads/main")
        lines = self.git("-C", self.at("pear-hq"), "status", "--porcelain").stdout.splitlines()
        self.assertTrue(lines and all(line.startswith("?? ") for line in lines), lines)
        self.assertEqual({line[3:].rstrip("/") for line in lines}, set(os.listdir(S)))

    def test_2_the_folder_is_the_scaffold(self):
        self.made("pear-hq")
        got = tree(self.at("pear-hq"))
        self.assertEqual({k: v[0] for k, v in got.items()}, {k: v[0] for k, v in tree(S).items()})
        for name, (_, mode) in got.items():
            self.assertEqual(mode, 0o755 if name == "scripts/recordlint" else 0o644, name)

    def test_3_its_checks_pass_as_written(self):
        self.made("pear-hq")
        here = self.at("pear-hq")
        p = subprocess.run(["scripts/recordlint"], cwd=here, capture_output=True, text=True,
                           env=self.env(), timeout=60)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("HANDOFF.md: held: 1 row", p.stdout + p.stderr)
        self.assertIn("NICE_TO_HAVE.md: held: 0 rows", p.stdout + p.stderr)
        p = subprocess.run(["shasum", "-a", "256", "-c", "--status", "scripts/recordlint.sha256"], cwd=here,
                           env=self.env(), timeout=30)
        self.assertEqual(p.returncode, 0)
        p = subprocess.run(["make", "-n", "check"], cwd=here, capture_output=True, text=True,
                           env=self.env(), timeout=30)  # -n: printed, none run
        self.assertEqual(p.returncode, 0, p.stderr)
        text = p.stdout
        found = [text.find(c) for c in ("$sum -c --status scripts/recordlint.sha256",
                                         "\nscripts/recordlint", "agentik " + "decision" + "s render --check")]
        self.assertTrue(all(i >= 0 for i in found) and found == sorted(found), text)
        self.assertEqual(sorted(tree(here)), sorted(FILES))

    def test_5_the_repo_file_says_hq(self):
        self.made("pear-hq")
        code, out, err = self.go("config", "suite.kind", "--json", cwd=self.at("pear-hq"))
        self.assertEqual(code, 0, err)
        setting = json.loads(out)["setting"]
        self.assertEqual((setting["value"], setting["source"]["layer"], setting["source"]["line"]), ("hq", "repo", 3))

    def test_6_a_second_time_is_already(self):
        self.made("pear-hq")
        before = tree(self.at("pear-hq"), skip=())
        code, out, err = self.go("init", "--kind", "hq", "pear-hq")
        self.assertEqual((code, out, err), (2, "", ALREADY))
        self.assertEqual(tree(self.at("pear-hq"), skip=()), before)

    def test_7_a_full_folder_is_refused(self):
        os.mkdir(self.at("full"))
        for name in ("d.txt", "b.txt", "a.txt", "c.txt"):
            with open(self.at("full", name), "w") as fh:
                fh.write(name)
        before = tree(self.at("full"))
        code, out, err = self.go("init", "--kind", "hq", "full")
        self.assertEqual((code, out, err), (2, "", FULL % "a.txt, b.txt, c.txt and 1 more"))
        self.assertEqual(tree(self.at("full")), before)
        for name in ("b.txt", "c.txt", "d.txt"):
            os.unlink(self.at("full", name))
        self.assertEqual(self.go("init", "--kind", "hq", "full")[2], FULL % "a.txt")

    def test_8_a_clone_keeps_its_repository(self):
        self.git("init", "-q", "-b", "trunk", self.at("clone"))
        with open(self.at("clone", ".DS_Store"), "w") as fh:
            fh.write("x")
        out, err = self.made("clone")
        self.assertTrue(out.splitlines()[0].endswith("in the git repository already there."), out)
        with open(self.at("clone", ".git", "HEAD")) as fh:
            self.assertEqual(fh.read().strip(), "ref: refs/heads/trunk")
        self.assertTrue(os.path.isfile(self.at("clone", ".DS_Store")))
        self.assertEqual(sorted(tree(self.at("clone"))), sorted(FILES + [".DS_Store"]))

    def test_9_inside_a_repository_is_refused(self):
        self.git("init", "-q", self.at("outer"))
        code, out, err = self.go("init", "--kind", "hq", self.at("outer", "sub"))
        self.assertEqual((code, out), (2, ""))
        self.assertIn("is inside %s; a hq needs its own folder" % self.at("outer"), err)
        self.assertFalse(os.path.lexists(self.at("outer", "sub")))

    def test_10_a_file_an_absent_parent_and_no_git(self):
        with open(self.at("afile"), "w") as fh:
            fh.write("x")
        code, out, err = self.go("init", "--kind", "hq", "afile")
        self.assertEqual((code, out, err), (2, "", "FAIL  afile is a file; init needs an empty folder "
                                                   "or one not there yet\n"))
        code, out, err = self.go("init", "--kind", "hq", "none/pear-hq")
        self.assertEqual((code, out, err), (2, "", "FAIL  none is not a folder, so init cannot make none/pear-hq; "
                                                   "make none first\n"))
        code, out, err = self.inproc("init", "--kind", "hq", self.at("bare"), env=self.env(PATH=self.stubs))
        self.assertEqual((code, out), (2, ""))
        self.assertIn("init needs git, which is not on PATH; install it", err)
        self.assertEqual(sorted(os.listdir(self.T)), ["afile"])

    def test_11_the_words_and_flags(self):
        for args, part in ((("init", "x"), "init needs --kind (hq); try "),
                           (("init", "--kind", "barn", "x"), "barn is not one of hq; try "),
                           (("init", "--kind", "hq"), "init needs a folder: "),
                           (("init", "--kind", "hq", "x", "y"), "init writes one folder, not a second, y; run "),
                           (("setup", "--kind", "hq"), "--kind")):
            code, out, err = self.go(*args)
            self.assertEqual((code, out), (2, ""), args)
            self.assertIn(part, err, args)
            self.assertEqual(len(err.splitlines()), 1 if args[0] == "init" else 2, err)
        self.assertEqual(sorted(os.listdir(self.T)), [])
        code, out, err = self.go("init", "--kind=hq", "eq")
        self.assertEqual(code, 0, err)
        code, out, err = self.go("help", "init")
        self.assertEqual(code, 0, err)
        self.assertRegex(out.splitlines()[0], r"^usage: \S+ init --kind hq <dir> \[flags\]$")
        self.assertIn("--dry-run", out)
        self.assertIn("--yes", out)

    def test_12_a_dry_run_writes_nothing(self):
        code, out, err = self.go("init", "--kind", "hq", self.at("dry"), "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "Plan: an hq in %s, 12 files. Nothing is written.\n" % self.at("dry")
                         + "".join("  %s\n" % f for f in FILES))
        self.assertEqual(err, "next: run the same command without --dry-run to write the files.\n")
        code, out, err = self.go("init", "--kind", "hq", self.at("dry"), "--dry-run", "--json")
        obj = json.loads(out)
        self.assertEqual((code, obj["dry_run"], obj["files"]), (0, True, FILES))
        self.assertFalse(os.path.lexists(self.at("dry")))
        os.mkdir(self.at("full"))
        for name in ("a.txt", "b.txt", "c.txt", "d.txt"):
            open(self.at("full", name), "w").close()
        code, out, err = self.go("init", "--kind", "hq", "full", "--dry-run")
        self.assertEqual((code, out, err), (2, "", FULL % "a.txt, b.txt, c.txt and 1 more"))

    def test_13_the_json_object(self):
        code, out, err = self.go("init", "--kind", "hq", "j", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out), {"schema": "agentik.init/1", "ok": True, "kind": "hq",
                                           "dir": self.at("j"), "dry_run": False, "git": "made", "files": FILES})
        code, out, err = self.go("init", "--kind", "hq", "j", "--json")
        self.assertEqual((code, len(out.splitlines())), (2, 1))
        obj = json.loads(out)
        self.assertEqual((obj["ok"], obj["error"]["code"]), (False, "already"))

    def test_14_a_folder_it_cannot_write(self):
        os.mkdir(self.at("ro"))
        os.chmod(self.at("ro"), 0o555)
        self.addCleanup(os.chmod, self.at("ro"), 0o755)
        code, out, err = self.go("init", "--kind", "hq", self.at("ro", "pear-hq"))
        self.assertEqual((code, out, len(err.splitlines())), (1, "", 1), err)
        self.assertIn("FAIL  init could not write %s (Permission denied);" % self.at("ro"), err)
        self.assertIn("is as it was", err)
        self.assertEqual(os.listdir(self.at("ro")), [])

    def test_15_git_fails(self):
        self.stub("bad/git", "#!/bin/sh\necho 'fatal: no' >&2\nexit 128\n")
        env = self.env(PATH="%s:%s" % (os.path.join(self.stubs, "bad"), self.env()["PATH"]))
        code, out, err = self.inproc("init", "--kind", "hq", self.at("x"), env=env)
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(err, "FAIL  git init failed in %s, so init wrote nothing; what git said is below"
                              "\nfatal: no\n" % self.at("x"))
        self.assertEqual(os.listdir(self.T), [])
        code, out, err = self.inproc("init", "--kind", "hq", self.at("x"), "--json", env=env)
        obj = json.loads(out)
        self.assertEqual((code, obj["error"]["code"], obj["error"]["said"]), (1, "git_failed", "fatal: no"))
        self.assertEqual(os.listdir(self.T), [])

    def test_16_piped_plain_on_a_terminal_dim(self):
        out, err = self.made("pear-hq")
        self.assertNotIn(ESC, out + err)
        code, shown = self.run_pty("init", "--kind", "hq", self.at("tty"))
        self.assertEqual(code, 0, shown)
        self.assertIn(ESC + "[2mREADME.md" + ESC + "[0m", shown)
        code, out, err = self.go("init", "--kind", "hq", "quiet", "-q")
        self.assertEqual((code, err), (0, ""))

    def test_17_from_a_frozen_tree(self):
        prefix = os.path.join(self.home, "p")
        code, out, err = self.go("install-cli", "--prefix", prefix)
        self.assertEqual(code, 0, err)
        share = os.path.join(prefix, "share", "agentik-suite")
        frozen = [os.path.join(share, d, "scaffold", "hq", "scripts", "recordlint") for d in os.listdir(share)]
        frozen = [f for f in frozen if os.path.isfile(f)]
        self.assertEqual(len(frozen), 1, frozen)
        self.assertEqual(stat.S_IMODE(os.stat(frozen[0]).st_mode), 0o644)
        self.go("init", "--kind", "hq", "frozen", exe=os.path.join(prefix, "bin", "agentik-suite"))
        got = tree(self.at("frozen"))
        self.assertEqual({k: v[0] for k, v in got.items()}, {k: v[0] for k, v in tree(S).items()})
        self.assertEqual(got["scripts/recordlint"][1], 0o755)
        self.assertTrue(os.path.isfile(self.at("frozen", ".git", "HEAD")))

    def test_18_home_is_untouched(self):
        before = self.snapshot()
        self.made("pear-hq")
        self.go("init", "--kind", "hq", "pear-hq")
        self.go("init", "--kind", "hq", "dry", "--dry-run", "--json")
        self.go("init", "--kind", "barn", "x")
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(os.path.exists(self.calls))

    def test_21_the_answers_come_from_the_seam(self):
        from agentik_suite import init
        seam = self.at("seam")
        with mock.patch.object(init, "_answers", lambda cmd, nouns: {"kind": "hq", "dir": seam}):
            code, out, err = self.inproc("init")
        self.assertEqual(code, 0, err)
        self.assertEqual(sorted(tree(seam)), sorted(FILES))

    def test_22_on_a_terminal_it_waits_for_no_answer(self):
        start = time.monotonic()
        code, shown = self.run_pty("init", self.at("ask"))
        self.assertLess(time.monotonic() - start, 2.0)
        self.assertEqual(code, 2, shown)
        self.assertIn("init needs --kind", shown)
        self.assertFalse(os.path.lexists(self.at("ask")))

    def test_23_another_writer_s_file_survives_the_move(self):
        """Review 1 F1: a file another program makes in DIR while `git init` runs stops the move as
        `not_empty` (shape G), also where a later rename would fail (shape G2), and the undo removes
        only what init wrote, never a file another program put in a folder init moved in (G3)."""
        from agentik_suite import init
        real_git, real_rename = init._git, os.rename
        mine = b"MY OWN NOTES\n"

        def writer(d):
            def slow_git(git, stage, env):
                said = real_git(git, stage, env)
                with open(os.path.join(d, "README.md"), "wb") as fh:
                    fh.write(mine)
                return said
            return slow_git

        def fails_on_scripts(a, b):
            if os.path.basename(a) == "scripts":
                raise OSError(28, "No space left on device", a)
            return real_rename(a, b)

        for shape, rename in (("g", real_rename), ("g2", fails_on_scripts)):
            d = self.at(shape)
            os.mkdir(d)
            with mock.patch.object(init, "_git", writer(d)), mock.patch.object(init.os, "rename", rename):
                code, out, err = self.inproc("init", "--kind", "hq", d)
            self.assertEqual((shape, code, out), (shape, 2, ""), err)
            self.assertIn("is not empty: it holds README.md;", err)
            self.assertEqual(os.listdir(d), ["README.md"], shape)
            with open(os.path.join(d, "README.md"), "rb") as fh:
                self.assertEqual(fh.read(), mine, shape)
        d = self.at("g3")
        os.mkdir(d)
        theirs = os.path.join(d, ".claude", "notes.txt")

        def writes_then_fails(a, b):
            if os.path.basename(a) == "scripts":
                with open(theirs, "wb") as fh:
                    fh.write(mine)
                raise OSError(28, "No space left on device", a)
            return real_rename(a, b)

        with mock.patch.object(init.os, "rename", writes_then_fails):
            code, out, err = self.inproc("init", "--kind", "hq", d)
        self.assertEqual((code, out), (1, ""), err)
        self.assertIn("No space left on device", err)
        self.assertEqual(sorted(tree(d, skip=())), [".claude/notes.txt"])
        self.assertEqual(sorted(os.listdir(d)), [".claude"])
        with open(theirs, "rb") as fh:
            self.assertEqual(fh.read(), mine)

    def test_24_a_git_that_is_no_repository_is_not_kept(self):
        """Review 1 F2: an empty file `.git` is no repository, so DIR is not empty: exit 2, nothing
        written; an empty `.git` folder, which git cannot read either, is refused the same way."""
        for name, make in (("fake", lambda p: open(p, "w").close()), ("hollow", os.mkdir)):
            os.mkdir(self.at(name))
            make(self.at(name, ".git"))
            code, out, err = self.go("init", "--kind", "hq", name)
            self.assertEqual((code, out, err), (2, "", FULL.replace("full", name, 1) % ".git"))
            self.assertEqual(os.listdir(self.at(name)), [".git"])
            if name == "fake":
                self.assertEqual(os.path.getsize(self.at(name, ".git")), 0)
            else:
                self.assertEqual(os.listdir(self.at(name, ".git")), [])

    def test_25_a_parent_as_typed_that_is_not_there(self):
        """Review 1 F5: `nope/..` with no `nope` is `no_parent`, though as text it names the cwd."""
        os.mkdir(self.at("e"))
        code, out, err = self.go("init", "--kind", "hq", "nope/..", cwd=self.at("e"))
        self.assertEqual((code, out, err), (2, "", "FAIL  nope is not a folder, so init cannot make nope/..; "
                                                   "make nope first\n"))
        self.assertEqual(os.listdir(self.at("e")), [])
        code, out, err = self.go("init", "--kind", "hq", "nope/../x", "--json", cwd=self.at("e"))
        self.assertEqual((code, json.loads(out)["error"]["code"]), (2, "no_parent"))
        self.assertEqual(os.listdir(self.at("e")), [])


if __name__ == "__main__":
    unittest.main()
