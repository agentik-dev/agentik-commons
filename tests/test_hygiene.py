"""scripts/hygiene: counts per group, the allowlist, binaries skipped, exits,
the private list read from outside the repo, and no matched text or private
regex ever printed. Fixture strings are assembled at runtime, and the private
list's regexes bracket a letter, so this file stays clean under the scan itself.
Every term of the private list here is invented."""
import json
import os
import random
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "hygiene"
ENV = "AGENTIK_HYGIENE_PRIVATE"

# The tests' private list, invented terms only: comments and blanks are skipped.
REGEXES = ["quuxvill[e]\\.example", "zorbla[x]-ops", "glimmerwic[k]"]
PRIVATE = ("# the tests' private list: invented terms\n\n"
           "domain\t%s\n   \nprivate\t%s\n  # an indented comment\nperson\t%s\n"
           % tuple(REGEXES))
GENERIC = ["home", "lan", "sibling", "secret", "email", "renamed"]

# One fixture per group; each assembled so the literal never sits in this file.
FIXTURES = {
    "home": "see /Us" + "ers/alice/notes",
    "lan": "host 192." + "168.1.9 and 10." + "0.0.7",
    "domain": "https://wiki.quuxvill" + "e.example/x",
    "private": "the zorbla" + "x-ops mirror",
    "person": "by Glimmer" + "wick",
    "sibling": "load resp" + "eak first",
}
# The text each fixture matches on, lower-cased.
MATCHED = ["/us" + "ers/alice", "192." + "168.", "10." + "0.0.7", "quuxvill" + "e.example",
           "zorbla" + "x-ops", "glimmer" + "wick", "resp" + "eak"]


def setUpModule():
    global PRIVATE_DIR, PRIVATE_FILE
    PRIVATE_DIR = tempfile.TemporaryDirectory()
    PRIVATE_FILE = os.path.join(PRIVATE_DIR.name, "private.tsv")
    Path(PRIVATE_FILE).write_text(PRIVATE)


def tearDownModule():
    PRIVATE_DIR.cleanup()


def git(repo, *args):
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True)


def run(repo, *args, env=None):
    """The scan, with the tests' private list unless `env` says otherwise."""
    full = dict(os.environ)
    full[ENV] = PRIVATE_FILE
    full.update(env or {})
    full = {k: v for k, v in full.items() if v is not None}
    p = subprocess.run([str(SCRIPT), "--repo", repo, *args],
                       capture_output=True, text=True, env=full)
    return p.returncode, p.stdout, p.stderr


def lf(group):
    """A group's every-hit counts, the allowlisted ones included."""
    return {k: group[k] for k in ("lines", "files")}


class HygieneTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        git(self.repo, "init", "-q")
        for group, text in FIXTURES.items():
            Path(self.repo, group + ".txt").write_text("clean\n" + text + "\n" + text + "\n")
        Path(self.repo, "docs").mkdir()
        Path(self.repo, "docs", "allowed.md").write_text(FIXTURES["sibling"] + "\n")
        Path(self.repo, "docs", "deep").mkdir()
        Path(self.repo, "docs", "deep", "x.md").write_text(FIXTURES["sibling"] + "\n")
        Path(self.repo, "blob.bin").write_bytes(b"\0\1" + FIXTURES["lan"].encode())
        Path(self.repo, "untracked.txt").write_text(FIXTURES["domain"] + "\n")
        Path(self.repo, ".hygiene-allow").write_text(
            "# comment\ndocs/*.md: sibling\nlan.txt: lan,home\n")
        git(self.repo, "add", "--", *[p for p in os.listdir(self.repo)
                                      if p not in (".git", "untracked.txt")])

    def tearDown(self):
        self.tmp.cleanup()

    def json_result(self, *args):
        code, out, _ = run(self.repo, "--json", *args)
        return code, json.loads(out)

    def test_counts_per_group(self):
        code, d = self.json_result()
        self.assertEqual(code, 1)
        for group in ("home", "lan", "private", "person"):
            self.assertEqual(lf(d["groups"][group]), {"lines": 2, "files": 1}, group)
        self.assertEqual(lf(d["groups"]["domain"]), {"lines": 3, "files": 2})
        self.assertEqual(lf(d["groups"]["sibling"]), {"lines": 4, "files": 3})

    def test_allowlist_and_binary_and_untracked(self):
        code, d = self.json_result()
        hits = {(f["path"], f["group"]): f["lines"] for f in d["files"]}
        self.assertNotIn(("lan.txt", "lan"), hits)
        self.assertNotIn(("docs/allowed.md", "sibling"), hits)
        # the glob's * stays inside one segment
        self.assertEqual(hits[("docs/deep/x.md", "sibling")], 1)
        self.assertFalse(any(p == "blob.bin" for p, _ in hits))
        # the working tree: an untracked file is scanned before its commit
        self.assertEqual(hits[("untracked.txt", "domain")], 1)
        self.assertEqual(d["hits_outside_allowlist"], sum(hits.values()))
        self.assertEqual(d["hits_outside_allowlist"], 2 * 5 + 1 + 1)

    def test_outside_counts_leave_out_allowed_files(self):
        code, d = self.json_result()
        # docs/allowed.md is allowed for sibling; sibling.txt and docs/deep/x.md are not
        self.assertEqual(d["groups"]["sibling"], {"lines": 4, "files": 3,
                                                  "outside_lines": 3, "outside_files": 2})
        self.assertEqual(d["groups"]["lan"], {"lines": 2, "files": 1,
                                              "outside_lines": 0, "outside_files": 0})
        self.assertEqual(sum(g["outside_lines"] for g in d["groups"].values()),
                         d["hits_outside_allowlist"])
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "a.md").write_text(FIXTURES["sibling"] + "\n")
            Path(repo, ".hygiene-allow").write_text("a.md: sibling\n")
            code, d = self.json_in(repo)
            g = d["groups"]["sibling"]
            self.assertEqual((code, g["files"], g["outside_files"], g["outside_lines"]),
                             (0, 1, 0, 0))

    def test_green_exits_zero(self):
        Path(self.repo, ".hygiene-allow").write_text(
            "*.txt: home,lan,domain,private,person,sibling\ndocs/*.md: sibling\n"
            "docs/*/*.md: sibling\n")
        code, d = self.json_result()
        self.assertEqual((code, d["hits_outside_allowlist"], d["files"]), (0, 0, []))

    def test_never_prints_matched_text(self):
        for args in ((), ("--json",)):
            code, out, err = run(self.repo, *args)
            self.assertEqual(code, 1)
            for token in MATCHED:
                self.assertNotIn(token, (out + err).lower(), args)
        self.check_text_table()  # folded, so the README's test count holds

    def test_nul_file_scans_secret_and_email(self):
        # ADV10-17: a NUL file's printable runs are scanned for home, secret and email;
        # h2: its whole content for the private rows
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            data = (b"\0 abcd" + b"@" + b"example.org sk-an" + b"t" + b"-abcdefghij\n"
                    + b"\0" + ("/Us" + "ers/alice/p.png").encode() + b"\0"
                    + FIXTURES["person"].encode() + b"\0\x01")
            Path(repo, "b.bin").write_bytes(data)
            code, d = self.json_in(repo)
            self.assertEqual(code, 1)
            self.assertEqual(sorted((f["path"], f["group"], f["lines"]) for f in d["files"]),
                             [("b.bin", "email", 1), ("b.bin", "home", 1),
                              ("b.bin", "person", 1), ("b.bin", "secret", 1)])

    def check_text_table(self):
        code, out, _ = run(self.repo)
        lines = out.splitlines()
        self.assertEqual(lines[0].split(), ["group", "lines", "files"])
        self.assertIn("home.txt  home  2", lines)
        self.assertEqual(lines[-1], "hits outside allowlist: 12")

    def test_working_tree_scanned(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "a.md").write_text(FIXTURES["person"] + "\n")
            Path(repo, "b.md").write_text(FIXTURES["person"] + "\n")
            Path(repo, ".gitignore").write_text("b.md\n")
            code, out, _ = run(repo, "--json")
            d = json.loads(out)
            # untracked a.md is scanned, ignored b.md never
            self.assertEqual((code, d["groups"]["person"]["files"]), (1, 1))
            self.assertEqual([f["path"] for f in d["files"]], ["a.md"])

    def test_person_evaluated_under_sittings(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "history", "sittings").mkdir(parents=True)
            Path(repo, "history", "sittings", "x.md").write_text(
                FIXTURES["person"] + "\n" + FIXTURES["sibling"] + "\n")
            Path(repo, "x.md").write_text(FIXTURES["person"] + "\n")
            git(repo, "add", "-A")
            code, out, _ = run(repo, "--json")
            d = json.loads(out)
            # a charter is scanned for the owner's terms too; sibling alone is skipped there
            self.assertEqual((d["groups"]["person"]["files"], d["hits_outside_allowlist"]),
                             (2, 2))
            self.assertEqual({(f["path"], f["group"]) for f in d["files"]},
                             {("x.md", "person"), ("history/sittings/x.md", "person")})

    def test_sibling_not_evaluated_under_sittings(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "history", "sittings").mkdir(parents=True)
            Path(repo, "history", "sittings", "x.md").write_text(
                FIXTURES["sibling"] + "\n" + FIXTURES["home"] + "\n")
            Path(repo, "x.md").write_text(FIXTURES["sibling"] + "\n")
            git(repo, "add", "-A")
            code, out, _ = run(repo, "--json")
            d = json.loads(out)
            self.assertEqual((d["groups"]["sibling"]["files"], d["groups"]["home"]["files"],
                              d["hits_outside_allowlist"]), (1, 1, 2))
            # a sibling named by path still trips home under the charters
            self.assertEqual({(f["path"], f["group"]) for f in d["files"]},
                             {("x.md", "sibling"), ("history/sittings/x.md", "home")})

    def test_script_scans_itself_clean(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "hygiene").write_bytes(SCRIPT.read_bytes())
            Path(repo, "test_hygiene.py").write_bytes(Path(__file__).read_bytes())
            git(repo, "add", "hygiene", "test_hygiene.py")
            code, out, _ = run(repo, "--json")
            self.assertEqual((code, json.loads(out)["hits_outside_allowlist"]), (0, 0))

    def test_usage_and_git_failure_exit_two(self):
        self.assertEqual(run(self.repo, "--bogus")[0], 2)
        self.assertEqual(run(self.repo, "--allow")[0], 2)
        self.assertEqual(run(self.repo, "--allow", "missing")[0], 2)
        Path(self.repo, ".hygiene-allow").write_text("no-colon-here\n")
        self.assertEqual(run(self.repo)[0], 2)
        with tempfile.TemporaryDirectory() as notgit:
            self.assertEqual(run(notgit)[0], 2)

    def test_hygiene_catches_secret_symlink_and_path(self):
        # ADV6-1: a key, a symlink to a home path, a file named for a private repo.
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "k.md").write_text("sk-an" + "t-x\n")
            os.symlink("/Us" + "ers/x", os.path.join(repo, "l"))
            Path(repo, "zorbla" + "x-ops.md").write_text("")
            code, d = self.json_in(repo)
            self.assertEqual((code, d["hits_outside_allowlist"]), (1, 3))
            self.assertEqual({(f["path"], f["group"]) for f in d["files"]},
                             {("k.md", "secret"), ("l", "home"),
                              ("zorbla" + "x-ops.md", "private")})

    def json_in(self, repo, *args):
        code, out, _ = run(repo, "--json", *args)
        return code, json.loads(out)

    def test_secret_group_catches_each_key_shape(self):
        keys = ["sk-an" + "t-api03-abcDEF_12-x", "gh" + "p_" + "a1B2" * 9,
                "github_" + "pat_" + "11AB" * 6, "AGE-SECRET-" + "KEY-1" + "QZ" * 20,
                "AK" + "IA" + "ABCDEFGH23456789", "-----BEG" + "IN RSA PRIV" + "ATE KEY-----",
                "-----BEG" + "IN PRIV" + "ATE KEY-----"]
        # the prefixes named in prose, and lowercase look-alikes, are not keys
        prose = ["`sk-an" + "t-`", "`gh" + "p_`", "BEG" + "IN .* PRIV" + "ATE KEY",
                 "ak" + "ia" + "abcdefgh23456789"]
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "keys.md").write_text("\n".join(keys) + "\n")
            Path(repo, "prose.md").write_text("\n".join(prose) + "\n")
            code, d = self.json_in(repo)
            self.assertEqual(code, 1)
            self.assertEqual(lf(d["groups"]["secret"]), {"lines": len(keys), "files": 1})
            out = run(repo)[1] + run(repo, "--json")[1]
            for key in keys:
                self.assertNotIn(key, out)

    def test_email_and_lan_172_and_local(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "e.md").write_text("mail al" + "ice@" + "example.com\nno at here\n")
            Path(repo, "n.md").write_text(
                "172." + "20.1.2\n172." + "31.0.1\nnas" + ".local here\n"
                "172.32.0.1\n172.15.0.1\n~/.local/state\n")
            code, d = self.json_in(repo)
            self.assertEqual(code, 1)
            self.assertEqual(lf(d["groups"]["email"]), {"lines": 1, "files": 1})
            self.assertEqual(lf(d["groups"]["lan"]), {"lines": 3, "files": 1})

    def test_binary_scanned_for_home_over_printable_runs(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            png = (b"\x89PNG\0\0" + ("/Us" + "ers/alice/p.png").encode() + b"\0"
                   + FIXTURES["person"].encode() + b"\0" + ("~/co" + "de/").encode()
                   + b"\0\x01")
            Path(repo, "a.png").write_bytes(png)
            code, d = self.json_in(repo)
            # one run of 8+ bytes carries the home path; the 7-byte run is not evaluated
            # for home; the person text is a private row's hit (h2)
            self.assertEqual(code, 1)
            self.assertEqual(d["files"], [{"path": "a.png", "group": "home", "lines": 1},
                                          {"path": "a.png", "group": "person", "lines": 1}])
            self.assertEqual(d["oversize"], 0)
            # UTF-16 (a BOM, or NULs on 90% of the odd or even bytes) is text (ADV10-8)
            text = "/Us" + "ers/alice/x\n" + FIXTURES["person"] + "\n"
            Path(repo, "le.md").write_bytes(text.encode("utf-16-le"))
            Path(repo, "be.md").write_bytes(text.encode("utf-16"))
            Path(repo, "zeros.bin").write_bytes(b"\0" * 64)
            # a file over 4 MiB is streamed, every line of it (ADV11-3)
            Path(repo, "big.txt").write_bytes(("/Us" + "ers/alice\n").encode() * 500000)
            code, d = self.json_in(repo)
            self.assertEqual(sorted((f["path"], f["group"], f["lines"]) for f in d["files"]),
                             [("a.png", "home", 1), ("a.png", "person", 1),
                              ("be.md", "home", 1), ("be.md", "person", 1),
                              ("big.txt", "home", 500000), ("le.md", "home", 1),
                              ("le.md", "person", 1)])
            self.assertEqual(d["oversize"], 1)

    def test_hygiene_oversize_is_scanned(self):
        # ADV11-3: 4 MiB + 1 of one line, then a home path: streamed, one hit, never a pass
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "f").write_bytes(b"x" * (4 * 1024 * 1024 + 1)
                                        + ("\n/Us" + "ers/me/x\n").encode())
            code, d = self.json_in(repo)
            self.assertEqual(code, 1)
            self.assertEqual(d["groups"]["home"]["lines"], 1)
            self.assertEqual(d["oversize"], 1)
            # a binary and a UTF-16 file over the cap stream too, a run across a chunk seen
            Path(repo, "f").unlink()
            Path(repo, "b.bin").write_bytes(b"\0" + b"y" * (1024 * 1024 - 4)
                                            + ("/Us" + "ers/me/bin").encode() + b"\0" * (4 << 20))
            Path(repo, "w.md").write_bytes(("z" * (5 << 20) + "\n/Us" + "ers/me/w\n")
                                           .encode("utf-16"))
            code, d = self.json_in(repo)
            self.assertEqual(sorted((f["path"], f["group"], f["lines"]) for f in d["files"]),
                             [("b.bin", "home", 1), ("w.md", "home", 1)])
            self.assertEqual(d["oversize"], 2)

    def test_hygiene_relay_adv11_15_first_line(self):
        # the relay's ADV11-15: a tracked file over 4 MiB whose first line holds a home
        # path and an email passed by path only, exit 0; streamed now (S14), both counted.
        # Binaries still skip lan, domain, private, person and sibling (ADV10-17, unchanged)
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "big.md").write_bytes(("/Us" + "ers/alice/x mail al" + "ice@"
                                              + "example.com\n").encode() + b"y" * (5 << 20))
            git(repo, "add", "big.md")
            code, d = self.json_in(repo)
            self.assertEqual(code, 1)
            self.assertEqual(sorted((f["path"], f["group"], f["lines"]) for f in d["files"]),
                             [("big.md", "email", 1), ("big.md", "home", 1)])
            self.assertEqual(d["oversize"], 1)

    def test_secret_allow_row_only_under_fixtures(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "tests", "fixtures").mkdir(parents=True)
            Path(repo, "tests", "fixtures", "k.md").write_text("sk-an" + "t-x\n")
            Path(repo, ".hygiene-allow").write_text("tests/fixtures/*.md: secret\n")
            self.assertEqual(self.json_in(repo)[0], 0)
            for row in ("*.md: secret", "tests/*.md: secret,home", "tests/fixture*/k.md: secret"):
                Path(repo, ".hygiene-allow").write_text(row + "\n")
                self.assertEqual(run(repo)[0], 2, row)

    def test_symlink_target_not_followed(self):
        with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as out:
            git(repo, "init", "-q")
            Path(out, "t.md").write_text(FIXTURES["person"] + "\n")
            os.symlink(os.path.join(out, "t.md"), os.path.join(repo, "link"))
            code, d = self.json_in(repo)
            # the target path is scanned; the target's content is not read
            self.assertEqual(d["groups"]["person"]["files"], 0)

    def test_private_list_loaded_never_printed(self):
        # the list's groups join the generic ones, in its order; no regex is ever printed
        code, d = self.json_result()
        self.assertEqual(list(d["groups"]), sorted(GENERIC + ["domain", "private", "person"]))
        code, out, err = run(self.repo)
        groups = [row.split()[0] for row in out.splitlines()[1:10]]
        self.assertEqual(groups, GENERIC + ["domain", "private", "person"])
        for args in ((), ("--json",), ("--require-private",)):
            code, out, err = run(self.repo, *args)
            self.assertEqual(code, 1)
            for rx in REGEXES:
                self.assertNotIn(rx, out + err, args)
            self.assertEqual(err, "", args)

    def test_private_list_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "none.tsv")
            code, out, err = run(self.repo, "--json", env={ENV: missing})
            self.assertEqual(err, "hygiene: no private list at %s; generic groups only\n"
                             % missing)
            # the scan runs on the generic groups, and its exit follows them
            d = json.loads(out)
            self.assertEqual((code, sorted(d["groups"])), (1, sorted(GENERIC)))
            with tempfile.TemporaryDirectory() as repo:
                git(repo, "init", "-q")
                Path(repo, "p.md").write_text(FIXTURES["person"] + "\n" + FIXTURES["domain"])
                self.assertEqual(run(repo, env={ENV: missing})[0], 0)
                self.assertEqual(run(repo)[0], 1)
                # an allow row naming a group the absent list would add is tolerated
                Path(repo, ".hygiene-allow").write_text("p.md: person\n")
                self.assertEqual(run(repo, env={ENV: missing})[0], 0)
                Path(repo, ".hygiene-allow").write_text("p.md: nosuchgroup\n")
                self.assertEqual(run(repo)[0], 2)

    def test_require_private_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "none.tsv")
            code, out, err = run(self.repo, "--require-private", env={ENV: missing})
            self.assertEqual((code, out), (2, ""))
            self.assertIn(missing, err)
            # unreadable: a directory, and a file that is not UTF-8
            bad = os.path.join(tmp, "bad.tsv")
            Path(bad).write_bytes(b"person\t\xff\xfe\n")
            for path in (tmp, bad):
                code, out, err = run(self.repo, "--require-private", env={ENV: path})
                self.assertEqual((code, out), (2, ""), path)
                code, out, err = run(self.repo, "--json", env={ENV: path})
                self.assertIn("unreadable; generic groups only", err)
                self.assertEqual(sorted(json.loads(out)["groups"]), sorted(GENERIC))
            # present: the flag changes nothing
            self.assertEqual(run(self.repo, "--require-private")[0], 1)
            Path(self.repo, ".hygiene-allow").write_text(
                "*.txt: home,lan,domain,private,person,sibling\ndocs/*.md: sibling\n"
                "docs/*/*.md: sibling\n")
            self.assertEqual(run(self.repo, "--require-private")[0], 0)

    def test_private_new_group_hit_and_default_path(self):
        # a new group name is allowed; a hit prints as any other; a line counts once
        # per group even when an in-file and a private regex both match it
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "x.md").write_text("the frobni" + "z board\n" + FIXTURES["home"] + "\n")
            text = "#codename\tx-ops\ncodename\tfrobni[z]\nhome\talic[e]\n"
            xdg = Path(tmp, "xdg", "agentik")
            xdg.mkdir(parents=True)
            Path(xdg, "hygiene-private.tsv").write_text(text)
            home = Path(tmp, "home", ".config", "agentik")
            home.mkdir(parents=True)
            Path(home, "hygiene-private.tsv").write_text(text)
            for env in ({ENV: None, "XDG_CONFIG_HOME": str(Path(tmp, "xdg"))},
                        {ENV: "", "XDG_CONFIG_HOME": "", "HOME": str(Path(tmp, "home"))}):
                code, out, err = run(repo, "--json", env=env)
                d = json.loads(out)
                self.assertEqual((code, err), (1, ""), env)
                self.assertEqual(lf(d["groups"]["codename"]), {"lines": 1, "files": 1})
                self.assertEqual(lf(d["groups"]["home"]), {"lines": 1, "files": 1})
                code, out, err = run(repo, env=env)
                self.assertIn("x.md  codename  1", out.splitlines())
                self.assertNotIn("frobni[z]", out + err)
            Path(repo, ".hygiene-allow").write_text("x.md: codename,home\n")
            self.assertEqual(run(repo, env={ENV: str(Path(xdg, "hygiene-private.tsv"))})[0], 0)

    def test_private_bad_line_exits_two_unprinted(self):
        with tempfile.TemporaryDirectory() as tmp:
            for line in ("person glimmerwic[k]", "per son\tglimmerwic[k]", "person\t",
                         "person\tglimmer(wic[k]"):
                path = os.path.join(tmp, "p.tsv")
                Path(path).write_text("# ok\n" + line + "\n")
                code, out, err = run(self.repo, env={ENV: path})
                self.assertEqual((code, out), (2, ""), line)
                self.assertIn("%s:2: bad entry" % path, err)
                self.assertNotIn("glimmer", err.lower(), line)


