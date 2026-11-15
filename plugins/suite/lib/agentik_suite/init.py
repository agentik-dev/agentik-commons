"""init: a fresh coordinating repo, an hq, written into an empty folder (packet ak11-init).

`init --kind KIND DIR [--dry-run] [--yes]` copies the scaffold `lib/scaffold/KIND` into DIR, a
folder that is absent or holds nothing but `.git` and `.DS_Store`, and runs `git init` there
where DIR holds no `.git`. It stages nothing and commits nothing. Its two answers, the kind and
the folder, come from `_answers` alone (R12): nothing is asked in this build. A refusal is exit 2
with one line and nothing written (R4); a failed write or `git init` is exit 1, DIR left as it
was (R5).
"""
import os
import shlex
import shutil
import subprocess
import tempfile

from . import settings, term

SCHEMA = "agentik.init/1"
KEPT = (".git", ".DS_Store")  # what an empty folder may hold already (R4.6)
SKIP = (".DS_Store",)  # never copied from the scaffold
WALL = 10.0  # git init's wall, in seconds (R5)
NAMED = 3  # the entries a refusal names before `and N more`


def scaffold(lib):
    return os.path.join(lib, "scaffold")


def kinds(lib):
    """The kinds, sorted: each folder under the scaffold's."""
    root = scaffold(lib)
    try:
        names = os.listdir(root)
    except OSError:
        return []
    return sorted(n for n in names if not n.startswith(".") and os.path.isdir(os.path.join(root, n)))


def _answers(cmd, nouns):
    """R12: what to write and where, each from its place on the command line, `--kind` and the
    word DIR; nothing is asked and no byte of stdin is read. Raises R4's refusals 1 and 2. A later
    row puts the suite's picker behind this one function, for a person on a terminal; the flag
    and the word still give every answer then."""
    found = kinds(cmd.lib)
    shown = {"kinds": ", ".join(found), "first": found[0] if found else "hq"}
    kind = cmd.opts["kind"]
    if not kind:
        raise cmd.Usage("no_kind", "err.init.kind.none", None, **shown, **cmd.slots())
    if kind not in found:
        raise cmd.Usage("bad_kind", "err.init.kind", None, kind=kind, **shown, **cmd.slots())
    if not nouns:
        raise cmd.Usage("no_dir", "err.init.dir", None, kind=kind, **cmd.slots())
    if len(nouns) > 1:
        raise cmd.Usage("extra_word", "err.init.extra", None, word=nouns[1], **cmd.slots())
    return {"kind": kind, "dir": nouns[0]}


def files(root):
    """Each file's path under `root`: README.md first, the rest in sorted order (R6)."""
    found = []
    for here, dirs, names in os.walk(root):
        dirs.sort()
        found += [os.path.relpath(os.path.join(here, n), root) for n in names if n not in SKIP]
    rest = sorted(f for f in found if f != "README.md")
    return (["README.md"] if "README.md" in found else []) + rest


def _above(path):
    """The nearest folder above `path` holding `.git`, by walking up with no process, or None."""
    here = os.path.dirname(os.path.realpath(path))
    while True:
        if os.path.lexists(os.path.join(here, ".git")):
            return here
        up = os.path.dirname(here)
        if up == here:
            return None
        here = up


def _is_kind(path, kind):
    """True where DIR's own repo file reads `suite.kind` as `kind`; a fault there reads as no."""
    try:
        tree = settings.read(os.path.join(path, ".claude", "agentik", "config.yaml"))[1]
    except (settings.Fault, OSError, ValueError):
        return False
    suite = tree.get("suite")
    return isinstance(suite, dict) and suite.get("kind") == kind


def _found(names):
    if len(names) > NAMED:
        return "%s and %d more" % (", ".join(names[:NAMED]), len(names) - NAMED)
    return names[0] if len(names) == 1 else "%s and %s" % (", ".join(names[:-1]), names[-1])


def _mode(path):
    with open(path, "rb") as fh:
        return 0o755 if fh.read(2) == b"#!" else 0o644


