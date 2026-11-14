"""The screen of status (packet su2-screen): one agentik.status/1 object drawn through term.

Five parts in a fixed order, always all five, then the sources and what was not read, then one
hint on stderr where a hand is needed or a source gave no answer. A part reads its own part of
the object, `at`, `covers`, `hand`, `fault` and its own sources only, so it may be drawn while
the later parts are still absent. Nothing here runs a tool, reads a file or reads the clock: a time is the
object's `at` less a value of it. A value the object does not give is drawn `?`. A command of the
suite's own is named by `slots`, the command's `cmd.slots()` (row sc2).
"""
import os
import time

PARTS = ("watchers", "sessions", "gate", "backlog", "runs")
SOURCES = {"watchers": (), "sessions": ("sessions",), "gate": ("gate",), "backlog": ("backlog",),
           "runs": ("unattended", "run")}
READ = ("ok", "changed")
STATES = ("ok", "hand", "partial", "not read")  # a part's; only `ok` is read whole
GAVE_NOTHING = ("timed out", "unreadable", "changed")
CAP = 5  # rows under a part's first, before `and {n} more`
HELPER_ORDER = ("busy", "quiet", "done")
DIM = "hint"


class Wrong(ValueError):
    """A value of the wrong kind; the part that reads it is drawn as not read."""


WRONG = (Wrong, TypeError, ValueError, AttributeError, KeyError, IndexError, OverflowError, OSError)


def seq(value):
    """The list the object gives, [] for null; a value of another kind is wrong."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise Wrong(value)
    return value


def mapping(value):
    """The object the object gives, {} for null; a value of another kind is wrong."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise Wrong(value)
    return value


def entries(obj, key):
    """`hand` or `sources`: an entry that is not an object belongs to no part and is left out."""
    return [e for e in seq(obj.get(key)) if isinstance(e, dict)]


def shown(value):
    return "?" if value is None else str(value)


def when(at):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(at))


