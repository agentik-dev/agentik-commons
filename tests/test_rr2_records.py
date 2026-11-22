"""Packet rr2-records-resolver: scripts/agentik_records.py answers where a repo's working records
are (hq design/28 §3 items 1 to 6, §11). Each case of tests/records_cases.json is built under a
fresh temp folder, HOME that folder, the user's and the system's git config files left out, and
git's search stopped above it, so no case reads a real repo's config or the live home."""
import ast
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "agentik_records.py"
CASES = ROOT / "tests" / "records_cases.json"
COPY = ROOT / "plugins" / "suite" / "lib" / "agentik_records.py"
LAUNCHER = ROOT / "plugins" / "suite" / "bin" / "agentik-suite"
MAIL = "builder" + "@" + "x.invalid"  # made up, and split so no line of this file is an address


def load():
    spec = importlib.util.spec_from_file_location("agentik_records_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def quiet_env(root):
    """The environment each case runs in: HOME the temp folder, no user or system git file."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"HOME": root, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CEILING_DIRECTORIES": os.path.dirname(root), "XDG_CONFIG_HOME": os.path.join(root, ".config"),
                "GIT_AUTHOR_NAME": "a builder", "GIT_AUTHOR_EMAIL": MAIL,
                "GIT_COMMITTER_NAME": "a builder", "GIT_COMMITTER_EMAIL": MAIL})
    return env


def git(env, folder, *args):
    subprocess.run(["git", "-C", folder, *args], check=True, env=env, capture_output=True)


def fill(text, root):
    return text.replace("{root}", root) if isinstance(text, str) else text


def declare(env, top, spec):
    path = os.path.join(top, spec["file"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if spec.get("tracked"):  # committed without the line, which is then added and left uncommitted
        with open(path, "w") as fh:
            fh.write("# a tracked file\n")
        git(env, top, "add", spec["file"])
        git(env, top, "commit", "-q", "-m", "tracked")
    with open(path, "a") as fh:
        fh.write("# a made-up repo's file\n%s\n" % spec["line"])
    if spec.get("commit", True):
        git(env, top, "add", spec["file"])
        git(env, top, "commit", "-q", "-m", "declare")


def repo(env, top):
    os.makedirs(top, exist_ok=True)
    git(env, top, "init", "-q", "-b", "main")
    with open(os.path.join(top, "README.md"), "w") as fh:
        fh.write("a made-up repo\n")
    git(env, top, "add", "README.md")
    git(env, top, "commit", "-q", "-m", "first")


def build(case, root, env):
    """The case's layout under root; the environment resolve runs in."""
    clone = os.path.join(root, case["clone"])
    repo(env, clone)
    if "declare" in case:  # before the worktrees, so their branches hold it too
        declare(env, clone, case["declare"])
    for tree in case.get("worktrees", ()):
        if isinstance(tree, list):  # detached at a commit
            git(env, clone, "worktree", "add", "-q", "--detach", os.path.join(root, tree[0]), tree[1])
        else:
            git(env, clone, "worktree", "add", "-q", os.path.join(root, tree), "-b", os.path.basename(tree))
    for old, new in case.get("moves", ()):
        os.makedirs(os.path.dirname(os.path.join(root, new)), exist_ok=True)
        os.rename(os.path.join(root, old), os.path.join(root, new))
    if "holder" in case:
        top = os.path.join(root, case["holder"]["path"])
        repo(env, top)
        if "declare" in case["holder"]:
            declare(env, top, case["holder"]["declare"])
    for folder in case.get("folders", ()):
        os.makedirs(os.path.join(root, folder), exist_ok=True)
    for link, target in case.get("links", ()):
        os.symlink(os.path.join(root, target), os.path.join(root, link))
    keys = case.get("key", [])
    for value in keys if isinstance(keys, list) else [keys]:
        git(env, clone, "config", "--local", "--add", "agentik.records", fill(value, root))
    if "config_text" in case:
        with open(os.path.join(clone, ".git", "config"), "a") as fh:
            fh.write(case["config_text"])
    if "worktree_key" in case:
        git(env, clone, "config", "--local", "extensions.worktreeConfig", "true")
        git(env, os.path.join(root, case["worktrees"][0]), "config", "--worktree", "agentik.records",
            fill(case["worktree_key"], root))
    run = dict(env)
    if "env_key" in case:
        run.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "agentik.records",
                    "GIT_CONFIG_VALUE_0": fill(case["env_key"], root)})
    return run


def has(need, root):
    """True where the file system under root has what a case `needs` (C5 of review 1's fix)."""
    other = {"case-blind": root.swapcase(), "firmlink": "/System/Volumes/Data" + root}[need]
    try:
        return os.path.samefile(root, other)
    except OSError:
        return False


