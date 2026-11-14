"""`status --json`: the five sources read at once into one `agentik.status/1` object.

A read comes from the fallback table's `status` list of a tool that has a row (never asked
`describe`), else from the `status` reads of any other `agentik-*` on PATH, asked through ak1b's
describe cache. Every read, every describe and one `ps` run in one `tools.run_all` call, each
under its own wall. A read is held to its pins: a missing one is `changed` and its values null,
the rest drawn. The object holds no sentence; the screen says every word (packet su2-read).
"""
import datetime
import json
import os
import re
import time

from . import covers as covering, status, tools

PARTS = ("watchers", "sessions", "gate", "backlog", "runs")
READS = {"sessions": "sessions", "gate": "gate", "backlog": "backlog", "run": "runs",
         "unattended": "runs"}
LISTED = ("watchers", "sessions", "gate", "runs")  # the parts held against the listing
WALL = 1.0
STDERR_MAX = 300
TEXT_MAX = 80  # a word an answer gives that the object holds as text: a run, a row, a reason
NOT_READ = ["owner", "rows"]
UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\Z")
SCHEMA = re.compile(r".*/([0-9]+)\Z")
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")  # C0, DEL and C1 (U+009B, CSI, among them)
DAY = re.compile(r"(\d{4}-\d\d-\d\d)")
NUM, TEXT, LIST, MAP, NONE, BOOL = "number", "text", "list", "map", "null", "bool"
KINDS = {TEXT: str, LIST: list, MAP: dict, NONE: type(None), BOOL: bool}


def _kind_ok(value, kinds):
    for k in kinds:
        if k == NUM:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return True
        elif isinstance(value, KINDS[k]):
            return True
    return False


class Pins:
    """A source's answer read by its pins: a key missing or of another kind marks it changed,
    and its name joins the source's `fields`."""

    def __init__(self, src):
        self.src = src

    def get(self, obj, key, *kinds):
        if isinstance(obj, dict) and key in obj and _kind_ok(obj[key], kinds):
            return obj[key]
        self.src["changed"] = True
        if key not in self.src["fields"]:
            self.src["fields"].append(key)
        return None


def _clean(text):
    """A text value with its control characters removed, its ends trimmed, cut at TEXT_MAX."""
    return CONTROL.sub("", text).strip()[:TEXT_MAX] if isinstance(text, str) else text


def _source(name, tool, argv, wall_s, exe):
    return {"name": name, "tool": tool, "argv": list(argv), "state": None, "ms": None, "exit": None,
            "stderr": None, "wall_s": wall_s, "exe": exe, "answer": None, "changed": False,
            "fields": [], "settled": False}


def _table_reads(row):
    found = []
    for read in row.get("status") if isinstance(row.get("status"), list) else ():
        if not (isinstance(read, dict) and isinstance(read.get("name"), str)
                and isinstance(read.get("argv"), list) and all(isinstance(w, str) for w in read["argv"])):
            continue
        wall = read.get("wall_s")
        found.append((read["name"], read["argv"], wall if _kind_ok(wall, (NUM,)) and wall > 0 else None))
    return found


def _first_line(err):
    for line in (err or b"").decode("utf-8", "replace").splitlines():
        line = CONTROL.sub("", line).strip()
        if line:
            return line[:STDERR_MAX]
    return None


def _settle(src, result, err, secs):
    code, out, state = result
    src["settled"], src["exit"] = True, code
    src["ms"] = int(round(secs * 1000)) if secs is not None else None
    if state == "timed out":
        src["state"], src["ms"] = "timed out", int(round(src["wall_s"] * 1000))
        return
    answer, ok = None, state == "ran" and code == 0
    if ok:
        try:
            answer = json.loads(out.decode("utf-8", "replace"))
        except (ValueError, RecursionError):
            ok = False
        if answer is None:
            ok = ok and src["name"] == "unattended"  # its bare null is an answer: no run
        elif not isinstance(answer, dict):
            ok = False
    if not ok:
        src["state"], src["stderr"] = "unreadable", _first_line(err)
        return
    schema = answer.get("schema") if isinstance(answer, dict) else None
    m = SCHEMA.match(schema) if isinstance(schema, str) else None
    src["state"], src["answer"] = "ok", answer
    if m and int(m.group(1)) > 1:
        src["changed"] = True
        src["fields"].append("schema")


