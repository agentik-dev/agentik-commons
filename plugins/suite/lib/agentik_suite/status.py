"""`status --check`: each watcher the user file declares that is not running, one line each.

The declaration is the user file's `watchers` alone (settings.user_path). The listing is one
`ps -axo pid,ppid,uid,etime,command` under a 1 s wall, or a saved one given by `--ps`. A watcher
runs when a process of the reader's uid has its `match` as the head of its command (the head
found past an interpreter, a shell or `env`, by basename or a link's target), and its beat file,
when it names one, is within its `fresh_s`. The check runs no tool, reads no cache, starts `ps`
at most, and says nothing when every watcher runs.
"""
import datetime
import json
import os
import re
import shutil
import time

from . import plan, settings, tools

PS = "/bin/ps"
PS_ARGS = ("-axo", "pid,ppid,uid,etime,command")
WALL = 1.0
BEAT_CAP = 1 << 16
WRAPPERS = ("sh", "bash", "zsh", "dash", "env")
VALUED = ("-X", "-W", "-o")  # after any wrapper, the next word is the flag's value
ENV_VALUED = ("-u",)  # after `env` alone (`env -u NAME prog`); after python or a shell, a plain flag
# A run on the way: `-c` or `-m`, attached to its value (`-mfoo`) or anywhere in a short
# cluster (`-ce`, `-lc`); a `-X` or `-W` word is its value's, never a run. A bare `-` (the
# program read from stdin) is no match either.
RUN = re.compile(r"-(?![XW-])[A-Za-z]*[cm]")
ASSIGN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
ISO = re.compile(r"(\d{4}-\d\d-\d\d)[T ](\d\d:\d\d(?::\d\d(?:\.\d+)?)?)(Z|[+-]\d\d:?\d\d)?\Z")
LINE = {"missing": "status.missing", "hung": "status.hung"}


def when(text):
    """Epoch seconds of an ISO 8601 time with `Z`, an offset, or neither (local); else None."""
    m = ISO.match(text or "")
    if not m:
        return None
    zone = m.group(3) or ""
    if zone == "Z":
        zone = "+00:00"
    elif zone and ":" not in zone:
        zone = zone[:3] + ":" + zone[3:]
    try:
        stamp = datetime.datetime.fromisoformat("%sT%s%s" % (m.group(1), m.group(2), zone))
    except ValueError:
        return None
    return stamp.timestamp()


def local(at):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(at))


def declared(env):
    """(path, [watcher], [unchecked name]); a settings.Fault, with `path`, for a file outside the
    subset or `watchers` that is no mapping of mappings."""
    path = settings.user_path(env)
    try:
        present, tree, lines = settings.read(path)
        watchers = tree.get("watchers")
        if watchers is None:
            return path, [], []
        if not isinstance(watchers, dict):
            raise settings.Fault(lines.get("watchers"), "watchers is not a mapping of names")
        found, unchecked = [], []
        for name, fields in watchers.items():
            if not isinstance(fields, dict):
                raise settings.Fault(lines.get("watchers." + name), "watcher %s is not a mapping" % name)
            w = {f: fields[f] if isinstance(fields.get(f), str) and fields[f].strip() else None
                 for f in settings.WATCHER_FIELDS}
            if w["match"] is None or w["start"] is None:
                unchecked.append(name)
                continue
            w["name"] = name
            found.append(w)
        return path, found, unchecked
    except settings.Fault as f:
        f.path = path
        raise


def ps_argv(env):
    if os.path.isfile(PS) and os.access(PS, os.X_OK):
        return [PS] + list(PS_ARGS)
    found = shutil.which("ps", path=env.get("PATH", ""))
    return [found] + list(PS_ARGS) if found else None


def listing(env):
    """The text of one ps run, or None: no ps, a non-zero exit, or past the wall."""
    argv = ps_argv(env)
    if argv is None:
        return None
    code, out, state = tools.run_all([("ps", argv)], env, deadline=time.monotonic() + WALL)["ps"]
    if state != "ran" or code != 0:
        return None
    return out.decode("utf-8", "replace")


def rows(text):
    """[(pid, uid, [word])] of each row past the head."""
    found = []
    for line in text.splitlines()[1:]:
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        try:
            pid, uid = int(parts[0]), int(parts[2])
        except ValueError:
            continue
        found.append((pid, uid, parts[4].split()))
    return found


def _wrapper(word):
    base = os.path.basename(word)
    return base.startswith("python") or base in WRAPPERS


