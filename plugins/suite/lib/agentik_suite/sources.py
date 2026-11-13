"""The one finder (row fk1-sources): what stands for a tool, and which file runs.

A tool T's candidates are the entries of Claude Code's installed_plugins.json, under
${CLAUDE_CONFIG_DIR:-~/.claude}/plugins/, every entry of every id's list whose plugin is named T:
the user's own (scope `user` or `managed`, or no scope) and the repo's (`project` or `local`, whose
`projectPath` is the cwd or holds it). Another project's entry is neither found nor seen.

What stands, first match: T's line in the user file's `sources`, resolved or not; else the only
candidate, when it is the user's own; else nothing, `undecided` or `absent`. The file that runs:
the first `agentik-T` on PATH that is a regular executable, passed over when it lies under the
root of an entry that is not T's standing source; then the standing root's `bin/agentik-T`.

It opens files and looks names up on PATH, and starts no process; it never imports `tools`.
"""
import os

import agentik_install

from . import plan, settings

SCHEMA = "agentik.sources/1"
OWN = ("user", "managed", None)
REPO = ("project", "local")
GITHUB = ("https://github.com/", "git" + "@github.com:")  # split: the scan reads an ssh URL as an address


def config_dir(env):
    return env.get("CLAUDE_CONFIG_DIR") or os.path.join(env.get("HOME") or "", ".claude")


def _real(path):
    try:
        return os.path.realpath(path)
    except (OSError, ValueError):
        return None


def _under(path, root):
    """True when the resolved `path` is `root` or lies inside it (both resolved)."""
    if not path or not root:
        return False
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def entries(env):
    """[{plugin, version, scope, root, projectPath}]: every entry of every id's list, in order."""
    found = plan._read_json(os.path.join(config_dir(env), "plugins", "installed_plugins.json"))
    table = found.get("plugins") if isinstance(found, dict) else None
    rows = []
    for pid, listed in (table.items() if isinstance(table, dict) else ()):
        for e in (listed if isinstance(listed, list) else ()):
            if not isinstance(e, dict):
                continue
            root = e.get("installPath")
            rows.append({"plugin": pid, "version": e.get("version"),
                         "scope": e.get("scope") if "scope" in e else None,
                         "root": root if isinstance(root, str) else None,
                         "projectPath": e.get("projectPath")})
    return rows


def whose(entry, cwd):
    """`user` for the user's own entry, `repo` for the cwd's project's, else None (R4)."""
    scope = entry["scope"]
    if scope in OWN:
        return "user"
    if scope in REPO and isinstance(entry["projectPath"], str) and cwd:
        if _under(_real(cwd), _real(entry["projectPath"])):
            return "repo"
    return None


def _name(pid):
    return pid.rpartition("@")[0] if "@" in pid else pid


def mirror(env):
    """True when the `agentik` marketplace records a source other than github's plan.SOURCE (R8)."""
    known = plan._read_json(os.path.join(config_dir(env), "plugins", "known_marketplaces.json"))
    entry = known.get(plan.MARKETPLACE) if isinstance(known, dict) else None
    source = entry.get("source") if isinstance(entry, dict) else None
    if not isinstance(source, dict):
        return False
    want = plan.SOURCE.lower()
    if source.get("source") == "github" and isinstance(source.get("repo"), str):
        return source["repo"].strip().lower() != want
    url = source.get("url")
    if isinstance(url, str):
        url = url.strip().lower().rstrip("/")
        if url.endswith(".git"):
            url = url[:-len(".git")]
        if any(url == lead + want for lead in GITHUB):
            return False
    return True


def _manifest(root):
    data = plan._read_json(os.path.join(root, ".claude-plugin", agentik_install.MANIFEST))
    return data if isinstance(data, dict) else None


def _seen(c):
    return {"plugin": c["plugin"], "version": c["version"], "scope": c["scope"] or "user",
            "root": c["root"]}


def _executable(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)  # a stat, never an open


def _runs(tool, env, all_entries, standing, root, version):
    """(runs, passed_over) as R6 says."""
    name = "agentik-" + tool
    first = None
    for entry in env.get("PATH", "").split(os.pathsep):
        path = os.path.join(entry or ".", name)
        if _executable(path):
            first = path
            break
    passed = None
    real_root = _real(root) if root else None
    if first:
        real = _real(first)
        for e in all_entries:
            other = _real(e["root"]) if e["root"] else None
            if e is standing or (real_root and other == real_root):
                continue
            if _under(real, other):
                passed = {"path": first, "of": e["plugin"]}
                break
        if passed is None:
            if _under(real, real_root):
                return {"path": first, "version": version, "of": "source"}, None
            launcher = agentik_install.read_launcher(first) or {}
            return ({"path": first, "version": launcher.get("version"),
                     "of": "placed" if launcher.get("tree") else "unknown"}, None)
    if root:
        path = os.path.join(root, "bin", name)
        if _executable(path):
            return {"path": path, "version": version, "of": "source"}, passed
    return None, passed


def find(tool, env, cwd, lines):
    """The row of `tool` (R5 to R8); `lines` is settings.declared's first value."""
    all_entries = entries(env)
    candidates = [e for e in all_entries if _name(e["plugin"]) == tool and whose(e, cwd)]
    line = lines.get(tool)
    standing, kind, plugin, root, version, scope, found = None, None, None, None, None, None, False
    if line is not None:
        value, form = line["value"], line["form"]
        if form == "plugin":
            plugin = value
            if _name(value) == tool:
                mine = [c for c in candidates if c["plugin"] == value]
                standing = ([c for c in mine if whose(c, cwd) == "user"] + mine + [None])[0]
            kind = "own" if value == "%s@%s" % (tool, plan.MARKETPLACE) else "plugin"
        else:
            kind = "folder"
            if form == "folder":
                root = os.path.join(env.get("HOME") or "", value[2:]) if value.startswith("~/") else value
                data = _manifest(root)
                if data is not None:
                    found, version = True, data.get("version")
    elif len(candidates) == 1 and whose(candidates[0], cwd) == "user":
        standing = candidates[0]
        plugin = standing["plugin"]
        kind = "own" if plugin == "%s@%s" % (tool, plan.MARKETPLACE) else "plugin"
    else:
        kind = "undecided" if candidates else "absent"
    if standing is not None:
        found, root, version = True, standing["root"], standing["version"]
        scope = standing["scope"] or "user"
    runs, passed = _runs(tool, env, all_entries, standing, root if found else None, version)
    return {"tool": tool, "kind": kind, "plugin": plugin, "root": root, "version": version,
            "scope": scope, "mirror": kind == "own" and mirror(env),
            "declared": {"path": line["path"], "line": line["line"]} if line else None,
            "found": found, "seen": [_seen(c) for c in candidates if c is not standing],
            "runs": runs, "passed_over": passed}


def read(env, cwd, names, more=True):
    """The rows of `names`, then, with `more`, of each declared name not among them. A user file
    outside the subset is settings.Fault."""
    lines, _ = settings.declared(env)
    order = list(names) + ([t for t in lines if t not in names] if more else [])
    return [find(tool, env, cwd, lines) for tool in order]