def _remedy(src):
    return " ".join(["agentik", src["tool"]] + [w for w in src["argv"] if w != "--json"])


def _uid_pids(procs, uid):
    return {p for p, u, words in procs if u == uid}


# ---- the parts --------------------------------------------------------------------------------

def _sessions(srcs, procs, uid):
    part = {"state": None, "checked": procs is not None, "window_min": None, "live": None,
            "ended": None, "past_window": None}
    read = [s for s in srcs if s["answer"] is not None]
    if not read:
        return part
    src = read[0]
    pin, answer = Pins(src), src["answer"]
    part["window_min"] = pin.get(answer, "since_min", NUM, NONE)
    lists = [v for v in answer.values() if isinstance(v, list)]
    if len(lists) != 1:
        src["changed"] = True
        return part
    seats, order = {}, []
    for entry in lists[0]:
        if not isinstance(entry, dict):
            src["changed"] = True
            continue
        e = {k: pin.get(entry, k, *kinds) for k, kinds in (
            ("id", (TEXT,)), ("parent", (TEXT, NONE)), ("state", (TEXT, NONE)), ("what", (TEXT, NONE)),
            ("context", (NUM, NONE)), ("window", (NUM, NONE)), ("turns", (NUM, NONE)))}
        if e["parent"] is None:
            if e["id"] is not None and e["id"] not in seats:
                seats[e["id"]] = {"id": e["id"], "name": e["what"], "state": e["state"],
                                  "context": e["context"], "window": e["window"], "turns": e["turns"],
                                  "pid": None, "helpers": {}}
                order.append(e["id"])
        else:
            order.append((e["parent"], e["state"]))
    for item in order:
        if isinstance(item, tuple) and item[0] in seats:
            word = item[1] if item[1] is not None else "unknown"
            helpers = seats[item[0]]["helpers"]
            helpers[word] = helpers.get(word, 0) + 1
    ids = [i for i in order if not isinstance(i, tuple)]
    if procs is None:
        part["live"], part["ended"] = [seats[i] for i in ids], None
        return part
    heads, bare = [], False
    for pid, u, words in procs:
        i = status.head(words)
        if u != uid or i is None or os.path.basename(words[i]) != "claude":
            continue
        found = [w.rpartition("=")[2] for w in words[i + 1:] if UUID.match(w.rpartition("=")[2])]
        if found:
            heads.append((pid, found))
        else:
            bare = True
    live, ended = [], 0
    for i in ids:
        pid = next((p for p, found in heads if i in found), None)
        if pid is not None or bare:
            seats[i]["pid"] = pid
            live.append(seats[i])
        else:
            ended += 1
    part["live"], part["ended"] = live, ended
    part["past_window"] = [{"id": found[0], "pid": p} for p, found in heads if found[0] not in seats]
    return part


def _base(repo):
    return os.path.basename(repo.rstrip("/")) if isinstance(repo, str) else None


def _gate(srcs, procs, uid, hand):
    part = {"state": None, "runner": None, "running": None, "queued": None, "last": None, "red": None}
    read = [s for s in srcs if s["answer"] is not None]
    if not read:
        return part
    src = read[0]
    pin, answer = Pins(src), src["answer"]
    est = pin.get(answer, "est", MAP, NONE) or {}

    def entries(key, fields):
        found = []
        for e in pin.get(answer, key, LIST) or ():
            got = {"id": pin.get(e, "id", TEXT, NUM)}
            repo = pin.get(e, "repo", TEXT, NONE)
            got.update({"name": _base(repo), "repo": repo})
            for f, kinds in fields:
                got[f] = pin.get(e, f, *kinds)
            found.append(got)
        return found

    def est_s(e):
        return est.get(e["id"]) if _kind_ok(est.get(e["id"]), (NUM,)) else None

    part["running"] = [dict(e, est_s=est_s(e)) for e in entries(
        "running", (("label", (TEXT, NONE)), ("seconds", (NUM, NONE))))]
    part["queued"] = [dict(e, est_s=est_s(e)) for e in entries(
        "queued", (("label", (TEXT, NONE)), ("position", (NUM, NONE)), ("wait", (TEXT, NONE))))]
    done = entries("done", (("exit", (NUM, NONE)), ("seconds", (NUM, NONE)), ("cut", (TEXT, NUM, MAP, NONE))))
    part["last"] = done[0] if done else None
    part["red"] = [e for e in done[1:] if e["exit"] != 0]
    runner = pin.get(answer, "runner", MAP, NONE)
    if runner is not None:
        pid = pin.get(runner, "pid", NUM)
        alive = None if procs is None else pid in _uid_pids(procs, uid)
        part["runner"] = {"pid": pid, "since": pin.get(runner, "since", NUM, NONE), "alive": alive}
    if (part["running"] or part["queued"]) and (runner is None or part["runner"]["alive"] is False):
        hand.append({"part": "gate", "kind": "no_runner", "name": None, "remedy": _remedy(src)})
    return part


