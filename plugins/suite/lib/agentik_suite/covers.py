"""What a read covers (design P13's one rule, packet su2-read R6): the checkouts, and the hq.

First match: the paths on the command line (`args`); the user file's `checkouts`, a leading `~/`
as HOME (`checkouts`); where the cwd's repo, or a git checkout in the folder that holds it,
declares `kind: hq` in the `suite` section of its `.claude/agentik/config.yaml`, that hq first,
then every git checkout of that folder by name (`hq`); the cwd's repo alone (`cwd`); else `none`.
`hq` is the first covered checkout that declares the kind, under every rule. A repo file that
cannot be read declares nothing. A user file outside the subset raises settings.Fault.
"""
import os

from . import settings


def _repo(cwd):
    """The nearest folder upward holding `.git`, or None."""
    found = settings.repo_path(cwd)
    return os.path.dirname(os.path.dirname(os.path.dirname(found))) if found else None


def _git(folder):
    return os.path.exists(os.path.join(folder, ".git"))


def declares_hq(checkout):
    try:
        present, tree, lines = settings.read(os.path.join(checkout, ".claude", "agentik", "config.yaml"))
    except settings.Fault:
        return False
    section = tree.get("suite")
    return isinstance(section, dict) and section.get("kind") == "hq"


def _home(path, env):
    if path == "~" or path.startswith("~/"):
        return os.path.join(env.get("HOME") or "", path[2:])
    return path


def _user_checkouts(env):
    try:
        present, tree, lines = settings.read(settings.user_path(env))
    except settings.Fault as f:
        f.path = settings.user_path(env)
        raise
    found = tree.get("checkouts")
    if not isinstance(found, list):
        return []
    return [_home(p, env) for p in found if isinstance(p, str) and p.strip()]


def _hq_folder(repo):
    """[hq, every other checkout of its folder by name] when the repo or a sibling is an hq."""
    folder = os.path.dirname(repo)
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return None
    sibs = [os.path.join(folder, n) for n in names if _git(os.path.join(folder, n))]
    if repo not in sibs:
        sibs.append(repo)
        sibs.sort(key=os.path.basename)
    hq = repo if declares_hq(repo) else next((s for s in sibs if declares_hq(s)), None)
    if hq is None:
        return None
    return [hq] + [s for s in sibs if s != hq]


def covers(env, cwd, paths):
    """{rule, hq, checkouts}."""
    rule, checkouts = "none", []
    if paths:
        rule, checkouts = "args", [os.path.abspath(p) for p in paths]
    else:
        listed = _user_checkouts(env)
        repo = _repo(cwd)
        if listed:
            rule, checkouts = "checkouts", listed
        elif repo:
            found = _hq_folder(repo)
            rule, checkouts = ("hq", found) if found else ("cwd", [repo])
    hq = next((c for c in checkouts if os.path.isdir(c) and declares_hq(c)), None)
    return {"rule": rule, "hq": hq, "checkouts": checkouts}
