"""The words that start a printed command, and the name a title gives (hq design/23 §3, row sc2).

One read gives three answers. `agentik` where the first `agentik` on PATH is a door that hands
verbs to the suite: a door at 0.2.0 or newer, with the tool on PATH for it to hand them to. The
door's path, with `~` for HOME, where `~/.local/bin/agentik` is such a door and that folder is off
PATH. Else the word the person typed, which the root `setup` and the plugin's launcher hand on in
AGENTIK_ARGV0: `./setup ...` for a setup line under `./setup`; the launcher's word for any verb
under the launcher; the launcher's absolute path, `~` for HOME, where the word no longer names the
file from the working folder, or none was handed on. Every answer is read when it is asked for,
so a line printed after setup placed the door names the door. With `full`, the form for --json,
a path is never cut to `~`.
"""
import os
import shlex

import agentik_install

ARGV0 = "AGENTIK_ARGV0"  # the word the root setup or the launcher was started with
FLOOR = "0.2.0"  # the first door that hands a word it has no tool for to the suite
DOOR, SETUP = "door", "setup"


def first_door(env):
    """The first `agentik` on PATH that is a regular executable file; a FIFO, a folder or
    anything else of that name is passed over and never opened."""
    return _on_path(env, agentik_install.DOOR)


def _on_path(env, name):
    for entry in env.get("PATH", "").split(os.pathsep):
        path = os.path.join(entry or ".", name)
        if os.path.isfile(path) and os.access(path, os.X_OK):  # a stat, never an open
            return path
    return None


def _hands_on(path):
    """True for a door at FLOOR or newer: it hands a word it has no tool for to the suite."""
    have = agentik_install.order((agentik_install.read_launcher(path) or {}).get("version"))
    return have is not None and have >= agentik_install.order(FLOOR)


def form(env, tool):
    """(DOOR, path) where `agentik` on PATH reaches the suite; ("placed", path) for a door at
    ~/.local/bin off PATH; ("typed", None) else."""
    path = first_door(env)
    if path and _hands_on(path) and _on_path(env, tool):
        return DOOR, path
    home = env.get("HOME")
    if home:
        bindir = os.path.join(home, ".local", "bin")
        placed = os.path.join(bindir, agentik_install.DOOR)
        entries = [os.path.normpath(p) for p in env.get("PATH", "").split(os.pathsep) if p]
        if os.path.normpath(bindir) not in entries and os.path.isfile(placed) \
                and os.access(placed, os.X_OK) and _hands_on(placed):
            return "placed", placed
    return "typed", None


def name(env, tool):
    """The title's name: the door's in the first two forms, the tool's in the third."""
    return agentik_install.DOOR if form(env, tool)[0] != "typed" else tool


def shown(path, home, full=False):
    """A path quoted for sh, from `~` where it is under HOME and full is not asked."""
    if not full and home:
        top = home.rstrip("/")
        if path.startswith(top + "/"):
            return "~/" + shlex.quote(path[len(top) + 1:])
    return shlex.quote(path)


def _names(word, cwd, env, target):
    """True where `word`, typed in `cwd` under env's PATH, starts the file `target`."""
    if not word or not target:
        return False
    if "/" in word:
        found = word if os.path.isabs(word) else os.path.join(cwd, word)
    else:
        found = _on_path(env, word)
        if not found:
            return False
    try:
        return os.path.isfile(found) and os.path.samefile(found, target)
    except OSError:
        return False


def files(lib, tool):
    """(the launcher, the root setup): the plugin's bin/<tool> and the checkout's setup beside
    the plugins folder; in a tree install-cli froze, the runner and no setup."""
    if agentik_install.is_frozen(lib):
        try:
            runner = agentik_install.names(lib)["runner"]
        except (OSError, ValueError):
            runner = tool
        return os.path.join(lib, runner), None
    plugin = os.path.dirname(lib)
    return os.path.join(plugin, "bin", tool), os.path.join(os.path.dirname(os.path.dirname(plugin)), "setup")


def start(env, lib, tool, typed, cwd, words, full=False):
    """The command for `words` (a verb and what follows, or none), as one string to paste."""
    words = [shlex.quote(w) for w in words]
    how, door = form(env, tool)
    home = env.get("HOME")
    if how == DOOR:
        return " ".join(["agentik"] + words)
    if how == "placed":
        return " ".join([shown(door, home, full)] + words)
    launcher, setup = files(lib, tool)
    if words[:1] == [SETUP] and _names(typed, cwd, env, setup):
        return " ".join([shlex.quote(typed)] + words[1:])
    if _names(typed, cwd, env, launcher) and not os.path.isabs(typed):
        return " ".join([shlex.quote(typed)] + words)
    return " ".join([shown(os.path.abspath(launcher), home, full)] + words)