def _git(git, stage, env):
    """(exit, what git said) for `git init -q -b main <stage>`, stdin closed, under WALL."""
    env = {k: v for k, v in env.items() if not k.startswith("GIT_")}  # no GIT_DIR from a hook
    try:
        p = subprocess.Popen([git, "init", "-q", "-b", "main", stage], stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    except OSError as e:
        return 1, e.strerror or str(e)
    try:
        out, err = p.communicate(timeout=WALL)
    except subprocess.TimeoutExpired:
        p.kill()
        out, err = p.communicate()
        return 1, (err or out).decode("utf-8", "replace")
    return p.returncode, (err or out).decode("utf-8", "replace") if p.returncode else ""


def _undo(moved):
    for path in reversed(moved):
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.lexists(path):
            try:
                os.unlink(path)
            except OSError:
                pass


def do_init(cmd, nouns):
    o, t = cmd.opts, cmd.t
    answers = _answers(cmd, nouns)
    kind, typed = answers["kind"], answers["dir"]
    slots = dict(cmd.slots(), kind=kind, dir=typed)
    git = shutil.which("git", path=cmd.env.get("PATH") or os.defpath)
    if git is None:
        raise cmd.Usage("no_git", "err.init.git", None, **slots)
    path = os.path.abspath(os.path.join(cmd.cwd, typed))
    parent = os.path.dirname(path)
    parent_shown = os.path.dirname(typed.rstrip("/")) or "."
    if not os.path.isdir(parent):
        raise cmd.Usage("no_parent", "err.init.parent", None, parent=parent_shown, **slots)
    if os.path.lexists(path) and not os.path.isdir(path):
        raise cmd.Usage("not_a_folder", "err.init.notdir", None, **slots)
    top = _above(path)
    if top:
        raise cmd.Usage("inside_repo", "err.init.inside", None, top=top, **slots)
    there = os.path.isdir(path)
    try:
        entries = sorted(os.listdir(path)) if there else []
    except OSError as e:
        raise cmd.Usage("write_failed", "err.init.write", None, exit_code=1, path=typed,
                        why=e.strerror or str(e), **slots)
    extra = [e for e in entries if e not in KEPT]
    if extra and _is_kind(path, kind):
        raise cmd.Usage("already", "err.init.already", None, **slots)
    if extra:
        raise cmd.Usage("not_empty", "err.init.full", None, found=_found(extra), **slots)
    source = os.path.join(scaffold(cmd.lib), kind)
    listed = files(source)
    kept = ".git" in entries
    if not o["dry_run"]:
        said = _write(cmd, source, listed, path, parent, there, kept, git, slots, parent_shown)
        if said is not None:
            return _git_failed(cmd, said, slots)
    if o["json"]:
        t.json({"schema": SCHEMA, "ok": True, "kind": kind, "dir": path, "dry_run": bool(o["dry_run"]),
                "git": "kept" if kept else "made", "files": listed})
        return 0
    title = "init.title.dry" if o["dry_run"] else "init.title.kept" if kept else "init.title.made"
    t.line(title, dir=typed, count=len(listed))
    t.table([(None, [term.path(f)], None) for f in listed])
    if o["dry_run"]:
        t.hint("hint.init.dry")
    else:
        t.hint("hint.init", dir=shlex.quote(typed))
    return 0


def _write(cmd, source, listed, path, parent, there, kept, git, slots, parent_shown):
    """R5: the tree staged beside DIR, then moved in; None when done, git's text when git init
    failed. An OSError is exit 1 with DIR as it was."""
    try:
        stage = tempfile.mkdtemp(dir=parent)
    except OSError as e:
        raise cmd.Usage("write_failed", "err.init.write", None, exit_code=1, path=parent_shown,
                        why=e.strerror or str(e), **slots)
    moved = []
    try:
        os.chmod(stage, 0o755)
        for rel in listed:
            to = os.path.join(stage, rel)
            os.makedirs(os.path.dirname(to), exist_ok=True)
            shutil.copyfile(os.path.join(source, rel), to)
            os.chmod(to, _mode(to))
        for here, dirs, _ in os.walk(stage):
            for d in dirs:
                os.chmod(os.path.join(here, d), 0o755)
        if not kept:
            code, said = _git(git, stage, cmd.env)
            if code != 0:
                return said
        if not there:
            os.rename(stage, path)
            return None
        for name in sorted(os.listdir(stage)):
            to = os.path.join(path, name)
            os.rename(os.path.join(stage, name), to)
            moved.append(to)
        return None
    except OSError as e:
        _undo(moved)
        where = e.filename if isinstance(e.filename, str) else path
        if where == stage or where.startswith(stage + os.sep):
            where = os.path.join(slots["dir"], os.path.relpath(where, stage))
        raise cmd.Usage("write_failed", "err.init.write", None, exit_code=1, path=where,
                        why=e.strerror or str(e), **slots)
    finally:
        if os.path.isdir(stage):
            shutil.rmtree(stage, ignore_errors=True)


def _git_failed(cmd, said, slots):
    """Exit 1: the gitfail line, then git's own text whole under it (R5)."""
    t = cmd.t
    said = said.rstrip("\n")
    if cmd.opts["json"]:
        t.json({"schema": SCHEMA, "ok": False,
                "error": {"code": "git_failed", "message": t.text("err.init.gitfail", **slots),
                          "remedy": None, "said": said}})
        return 1
    t.error("err.init.gitfail", **slots)
    for line in said.splitlines():
        t.line("init.said", err=True, text=line)
    return 1