# The names the tools had before agentik-r1, assembled so this file scans clean.
OLD = ["claude-code-" + "session", "claude-code-" + "decision" + "s", "claude-code-" + "respea" + "k",
       "claude-code-" + "agents", "agent-" + "relay", "claude-" + "session",
       "claude-" + "api-agent", "claude-" + "local", "claude-" + "fanout", "claude-" + "costs",
       "claude-" + "agents", "local" + "rig", "agent" + "route", "`" + "relay run",
       "`" + "decision" + "s show 5"]
# Look-alikes the group leaves alone: a longer word, an uppercase verb, no backtick.
NOT_OLD = ["my-claude-code-" + "session", "xclaude-code-" + "agents", "claude-" + "localhost",
           "local" + "rigs", "`" + "relay Run", "`" + "relay 5", "relay " + "run",
           "`agentik relay run`", "`" + "decision" + "s", "Agent" + "routes"]


def run_files(files, *args):
    """The scan over a scratch repo holding `files`, all added."""
    with tempfile.TemporaryDirectory() as repo:
        git(repo, "init", "-q")
        for name, text in files.items():
            Path(repo, name).parent.mkdir(parents=True, exist_ok=True)
            Path(repo, name).write_text(text)
        git(repo, "add", "-A")
        return run(repo, *args)


