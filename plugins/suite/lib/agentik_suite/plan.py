"""The setup plan: seven reads, each with a state, and what setup would do where it is not ok.

Every step is a read: it opens files and looks names up on PATH, and starts no process, `claude`
included, but one: a plugin that ships its command and has no launcher on PATH is asked
`describe --json` through the suite's own reader (tools.describe_all, its cache and its wall), and
one whose counted answer lists no `install-cli` verb runs from its own folder (row
sp1-launcher-step). A plugin's files are Claude Code's own, under ${CLAUDE_CONFIG_DIR:-~/.claude}/plugins/:
known_marketplaces.json, an object keyed by marketplace name, and installed_plugins.json, read
through the finder (`sources`, row fk1-sources): steps 3, 4 and 7 plan by the source that stands
for each name (row fk2-plan), and setup installs no id outside its own marketplace. An absent or unreadable file
reads as nothing known, as does one that fails to parse. A step is a dict: n, id, state (ok, todo or blocked), subject, the
message id and values of its detail, the command (None when there is none) and its line: `run`, one
a yes runs (steps 2 to 5), `add` for the shell profile (step 6), or `later`, the reader's own to
run after setup (step 7's doctors), or `page`, a tool's page, which nothing opens: a tool whose
table row holds a `page` installs its own command, so steps 4 and 7 place, describe and run
nothing of it but the finder's file (row fh13), and its step 4 row then holds `page`. A
plugin's install-cli places the door, so while step 4 has a row to do the door's row names no line
(row sm1-setup-ask R2).
"""
import json
import os
import shlex
import shutil
import sys

import agentik_install

MARKETPLACE = "agentik"
SOURCE = "agentik-dev/agentik-commons"
FLOOR = (3, 9)
DOOR = agentik_install.DOOR
SUITE = "agentik-suite"  # the command the door hands a word it has no tool for
PROFILE_LINE = 'export PATH="$HOME/.local/bin:$PATH"'


def _read_json(path):
    """The JSON at `path`, or None; a path that is no regular file is never opened (ak2b review 1)."""
    data = agentik_install.read_regular(path)
    if data is None:
        return None
    try:
        return json.loads(data.decode("utf-8"))
    except (ValueError, RecursionError):  # a file nested past the parser's depth too
        return None


def manifest(lib):
    """The manifest: in a frozen tree the copy beside the code, so the installed command plans
    the default set too; in the plugin its .claude-plugin/plugin.json."""
    if agentik_install.is_frozen(lib):
        path = os.path.join(lib, agentik_install.MANIFEST)
    else:
        path = os.path.join(os.path.dirname(lib), ".claude-plugin", agentik_install.MANIFEST)
    found = _read_json(path)
    return found if isinstance(found, dict) else {}


def own_command(lib, tool):
    """The path that runs this command: <plugin>/bin/<tool> in a plugin, <lib>/<runner> in a
    frozen tree, the runner's name from the conf."""
    if not agentik_install.is_frozen(lib):
        return os.path.join(os.path.dirname(lib), "bin", tool)
    try:
        return os.path.join(lib, agentik_install.names(lib)["runner"])
    except (OSError, ValueError):
        return os.path.join(lib, tool)


def own_door(lib):
    """The door this command's install-cli writes: the plugin's bin/agentik, or the tree's."""
    if agentik_install.is_frozen(lib):
        return os.path.join(lib, agentik_install.DOOR)
    return os.path.join(os.path.dirname(lib), "bin", agentik_install.DOOR)


def default_set(lib):
    """The plugins the manifest's dependencies list, a bare name or {name, ...}."""
    names = []
    for dep in manifest(lib).get("dependencies") or []:
        dep = dep.get("name") if isinstance(dep, dict) else dep
        if isinstance(dep, str) and dep and dep not in names:
            names.append(dep)
    return names


def shown(path, home):
    """A path as the user would type it: under HOME, from `~`."""
    if home and (path == home or path.startswith(home.rstrip("/") + "/")):
        return "~" + path[len(home.rstrip("/")):]
    return path


def _step(n, sid, state, subject, mid, command=None, line="run", **values):
    return {"n": n, "id": sid, "state": state, "subject": subject, "mid": mid,
            "values": values, "command": command, "line": line}


def in_place(sources, env):
    """The names, of {name: command}, whose counted describe answer lists no verb install-cli; a
    command that answers nothing counted is not among them."""
    if not sources:
        return set()
    from . import tools  # tools imports this module at its top
    found, _ = tools.describe_all([{"name": n, "exe": e} for n, e in sorted(sources.items())], env)
    names = set()
    for name, (state, answer) in found.items():
        verbs = [v.get("name") if isinstance(v, dict) else v for v in (answer or {}).get("verbs") or ()]
        if state == "answers" and "install-cli" not in verbs:
            names.add(name)
    return names