def head(words):
    """The index of the command's head, or None: none left, or a -c, -m or bare - on the way."""
    i = 0
    while i < len(words) and _wrapper(words[i]):
        valued = VALUED + ENV_VALUED if os.path.basename(words[i]) == "env" else VALUED
        i += 1
        while i < len(words):
            word = words[i]
            if word == "-" or RUN.match(word):
                return None
            if word in valued:
                i += 2
            elif word.startswith("-") or ASSIGN.match(word):
                i += 1
            else:
                break
    return i if i < len(words) else None


def _names(word):
    names = {os.path.basename(word)}
    if os.path.isabs(word):
        names.add(os.path.basename(os.path.realpath(word)))
    return names


def matches(match, words):
    want = match.split()
    i = head(words)
    if i is None or os.path.basename(want[0]) not in _names(words[i]):
        return False
    return words[i + 1:i + len(want)] == want[1:]


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and value == value and abs(value) != float("inf")


def beat(w, env):
    """The beat as {at, fresh_s, writer, line}, or None."""
    path = w["beat"]
    if not path:
        return None
    if path.startswith("~/"):
        path = os.path.join(env.get("HOME") or "", path[2:])
    if not os.path.isabs(path):
        return None
    try:
        with open(path, "rb") as fh:
            obj = json.loads(fh.read(BEAT_CAP).decode("utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(obj, dict) or not _number(obj.get("at")) or not _number(obj.get("fresh_s")):
        return None
    if any(obj.get(k) is not None and not isinstance(obj[k], str) for k in ("writer", "line")):
        return None
    try:
        local(obj["at"])
    except (OverflowError, OSError, ValueError):
        return None  # an `at` the clock refuses (outside time_t) is no time, so no beat
    return {"at": obj["at"], "fresh_s": obj["fresh_s"], "writer": obj.get("writer"),
            "line": obj.get("line")}


def check(w, procs, now, env, uid):
    """{name, state, pid, since, beat_writer, beat_line, start} for one watcher."""
    b = beat(w, env)
    own = b is not None and (w["writer"] is None or b["writer"] == w["writer"])
    fresh = b is not None and max(0, now - b["at"]) <= b["fresh_s"]
    pid = None
    if procs is not None:
        pid = next((p for p, u, words in procs if u == uid and matches(w["match"], words)), None)
    if procs is None:
        state = "unknown"
    elif pid is None:
        state = "missing"
    else:
        state = "running" if b is None or fresh else "hung"
    return {"name": w["name"], "state": state, "pid": pid, "since": b["at"] if own else None,
            "beat_writer": b["writer"] if b else None,
            "beat_line": b["line"] if own and fresh else None, "start": w["start"]}


def do_status(cmd, nouns):
    o, t, Usage = cmd.opts, cmd.t, cmd.Usage
    cmd._no_nouns(nouns)
    again = "%s status --check" % cmd.tool
    if not o["check"]:
        raise Usage("check_only", "err.status.check", again, tool=cmd.tool)
    now = time.time()
    if o["now"] is not None:
        now = when(o["now"])
        if now is None:
            raise Usage("bad_time", "err.status.now", again, value=o["now"])
    text = None
    if o["ps"] is not None:
        try:
            with open(o["ps"], "rb") as fh:
                text = fh.read().decode("utf-8", "replace")
        except OSError:
            raise Usage("bad_listing", "err.status.ps", again, path=o["ps"])
    try:
        path, watchers, unchecked = declared(cmd.env)
    except settings.Fault as f:
        home = cmd.env.get("HOME")
        fault = t.text("config.fault" if f.line else "config.fault.noline",
                       path=plan.shown(f.path, home), line=f.line, why=f.why)
        raise Usage("bad_file", "err.status.file", again, fault=fault, tool=cmd.tool)
    procs = None
    if watchers:
        if text is None:
            text = listing(cmd.env)
        procs = rows(text) if text is not None else None
    found = [check(w, procs, now, cmd.env, os.getuid()) for w in watchers]
    shown = [r for r in found if r["state"] != "running"]
    if o["json"]:
        t.json({"schema": "agentik.status/1", "ok": True, "check": True, "watchers": found})
    else:
        for r in shown:
            if r["state"] == "unknown":
                t.line("status.unknown", name=r["name"])
            elif r["since"] is not None:
                t.line(LINE[r["state"]] + ".since", name=r["name"], start=r["start"],
                       when=local(r["since"]))
            else:
                t.line(LINE[r["state"]], name=r["name"], start=r["start"])
    for name in unchecked:
        t.hint("hint.status.unchecked", name=name, path=plan.shown(path, cmd.env.get("HOME")),
               tool=cmd.tool)
    return 1 if shown else 0