class RenamedTest(unittest.TestCase):
    """The `renamed` group (agentik-r1 6.1): its patterns, over the live files only."""

    def scan(self, files):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            for name, text in files.items():
                Path(repo, name).parent.mkdir(parents=True, exist_ok=True)
                Path(repo, name).write_text(text)
            git(repo, "add", "-A")
            code, out, _ = run(repo, "--json")
            d = json.loads(out)
            return code, d, sorted(f["path"] for f in d["files"] if f["group"] == "renamed")

    def test_each_old_name_hits_and_look_alikes_do_not(self):
        code, d, paths = self.scan({"old.md": "\n".join(OLD) + "\n",
                                    "new.md": "\n".join(NOT_OLD) + "\n"})
        self.assertEqual(code, 1)
        self.assertEqual(lf(d["groups"]["renamed"]), {"lines": len(OLD), "files": 1})
        self.assertEqual(paths, ["old.md"])

    def test_a_slug_that_runs_on_past_the_name_does_not_hit(self):
        # a public URL whose slug continues after a tool name is not an old id
        # (research finding rf1-3); the old ids still hit before `@`, `:`, `/` and the end
        slugs = ["https://example.com/blog/claude-code-" + "session-management-and-1m-context",
                 "see claude-code-" + "agents-tips, claude-code-" + "decision" + "s_log"]
        ids = ["claude-code-" + "session@claude-code-" + "session",
               "/agents:status from claude-code-" + "agents:", "../claude-code-" + "respea" + "k/x",
               "the claude-code-" + "decision" + "s."]
        code, d, paths = self.scan({"slug.md": "\n".join(slugs) + "\n",
                                    "ids.md": "\n".join(ids) + "\n"})
        self.assertEqual(code, 1)
        self.assertEqual(paths, ["ids.md"])
        self.assertEqual(lf(d["groups"]["renamed"]), {"lines": len(ids), "files": 1})

    def test_live_files_only(self):
        text = OLD[4] + "\n"
        files = {name: text for name in (
            "a.md", "sub/b.py", "history/sessions/PROMPT-x.md", "history/sessions/BRIEF-y.md",
            "design/x.md", "bugs/b.md", "history/sessions/NEXT", "history/other.md",
            "NICE_TO_HAVE.md", "sub/NICE_TO_HAVE.md", "CHANGELOG.md", "sub/CHANGELOG",
            "history/sessions/deep/PROMPT-z.md")}
        code, d, paths = self.scan(files)
        self.assertEqual(code, 1)
        self.assertEqual(paths, ["a.md", "history/sessions/BRIEF-y.md",
                                 "history/sessions/PROMPT-x.md", "sub/b.py"])
        # a record's path is not live either; the other groups still scan records
        code, d, paths = self.scan({"design/" + OLD[5] + ".md": "", "design/h.md":
                                    "/Us" + "ers/alice\n"})
        self.assertEqual((code, paths, d["groups"]["home"]["files"]), (1, [], 1))
        code, d, paths = self.scan({"design/" + OLD[5] + ".md": text})
        self.assertEqual((code, paths, d["hits_outside_allowlist"]), (0, [], 0))

    def test_newest_charter_per_chain_in_integer_order(self):
        text = OLD[0] + "\n"
        sit = "history/sittings/"
        code, d, paths = self.scan({
            ".hygiene-live": "# the running chains\nx\n\ny\n-\nz\n",
            sit + "2026-10-13-9-x.md": text, sit + "2026-10-13-10-x.md": "clean\n",
            sit + "2026-10-12-30-y.md": "clean\n", sit + "2026-10-13-2-y.md": text,
            sit + "2026-10-13-1.md": text, sit + "2026-10-13-3.md": "clean\n",
            sit + "2026-10-14-1-z.md": text, sit + "notes.md": text})
        # x: -10 is newest (clean); y: the later date wins over the larger n; the empty
        # chain's newest is -3 (clean); z has one charter; notes.md is no charter
        self.assertEqual(code, 1)
        self.assertEqual(paths, [sit + "2026-10-13-2-y.md", sit + "2026-10-14-1-z.md"])

    def test_only_declared_chains_are_live(self):
        sit = "history/sittings/"
        charters = {sit + "2026-10-13-10-x.md": OLD[0] + "\n", sit + "2026-10-13-4.md": OLD[4] + "\n",
                    sit + "2026-10-13-2-once.md": OLD[5] + "\n"}
        # no .hygiene-live: no charter is live, so nothing counts
        code, d, paths = self.scan(dict(charters))
        self.assertEqual((code, d["groups"]["renamed"]["files"], paths), (0, 0, []))
        for live, want in (("", []), ("# none yet\n", []), ("x\n", [sit + "2026-10-13-10-x.md"]),
                           ("-\n", [sit + "2026-10-13-4.md"]),
                           ("x\n-\n", [sit + "2026-10-13-10-x.md", sit + "2026-10-13-4.md"])):
            code, d, paths = self.scan(dict(charters, **{".hygiene-live": live}))
            self.assertEqual((code, paths), (1 if want else 0, want), live)
        for bad in ("a/b\n", "x y\n"):
            code, out, err = run_files(dict(charters, **{".hygiene-live": bad}))
            self.assertEqual(code, 2, bad)

    def test_allow_row_and_own_patterns(self):
        code, d, paths = self.scan({"GUIDE.md": OLD[5] + "\n",
                                    ".hygiene-allow": "# the alias paragraph\nGUIDE.md: renamed\n"})
        self.assertEqual((code, d["groups"]["renamed"]["files"], d["files"]), (0, 1, []))
        code, d, paths = self.scan({"hygiene": SCRIPT.read_text()})
        self.assertEqual((code, paths), (0, []))