def _real(path):
    try:
        return os.path.realpath(path)
    except (OSError, ValueError):
        return path


def _under(path, root):
    """True when `path`, resolved, is `root`, resolved, or lies inside it."""
    if not path or not root:
        return False
    path, root = _real(path), _real(root)
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def _same(a, b):
    """True when `a` and `b` are one file; never raises (review 1 F2)."""
    try:
        return os.path.samefile(a, b)
    except (OSError, ValueError):
        return False


def _earlier(path, bindir, search):
    """True when `path`'s folder comes before `bindir` on PATH, and `bindir` is on it; each folder
    resolved, so a folder linked to `bindir` is `bindir` (review 1 F2)."""
    entries = [_real(os.path.normpath(p or ".")) for p in search.split(os.pathsep)]
    here, there = _real(os.path.dirname(path)), _real(bindir)
    if there not in entries or here not in entries:
        return False
    return entries.index(here) < entries.index(there)


def _cwd(cwd):
    if cwd is not None:
        return cwd
    try:
        return os.getcwd()
    except OSError:
        return None


def _command(root, name):
    """The source's own `bin/agentik-<name>`, or None: a file that is not a regular file, or that
    resolves out of the root, is no command, as the finder holds it (review 1 F1)."""
    path = os.path.join(root, "bin", "agentik-" + name)
    return path if os.path.isfile(path) and _under(path, root) else None


def _page_runs(row, where):
    """The file that runs for a tool with a page: the one the finder names, else W when the
    finder's own test calls it executable, on PATH or not (row fh13 review 1 F2)."""
    from . import sources  # sources imports this module at its top
    runs = (row["runs"] or {}).get("path")
    return runs or (where if sources._executable(where) else None)


def _plugin_row(n, name, row, home):
    """Step 3 for a source that is not the marketplace's own: (step, (version, command) or None)."""
    root, ver = row["root"], row["version"]
    if row["kind"] == "undecided":
        seen = row["seen"]
        ids = list(dict.fromkeys(s["plugin"] for s in seen))  # plugins, not entries (review 1 F3)
        if len(seen) == 1 and seen[0]["scope"] in ("project", "local"):
            return _step(n, "plugin", "todo", name, "setup.plugin.held.repo", name=name), None
        if len(ids) == 1:
            return _step(n, "plugin", "todo", name, "setup.plugin.held.twice", name=name, id=ids[0]), None
        return _step(n, "plugin", "todo", name, "setup.plugin.held", name=name, count=len(ids)), None
    subject = row["plugin"] or (shown(root, home) if isinstance(root, str) else name)
    if row["found"] and isinstance(root, str) and os.path.isdir(root):
        if isinstance(ver, str) and ver:
            step = _step(n, "plugin", "ok", subject, "setup.plugin.source", name=name, version=ver)
        else:
            step = _step(n, "plugin", "ok", subject, "setup.plugin.source.none", name=name)
        return step, (ver, _command(root, name))
    at = row["declared"]
    if at and not row["found"]:
        return _step(n, "plugin", "todo", subject, "setup.plugin.declared",
                     at="%s:%s" % (shown(at["path"], home), at["line"])), None
    return _step(n, "plugin", "todo", subject, "setup.plugin.gone"), None


