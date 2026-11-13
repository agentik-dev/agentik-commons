"""The tools the suite lists, and their own answers about themselves.

A tool is listed when it is the suite itself, an `agentik-<name>` on PATH, or `<name>@agentik`
in Claude Code's installed_plugins.json. Each executable but the suite's runs as `agentik-<name>
describe --json`, every one at once, under one wall of WALL seconds; one still running then is
killed with its process group. A counted answer is cached, one file a tool, under
`${XDG_CACHE_HOME:-~/.cache}/agentik/suite/`, while the executable's resolved path, size and
modified time hold; a config read is never cached. The suite runs no program but a listed
tool's executable, with the words a tool's read names after it.
"""
import json
import os
import re
import signal
import subprocess
import tempfile
import time

from . import plan

WALL = 2.0
DESCRIBE = re.compile(r"agentik\.describe/([0-9]+)\Z")
CONFIG = re.compile(r"agentik\.config/([0-9]+)\Z")
DESCRIBE_KEYS = ("tool", "version", "summary", "repo", "plugin", "needs", "verbs", "reads")
READ_KINDS = ("config", "doctor", "status")
NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")


def _config_dir(env):
    return env.get("CLAUDE_CONFIG_DIR") or os.path.join(env.get("HOME") or "", ".claude")


def listed(suite, on_path, env):
    """[{name, exe, plugin}]: the suite first, then the rest by name."""
    found = {suite: {"name": suite, "exe": None, "plugin": False}}
    for entry in on_path:
        name = entry["name"][len("agentik-"):]
        if name != suite and NAME.match(name):
            found.setdefault(name, {"name": name, "exe": entry["path"], "plugin": False})
    installed = plan._read_json(os.path.join(_config_dir(env), "plugins", "installed_plugins.json"))
    table = installed.get("plugins") if isinstance(installed, dict) else None
    for key in table if isinstance(table, dict) else ():
        name, at, market = key.partition("@")
        if at and market == plan.MARKETPLACE and NAME.match(name):
            found.setdefault(name, {"name": name, "exe": None, "plugin": True})["plugin"] = True
    rest = sorted(n for n in found if n != suite)
    return [found[suite]] + [found[n] for n in rest]


def _kill(proc):
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except OSError:
        pass
    try:
        proc.communicate(timeout=1)
    except (subprocess.TimeoutExpired, OSError, ValueError):
        pass


def run_all(jobs, env, wall=WALL):
    """{key: (exit or None, stdout bytes, state)} for jobs [(key, argv)], every one started at
    once, under one wall; state is `ran`, `timed out` or `unreadable` (it could not start)."""
    deadline = time.monotonic() + wall
    procs, results = {}, {}
    for key, argv in jobs:
        try:
            procs[key] = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                          stderr=subprocess.DEVNULL, env=dict(env),
                                          start_new_session=True)
        except (OSError, ValueError):
            results[key] = (None, b"", "unreadable")
    for key, proc in procs.items():
        try:
            out, _ = proc.communicate(timeout=max(0.05, deadline - time.monotonic()))
            results[key] = (proc.returncode, out, "ran")
        except subprocess.TimeoutExpired:
            _kill(proc)
            results[key] = (None, b"", "timed out")
    return results


def _object(code, out, pattern):
    """The answer's object when it counts, else None."""
    if code != 0:
        return None
    try:
        obj = json.loads(out.decode("utf-8", "replace"))
    except (ValueError, RecursionError):
        return None
    if not isinstance(obj, dict) or obj.get("ok") is not True:
        return None
    m = pattern.match(obj.get("schema") if isinstance(obj.get("schema"), str) else "")
    if not m or int(m.group(1)) > 1:
        return None
    return obj


def counted_describe(code, out):
    obj = _object(code, out, DESCRIBE)
    if obj is None or any(k not in obj for k in DESCRIBE_KEYS):
        return None
    if not all(isinstance(obj[k], list) for k in ("needs", "verbs", "reads")):
        return None
    kinds = []
    for read in obj["reads"]:
        if not (isinstance(read, dict) and read.get("kind") in READ_KINDS
                and isinstance(read.get("argv"), list)
                and all(isinstance(w, str) for w in read["argv"])):
            return None
        kinds.append(read["kind"])
    if kinds.count("config") > 1 or kinds.count("doctor") > 1:
        return None
    return obj