class ReadErrorTest(unittest.TestCase):
    """A file the scan cannot read is a failed precondition: exit 2 and one stderr
    line, never 1 (a hit) and never a traceback."""

    def one_line_two(self, repo, *args):
        code, out, err = run(repo, *args)
        self.assertEqual((code, out), (2, ""), args)
        self.assertEqual(len(err.splitlines()), 1, err)
        self.assertTrue(err.startswith("hygiene: "), err)
        self.assertNotIn("Traceback", err)

    def test_read_errors_exit_two_with_one_line(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "a.md").write_text("clean\n")
            Path(repo, "A").write_bytes(b"a.md: home\n\xff\n")
            self.one_line_two(repo, "--allow", os.path.join(repo, "A"))
            Path(repo, "adir").mkdir()
            self.one_line_two(repo, "--allow", os.path.join(repo, "adir"))
            Path(repo, ".hygiene-allow").mkdir()
            self.one_line_two(repo)
            Path(repo, ".hygiene-allow").rmdir()
            self.assertEqual(run(repo)[0], 0)
            if os.geteuid() != 0:
                locked = Path(repo, "locked.md")
                locked.write_text("clean\n")
                locked.chmod(0)
                try:
                    self.one_line_two(repo)
                finally:
                    locked.chmod(0o644)


