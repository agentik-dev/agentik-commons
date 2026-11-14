"""The facts an issue may hold: a closed list, each typed and bounded (hq design/22 §3 item 2).

`facts` reads the machine once and gives one object, `agentik.issue-facts/1`; it reads named
keys only, prints nothing and scrubs nothing. A typed value is validated: a value that is not of
its type reads `unreadable`, an absent one None. A free value (a doctor row's name and detail,
the command run, each output line, the words expected) is returned whole, never cut, so the
caller's scrub sees all of it before `bound` cuts it to the table below (hq design/22 item 4:
layer 1 runs before any cut); a value over READ_CAP reads `unreadable` whole. `map_free`
reaches each free value in a fixed order. The tools an issue may name are those of `public.json`, beside the
package, made from the suite's own marketplace file: a tool or plugin outside it is counted and
never named. Never read: a transcript, a prompt, a run's id, a ledger, a CLAUDE.md, a
charter or any file of a repo, the working folder, PATH's value or any other environment value
(PATH is walked, CLAUDECODE is tested), a settings or state file's content, a key or a token.
"""
import json
import os
import re
import sys
import time

import agentik_install

from . import plan, tools

SCHEMA = "agentik.issue-facts/1"
DOCTOR = "agentik.doctor/1"
PUBLIC = "public.json"
DOOR = "door"
UNREADABLE = "unreadable"
NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
REPO = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?/[A-Za-z0-9._-]+\Z")
VERSION = re.compile(r"[0-9]{1,9}\.[0-9]{1,9}\.[0-9]{1,9}(?:-(?:alpha|beta|rc)\.[0-9]{1,9})?\Z")
COMMIT = re.compile(r"[0-9a-f]{12}\Z")
# `claude --version`'s N.N.N: no dotted run that goes on to a fourth part, before or after, so
# no three parts of an address in a tool's output pass for a version.
CLAUDE = re.compile(r"(?<![0-9])(?<![0-9]\.)[0-9]{1,9}\.[0-9]{1,9}\.[0-9]{1,9}(?![0-9]*\.[0-9])")
SYSTEMS = ("Darwin", "Linux")
ARCHES = ("arm64", "x86_64", "aarch64")
RELEASE = 20
CLAUDE_WALL = 5.0
CLAUDE_READ = 4096
# A placeholder the scrub writes, numbered as `<path-12>` or single as `<secret>`: `bound`
# never cuts inside one.
PLACEHOLDER = re.compile(r"<[a-z][a-z-]*(?:-[0-9]+)?>")
# What `facts` keeps: a free value of READ_CAP bytes or fewer whole, a longer one as `unreadable`
# whole (no cut lands before the scrub: rp6 review 1 F1), READ_ROWS rows, the last TAIL_LINES
# lines of the output's last TAIL bytes, PLUGINS public plugins by name. A window that starts
# inside its one line is a read's edge no scrub can see past: the line loses its first EDGE bytes
# and the rest of the word there, so no secret of EDGE bytes and no word straddles it.
READ_CAP = 1 << 20
EDGE = 1024
READ_ROWS = 200
TAIL = 64 * 1024
TAIL_LINES = 200
PLUGINS = 12
# What `bound` keeps, in UTF-8 bytes: 12 rows, a row's name 60 and detail 200; the command 200;
# the last 20 lines, each 200; the words expected 600.
ROWS, ROW_NAME, ROW_DETAIL = 12, 60, 200
RAN, LINES, LINE, EXPECTED = 200, 20, 200, 600


def load_public(lib):
    """{"marketplace": NAME, "tools": {tool: "OWNER/REPO"}} from `lib`/public.json; ValueError for
    an absent file or any other shape."""
    found = plan._read_json(os.path.join(lib, PUBLIC))
    if not isinstance(found, dict) or set(found) != {"marketplace", "tools"}:
        raise ValueError("%s: not {marketplace, tools}" % PUBLIC)
    market, tools = found["marketplace"], found["tools"]
    if not isinstance(market, str) or not NAME.match(market):
        raise ValueError("%s: marketplace is no name" % PUBLIC)
    if not isinstance(tools, dict) or not tools:
        raise ValueError("%s: tools is no table" % PUBLIC)
    for tool, repo in tools.items():
        if not NAME.match(tool) or not isinstance(repo, str) or not REPO.match(repo) or \
                repo.split("/")[1] in (".", ".."):
            raise ValueError("%s: %r is no tool and OWNER/REPO" % (PUBLIC, tool))
    return {"marketplace": market, "tools": dict(tools)}


def _cut(text, limit):
    """`text` in at most `limit` UTF-8 bytes, cut on a character's edge and, when the cut falls
    inside a placeholder, before it."""
    data = text.encode("utf-8")
    if len(data) <= limit:
        return text
    end = limit
    while end and data[end] & 0xC0 == 0x80:
        end -= 1
    cut = len(data[:end].decode("utf-8"))
    for m in PLACEHOLDER.finditer(text):
        if m.start() >= cut:
            break
        if m.end() > cut:
            cut = m.start()
            break
    return text[:cut]