def counted_config(code, out):
    obj = _object(code, out, CONFIG)
    if obj is None or not isinstance(obj.get("layers"), list) or not isinstance(obj.get("settings"), list):
        return None
    layers = [l for l in obj["layers"] if isinstance(l, dict)]
    settings = []
    for s in obj["settings"]:
        if not (isinstance(s, dict) and isinstance(s.get("key"), str) and s["key"]):
            return None
        s = dict(s)
        for k in ("source", "change"):
            s[k] = s.get(k) if isinstance(s.get(k), dict) else {}
        s["values"] = [v for v in s.get("values") or [] if isinstance(v, dict)] \
            if isinstance(s.get("values"), list) else []
        settings.append(s)
    obj = dict(obj, layers=layers, settings=settings)
    return obj


# ---- the describe cache ---------------------------------------------------------------------

def cache_dir(env):
    base = env.get("XDG_CACHE_HOME") or os.path.join(env.get("HOME") or "", ".cache")
    return os.path.join(base, "agentik", "suite")


def _stamp(exe):
    real = os.path.realpath(exe)
    st = os.stat(real)
    return {"path": real, "size": st.st_size, "mtime_ns": st.st_mtime_ns}


def _cached(folder, name, stamp):
    found = plan._read_json(os.path.join(folder, name + ".json"))
    if isinstance(found, dict) and found.get("stamp") == stamp:
        return counted_describe(0, json.dumps(found.get("answer")).encode())
    return None


def _keep(folder, name, stamp, answer):
    """Written by a rename, so a reader sees the old file or the new one; a failure keeps none."""
    try:
        os.makedirs(folder, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=folder, prefix="." + name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump({"stamp": stamp, "answer": answer}, fh)
            os.replace(tmp, os.path.join(folder, name + ".json"))
        except (OSError, ValueError, TypeError):
            os.unlink(tmp)
    except OSError:
        pass


def describe_all(entries, env):
    """{name: (state, answer or None)} for each entry with an executable."""
    folder, found, jobs, stamps = cache_dir(env), {}, [], {}
    for e in entries:
        try:
            stamps[e["name"]] = _stamp(e["exe"])
        except OSError:
            found[e["name"]] = ("unreadable", None)
            continue
        answer = _cached(folder, e["name"], stamps[e["name"]])
        if answer is not None:
            found[e["name"]] = ("answers", answer)
        else:
            jobs.append((e["name"], [e["exe"], "describe", "--json"]))
    for name, (code, out, state) in run_all(jobs, env).items():
        answer = counted_describe(code, out) if state == "ran" else None
        if answer is not None:
            _keep(folder, name, stamps[name], answer)
            found[name] = ("answers", answer)
        else:
            found[name] = ("timed out" if state == "timed out" else "unreadable", None)
    return found


def config_read(answer):
    for read in answer.get("reads") or ():
        if read.get("kind") == "config":
            return read
    return None


# ---- the fallback table ---------------------------------------------------------------------

def fallback(lib):
    found = plan._read_json(os.path.join(lib, "fallback.json"))
    return {k: v for k, v in found.items() if isinstance(v, dict)} if isinstance(found, dict) else {}


def descriptions(env):
    """{plugin name: description} from the agentik marketplace's own file."""
    known = plan._read_json(os.path.join(_config_dir(env), "plugins", "known_marketplaces.json"))
    entry = known.get(plan.MARKETPLACE) if isinstance(known, dict) else None
    where = entry.get("installLocation") if isinstance(entry, dict) else None
    if not isinstance(where, str):
        return {}
    market = plan._read_json(os.path.join(where, ".claude-plugin", "marketplace.json"))
    plugins = market.get("plugins") if isinstance(market, dict) else None
    return {p["name"]: p["description"] for p in plugins or ()
            if isinstance(p, dict) and isinstance(p.get("name"), str)
            and isinstance(p.get("description"), str)}
