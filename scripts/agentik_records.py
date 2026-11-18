"""agentik_records: where a repo's working records are (hq design/28 §3 items 1 to 6, §11;
GUIDE §12). Canonical in agentik-commons; `scripts/sync` places it at plugin/lib/agentik_records.py,
byte-identical in every tool, under vendored.sha256. Standard library, Python 3.9.

`resolve(start)` answers the `agentik.records/1` object for the folder `start`: `repo`, the main
checkout, found through the common git folder; `records`, the folder that holds the records;
`holder`, the top of the git repository whose working folder holds `records`, or None; `prefix`,
`records` relative to `holder`; `state`; and `why`. The states:

- `own`: no key, and the tree does not declare `out`. `records` and `holder` are the top of the
  working tree `start` stands in, so a worktree answers its own top; `prefix` is `.`.
- `out`: the key resolves; `records` is its folder.
- `unset`: the tree declares `out` and the clone has no key; `why` is `no-key`.
- `broken`: the key is set and does not resolve; no records folder is answered, and `why` is one
  of `unread`, `relative`, `missing`, `inside`, `name` or `holder`.

The key is `agentik.records` in the clone's own config, read as
`git config --local --path --get agentik.records`: never the user's file, the environment or a
worktree's own file. It resolves when it is absolute, an existing folder, outside the main
checkout and every worktree of the clone by real path, named as the main checkout's folder is,
and in a holder whose tree does not declare `out` itself. The declaration is the whole line
`suite.records: out` in `.claude/agentik/config.yaml` or `records: out` in `.hygiene-allow`, read
from the file at HEAD through git; a line in an untracked, uncommitted or local file declares
nothing. Git runs as `git -C <folder>`, never in the current directory, with the repository's
own environment variables dropped. `NoRepo` is raised where `start` is no folder, git is absent,
or `start` stands in no git working tree. Paths are real paths. It writes nothing.
"""
import os
import subprocess

SCHEMA = "agentik.records/1"
KEY = "agentik.records"
DECLARED = ((".claude/agentik/config.yaml", "suite.records: out"), (".hygiene-allow", "records: out"))
# `git rev-parse --local-env-vars`, and the environment's config items: a hook's GIT_DIR would
# answer for another repository than the folder named
LOCAL_ENV = ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
             "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
             "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX",
             "GIT_INTERNAL_SUPER_PREFIX", "GIT_SHALLOW_FILE", "GIT_COMMON_DIR")


class NoRepo(Exception):
    """`start` is no folder, git is absent, or `start` stands in no git working tree."""


def _env():
    return {k: v for k, v in os.environ.items()
            if k not in LOCAL_ENV and not k.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))}


def _git(folder, *args):
    """(exit, stdout less its last newline) of git run in `folder`; (None, "") with no git."""
    try:
        p = subprocess.run(["git", "-C", folder] + list(args), stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=_env())
    except OSError:
        return None, ""
    out = os.fsdecode(p.stdout)
    return p.returncode, out[:-1] if out.endswith("\n") else out


def _declares(top):
    """True where the tree at `top` declares `out` in a tracked file at HEAD."""
    for path, line in DECLARED:
        code, text = _git(top, "cat-file", "-p", "HEAD:" + path)
        if code == 0 and any(row.rstrip() == line for row in text.splitlines()):
            return True
    return False


def _under(path, top):
    return path == top or path.startswith(top.rstrip(os.sep) + os.sep)


def _answer(repo, state, why=None, records=None, holder=None, prefix=None):
    return {"schema": SCHEMA, "repo": repo, "records": records, "holder": holder, "prefix": prefix,
            "state": state, "why": why}


def resolve(start):
    if not os.path.isdir(start):
        raise NoRepo(start)
    start = os.path.realpath(start)
    code, top = _git(start, "rev-parse", "--show-toplevel")
    if code != 0 or not top:
        raise NoRepo(start)
    top = os.path.realpath(top)
    code, common = _git(start, "rev-parse", "--git-common-dir")
    code_list, listing = _git(start, "worktree", "list", "--porcelain", "-z")
    if code != 0 or code_list != 0:
        raise NoRepo(start)
    trees = [os.path.realpath(item[len("worktree "):]) for item in listing.split("\0")
             if item.startswith("worktree ")]
    common = os.path.realpath(os.path.join(start, common))
    repo = os.path.dirname(common) if os.path.basename(common) == ".git" else (trees or [top])[0]
    code, value = _git(start, "config", "--local", "--path", "--get", KEY)
    if code == 1:
        if _declares(top):
            return _answer(repo, "unset", "no-key")
        return _answer(repo, "own", records=top, holder=top, prefix=".")
    if code != 0:
        return _answer(repo, "broken", "unread")
    if not os.path.isabs(value):
        return _answer(repo, "broken", "relative")
    records = os.path.realpath(value)
    if not os.path.isdir(records):
        return _answer(repo, "broken", "missing")
    if any(_under(records, tree) for tree in [repo, top] + trees):
        return _answer(repo, "broken", "inside")
    if os.path.basename(os.path.normpath(value)) != os.path.basename(repo):
        return _answer(repo, "broken", "name")
    code, holder = _git(records, "rev-parse", "--show-toplevel")
    if code != 0 or not holder:
        return _answer(repo, "out", records=records)
    holder = os.path.realpath(holder)
    if _declares(holder):
        return _answer(repo, "broken", "holder")
    return _answer(repo, "out", records=records, holder=holder, prefix=os.path.relpath(records, holder))
