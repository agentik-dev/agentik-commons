"""The setup plan: seven reads, each with a state, and what setup would do where it is not ok.

Every step is a read: it opens files and looks names up on PATH, and starts no process, `claude`
included. A plugin's files are Claude Code's own, under ${CLAUDE_CONFIG_DIR:-~/.claude}/plugins/:
known_marketplaces.json, an object keyed by marketplace name, and installed_plugins.json, whose
plugins["<name>@<marketplace>"][0] holds version and installPath. An absent or unreadable file
reads as nothing known. A step is a dict: n, id, state (ok, todo or blocked), subject, the
message id and values of its detail, and the command setup would run (None when there is none).
"""
import json
import os
import shutil
import sys

import agentik_install

MARKETPLACE = "agentik"
SOURCE = "agentik-dev/agentik-commons"
FLOOR = (3, 9)
PROFILE_LINE = 'export PATH="$HOME/.local/bin:$PATH"'


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def manifest(lib):
    return _read_json(os.path.join(os.path.dirname(lib), ".claude-plugin", "plugin.json")) or {}


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


def build(names, env, lib, tool, version):
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

    # 3: each plugin
    installed = _read_json(os.path.join(config, "plugins", "installed_plugins.json"))
    table = installed.get("plugins") if isinstance(installed, dict) else None
    have = {}
    for name in names:
        key = "%s@%s" % (name, MARKETPLACE)
        entry = table.get(key) if isinstance(table, dict) else None
        entry = entry[0] if isinstance(entry, list) and entry and isinstance(entry[0], dict) else None
        if entry and isinstance(entry.get("version"), str) and entry.get("version"):
            have[name] = entry
            steps.append(_step(3, "plugin", "ok", key, "setup.plugin.ok", version=entry["version"]))
        else:
            steps.append(_step(3, "plugin", "todo", key, "setup.plugin.missing",
                               "claude plugin install %s" % key))

    # 4: each plugin's launcher on the terminal's PATH
    for name in names:
        exe = "agentik-%s" % name
        where = os.path.join(bindir, exe)
        if name not in have:
            steps.append(_step(4, "launcher", "todo", shown(where, home), "setup.launcher.wait"))
            continue
        want = have[name]["version"]
        root = have[name].get("installPath")
        command = "%s install-cli" % os.path.join(root, "bin", exe) if isinstance(root, str) and root else None
        read = agentik_install.read_launcher(where)
        if read is None:
            steps.append(_step(4, "launcher", "todo", shown(where, home), "setup.launcher.missing",
                               command))
        elif read.get("version") == want:
            steps.append(_step(4, "launcher", "ok", shown(where, home), "setup.launcher.ok",
                               version=want))
        elif read.get("version"):
            steps.append(_step(4, "launcher", "todo", shown(where, home), "setup.launcher.behind",
                               command, have=read["version"], want=want))
        else:
            steps.append(_step(4, "launcher", "todo", shown(where, home), "setup.launcher.unread",
                               command, want=want))

    # 5: the suite's own launcher and the door
    own = os.path.join(bindir, tool)
    read = agentik_install.read_launcher(own)
    here = shown(os.path.join(os.path.dirname(lib), "bin", tool), home)
    if read is not None and read.get("version") == version:
        steps.append(_step(5, "suite", "ok", shown(own, home), "setup.suite.ok", version=version))
    elif read is not None:
        steps.append(_step(5, "suite", "todo", shown(own, home), "setup.suite.behind",
                           have=read.get("version") or "?", want=version, path=here))
    else:
        steps.append(_step(5, "suite", "todo", shown(own, home), "setup.suite.missing", path=here))
    door = os.path.join(bindir, agentik_install.DOOR)
    if os.path.isfile(door):
        steps.append(_step(5, "door", "ok", shown(door, home), "setup.door.ok"))
    else:
        steps.append(_step(5, "door", "todo", shown(door, home), "setup.door.missing"))

    # 6: ~/.local/bin on PATH
    entries = [os.path.normpath(p) for p in search.split(os.pathsep) if p]
    if os.path.normpath(bindir) in entries:
        steps.append(_step(6, "path", "ok", shown(bindir, home), "setup.path.ok"))
    else:
        steps.append(_step(6, "path", "todo", shown(bindir, home), "setup.path.missing",
                           PROFILE_LINE, line="add"))

    # 7: the doctors, last
    for name in names:
        exe = "agentik-%s" % name
        steps.append(_step(7, "doctor", "todo", exe, "setup.doctor.todo", "%s doctor" % exe))
    if not names:
        steps.append(_step(7, "doctor", "ok", tool, "setup.doctor.none"))
    return steps