class CasesTest(unittest.TestCase):
    def test_cases(self):
        records = load()
        cases = json.loads(CASES.read_text())["cases"]
        self.assertGreaterEqual(len(cases), 20)
        for case in cases:
            with self.subTest(case["name"]), tempfile.TemporaryDirectory() as tmp:
                root = os.path.realpath(tmp)
                if "needs" in case and not has(case["needs"], root):
                    self.skipTest("the temp folder's file system is not " + case["needs"])
                env = quiet_env(root)
                run = build(case, root, env)
                expect = {k: fill(v, root) for k, v in case["expect"].items()}
                with mock.patch.dict(os.environ, run, clear=True):
                    try:
                        got = records.resolve(os.path.join(root, case["from"]))
                    except records.NoRepo:
                        got = {"error": "no-repo"}
                self.assertEqual(got, expect)

    def test_the_states_and_whys_are_each_a_case(self):
        cases = json.loads(CASES.read_text())["cases"]
        seen = {(c["expect"].get("state"), c["expect"].get("why")) for c in cases}
        for pair in [("own", None), ("out", None), ("unset", "no-key"), ("broken", "unread"), ("broken", "many"), ("broken", "relative"),
                     ("broken", "missing"), ("broken", "inside"), ("broken", "name"), ("broken", "holder")]:
            self.assertIn(pair, seen)

    def test_a_hooks_git_dir_does_not_move_the_answer(self):
        records = load()
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.realpath(tmp)
            env = quiet_env(root)
            repo(env, os.path.join(root, "code/widget"))
            repo(env, os.path.join(root, "code/other"))
            env["GIT_DIR"] = os.path.join(root, "code/other/.git")
            with mock.patch.dict(os.environ, env, clear=True):
                got = records.resolve(os.path.join(root, "code/widget"))
            self.assertEqual((got["state"], got["records"]), ("own", os.path.join(root, "code/widget")))

    def test_shape(self):
        text = SCRIPT.read_text()
        self.assertTrue(text.startswith('"""'))
        imports = {a.name for node in ast.walk(ast.parse(text)) if isinstance(node, ast.Import) for a in node.names}
        imports |= {node.module for node in ast.walk(ast.parse(text)) if isinstance(node, ast.ImportFrom)}
        self.assertLessEqual(imports, {"os", "subprocess"})


