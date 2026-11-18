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
                "GIT_AUTHOR_NAME": "a builder", "GIT_AUTHOR_EMAIL": "builder@example.invalid",
                "GIT_COMMITTER_NAME": "a builder", "GIT_COMMITTER_EMAIL": "builder@example.invalid"})
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
        git(env, clone, "worktree", "add", "-q", os.path.join(root, tree), "-b", os.path.basename(tree))
    if "holder" in case:
        top = os.path.join(root, case["holder"]["path"])
        repo(env, top)
        if "declare" in case["holder"]:
            declare(env, top, case["holder"]["declare"])
    for folder in case.get("folders", ()):
        os.makedirs(os.path.join(root, folder), exist_ok=True)
    for link, target in case.get("links", ()):
        os.symlink(os.path.join(root, target), os.path.join(root, link))
    if "key" in case:
        git(env, clone, "config", "--local", "agentik.records", fill(case["key"], root))
    if "worktree_key" in case:
        git(env, clone, "config", "--local", "extensions.worktreeConfig", "true")
        git(env, os.path.join(root, case["worktrees"][0]), "config", "--worktree", "agentik.records",
            fill(case["worktree_key"], root))
    run = dict(env)
    if "env_key" in case:
        run.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "agentik.records",
                    "GIT_CONFIG_VALUE_0": fill(case["env_key"], root)})
    return run


class CasesTest(unittest.TestCase):
    def test_cases(self):
        records = load()
        cases = json.loads(CASES.read_text())["cases"]
        self.assertGreaterEqual(len(cases), 20)
        for case in cases:
            with self.subTest(case["name"]), tempfile.TemporaryDirectory() as tmp:
                root = os.path.realpath(tmp)
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
        for pair in [("own", None), ("out", None), ("unset", "no-key"), ("broken", "relative"),
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