class PrivateListTest(unittest.TestCase):
    """Packet h2: a private term in a binary is a hit in both scans (n11), and
    --require-private wants a list holding a term (n12). Terms invented, assembled."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        git(self.repo, "init", "-q", "-b", "main")
        Path(self.repo, "a.md").write_text("clean\n")
        self.commit("base")

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self, message):
        git(self.repo, "add", "-A")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t" + "@x.invalid",
            "commit", "-q", "--allow-empty", "-m", message)
        out = subprocess.run(["git", "-C", self.repo, "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True).stdout
        return out.strip()[:12]

    def one_line(self, path, *args):
        code, out, err = run(self.repo, *args, env={ENV: path})
        self.assertEqual((code, out), (2, ""), (path, args))
        self.assertEqual(len(err.splitlines()), 1, err)
        self.assertIn(path, err)
        self.assertIn("nothing scanned", err)

    def outside(self, *args, env=None):
        code, out, err = run(self.repo, "--json", *args, env=env)
        d = json.loads(out)
        return code, {(f["path"], f["group"]): f["lines"] for f in d["files"]}, d

    def test_h1_require_private_and_a_list_with_no_term_exit_two(self):
        base = self.commit("empty")
        Path(self.repo, "p.md").write_text(FIXTURES["person"] + "\n")
        self.commit("adds a term")
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in (("c.tsv", "# a comment\n  # another\n"),
                               ("b.tsv", "\n  \n\t\n"), ("z.tsv", "")):
                path = os.path.join(tmp, name)
                Path(path).write_text(text)
                self.one_line(path, "--require-private")
                self.one_line(path, "--require-private", "--commits", base + "..main")

    def test_h2_require_private_missing_or_unreadable_says_nothing_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "bad.tsv")
            Path(bad).write_bytes(b"person\t\xff\n")
            for path in (os.path.join(tmp, "none.tsv"), tmp, bad):
                self.one_line(path, "--require-private")
                self.one_line(path, "--require-private", "--commits", "HEAD")

    def test_h3_without_the_flag_an_empty_list_is_unchanged(self):
        Path(self.repo, "p.md").write_text(FIXTURES["person"] + "\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "c.tsv")
            Path(path).write_text("# a comment\n")
            self.assertEqual(run(self.repo, env={ENV: path})[::2], (0, ""))
            Path(self.repo, "h.md").write_text(FIXTURES["home"] + "\n")
            self.assertEqual(run(self.repo, env={ENV: path})[::2], (1, ""))

    def test_h4_a_private_term_in_a_binary_is_a_hit_in_the_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "p.tsv")
            Path(path).write_text(PRIVATE + "accent\tz[\u00e9]nobia\nshort\tqw[z]x\n")
            files = {"run.bin": b"\0\1" + FIXTURES["person"].encode(),
                     "upper.bin": b"\0\xc3\xa9" + FIXTURES["person"].upper().encode() + b"\xff",
                     "accent.bin": b"\0\0" + ("z" + "\u00e9nobia").encode() + b"\0",
                     "short.bin": b"\0\0" + ("qw" + "zx").encode() + b"\0\x01",
                     "lan.bin": b"\0\0" + FIXTURES["lan"].encode() + b"\0",
                     "sib.bin": b"\0\0" + FIXTURES["sibling"].encode() + b"\0"}
            for name, data in files.items():
                Path(self.repo, name).write_bytes(data)
            code, hits, _ = self.outside(env={ENV: path})
            self.assertEqual((code, hits), (1, {("run.bin", "person"): 1,
                                                ("upper.bin", "person"): 1,
                                                ("accent.bin", "accent"): 1,
                                                ("short.bin", "short"): 1}))
            for args in ((), ("--json",)):
                _, out, err = run(self.repo, *args, env={ENV: path})
                for token in MATCHED + ["qw" + "zx", "n" + "obia"]:
                    self.assertNotIn(token, (out + err).lower(), args)

    def test_h5_a_streamed_binary_is_searched_whole(self):
        Path(self.repo, "big.bin").write_bytes(b"\0" + b"\x01" * (5 << 20)
                                               + FIXTURES["private"].encode() + b"\0")
        code, hits, d = self.outside()
        self.assertEqual((code, hits, d["oversize"]), (1, {("big.bin", "private"): 1}, 1))

    def test_h6_a_private_term_in_a_binary_is_a_hit_in_the_range(self):
        base = self.commit("empty")
        Path(self.repo, "pic.png").write_bytes(b"PNG\0\0\0" + FIXTURES["person"].encode()
                                               + b"\0\x01")
        sha = self.commit("adds a picture")
        Path(self.repo, "pic.png").unlink()
        self.commit("drops it")
        code, hits, d = self.outside("--commits", base + "..main")
        self.assertEqual((code, hits, d["commits"]["hit"]),
                         (1, {("pic.png", "person"): 1}, [sha]))

    def both(self, base, path):
        """The hits of the tree and of the range base..main, each with its exit."""
        tree = self.outside(env={ENV: path})
        rng = self.outside("--commits", base + "..main", env={ENV: path})
        return (tree[0], tree[1]), (rng[0], rng[1])

    def test_h7_an_anchored_private_row_finds_its_term_at_a_run_edge(self):
        # h2 round 1, F1: at f0fba84 a private home or email row met a run's edges
        term = "zorbl" + "axquux"
        base = self.commit("empty")
        Path(self.repo, "x.bin").write_bytes(b"\0\1" + term.encode() + b"\0\1")
        Path(self.repo, "x.txt").write_text("a\n" + term + "\n")
        # a term shorter than a run, alone on a line of a binary: the anchors meet a newline
        Path(self.repo, "y.bin").write_bytes(b"\0\1\n" + ("qw" + "zx").encode() + b"\n\0")
        self.commit("adds the files")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "p.tsv")
            Path(path).write_text("home\t^zorbl[a]xquux\nemail\tzorbl[a]xquux$\n"
                                  "short\t^qw[z]x$\n")
            want = (1, {("x.bin", "home"): 1, ("x.bin", "email"): 1, ("x.txt", "home"): 1,
                        ("x.txt", "email"): 1, ("y.bin", "short"): 1})
            self.assertEqual(self.both(base, path), (want, want))

    def test_h8_one_occurrence_counts_once_in_home(self):
        # h2 round 1, F5: the generic home row and a private home row on one occurrence
        text = "/Us" + "ers/zorbl" + "ax"
        base = self.commit("empty")
        Path(self.repo, "h.bin").write_bytes(b"\0\1" + text.encode() + b"\0")
        Path(self.repo, "h.txt").write_text(text + "\n")
        self.commit("adds the files")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "p.tsv")
            Path(path).write_text("home\tzorbl[a]x\n")
            want = (1, {("h.bin", "home"): 1, ("h.txt", "home"): 1})
            self.assertEqual(self.both(base, path), (want, want))

    def private_hits(self, rows, *args):
        """{(path, group): lines} of the tree (no args) or a range, under a private list
        of `rows`; each scan must end within 30 s."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "p.tsv")
            Path(path).write_text("".join("%s\t%s\n" % row for row in rows))
            env = dict(os.environ, **{ENV: path})
            p = subprocess.run([str(SCRIPT), "--repo", self.repo, "--json", *args],
                               capture_output=True, text=True, env=env, timeout=30)
            return {(f["path"], f["group"]): f["lines"] for f in json.loads(p.stdout)["files"]}

    def test_h9_a_leading_dot_star_row_reads_a_binary_without_a_newline_in_linear_time(self):
        # packet h2-hygiene-binary, R2 (NICE n13): a row's leading `.*` is searched without
        # it; at 9f20220 each 256 KiB binary took minutes
        pad = (b"\0" * 61 + b"\1\2\3") * 4096
        noise = bytes(b for b in random.Random(7).randbytes(300 << 10) if b != 10)[:256 << 10]
        base = self.commit("empty")
        Path(self.repo, "clean.bin").write_bytes(pad)
        Path(self.repo, "noise.bin").write_bytes(b"\0" + noise)
        Path(self.repo, "z.bin").write_bytes(b"\0\1" + ("qw" + "zx").encode() + b"\0\1")
        self.commit("adds three binaries")
        for args in ((), ("--commits", base + "..main")):
            hits = self.private_hits([("short", ".*qw[z]x")], *args)
            self.assertEqual({k: v for k, v in hits.items() if k[1] == "short"},
                             {("z.bin", "short"): 1}, args)

    def test_h10_a_row_across_a_control_or_bad_byte_keeps_the_pin_answer(self):
        # h2-hygiene-binary round 1: at dfabbd0 a binary's control and bad bytes broke its
        # lines, and these rows lost the hits 9f20220 found (or gained the anchored ones)
        n, u16 = b"\0", ("zq" + "term").encode("utf-16-le")
        cases = [  # (file, content, row, hit at 9f20220)
            ("a.bin", n + b"zqfoo\0zqbar" + n, r"zqfoo.*zqbar", True),
            ("b.bin", n + b"zqfoo\0zqbar" + n, r"zqfoo.zqbar", True),
            ("c.bin", n + b"zqfoo\0zqbar" + n, r"zqfoo\x00zqbar", True),
            ("d.bin", n + b"zqfoo\r\nzqbar" + n, r"zqfoo\r\nzqbar", True),
            ("e.bin", n + b"zqfoo\x7fzqbar" + n, r"zqfoo.zqbar", True),
            ("f.bin", n + b"zqfoo\xffzqbar" + n, r"zqfoo.zqbar", True),
            ("g.bin", n + b"zqfoo\xef\xbf\xbdzqbar" + n, r"zqfoo.zqbar", True),
            ("h.bin", b"\0\1\2zqalice\x05\x17zqsmith\0", r"zqalice.{0,3}zqsmith", True),
            ("i.bin", b"\0\0\1\1" * 2048 + u16 + n, r"z\x00?q\x00?t\x00?e\x00?r\x00?m", True),
            ("j.bin", b"\0\0\1\1" * 2048 + u16 + n, r"z.q.t.e.r.m", True),
            ("k.bin", n + b"\x01zqterm" + n, r"^zqterm", False),
            ("l.bin", n + b"zqterm\x01" + n, r"zqterm$", False),
        ]
        base = self.commit("empty")
        for name, data, _, _ in cases:
            Path(self.repo, name).write_bytes(data)
        self.commit("adds the binaries")
        rows = [("g" + name[0], row) for name, _, row, _ in cases]
        want = {(name, "g" + name[0]) for name, _, _, hit in cases if hit}
        for args in ((), ("--commits", base + "..main")):
            hits = self.private_hits(rows, *args)
            own = {(name, "g" + name[0]) for name, _, _, _ in cases}
            self.assertEqual(own & set(hits), want, args)

    def test_h11_a_leading_or_trailing_dot_star_counts_as_the_row_without_it(self):
        # packet h2-hygiene-binary, R2: the same files and line counts, tree and range
        t = "zq" + "term"
        files = {"a.txt": t + "\n", "b.txt": "x " + t + " y\n" + t + t + "\n",
                 "c.txt": "no\n" + t + "\r\nmore " + t + "\n", "d.txt": "clean\n",
                 "e.md": "# " + t.upper() + "\n", "f.bin": b"\0" + t.encode() + b"\0",
                 "g.bin": b"\0\1" + t.encode() + b" a run of text\0\xff" + t.encode(),
                 "h.bin": b"\0" * 9000 + b"\xff" + t.encode() + b"\n" + t.encode(),
                 "i.bin": b"\0\1\2\3", "j.txt": (t + "\n").encode("utf-16"),
                 "k.txt": "a" * 5000 + t + "\n", t + ".txt": "path only\n"}
        base = self.commit("empty")
        for name, data in files.items():
            if isinstance(data, bytes):
                Path(self.repo, name).write_bytes(data)
            else:
                Path(self.repo, name).write_text(data)
        self.commit("adds the files")
        for args in ((), ("--commits", base + "..main")):
            plain = self.private_hits([("dot", "zq[t]erm")], *args)
            self.assertEqual(len([k for k in plain if k[1] == "dot"]), 10, plain)
            for row in (".*zq[t]erm", "zq[t]erm.*", ".*zq[t]erm.*", "(?i).*zq[t]erm"):
                self.assertEqual(self.private_hits([("dot", row)], *args), plain, (row, args))

if __name__ == "__main__":
    unittest.main()