def build(names, env, lib, tool, version, cwd=None):
    from . import tools  # tools imports this module at its top
    home = env.get("HOME") or ""
    search = env.get("PATH", "")
    config = env.get("CLAUDE_CONFIG_DIR") or os.path.join(home, ".claude")
    bindir = os.path.join(home, ".local", "bin")
    steps = []

    # 1: what setup itself needs
    for cmd in ("claude", "git"):
        found = shutil.which(cmd, path=search)
        if found:
            steps.append(_step(1, "prereqs", "ok", cmd, "setup.cmd.found", path=found))
        else:
            steps.append(_step(1, "prereqs", "blocked", cmd, "setup.cmd.missing"))
    ver = "%d.%d.%d" % sys.version_info[:3]
    floor = "%d.%d" % FLOOR
    if sys.version_info[:2] >= FLOOR:
        steps.append(_step(1, "prereqs", "ok", "python3", "setup.python.ok",
                           version=ver, path=sys.executable, floor=floor))
    else:
        steps.append(_step(1, "prereqs", "blocked", "python3", "setup.python.low",
                           version=ver, path=sys.executable, floor=floor))

    # 2: the marketplace
    known = _read_json(os.path.join(config, "plugins", "known_marketplaces.json"))
    if isinstance(known, dict) and MARKETPLACE in known:
        steps.append(_step(2, "marketplace", "ok", MARKETPLACE, "setup.market.ok"))
    else:
        steps.append(_step(2, "marketplace", "todo", MARKETPLACE, "setup.market.missing",
                           "claude plugin marketplace add %s" % SOURCE))

    # 3: each plugin by the source that stands for it (row fk2-plan R4): the marketplace's own,
    # installed when its installPath folder is there, else installed from it; another source ok
    # when found, else a row with no command; two or a repo's lone one, one held row in place of
    # steps 3, 4 and 7. One may ship no launcher.
    rows = tools.rows(env, lib, _cwd(cwd), names=names)
    have = {}
    for name in names:
        row = rows[name]
        if row["kind"] not in ("own", "absent"):
            step, got = _plugin_row(3, name, row, home)
            steps.append(step)
            if got:
                have[name] = got
            continue
        key = "%s@%s" % (name, MARKETPLACE)
        install = "claude plugin install %s" % shlex.quote(key)
        ver, root = (row["version"], row["root"]) if row["kind"] == "own" else (None, None)
        if not (isinstance(ver, str) and ver):
            steps.append(_step(3, "plugin", "todo", key, "setup.plugin.missing", install))
        elif isinstance(root, str) and os.path.isdir(root):
            have[name] = (ver, _command(root, name))
            steps.append(_step(3, "plugin", "ok", key, "setup.plugin.ok", version=ver))
        else:
            steps.append(_step(3, "plugin", "todo", key, "setup.plugin.broken", install, version=ver))

    # 4: each plugin's launcher on the terminal's PATH, placed by the plugin's own install-cli; a
    # tool with a page installs its own, so setup names the page or the file the finder names (fh13)
    table = tools.fallback(lib)
    pages = {n: p for n, p in ((n, tools.page(table, n)) for n in names) if p}
    placed = []
    inplace = in_place({n: have[n][1] for n in names if n in have and have[n][1] and n not in pages
                        and agentik_install.read_launcher(os.path.join(bindir, "agentik-" + n)) is None},
                       env)
    direct = set()  # step 4 places nothing, since the file that runs is not the one it would place
    for name in names:
        row = rows[name]
        if name not in have and row["kind"] not in ("own", "absent"):
            continue  # not found or held: step 3's row is the only one (R4)
        exe = "agentik-%s" % name
        where = os.path.join(bindir, exe)
        if name in pages:
            runs = _page_runs(row, where)
            if runs:  # R3
                steps.append(_step(4, "launcher", "ok", shown(where, home), "setup.launcher.theirs",
                                   name=name, path=shown(runs, home)))
            else:  # R2
                steps.append(_step(4, "launcher", "todo", shown(where, home), "setup.launcher.page",
                                   line="page", name=name))
                steps[-1]["page"] = pages[name]
            continue
        read = agentik_install.read_launcher(where)
        if read is not None:
            placed.append(where)
        if name not in have:
            steps.append(_step(4, "launcher", "todo", shown(where, home), "setup.launcher.wait"))
            continue
        want, source = have[name]
        command = "%s install-cli" % shlex.quote(source) if source else None
        runs = (row["runs"] or {}).get("path")
        if not source:
            steps.append(_step(4, "launcher", "ok", shown(where, home), "setup.launcher.none"))
            placed = [p for p in placed if p != where]
        elif runs and not _same(runs, where) and not _under(runs, row["root"]) \
                and _earlier(runs, bindir, search):
            steps.append(_step(4, "launcher", "todo", shown(where, home), "setup.launcher.earlier",
                               path=shown(runs, home)))
            direct.add(name)
        elif os.path.islink(where) and os.path.isfile(where) and _under(where, row["root"]):
            steps.append(_step(4, "launcher", "ok", shown(where, home), "setup.launcher.link"))
            direct.add(name)
        elif read is None and name in inplace:
            steps.append(_step(4, "launcher", "ok", shown(where, home), "setup.launcher.inplace"))
        elif read is None:
            steps.append(_step(4, "launcher", "todo", shown(where, home), "setup.launcher.missing",
                               command))
        elif not (isinstance(want, str) and want):  # nothing to compare (review 1 F4)
            steps.append(_step(4, "launcher", "ok", shown(where, home), "setup.launcher.noversion"))
        elif read.get("version") == want:
            steps.append(_step(4, "launcher", "ok", shown(where, home), "setup.launcher.ok",
                               version=want))
            placed.insert(0, placed.pop())  # a launcher at its version is the first to name
        elif read.get("version"):  # another source's version is never called behind (R5)
            mid = "setup.launcher.behind" if row["kind"] == "own" else "setup.launcher.other"
            steps.append(_step(4, "launcher", "todo", shown(where, home), mid,
                               command, have=read["version"], want=want))
        else:
            steps.append(_step(4, "launcher", "todo", shown(where, home), "setup.launcher.unread",
                               command, want=want))

    # 5: the suite's own launcher and the door, each placed by this command's own install-cli
    own = os.path.join(bindir, tool)
    read = agentik_install.read_launcher(own)
    place = "%s install-cli" % shlex.quote(own_command(lib, tool))
    theirs, newer = (read or {}).get("version"), False
    if theirs and theirs != version:
        a, b = agentik_install.order(theirs), agentik_install.order(version)
        newer = a is not None and b is not None and a > b
    if read is None:
        steps.append(_step(5, "suite", "todo", shown(own, home), "setup.suite.missing", place))
    elif theirs == version:
        steps.append(_step(5, "suite", "ok", shown(own, home), "setup.suite.ok", version=version))
    elif newer:  # never moved backward: its own install-cli places the door (ak2b review 1)
        steps.append(_step(5, "suite", "ok", shown(own, home), "setup.suite.newer",
                           have=theirs, want=version))
        place = "%s install-cli" % shlex.quote(own)
    elif theirs and agentik_install.order(theirs) is not None:
        steps.append(_step(5, "suite", "todo", shown(own, home), "setup.suite.behind", place,
                           have=read["version"], want=version))
    else:
        steps.append(_step(5, "suite", "todo", shown(own, home), "setup.suite.unread", place,
                           want=version))
    door = os.path.join(bindir, agentik_install.DOOR)
    fate = agentik_install.door_fate(door, own_door(lib))
    if fate == "keep":
        steps.append(_step(5, "door", "ok", shown(door, home), "setup.door.ok"))
    elif fate in ("link", "unversioned"):
        mid = {"link": "setup.door.link", "unversioned": "setup.door.unversioned"}[fate]
        steps.append(_step(5, "door", "ok", shown(door, home), mid))
    elif steps[-1]["command"]:
        steps.append(_step(5, "door", "todo", shown(door, home), "setup.door.above"))
    elif any(s["n"] == 4 and s["state"] == "todo" and (s["command"] or s["mid"] == "setup.launcher.wait")
             for s in steps):  # a plugin's install-cli places it
        steps.append(_step(5, "door", "todo", shown(door, home), "setup.door.plugin"))
    else:
        steps.append(_step(5, "door", "todo", shown(door, home), "setup.door.place", place))

    # 6: ~/.local/bin on PATH
    entries = [os.path.normpath(p) for p in search.split(os.pathsep) if p]
    if os.path.normpath(bindir) in entries:
        steps.append(_step(6, "path", "ok", shown(bindir, home), "setup.path.ok"))
    else:
        steps.append(_step(6, "path", "todo", shown(bindir, home), "setup.path.missing",
                           PROFILE_LINE, line="add"))

    # 7: the doctors, last, each named once its launcher is placed
    for name in names:
        if name not in have and rows[name]["kind"] not in ("own", "absent"):
            continue
        exe = "agentik-%s" % name
        where = os.path.join(bindir, exe)
        runs = (rows[name]["runs"] or {}).get("path")  # the file that runs names the line (R6)
        if name in pages:
            runs = _page_runs(rows[name], where)
        if name in pages and not runs:  # fh13 R4
            steps.append(_step(7, "doctor", "todo", exe, "setup.doctor.page"))
        elif name in pages:
            steps.append(_step(7, "doctor", "todo", exe, "setup.doctor.todo",
                               "%s doctor" % shlex.quote(runs), line="later"))
        elif name in have and not have[name][1]:
            steps.append(_step(7, "doctor", "ok", exe, "setup.doctor.nocmd"))
        elif name in inplace:  # its command runs from the plugin's folder, as a placed one would
            steps.append(_step(7, "doctor", "todo", exe, "setup.doctor.todo",
                               "%s doctor" % shlex.quote(runs or have[name][1]), line="later"))
        elif where in placed or name in direct:
            steps.append(_step(7, "doctor", "todo", exe, "setup.doctor.todo",
                               "%s doctor" % shlex.quote(runs or where), line="later"))
        else:
            steps.append(_step(7, "doctor", "todo", exe, "setup.doctor.wait"))
    if not names:
        steps.append(_step(7, "doctor", "ok", tool, "setup.doctor.none"))

    # with step 1 blocked no line can work yet, so no step names one to run, and the door's row,
    # its message chosen after this pass, promises none
    if any(s["state"] == "blocked" for s in steps):
        for s in steps:
            if s["line"] in ("run", "later"):
                s["command"] = None
            if s["id"] == "door" and s["state"] != "ok":
                s["mid"] = "setup.door.blocked"
    return steps