def _past_edge(line):
    """A line the read's window cut into at its start, less its first EDGE bytes and the rest of
    the word there: what is kept starts after a space the window holds whole."""
    data = line.encode("utf-8", "replace")
    start = min(len(data), EDGE)
    while start < len(data) and data[start] & 0xC0 == 0x80:
        start += 1
    rest = data[start:].decode("utf-8")
    space = re.search(r"\s", rest)
    return rest[space.end():] if space else ""


def _free(value):
    """A free value as read, whole, a lone surrogate replaced; `unreadable` past READ_CAP bytes,
    so nothing is cut before the scrub; None for no text."""
    if not isinstance(value, str):
        return None
    text = value.encode("utf-8", "replace").decode("utf-8")
    return text if len(text.encode("utf-8")) <= READ_CAP else UNREADABLE


def _typed(value, pattern):
    if value is None:
        return None
    return value if isinstance(value, str) and pattern.match(value) else UNREADABLE


def _commit(value):
    if value is None:
        return None
    return _typed(value[:12].lower(), COMMIT) if isinstance(value, str) else UNREADABLE


def _on_path(env, command, run=False):
    """The first `command` on env's PATH that is a regular file (and executable, for `run`); an
    entry that is no absolute path is passed over, so the working folder is never looked in."""
    for entry in env.get("PATH", "").split(os.pathsep):
        if not os.path.isabs(entry):
            continue
        path = os.path.join(entry, command)
        if os.path.isfile(path) and (not run or os.access(path, os.X_OK)):
            return path
    return None


def _launcher(env, command, raw):
    """The VERSION of the first `command` on PATH, typed; its raw value is added to `raw`."""
    path = _on_path(env, command)
    found = agentik_install.read_launcher(path) if path else None
    value = (found or {}).get("version")
    raw.append(value)
    return _typed(value, VERSION)


def _unread(raw):
    """A pattern for each raw launcher version that is no VERSION, as a whole word, as read and as
    `_free` would give it; None when there is none. A doctor row's detail can carry one (the
    door check's `have`), so `checks` reads each as `unreadable`."""
    words = set()
    for w in raw:
        if isinstance(w, str) and w and not VERSION.match(w):
            words |= {w, w.encode("utf-8", "replace").decode("utf-8")}
    if not words:
        return None
    alt = "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
    return re.compile(r"(?<![A-Za-z0-9])(?:%s)(?![A-Za-z0-9])" % alt)


def _installed(env):
    """Claude Code's installed plugins, by key; {} when the config folder is no absolute path (HOME
    empty or unset, a relative CLAUDE_CONFIG_DIR), so the working folder is never read."""
    folder = tools._config_dir(env)
    if not os.path.isabs(folder):
        return {}
    found = plan._read_json(os.path.join(folder, "plugins", "installed_plugins.json"))
    table = found.get("plugins") if isinstance(found, dict) else None
    return table if isinstance(table, dict) else {}


def _entry(table, key):
    entry = table.get(key)
    if isinstance(entry, list):
        entry = entry[0] if entry else None
    return entry if isinstance(entry, dict) else {}


def _suite():
    return plan.SUITE[len("agentik-"):]


def versions(env, public, table, raw):
    suite, market = _suite(), public["marketplace"]
    rows = []
    for name in [suite, DOOR] + sorted(t for t in public["tools"] if t != suite):
        if name == DOOR:
            rows.append({"name": DOOR, "plugin": None, "commit": None,
                         "launcher": _launcher(env, agentik_install.DOOR, raw)})
            continue
        entry = _entry(table, "%s@%s" % (name, market))
        rows.append({"name": name, "plugin": _typed(entry.get("version"), VERSION),
                     "commit": _commit(entry.get("gitCommitSha")),
                     "launcher": _launcher(env, "agentik-" + name, raw)})
    return rows


def _claude(env):
    path = _on_path(env, "claude", run=True)
    if path is None:
        return UNREADABLE
    code, out, state = tools.run_all([("claude", [path, "--version"])], env,
                                     deadline=time.monotonic() + CLAUDE_WALL)["claude"]
    m = CLAUDE.search(out[:CLAUDE_READ].decode("ascii", "replace")) if state == "ran" and code == 0 else None
    return m.group() if m else UNREADABLE


def system(env):
    u = os.uname()
    return {"os": u.sysname if u.sysname in SYSTEMS else "other",
            "release": re.match(r"[0-9.]*", u.release).group()[:RELEASE] or UNREADABLE,
            "arch": u.machine if u.machine in ARCHES else "other",
            "python": "%d.%d.%d" % tuple(sys.version_info[:3]),
            "claude": _claude(env),
            "where": "in Claude Code" if "CLAUDECODE" in env else "at a terminal"}