def _backlog(srcs):
    part = {"state": None, "open": None, "first": None, "items": None, "checkouts": None,
            "skipped": None}
    read = [s for s in srcs if s["answer"] is not None]
    if not read:
        return part
    src = read[0]
    pin, answer = Pins(src), src["answer"]
    repos = pin.get(answer, "repos", LIST) or []
    part["skipped"] = pin.get(answer, "skipped", LIST)
    seen, handoffs, items = set(), [], {}
    for repo in repos:
        handoff = pin.get(repo, "handoff", TEXT, NONE)
        for step in pin.get(repo, "steps", LIST) or ():
            n, line = pin.get(step, "n", NUM), pin.get(step, "line", NUM, NONE)
            title, done = pin.get(step, "title", TEXT, NONE), pin.get(step, "done", BOOL, NONE)
            if done or (handoff, n) in seen:
                continue
            seen.add((handoff, n))
            handoffs.append((handoff, line, n, title))
        for item in pin.get(repo, "items", LIST) or ():
            placed = pin.get(item, "placed_as", TEXT, NONE)
            key = placed if placed is not None else "unplaced"
            items[key] = items.get(key, 0) + 1
    part["open"], part["items"], part["checkouts"] = len(seen), items, len(repos)
    if handoffs:
        first = handoffs[0][0]
        steps = [h for h in handoffs if h[0] == first]
        best = min(steps, key=lambda h: (h[1] is None, h[1] if h[1] is not None else 0))
        part["first"] = {"n": best[2], "title": best[3]}
    return part


def _counts(states):
    found = {}
    for s in states:
        found[s] = found.get(s, 0) + 1
    return found


def _runs(srcs, procs, uid, now, hand):
    part = {"state": None, "shown": None, "aged": None}
    read = [s for s in srcs if s["state"] in ("ok", "changed")]
    if not read:
        return part
    today = datetime.date.fromtimestamp(now)
    days = (today.isoformat(), (today - datetime.timedelta(days=1)).isoformat())
    shown, aged = [], 0
    for src in read:
        pin, answer = Pins(src), src["answer"]
        if src["name"] == "run":
            night = pin.get(answer, "night", TEXT)
            state = pin.get(answer, "state", TEXT, NONE)
            pid = pin.get(answer, "pid", NUM, NONE)
            rows = [pin.get(r, "state", TEXT, NONE) for r in pin.get(answer, "rows", LIST) or ()]
            if not night:
                continue
            alive = None if procs is None or not pid else pid in _uid_pids(procs, uid)
            run = {"source": "run", "by": src["tool"], "run": night, "state": state, "row": None,
                   "age_s": None, "pid": pid, "alive": alive, "rows": _counts(rows)}
            if state == "running" and alive is False:
                hand.append({"part": "runs", "kind": "run_gone", "name": night, "tool": src["tool"],
                             "remedy": _remedy(src)})
        else:
            if answer is None:
                continue
            rid = _clean(pin.get(answer, "run", TEXT))
            rows = pin.get(answer, "rows", MAP, NONE) or {}
            running = pin.get(answer, "running", MAP, NONE)
            stop = pin.get(answer, "stop", TEXT, MAP, NONE)
            row = age = None
            if running is not None:
                row = _clean(pin.get(running, "row", TEXT, NONE))
                age = pin.get(running, "age_s", NUM, NONE)
                if age is not None and not abs(age) < float("inf"):  # NaN or infinity
                    age = pin.get({}, "age_s", NUM)
            if stop is not None and running is None:
                reason = _clean(stop if isinstance(stop, str) else pin.get(stop, "reason", TEXT))
                state = "stopped: %s" % reason if reason else "stopped"
            else:
                state = "running" if running is not None else "ended"
            run = {"source": src["name"], "by": src["name"], "run": rid, "state": state,
                   "row": row, "age_s": age, "pid": None, "alive": None,
                   "rows": {k: len(v) for k, v in rows.items() if isinstance(v, list)}}
        m = DAY.match(run["run"] or "")
        if run["state"] == "running" or (m and m.group(1) in days):
            shown.append(run)
        else:
            aged += 1
    part["shown"], part["aged"] = shown, aged
    return part