def age(t, seconds):
    """One unit, floored: s, min, h, d."""
    if seconds is None:
        return "?"
    s = max(int(seconds), 0)
    for unit, size, below in (("s", 1, 60), ("min", 60, 3600), ("h", 3600, 86400)):
        if s < below:
            return t.text("status.age." + unit, n=s // size)
    return t.text("status.age.d", n=s // 86400)


def since(obj, at):
    return None if at is None or obj.get("at") is None else obj["at"] - at


def context(value):
    if value is None:
        return "?"
    k = int(value / 1000.0 + 0.5)
    if k < 1000:
        return "%dk" % k
    m = ("%.1f" % (value / 1e6)).rstrip("0").rstrip(".")
    return "%sM" % m


def seconds(ms):
    return "?" if ms is None else "%.1f" % (ms / 1000.0)


def wall(value):
    return "?" if value is None else "%g" % value


def one(t, mid, n, **values):
    """The singular message for one, the plural for any other count, `?` included."""
    return t.text(mid + ".one" if n == 1 else mid, n=shown(n), **values)


def last_name(path):
    return "?" if not path else os.path.basename(str(path).rstrip("/")) or str(path)


def command(source):
    if not source:
        return "?"
    return " ".join(["agentik", shown(source.get("tool"))]
                    + [str(a) for a in seq(source.get("argv")) if a != "--json"])


def row(text, style=None, whole=False):
    return (text, style, whole)


def capped(t, rows, source):
    if len(rows) <= CAP:
        return rows
    more = t.text("status.more", n=len(rows) - (CAP - 1), command=command(source))
    return rows[:CAP - 1] + [row(more, DIM, True)]


# ---- the parts

def _fault(t, obj):
    """The read's own fault, said once, in the first part: rows never cut, and a warn mark."""
    fault = obj.get("fault")
    if fault is None:
        return []
    if fault == "bad_listing":
        return [row(t.text("status.fault.listing"), whole=True),
                row(t.text("status.fault.listing.parts"), whole=True)]
    return [row(t.text("status.fault.unknown", fault=shown(fault)), whole=True)]


def _watchers(t, obj, hand, slots):
    """The rows and the mark: `warn` for a hand, for the read's fault, or for a watcher the
    object does not say runs."""
    fault = _fault(t, obj)
    if "watchers" not in obj:
        return fault + [row(t.text("status.part.absent", part=t.text("status.label.watchers")))], "warn"
    watchers = seq(obj.get("watchers"))
    if not watchers:
        return fault + [row(t.text("status.watcher.none"))], "warn" if hand or fault else "note"
    rows = list(fault)
    for w in watchers:
        name, state = shown(w.get("name")), w.get("state")
        if state in ("missing", "hung"):
            if w.get("since") is not None:
                rows.append(row(t.text("status.watcher.%s.since" % state, name=name,
                                       when=when(w["since"]), age=age(t, since(obj, w["since"]))),
                                whole=True))
            else:
                rows.append(row(t.text("status.watcher." + state, name=name), whole=True))
            if w.get("start"):
                rows.append(row(t.text("status.watcher.start", start=w["start"]), DIM, True))
        elif state == "running":
            if w.get("beat_line"):
                rows.append(row(t.text("status.watcher.beat", name=name,
                                       age=age(t, since(obj, w.get("beat_at"))))))
                rows.append(row(w["beat_line"], DIM))
            else:
                rows.append(row(t.text("status.watcher.running", name=name)))
        elif state == "unknown":
            mid = "status.watcher.unchecked" if fault else "status.watcher.unknown"
            rows.append(row(t.text(mid, name=name), whole=True))
        else:
            rows.append(row(t.text("status.watcher.state", name=name, state=shown(state)), whole=True))
        if w.get("beat_writer") and w.get("writer") and w["beat_writer"] != w["writer"]:
            rows.append(row(t.text("status.watcher.writer", by=w["beat_writer"], writer=w["writer"])))
    running = all(w.get("state") == "running" for w in watchers)
    return rows, "warn" if hand or fault or not running else "ok"


def _helpers(t, helpers, skip_busy):
    counts = dict(mapping(helpers))
    words = [w for w in HELPER_ORDER if w in counts] + [w for w in counts if w not in HELPER_ORDER]
    parts = []
    for word in words:
        n = counts[word]
        if not n or (skip_busy and word == "busy"):
            continue
        if parts:
            parts.append(t.text("status.count", n=n, word=word))
        else:
            parts.append(one(t, "status.helpers", n, word=word))
    return parts


def _sessions(t, obj, part, hand, sources, slots):
    live = sorted(seq(part.get("live")), key=lambda s: (str(s.get("name") or ""), str(s.get("id") or "")))
    past = seq(part.get("past_window"))
    window = shown(part.get("window_min"))
    n = len(live) + len(past)
    busy = sum(mapping(s.get("helpers")).get("busy") or 0 for s in live)
    quiet = sum(mapping(s.get("helpers")).get("quiet") or 0 for s in live)
    head = [t.text("status.sessions.live", n=n) if n else t.text("status.sessions.none")]
    if busy:
        head.append(one(t, "status.helpers", busy, word="busy"))
    if quiet:
        head.append(t.text("status.count", n=quiet, word="quiet") if busy
                    else one(t, "status.helpers", quiet, word="quiet"))
    first = ", ".join(head)
    if part.get("ended"):
        first += "; " + t.text("status.sessions.ended", n=part["ended"], window=window)
    rows = []
    for s in live:
        ctx = context(s.get("context"))
        if s.get("window") is not None:
            ctx += "/" + context(s["window"])
        helpers = mapping(s.get("helpers"))
        waits = s.get("state") == "idle" and helpers.get("busy")
        state = one(t, "status.waits", helpers["busy"]) if waits else shown(s.get("state"))
        rest = _helpers(t, helpers, bool(waits))
        if rest:
            state += "; " + ", ".join(rest)
        rows.append(row([shown(s.get("name")), ctx, one(t, "status.turns", s.get("turns")), state]))
    for p in past:
        rows.append(row([shown(p.get("id"))[:8], "", "", t.text("status.past", window=window)]))
    rows = [row(first)] + capped(t, rows, _source(sources, "sessions"))
    if part.get("checked") is False and obj.get("fault") is None:  # a fault is said once, above
        rows.append(row(t.text("status.unchecked")))
    return rows


def _job(t, job):
    if job.get("label"):
        return t.text("status.job.label", name=shown(job.get("name")), label=job["label"])
    return shown(job.get("name"))


def _failed(t, job):
    text = t.text("status.job.failed")
    return t.text("status.cut", text=text, cut=job["cut"]) if job.get("cut") else text


def _gate(t, obj, part, hand, sources, slots):
    running, queued, red = (seq(part.get(k)) for k in ("running", "queued", "red"))
    alone = [h for h in hand if h.get("kind") == "no_runner"]
    head = []
    if running:
        head.append(t.text("status.gate.running.alone" if alone and not queued else "status.gate.running",
                           n=len(running)))
    if queued:
        head.append(t.text("status.gate.queued.alone" if alone else "status.gate.queued", n=len(queued)))
    first = ", ".join(head) or t.text("status.gate.idle")
    last = mapping(part.get("last"))
    if last:
        code = last.get("exit")
        mid = "unknown" if code is None else "passed" if code == 0 else "failed"
        text = t.text("status.gate." + mid, name=shown(last.get("name")))
        first += "; " + (t.text("status.cut", text=text, cut=last["cut"]) if last.get("cut") else text)
    rows = [row(first, whole=bool(alone))]
    if alone and alone[0].get("remedy"):
        rows.append(row(t.text("status.see", remedy=alone[0]["remedy"]), DIM, True))
    jobs = []
    for job in running:
        secs = job.get("seconds")
        took = age(t, secs)
        if job.get("est_s") is not None:
            took = t.text("status.job.of", seconds=took, est=age(t, job["est_s"]))
        jobs.append(row([t.text("status.job.running"), _job(t, job), took]))
    for job in queued:
        said = []
        if job.get("wait"):
            said.append(t.text("status.job.waits", wait=job["wait"]))
        if job.get("est_s") is not None:
            said.append(t.text("status.job.est", est=age(t, job["est_s"])))
        jobs.append(row([t.text("status.job.queued"), _job(t, job), "; ".join(said)]))
    for job in red:
        jobs.append(row([t.text("status.job.red"), _job(t, job), _failed(t, job)]))
    return rows + capped(t, jobs, _source(sources, "gate"))


def _covers(t, obj, part):
    covers = mapping(obj.get("covers"))
    rule, n = covers.get("rule"), part.get("checkouts")
    if rule == "cwd":
        return t.text("status.covers.cwd", name=last_name((seq(covers.get("checkouts")) or [None])[0]))
    if rule == "hq":
        return one(t, "status.covers.hq", n, hq=last_name(covers.get("hq")))
    if rule in ("checkouts", "args"):
        return one(t, "status.covers." + rule, n)
    return "?"


def _level(key):
    head = key.rstrip("0123456789")
    tail = key[len(head):]
    return (head, int(tail) if tail else -1, key)


def _backlog(t, obj, part, hand, sources, slots):
    rows = [row(one(t, "status.backlog.open", part.get("open"), covers=_covers(t, obj, part)))]
    first = mapping(part.get("first"))
    if first:
        rows.append(row(t.text("status.backlog.first", n=shown(first.get("n")), title=shown(first.get("title")))))
    items = dict(mapping(part.get("items")))
    unplaced = items.pop("unplaced", None)
    said = ["%s %s" % (k, shown(items[k])) for k in sorted(items, key=_level)]
    if unplaced:
        said.append(t.text("status.backlog.unplaced", n=unplaced))
    if said:
        rows.append(row(t.text("status.backlog.items", items=", ".join(said))))
    if seq(part.get("skipped")):
        names = ", ".join(last_name(p) for p in part["skipped"])
        rows.append(row(t.text("status.backlog.skipped", names=names)))
    return rows


def _runs(t, obj, part, hand, sources, slots):
    shown_runs = seq(part.get("shown"))
    if not shown_runs:
        return [row(t.text("status.runs.none"))]
    gone = [h for h in hand if h.get("kind") == "run_gone"]
    rows = []
    for r in shown_runs:
        by, run = shown(r.get("by")), shown(r.get("run"))
        entry = _gone(gone, r)
        if entry:
            rows.append(row(t.text("status.run.gone", by=by, run=run, pid=shown(r.get("pid"))), whole=True))
            if entry.get("remedy"):
                rows.append(row(t.text("status.see", remedy=entry["remedy"]), DIM, True))
            continue
        text = t.text("status.run", by=by, run=run, state=shown(r.get("state")))
        if r.get("row"):
            text = t.text("status.run.row", text=text, row=r["row"])
        if r.get("age_s") is not None:
            text = t.text("status.run.age", text=text, age=age(t, r["age_s"]))
        counts = [t.text("status.count", n=n, word=w) for w, n in mapping(r.get("rows")).items() if n]
        if counts:
            text += "; " + ", ".join(counts)
        rows.append(row(text))
    return rows


def _gone(gone, r):
    """The `run_gone` entry of `hand` for this run: its id and its tool together, the tool read
    from the entry's `tool` and matched to the run's `by` where the entry gives one. A run the
    object says is alive is never gone."""
    if r.get("alive") is True:
        return None
    return next((h for h in gone if h.get("name") == r.get("run")
                 and h.get("tool", r.get("by")) == r.get("by")), None)


def _source(sources, name):
    return next((s for s in sources if s.get("name") == name), None)


def _gave_nothing(t, sources, whole):
    """The rows of the part's sources that gave nothing; `whole` when the part is not read."""
    rows = []
    for s in sources:
        state, which = s.get("state"), shown(s.get("tool"))  # another tool's name
        if state == "not installed" and whole:
            rows.append(row(t.text("status.source.absent", tool=which)))
        elif state == "timed out":
            rows.append(row(t.text("status.source.slow", tool=which, wall=wall(s.get("wall_s")))))
        elif state == "unreadable":
            cmd = " ".join(["agentik-" + which] + [str(a) for a in seq(s.get("argv")) if a != "--json"])
            failed = s.get("exit") not in (0, None)
            rows.append(row(t.text("status.source.failed" if failed else "status.source.nojson", command=cmd)))
            if s.get("stderr"):
                rows.append(row(s["stderr"], whole=True))
        elif state == "changed":
            rows.append(row(t.text("status.source.changed", tool=which)))
    if whole and not rows:
        rows.append(row(t.text("status.source.none")))
    return rows


BUILD = {"sessions": _sessions, "gate": _gate, "backlog": _backlog, "runs": _runs}


def part(t, obj, name, slots):
    """One of the five parts: its mark, its label and its rows, behind one guard, so a value of
    the wrong kind or a time out of range makes this part read not read and the others draw."""
    label = t.text("status.label." + name)
    try:
        mark, rows = _part(t, obj, name, slots, label)
    except WRONG:
        mark, rows = "warn", [row(t.text("status.wrong", part=label))]
    t.grid(mark, label, rows)


def _part(t, obj, name, slots, label):
    hand = [h for h in entries(obj, "hand") if h.get("part") == name]
    sources = [s for s in entries(obj, "sources") if s.get("name") in SOURCES[name]]
    if name == "watchers":
        rows, mark = _watchers(t, obj, hand, slots)
        return mark, rows
    p = mapping(obj.get(name))
    state = p.get("state")
    note = state in ("partial", "not read")
    if name == "backlog" and mapping(obj.get("covers")).get("rule") == "none":
        rows, note = [row(t.text("status.backlog.nowhere", status=slots["status"]))], True
    elif name not in obj:
        rows = [row(t.text("status.part.absent", part=label))]
    elif state is None:
        rows = [row(t.text("status.part.stateless", part=label))]
    elif state not in STATES:
        rows = [row(t.text("status.part.unknown", part=label, state=shown(state)))]
    elif state == "not read":
        rows = _gave_nothing(t, sources, True)
    else:
        rows = BUILD[name](t, obj, p, hand, sources, slots) + _gave_nothing(t, sources, False)
    said = state == "ok" or note  # read whole, or said to be read in part or not at all
    return "warn" if hand or not said else "note" if note else "ok", rows


def foot(t, obj, slots):
    """The two last labels, with no mark, each behind its guard, and the hint."""
    label = t.text("status.label.sources")
    try:
        rows = _sources(t, obj)
    except WRONG:
        rows = [row(t.text("status.wrong", part=label), DIM)]
    t.grid(None, label, rows)
    label = t.text("status.label.not_read")
    try:
        rows = _not_read(t, obj)
    except WRONG:
        rows = [row(t.text("status.wrong", part=label), DIM)]
    if rows:
        t.grid(None, label, rows)
    try:
        hint = _hint(obj, slots)
    except WRONG:
        hint = None
    if hint:
        t.hint(*hint)


def _sources(t, obj):
    sources = entries(obj, "sources")
    read = [s for s in sources if s.get("state") in READ]
    if read:
        slow = max(read, key=lambda s: s.get("ms") if s.get("ms") is not None else -1)
        rows = [row(t.text("status.sources.read", n=len(read), s=seconds(obj.get("ms")),
                           tool=shown(slow.get("tool")), slow=seconds(slow.get("ms"))), DIM)]
    else:
        rows = [row(t.text("status.sources.none"), DIM)]
    absent = sorted({"agentik-%s" % shown(s.get("tool")) for s in sources if s.get("state") == "not installed"})
    if absent:
        rows.append(row(t.text("status.sources.absent", names=", ".join(absent)), DIM))
    for s in sources:
        if s.get("state") == "not drawn":
            rows.append(row(t.text("status.sources.undrawn", tool=shown(s.get("tool")), name=shown(s.get("name"))),
                            DIM))
    return rows


def _not_read(t, obj):
    words = []
    for w in seq(obj.get("not_read")):
        if not isinstance(w, str):
            raise Wrong(w)
        words.append(t.messages.get("status.not_read." + w) or w)
    return [row(", ".join(words), DIM)] if words else []


def _hint(obj, slots):
    """The hint's id and its values, or None."""
    hand = entries(obj, "hand")
    if hand:
        remedy = next((h["remedy"] for h in hand if h.get("remedy")), None)
        mid = "hint.status.hand" + (".one" if len(hand) == 1 else "") + ("" if remedy else ".bare")
        return mid, {"n": len(hand), "remedy": remedy}
    if any(s.get("state") in GAVE_NOTHING for s in entries(obj, "sources")):
        return "hint.status.doctor", {"doctor": slots["doctor"]}
    return None


def draw(t, obj, slots):
    """The whole screen: the five parts in order, then the foot."""
    for name in PARTS:
        part(t, obj, name, slots)
    foot(t, obj, slots)