def checks(found, public, unread=None):
    """The doctor's fail and warn rows of the suite and of each public tool, fail first; every
    other check counted in `passed`. Only the keys the schema lists are read; a detail's word
    that `unread` matches reads `unreadable`."""
    rows = {"read": False, "rows": [], "failed": 0, "warned": 0, "passed": 0}
    if not isinstance(found, dict) or found.get("schema") != DOCTOR or \
            not isinstance(found.get("tools"), list):
        return rows
    named = set(public["tools"]) | {_suite()}
    fails, warns, passed = [], [], 0
    for group in found["tools"]:
        if not isinstance(group, dict) or not isinstance(group.get("checks"), list):
            continue
        tool = group.get("name")
        tool = tool if isinstance(tool, str) and tool in named else None
        for c in group["checks"]:
            if not isinstance(c, dict):
                continue
            status = c.get("status")
            if tool is None or status not in ("fail", "warn"):
                passed += 1
                continue
            detail = c.get("detail")
            if unread is not None and isinstance(detail, str):
                detail = unread.sub(UNREADABLE, detail)
            row = {"tool": tool, "status": status, "name": _free(c.get("name")) or "",
                   "detail": _free(detail) or ""}
            (fails if status == "fail" else warns).append(row)
    rows.update(read=True, rows=(fails + warns)[:READ_ROWS], failed=len(fails),
                warned=len(warns), passed=passed)
    return rows


def plugins(public, table):
    market, names, others = public["marketplace"], [], 0
    for key in table:
        name, at, where = key.partition("@")
        if at and where == market and name in public["tools"]:
            names.append(name)
        else:
            others += 1
    names = sorted(names)
    others += len(names[PLUGINS:])
    return {"named": [{"name": n, "version": _typed(_entry(table, "%s@%s" % (n, market)).get("version"),
                                                   VERSION)} for n in names[:PLUGINS]],
            "others": others}


def _tail(path):
    """The last TAIL_LINES lines of the last TAIL bytes of the regular file at `path`, bad bytes
    replaced; a first line the window cut into is dropped when another line follows it, and when
    none does, the window sits inside one line and that line's tail is kept past its edge
    (`_past_edge`). [] for no such file."""
    if not isinstance(path, str) or not path or not os.path.isfile(path):
        return []
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    except (OSError, ValueError):
        return []
    try:
        st = os.fstat(fd)
        if st.st_mode & 0o170000 != 0o100000:  # a regular file still
            return []
        start = max(0, st.st_size - TAIL)
        os.lseek(fd, start, os.SEEK_SET)
        chunks, size = [], 0
        while size < TAIL:
            data = os.read(fd, TAIL - size)
            if not data:
                break
            chunks.append(data)
            size += len(data)
    except OSError:
        return []
    finally:
        os.close(fd)
    lines = b"".join(chunks).decode("utf-8", "replace").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    lines = [l[:-1] if l.endswith("\r") else l for l in lines]
    if start and len(lines) > 1:
        lines.pop(0)
    elif start and lines:  # the window sits inside one line: its tail, past the window's edge
        lines = [_past_edge(lines[0])]
    return [_free(l) for l in lines[-TAIL_LINES:]]


def _exit(value):
    ok = isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 255
    return value if ok else None


def facts(env, lib, given, read_doctor):
    """The `agentik.issue-facts/1` object. `given` is {tool, ran, exit, output, expected}, each
    possibly None; `read_doctor()` gives an `agentik.doctor/1` object or None. Raises ValueError
    when public.json is not of its shape."""
    public = load_public(lib)
    table, raw = _installed(env), []
    try:
        found = read_doctor()
    except Exception:  # a doctor that cannot be read reads as none
        found = None
    tool, rows = given.get("tool"), versions(env, public, table, raw)
    return {"schema": SCHEMA, "tool": tool if isinstance(tool, str) and tool in public["tools"] else None,
            "versions": rows,
            "system": system(env),
            "checks": checks(found, public, _unread(raw)),
            "plugins": plugins(public, table),
            "output": {"ran": _free(given.get("ran")), "exit": _exit(given.get("exit")),
                       "lines": _tail(given.get("output"))},
            "words": {"expected": _free(given.get("expected"))}}


def map_free(facts, fn):
    """A copy of `facts` with `fn` over each free value that is text: each row's name then
    detail, the command, each output line, the words expected."""
    out = json.loads(json.dumps(facts))

    def one(value):
        return fn(value) if isinstance(value, str) else value
    for row in out["checks"]["rows"]:
        row["name"], row["detail"] = one(row["name"]), one(row["detail"])
    out["output"]["ran"] = one(out["output"]["ran"])
    out["output"]["lines"] = [one(l) for l in out["output"]["lines"]]
    out["words"]["expected"] = one(out["words"]["expected"])
    return out


def bound(facts):
    """A copy of `facts` cut to the bounds above, after the caller's scrub."""
    out = json.loads(json.dumps(facts))
    rows = out["checks"]["rows"] = out["checks"]["rows"][:ROWS]
    for row in rows:
        row["name"], row["detail"] = _cut(row["name"], ROW_NAME), _cut(row["detail"], ROW_DETAIL)
    o = out["output"]
    o["ran"] = _cut(o["ran"], RAN) if isinstance(o["ran"], str) else o["ran"]
    o["lines"] = [_cut(l, LINE) for l in o["lines"][-LINES:]]
    w = out["words"]
    w["expected"] = _cut(w["expected"], EXPECTED) if isinstance(w["expected"], str) else w["expected"]
    return out