class SyncTest(unittest.TestCase):
    """R7: in a made-up tool tree with plugin/lib/, sync places the resolver, lists it and names it;
    the placed copy runs under -I with that plugin/lib alone on the path."""

    def test_sync_places_the_resolver(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.realpath(tmp)
            env = quiet_env(root)
            tool = os.path.join(root, "widget")
            repo(env, tool)
            os.makedirs(os.path.join(tool, "plugin", ".claude-plugin"))
            os.makedirs(os.path.join(tool, "plugin", "lib"))
            Path(tool, "plugin/.claude-plugin/plugin.json").write_text(json.dumps({"name": "widget", "version": "0.1.0"}))
            p = subprocess.run([str(ROOT / "scripts" / "sync"), tool], capture_output=True, text=True, env=env)
            self.assertEqual((p.returncode, p.stderr), (0, ""))
            self.assertIn("lib/agentik_install.py, lib/agentik_records.py, lib/agentik_term/", p.stdout)
            placed = Path(tool, "plugin/lib/agentik_records.py")
            self.assertEqual(placed.read_bytes(), SCRIPT.read_bytes())
            self.assertIn("  plugin/lib/agentik_records.py\n", Path(tool, "scripts/vendored.sha256").read_text())
            probe = ("import sys; sys.path.insert(0, sys.argv[1]); import agentik_records as r; "
                     "print(r.resolve(sys.argv[2])['state'])")
            p = subprocess.run(["/usr/bin/python3", "-I", "-c", probe, str(placed.parent), tool],
                               capture_output=True, text=True, env=env)
            self.assertEqual((p.returncode, p.stdout), (0, "own\n"), p.stderr)


class SuiteTest(unittest.TestCase):
    """R8: the suite's copy, `records` from the worktree's own launcher, and the doctor's row, each
    in a temp clone with HOME a temp folder."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = os.path.realpath(tmp.name)
        self.env = quiet_env(self.root)
        self.env.update({"PATH": "/usr/bin:/bin", "XDG_CACHE_HOME": os.path.join(self.root, "cache")})
        self.clone = os.path.join(self.root, "code", "widget")
        repo(self.env, self.clone)

    def suite(self, cwd, *args):
        p = subprocess.run([str(LAUNCHER), *args], capture_output=True, text=True, env=self.env, cwd=cwd,
                           timeout=60)
        return p.returncode, p.stdout, p.stderr

    def test_the_copy_is_byte_equal(self):
        self.assertEqual(COPY.read_bytes(), SCRIPT.read_bytes())

    def test_launcher_records_json_in_a_clone_and_its_worktree(self):
        code, out, err = self.suite(self.clone, "records", "--json")
        self.assertEqual((code, err), (0, ""))
        got = json.loads(out)
        self.assertEqual((got["schema"], got["state"], got["records"]), ("agentik.records/1", "own", self.clone))
        tree = os.path.join(self.root, "code", "widget-b")
        git(self.env, self.clone, "worktree", "add", "-q", tree, "-b", "b")
        code, out, err = self.suite(tree, "records", "--json")
        self.assertEqual((code, json.loads(out)["records"], json.loads(out)["repo"]), (0, tree, self.clone))
        code, out2, err = self.suite(self.root, "records", "--json", tree)  # DIR names the folder
        self.assertEqual(json.loads(out2), json.loads(out))

    def test_launcher_records_plain_writes_nothing(self):
        os.makedirs(os.path.join(self.root, "recs", "gadget"))
        git(self.env, self.clone, "config", "--local", "agentik.records", os.path.join(self.root, "recs", "gadget"))
        before = sorted(str(p) for p in Path(self.root).rglob("*") if "cache" not in p.parts)
        code, out, err = self.suite(self.clone, "records")
        self.assertEqual((code, err), (0, ""))
        rows = out.splitlines()
        self.assertEqual([r.split(":", 1)[0] for r in rows], ["repo", "records", "holder", "prefix", "state", "why"])
        self.assertIn("state: broken", rows)
        self.assertIn("records: none", rows)
        self.assertTrue(rows[-1].startswith("why: agentik.records names a folder whose name"), rows[-1])
        self.assertTrue(rows[-1].endswith("; agentik.records is " + os.path.join(self.root, "recs", "gadget")), rows[-1])
        self.assertEqual(sorted(str(p) for p in Path(self.root).rglob("*") if "cache" not in p.parts), before)

    def test_broken_names_the_key_and_its_values_cleaned(self):
        """C4: the broken line names agentik.records and each value, an escape byte taken out."""
        os.makedirs(os.path.join(self.root, "a", "widget"))
        git(self.env, self.clone, "config", "--local", "agentik.records", os.path.join(self.root, "a", "widget"))
        git(self.env, self.clone, "config", "--local", "--add", "agentik.records", "x\x1b[31m/widget")
        code, out, err = self.suite(self.clone, "records")
        self.assertEqual((code, err), (0, ""))
        self.assertNotIn("\x1b", out)
        self.assertEqual(out.splitlines()[-1], "why: this clone sets agentik.records more than once; agentik.records is "
                         + os.path.join(self.root, "a", "widget") + ", x/widget")  # the whole CSI gone (sc17 R9)
        code, rows = self.doctor_row(self.clone)
        self.assertEqual([r["status"] for r in rows], ["fail"])
        self.assertNotIn("\x1b", rows[0]["detail"])
        self.assertIn("; agentik.records is ", rows[0]["detail"])

    def test_out_with_no_holder_says_nothing_is_committed(self):
        os.makedirs(os.path.join(self.root, "recs", "widget"))
        git(self.env, self.clone, "config", "--local", "agentik.records", os.path.join(self.root, "recs", "widget"))
        code, out, err = self.suite(self.clone, "records")
        self.assertIn("holder: none, so nothing is committed: no git repo holds the folder", out.splitlines())

    def test_records_refusals(self):
        loose = os.path.join(self.root, "loose")
        os.mkdir(loose)
        self.assertEqual(self.suite(loose, "records")[0], 2)
        self.assertEqual(self.suite(self.clone, "records", "nowhere")[0], 2)
        self.assertEqual(self.suite(self.clone, "records", ".", "again")[0], 2)

    def doctor_row(self, cwd):
        code, out, err = self.suite(cwd, "doctor", "--json")
        suite = json.loads(out)["tools"][0]["checks"]
        return code, [c for c in suite if c["name"] == "records"]

    def test_doctor_row_by_state(self):
        code, rows = self.doctor_row(self.clone)
        self.assertEqual([r["status"] for r in rows], ["ok"])
        self.assertTrue(rows[0]["detail"].startswith("the records of "), rows[0]["detail"])  # own is not named
        Path(self.clone, ".hygiene-allow").write_text("records: out\n")
        git(self.env, self.clone, "add", ".hygiene-allow")
        git(self.env, self.clone, "commit", "-q", "-m", "declare")
        code, rows = self.doctor_row(self.clone)
        self.assertEqual([(r["status"], r["detail"].split(":")[0]) for r in rows], [("warn", "unset")])
        git(self.env, self.clone, "config", "--local", "agentik.records", "relative/widget")
        code, rows = self.doctor_row(self.clone)
        self.assertEqual([(r["status"], r["detail"]) for r in rows],
                         [("fail", "broken: agentik.records is not an absolute path; agentik.records is relative/widget")])
        self.assertEqual(code, 1)
        os.makedirs(os.path.join(self.root, "hq", "widget"))
        git(self.env, self.clone, "config", "--local", "agentik.records", os.path.join(self.root, "hq", "widget"))
        code, rows = self.doctor_row(self.clone)
        self.assertEqual([(r["status"], r["detail"].split(":")[0]) for r in rows], [("ok", "out")])
        self.assertTrue(rows[0]["detail"].endswith(", in no git repo, so nothing is committed"), rows[0]["detail"])
        git(self.env, os.path.join(self.root, "hq"), "init", "-q", "-b", "main")
        code, rows = self.doctor_row(self.clone)
        self.assertNotIn("nothing is committed", rows[0]["detail"])
        loose = os.path.join(self.root, "loose")
        os.mkdir(loose)
        self.assertEqual(self.doctor_row(loose)[1], [])