def _watchers(watchers, procs, now, env, uid, hand):
    found = [status.check(w, procs, now, env, uid) for w in watchers]
    for r in found:
        if r["state"] != "running":
            hand.append({"part": "watchers", "kind": "watcher_" + r["state"], "name": r["name"],
                         "remedy": r["start"] if r["state"] != "unknown" else None})
    return found


# ---- the read ---------------------------------------------------------------------------------

def compose(cmd, paths, now, ps_text, on_part=None):
    """The `agentik.status/1` object; `on_part(name, obj)` once a part, in PARTS' order, as soon
    as it and every part before it are settled. A settings.Fault for a user file outside the
    subset."""
    t0 = time.monotonic()
    env, uid = cmd.env, os.getuid()
    try:
        cwd = getattr(cmd, "cwd", None) or os.getcwd()
    except OSError:  # the working folder is gone: R2's fault for a path that is no folder
        raise cmd.Usage("bad_path", "err.status.path", "%s status" % cmd.tool,
                        path=cmd.env.get("PWD") or ".")
    _, watchers, _ = status.declared(env)
    cov = covering.covers(env, cwd, paths)
    at = int(now) if float(now).is_integer() else now
    head = {"schema": "agentik.status/1", "ok": True, "check": False, "fault": None, "at": at,
            "covers": cov}

    own = cmd.tool[len("agentik-"):] if cmd.tool.startswith("agentik-") else cmd.tool
    on_path = {e["name"][len("agentik-"):]: e["path"] for e in cmd._on_path()}
    table = tools.fallback(cmd.lib)
    srcs, absent, given = [], [], set()
    jobs, keys = [], {}

    def add(src):
        """List a read: drawn and started, or `not drawn`; None for backlog under rule none."""
        if src["name"] == "backlog" and cov["rule"] == "none":
            return []
        srcs.append(src)
        if src["name"] not in READS or src["name"] in given:
            src["state"], src["settled"], src["wall_s"] = "not drawn", True, None
            return []
        given.add(src["name"])
        argv = [src["exe"]] + src["argv"]
        if src["name"] == "backlog":
            handoff = os.path.join(cov["hq"], "HANDOFF.md") if cov["hq"] else None
            if handoff and os.path.isfile(handoff):
                argv += ["--order", handoff]
            argv += cov["checkouts"]
        key = ("read", len(srcs) - 1)
        keys[key] = src
        return [(key, argv)]

    for name, row in table.items():
        for rname, argv, wall in _table_reads(row):
            src = _source(rname, name, argv, wall or WALL, on_path.get(name))
            if src["exe"]:
                jobs.extend(add(src))
            else:
                absent.append(src)

    folder, asked, stamps = tools.cache_dir(env), [], {}
    for name in sorted(on_path):
        if name in table or name == own or not tools.NAME.match(name):
            continue
        entry = {"name": name, "exe": on_path[name], "answer": None, "settled": False}
        asked.append(entry)
        try:
            stamps[name] = tools._stamp(entry["exe"])
        except OSError:
            entry["settled"] = True
            continue
        entry["answer"] = tools._cached(folder, name, stamps[name])
        if entry["answer"] is not None:
            entry["settled"] = True
        else:
            jobs.append((("describe", name), [entry["exe"], "describe", "--json"]))
    released = set()

    def release():
        """Each settled describe's reads, in tool order, up to the first still unsettled."""
        found = []
        for entry in asked:
            if not entry["settled"]:
                break
            if entry["name"] in released:
                continue
            released.add(entry["name"])
            for read in (entry["answer"] or {}).get("reads") or ():
                if read.get("kind") == "status" and isinstance(read.get("name"), str):
                    found.extend(add(_source(read["name"], entry["name"], read["argv"], WALL,
                                             entry["exe"])))
        if all(e["settled"] for e in asked):
            for src in absent:
                if src["name"] in READS and src["name"] not in given and not (
                        src["name"] == "backlog" and cov["rule"] == "none"):
                    given.add(src["name"])
                    srcs.append(dict(src, state="not installed", settled=True))
            del absent[:]
        return found

    jobs.extend(release())
    listing = {"settled": ps_text is not None, "procs": status.rows(ps_text) if ps_text is not None else None}
    if ps_text is None:
        argv = status.ps_argv(env)
        if argv is None:
            listing["settled"] = True
        else:
            jobs.append((("ps",), argv))

    parts, hand, done = {}, [], []
    walls = {key: keys[key]["wall_s"] if key[0] == "read" else WALL for key, _ in jobs}
    errs, times = {}, {}

    def part_srcs(name):
        return [s for s in srcs if READS.get(s["name"]) == name and s["state"] != "not drawn"]

    def settled(name):
        if name in LISTED and not listing["settled"]:
            return False
        if not all(e["settled"] for e in asked) and any(
                n not in given for n, p in READS.items() if p == name):
            return False
        return all(s["settled"] for s in part_srcs(name))

    def build(name):
        procs, mine = listing["procs"], []
        ss = part_srcs(name)
        if name == "watchers":
            parts[name] = _watchers(watchers, procs, now, env, uid, mine)
        elif name == "sessions":
            parts[name] = _sessions(ss, procs, uid)
        elif name == "gate":
            parts[name] = _gate(ss, procs, uid, mine)
        elif name == "backlog":
            parts[name] = _backlog(ss)
        else:
            parts[name] = _runs(ss, procs, uid, now, mine)
        for s in ss:
            if s["state"] == "ok" and s["changed"]:
                s["state"] = "changed"
        if name != "watchers":
            read = any(s["state"] in ("ok", "changed") for s in ss)
            if mine:
                state = "hand"
            elif not read:
                state = "not read"
            elif any(s["state"] in ("timed out", "unreadable", "changed") for s in ss) or (
                    name in LISTED and procs is None):
                state = "partial"
            else:
                state = "ok"
            parts[name]["state"] = state
        hand.extend(mine)
        if on_part:
            obj = dict(head, **{name: parts[name]})
            obj["hand"] = mine
            obj["sources"] = [_shown(s) for s in ss]
            on_part(name, obj)

    def advance():
        while len(done) < len(PARTS) and settled(PARTS[len(done)]):
            build(PARTS[len(done)])
            done.append(PARTS[len(done)])

    def then(key, result):
        more = []
        if key == ("ps",):
            code, out, state = result
            listing["settled"] = True
            if state == "ran" and code == 0:
                procs = status.rows(out.decode("utf-8", "replace"))
                if status.holds_self(procs):
                    listing["procs"] = procs
                else:  # the parts that need it read partial, with no process judged
                    head["fault"] = "bad_listing"
        elif key[0] == "describe":
            entry = next(e for e in asked if e["name"] == key[1])
            code, out, state = result
            answer = tools.counted_describe(code, out) if state == "ran" else None
            if answer is not None:
                tools._keep(folder, key[1], stamps[key[1]], answer)
            entry["answer"], entry["settled"] = answer, True
            more = release()
            for k, _ in more:
                walls[k] = keys[k]["wall_s"]
        else:
            _settle(keys[key], result, errs.get(key), times.get(key))
        advance()
        return more

    advance()
    if jobs:
        tools.run_all(jobs, env, then=then, walls=walls, errs=errs, times=times)
    for key, src in keys.items():  # a read the run never settled (it cannot: each has a wall)
        if not src["settled"]:
            _settle(src, (None, b"", "timed out"), None, None)
    for entry in asked:
        entry["settled"] = True
    release()
    listing["settled"] = True
    advance()

    obj = dict(head, ms=int(round((time.monotonic() - t0) * 1000)))
    for name in PARTS:
        obj[name] = parts[name]
    obj["hand"] = hand
    order = {p: i for i, p in enumerate(PARTS)}
    ranked = sorted(enumerate(srcs), key=lambda p: (
        p[1]["state"] == "not drawn", order.get(READS.get(p[1]["name"]), 99), p[0]))
    obj["sources"] = [_shown(s) for _, s in ranked]
    obj["not_read"] = list(NOT_READ)
    return obj


def _shown(src):
    shown = {k: src[k] for k in ("name", "tool", "argv", "state", "ms", "exit", "stderr", "wall_s")}
    shown["fields"] = list(src["fields"]) or None  # the pins its answer failed, by key
    return shown
