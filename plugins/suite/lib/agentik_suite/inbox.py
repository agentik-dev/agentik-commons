"""`inbox`: one list of what waits on the owner across every checkout (packet in4-inbox).

The checkouts are covers.covers' (design P13's one rule), with a second naming of one folder on
the command line dropped and an entry of the user file's list that is neither absolute nor under
`~/` left out with a note. Three reads, by name: `questions` and `charter`, one call each with
every checkout after the argv, and `backlog`, one call a checkout; each is found in the fallback
table's `inbox` list of a row whose tool is on PATH, else among the `status` reads of the other
tools' describe answers, and all run at once under one wall of WALL seconds. What waits: each open
question, each line of a charter's Waits part, each build-order step waiting on the owner.

It is a read: it writes nothing but the describe cache, starts no process but a listed tool's,
asks nothing, never loops, opens no file in a checkout and runs no git. A checkout's name, path
and contents reach it at run time, from the command line, the user file and the tools' answers.
"""
import datetime
import json
import os
import re
import time

from . import covers as covering, plan, settings, status, term, tools

WALL = 5.0
READS = ("questions", "backlog", "charter")
TABLE = "inbox"  # the fallback table's list of a row's inbox reads
NUMBER = re.compile(r"[1-9][0-9]*\Z")  # ASCII digits with no leading zero
STATES = ("open", "answered", "unreadable")
Q_KEYS = ("n", "title", "line", "state", "why", "proposed", "recommended", "text")
C_KEYS = ("repo", "file", "name", "mtime", "closed", "next_act", "waits")
S_KEYS = ("n", "title", "line", "level", "state")
DAY = re.compile(r"(\d{4})-(\d\d)-(\d\d)")
RULE = {"args": "inbox.covers.args", "checkouts": "inbox.covers.user", "hq": "inbox.covers.hq",
        "cwd": "inbox.covers.cwd"}
INDENT = 3  # a block's rows


def number(noun):
    return bool(NUMBER.match(noun))


# ---- the two seams' work: which checkouts, and which reads --------------------------------------

def _covers(cmd, paths, notes):
    """covers.covers' {rule, hq, checkouts}, less a second naming of one folder on the command
    line and less an entry of the user file's list that is neither absolute nor under `~/` (each
    one named in `notes`); a list with none left falls to the next rule. A settings.Fault for a
    user file outside the subset."""
    cov = covering.covers(cmd.env, cmd.cwd, paths)
    rule, found = cov["rule"], cov["checkouts"]
    if rule == "args":
        seen, kept = set(), []
        for path in found:
            if os.path.realpath(path) not in seen:
                seen.add(os.path.realpath(path))
                kept.append(path)
        found = kept
    elif rule == "checkouts":
        notes.extend(p for p in found if not os.path.isabs(p))
        found = [p for p in found if os.path.isabs(p)]
        if not found:
            repo = covering._repo(cmd.cwd)
            beside = covering._hq_folder(repo) if repo else None
            rule, found = ("hq", beside) if beside else ("cwd", [repo]) if repo else ("none", [])
    hq = next((c for c in found if os.path.isdir(c) and covering.declares_hq(c)), None)
    return {"rule": rule, "hq": hq, "checkouts": found}


def _listed(reads):
    for read in reads if isinstance(reads, list) else ():
        if isinstance(read, dict) and isinstance(read.get("name"), str) and isinstance(read.get("argv"), list) \
                and all(isinstance(w, str) for w in read["argv"]):
            yield read["name"], list(read["argv"])


def _reads(cmd):
    """{read: {tool, exe, argv}}: first each row of the fallback table whose tool is on PATH, by
    name, its `inbox` list; then, for a read still not found, the `status` reads of the other
    tools on PATH by name, from their describe answers (cache and wall: tools.describe_all). A
    tool with a row is never asked describe."""
    on_path = {e["name"][len("agentik-"):]: e["path"] for e in cmd._on_path()}
    own = cmd.tool[len("agentik-"):] if cmd.tool.startswith("agentik-") else cmd.tool
    table, found = tools.fallback(cmd.lib), {}
    for name in sorted(table):
        for read, argv in _listed(table[name].get(TABLE)) if name in on_path else ():
            if read in READS and read not in found:
                found[read] = {"tool": name, "exe": on_path[name], "argv": argv}
    asked = [{"name": n, "exe": on_path[n]} for n in sorted(on_path)
             if n not in table and n != own and tools.NAME.match(n)]
    if asked and any(r not in found for r in READS):
        answers = tools.describe_all(asked, cmd.env)[0]
        for entry in asked:
            answer = answers.get(entry["name"], (None, None))[1] or {}
            for read in answer.get("reads") or ():
                name = read.get("name")
                if read.get("kind") == "status" and name in READS and name not in found:
                    found[name] = {"tool": entry["name"], "exe": entry["exe"], "argv": list(read["argv"])}
    return found


# ---- an answer held to R3's object --------------------------------------------------------------

def _has(obj, keys):
    return isinstance(obj, dict) and all(k in obj for k in keys)


def _int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _schema(obj, name):
    m = re.match(r"agentik\.%s/([0-9]+)\Z" % name, obj.get("schema") or "") \
        if isinstance(obj.get("schema"), str) else None
    return bool(m) and int(m.group(1)) <= 1 and obj.get("ok") is True


def _day(text):
    m = DAY.match(text) if isinstance(text, str) else None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None
    except ValueError:
        return None


def _when(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and abs(value) < float("inf"):
        return float(value)
    return status.when(value) if isinstance(value, str) else None


def _skips(obj):
    return isinstance(obj.get("skipped"), list) and all(
        _has(s, ("repo", "why")) and isinstance(s["repo"], str) for s in obj["skipped"])


def _questions(obj):
    if not (_has(obj, ("repos", "skipped")) and _schema(obj, "questions") and isinstance(obj["repos"], list)
            and _skips(obj)):
        return False
    for r in obj["repos"]:
        if not (_has(r, ("repo", "file", "questions", "answered", "decided")) and isinstance(r["repo"], str)
                and isinstance(r["questions"], list) and _has(r["decided"], ("count", "newest"))
                and _int(r["decided"]["count"])):
            return False
        for q in r["questions"]:
            if not (_has(q, Q_KEYS) and _int(q["n"]) and q["state"] in STATES):
                return False
            if q["state"] == "open" and _day(q["proposed"]) is None:
                return False
    return True


def _charter(obj):
    if not (_has(obj, ("repos", "skipped")) and _schema(obj, "charter") and isinstance(obj["repos"], list)
            and _skips(obj)):
        return False
    for r in obj["repos"]:
        if not (_has(r, C_KEYS) and isinstance(r["repo"], str) and _when(r["mtime"]) is not None):
            return False
        if r["waits"] is not None and not (isinstance(r["waits"], list) and all(
                _has(w, ("line", "what", "command")) for w in r["waits"])):
            return False
    return True


def _backlog(obj):
    if not (_has(obj, ("repos", "skipped")) and isinstance(obj["repos"], list)
            and isinstance(obj["skipped"], list) and all(isinstance(s, str) for s in obj["skipped"])):
        return False
    for r in obj["repos"]:
        if not (_has(r, ("repo", "handoff", "steps")) and isinstance(r["repo"], str) and isinstance(r["steps"], list)):
            return False
        for s in r["steps"]:
            if not (_has(s, S_KEYS) and (s["state"] is None or _has(s["state"], ("word", "on", "text")))):
                return False
    return True


SHAPES = {"questions": _questions, "charter": _charter, "backlog": _backlog}


def _settle(call, result):
    """The call's state, `ok` or one of R7's, and its answer."""
    code, out, state = result
    call["exit"] = code
    if state == "timed out":
        call["state"] = "timed_out"
        return
    if state == "ran" and code != 0:
        call["state"] = "no_answer"
        return
    try:
        answer = json.loads(out.decode("utf-8", "replace")) if state == "ran" else None
    except (ValueError, RecursionError):
        answer = None
    if isinstance(answer, dict) and SHAPES[call["name"]](answer):
        call["state"], call["answer"] = "ok", answer
    else:  # exit 0 and no R3 object, or past tools.CAP, or it could not start
        call["state"] = "unknown"


# ---- the read ----------------------------------------------------------------------------------

def _rel(path, repo):
    """A path from the checkout, where it is under it."""
    if not isinstance(path, str):
        return path
    if os.path.isabs(path):
        top, real = os.path.realpath(repo), os.path.realpath(path)
        if real.startswith(top.rstrip("/") + "/"):
            return os.path.relpath(real, top)
    return path


def _by_repo(entries):
    found = {}
    for e in entries:
        found.setdefault(os.path.realpath(e["repo"] if isinstance(e, dict) else e), e)
    return found


def _checkout(path):
    co = {"repo": path, "name": os.path.basename(path.rstrip("/")) or path, "read": True, "why": None,
          "skipped": {}, "questions": [], "hands": None, "rows": [], "sitting": None, "decided": None,
          "answered": None, "unread": []}
    if not os.path.isdir(path):
        co["read"], co["why"] = False, "notdir"
    else:
        try:
            os.listdir(path)
        except OSError:
            co["read"], co["why"] = False, "denied"
    return co


def _call(name, found, repo, argv_tail):
    r = found[name]
    return {"name": name, "tool": r["tool"], "exe": r["exe"], "argv": r["argv"], "tail": argv_tail,
            "repo": repo, "state": None, "exit": None, "answer": None}


def read(cmd, cov, found):
    """(checkouts, calls): every checkout with what each read gave it, and every call made, or
    one `no_tool` entry for a read no command gives."""
    cos = [_checkout(p) for p in cov["checkouts"]]
    ready = [co for co in cos if co["read"]]
    calls = []
    for name in READS:
        if name not in found:
            calls.append({"name": name, "tool": None, "exe": None, "argv": None, "tail": [], "repo": None,
                          "state": "no_tool", "exit": None, "answer": None})
        elif ready and name == "backlog":
            calls.extend(_call(name, found, co["repo"], [co["repo"]]) for co in ready)
        elif ready:
            calls.append(_call(name, found, None, [co["repo"] for co in ready]))
    jobs = [(i, [c["exe"]] + c["argv"] + c["tail"]) for i, c in enumerate(calls) if c["state"] is None]
    if jobs:
        results = tools.run_all(jobs, cmd.env, deadline=time.monotonic() + WALL)
        for i, _ in jobs:
            _settle(calls[i], results.get(i, (None, b"", "timed out")))
    for co in ready:
        real = os.path.realpath(co["repo"])
        for call in calls:
            if call["repo"] is not None and os.path.realpath(call["repo"]) != real:
                continue
            if call["state"] != "ok":
                co["unread"].append(call["name"])
                continue
            answer = call["answer"]
            entry = _by_repo(answer["repos"]).get(real)
            if entry is None:
                skipped = _by_repo(answer["skipped"]).get(real)
                if skipped is not None:
                    co["skipped"][call["name"]] = skipped.get("why") if isinstance(skipped, dict) else None
                continue
            _take(co, call["name"], entry)
    return cos, calls


def _take(co, name, entry):
    repo = co["repo"]
    if name == "questions":
        co["answered"], co["decided"] = entry["answered"], entry["decided"]
        co["questions"] = [{"n": q["n"], "title": q["title"], "state": q["state"], "why": q["why"],
                            "recommended": q["recommended"], "proposed": q["proposed"],
                            "file": _rel(entry["file"], repo), "line": q["line"],
                            "waits": q["state"] == "open", "text": q["text"]} for q in entry["questions"]]
    elif name == "charter":
        co["sitting"] = {"charter": entry["name"], "mtime": entry["mtime"], "closed": entry["closed"],
                         "next_act": entry["next_act"]}
        if entry["waits"] is not None:
            co["hands"] = [{"what": w["what"], "command": w["command"], "file": _rel(entry["file"], repo),
                            "line": w["line"]} for w in entry["waits"]]
    else:
        co["rows"] = [{"n": s["n"], "title": s["title"], "text": s["state"]["text"],
                       "file": _rel(entry["handoff"], repo), "line": s["line"], "level": s["level"]}
                      for s in entry["steps"] if isinstance(s["state"], dict)
                      and s["state"]["word"] == "waiting" and s["state"]["on"] == "the owner"]


def _count(co):
    return sum(1 for q in co["questions"] if q["waits"]) + len(co["hands"] or ()) + len(co["rows"])


# ---- the words ---------------------------------------------------------------------------------

def _age(t, mtime, now):
    secs = max(0.0, now - (_when(mtime) or now))
    if secs < 3600:
        return t.text("inbox.age.min", n=int(secs // 60))
    if secs < 48 * 3600:
        return t.text("inbox.age.h", n=int(secs // 3600))
    return t.text("inbox.age.d", n=int(secs // 86400))


def _asked(t, proposed, now):
    day = _day(proposed)
    days = (datetime.date.fromtimestamp(now) - day).days if day else 0
    return t.text("inbox.age.today") if days <= 0 else t.text("inbox.age.d", n=days)


def _command(call):
    return " ".join([os.path.basename(call["exe"])] + call["argv"]) if call["exe"] else None


def _wall():
    return int(WALL) if float(WALL).is_integer() else WALL


def _unanswered(t, calls, cos):
    """The texts of R7's rows, in READS' order: `backlog`'s once where every call ended in one
    state, else once for each checkout whose call gave none."""
    names = {os.path.realpath(co["repo"]): co["name"] for co in cos}
    texts = []
    for name in READS:
        mine = [c for c in calls if c["name"] == name]
        bad = [c for c in mine if c["state"] != "ok"]
        if not bad:
            continue
        once = name != "backlog" or (len(bad) == len(mine) and len({c["state"] for c in bad}) == 1)
        for c in bad[:1] if once else bad:
            word = name if once or c["repo"] is None else t.text(
                "inbox.read.where", read=name, name=names.get(os.path.realpath(c["repo"]), c["repo"]))
            texts.append(t.text("inbox.read." + c["state"], read=word, command=_command(c), exit=c["exit"],
                                wall=_wall()))
    return texts


def _hand_what(h):
    what = h["what"] if isinstance(h["what"], str) else ""
    return what[2:] if h["command"] is None and what.startswith("- ") else what


def _shown(value):
    return "" if value is None else value


def _head(t, co):
    if not co["read"]:
        return "note", t.text("inbox.repo.unread", why=t.text("inbox.why." + co["why"]))
    n = _count(co)
    if n:
        return "warn", t.text("inbox.repo.waits.one") if n == 1 else t.text("inbox.repo.waits", n=n)
    if co["unread"]:
        return "note", t.text("inbox.repo.partial")
    return "ok", t.text("inbox.repo.none")


def _rows(t, co, now):
    """The block's rows: (kind, text, after, dim), questions first, then hands, rows, sitting, decided."""
    rows = []
    for q in co["questions"]:
        if q["state"] == "open":
            after = t.text("inbox.question.open", label=_shown(q["recommended"]), age=_asked(t, q["proposed"], now))
        elif q["state"] == "answered":
            after = t.text("inbox.question.answered")
        else:
            after = t.text("inbox.question.unreadable", why=_shown(q["why"]))
        rows.append((t.text("inbox.kind.question", n=q["n"]), _shown(q["title"]), after, False))
    for h in co["hands"] or ():
        if h["command"] is None:
            after = t.text("inbox.hand.bare", file=_shown(h["file"]), line=_shown(h["line"]))
        else:
            after = t.text("inbox.hand.run", command=h["command"])
        rows.append((t.text("inbox.kind.hand"), _hand_what(h), after, False))
    for r in co["rows"]:
        rows.append((t.text("inbox.kind.row", n=r["n"]), _shown(r["text"]),
                     t.text("inbox.row.holds", title=_shown(r["title"])), False))
    s = co["sitting"]
    if s is not None:
        values = {"charter": _shown(s["charter"]), "age": _age(t, s["mtime"], now), "word": _shown(s["next_act"])}
        mid = "inbox.sitting.closed" if s["closed"] else "inbox.sitting.nopart" if co["hands"] is None \
            else "inbox.sitting"
        rows.append((t.text("inbox.kind.sitting"), t.text(mid, **values), None, True))
    d = co["decided"]
    if d is not None and d["count"] > 0:
        rows.append((t.text("inbox.kind.decided"), t.text("inbox.decided", count=d["count"],
                                                          newest=_shown(d["newest"])), None, True))
    return rows


def _check_lines(t, unanswered, cos):
    lines = [t.text("inbox.check.read", what=w) for w in unanswered]
    for co in cos:
        name = co["name"]
        if not co["read"]:
            lines.append(t.text("inbox.check.unread", name=name, why=t.text("inbox.why." + co["why"])))
            continue
        for q in co["questions"]:
            if q["waits"]:
                lines.append(t.text("inbox.check.question", name=name, n=q["n"], title=_shown(q["title"]),
                                    label=_shown(q["recommended"])))
        for h in co["hands"] or ():
            if h["command"] is None:
                lines.append(t.text("inbox.check.hand.bare", name=name, what=_hand_what(h), file=_shown(h["file"]),
                                    line=_shown(h["line"])))
            else:
                lines.append(t.text("inbox.check.hand", name=name, what=_hand_what(h), command=h["command"]))
        for r in co["rows"]:
            lines.append(t.text("inbox.check.row", name=name, n=r["n"], text=_shown(r["text"])))
    return lines


# ---- the verb ----------------------------------------------------------------------------------

def do_inbox(cmd, nouns):
    """`inbox [REPO...] [NUMBER...] [--check] [--json]` (packet in4-inbox R2 to R14)."""
    o, t, Refusal = cmd.opts, cmd.t, cmd.Refusal
    home = cmd.env.get("HOME")
    numbers = [k for k, noun in enumerate(nouns) if number(noun)]
    if o["check"] and numbers:
        raise Refusal("two_answers", "err.inbox.both", cmd.again({cmd.at[k + 1]: [] for k in numbers}))
    notes = []
    try:
        cov = _covers(cmd, [n for n in nouns if not number(n)], notes)
    except settings.Fault as f:
        fault = t.text("config.fault" if f.line else "config.fault.noline",
                       path=plan.shown(f.path, home), line=f.line, why=f.why)
        raise Refusal("bad_file", "err.inbox.file", None, fault=fault)
    user = plan.shown(settings.user_path(cmd.env), home)
    if cov["rule"] == "none":
        raise Refusal("no_checkout", "err.inbox.nowhere", cmd.say("help", "inbox"), path=user)
    found = _reads(cmd)
    if not found:
        raise Refusal("no_reads", "err.inbox.tools", cmd.say("setup"), exit_code=3)
    if notes and not (t.quiet or o["check"]):
        t.table([("note", [t.text("inbox.note.entry", entry=n, path=user)], None) for n in notes],
                err=True, indent=0)
    cos, calls = read(cmd, cov, found)
    now = time.time()
    count = sum(_count(co) for co in cos if co["read"])
    complete = all(c["state"] == "ok" for c in calls) and all(co["read"] for co in cos)
    unanswered = _unanswered(t, calls, cos)
    obj = {"schema": "agentik.inbox/1", "ok": True, "covers": cov, "count": count, "complete": complete,
           "reads": [{"name": c["name"], "tool": c["tool"], "state": c["state"], "exit": c["exit"],
                      "repo": c["repo"]} for c in calls],
           "checkouts": [{k: co[k] for k in ("repo", "name", "read", "why", "skipped", "hands", "rows",
                                            "sitting", "decided", "answered")}
                         for co in cos]}
    for shown, co in zip(obj["checkouts"], cos):
        shown["questions"] = [{k: q[k] for k in ("n", "title", "state", "why", "recommended", "proposed",
                                                 "file", "line", "waits")} for q in co["questions"]]
    if numbers:
        return _opened(cmd, nouns, numbers, cos, obj, now)
    if o["check"]:
        lines = _check_lines(t, unanswered, cos)
        if o["json"]:
            t.json(dict(obj, check=True, lines=lines))
        else:
            for line in lines:
                t.line("inbox.open.line", text=line)
        return 1 if lines else 0
    if o["json"]:
        t.json(obj)
        return 0
    _list(cmd, cov, cos, unanswered, count, complete, now)
    first = next((q["n"] for co in cos for q in co["questions"] if q["waits"]), None)
    if unanswered:
        t.hint("hint.inbox.doctor", **cmd.slots())
    elif cov["rule"] == "cwd":
        t.hint("hint.inbox.checkouts", path=user)
    elif first is not None:
        t.hint("hint.inbox.open", n=first, command=cmd.again({cmd.at[0]: ["inbox", str(first)]}))
    return 0


def _list(cmd, cov, cos, unanswered, count, complete, now):
    t = cmd.t
    where = t.text("inbox.checkouts.one") if len(cos) == 1 else t.text("inbox.checkouts", m=len(cos))
    hq = os.path.basename((cov["hq"] or "").rstrip("/"))
    covers = t.text(RULE[cov["rule"]], name=hq)
    if count:
        mid = "inbox.title" if complete else "inbox.title.partial"
    else:
        mid = "inbox.title.none" if complete else "inbox.title.partial.none"
    t.line(mid, n=count, checkouts=where, covers=covers)
    t.table([("note", [t.text("inbox.kind.unread"), text], None) for text in unanswered], indent=0)
    ellipsis = "…" if t.out.glyphs else "..."
    for co in cos:
        t.blank()
        mark, text = _head(t, co)
        t.table([(mark, [term.name(co["name"]), text], None)], indent=0)
        rows = _rows(t, co, now) if co["read"] else []
        if not rows:
            continue
        lead = INDENT + max(len(r[0]) for r in rows) + len(term.GAP)
        table = []
        for kind, text, after, dim in rows:
            if dim:
                if t.out.tty:  # a sitting's last word ends one column short of the width
                    room = t.out.width() - 1 - lead
                    if term.columns(text) > room > 0:
                        text = term.fit(text, room, ellipsis)
                table.append((None, [term.path(kind), term.path(text)], None))
            else:
                table.append((None, [kind, text], after))
        t.table(table, indent=INDENT)


def _opened(cmd, nouns, numbers, cos, obj, now):
    """R12: each checkout read that holds a question of each number given, its block as written."""
    t = cmd.t
    held = {}
    for k in numbers:
        n = int(nouns[k])
        held[k] = [(co, q) for co in cos if co["read"] for q in co["questions"] if q["n"] == n]
    missing = [k for k in numbers if not held[k]]
    if missing:
        raise cmd.Refusal("unknown_number", "err.inbox.number", cmd.again({cmd.at[k + 1]: [] for k in missing}),
                          n=nouns[missing[0]])
    opened = [(co, q) for k in numbers for co, q in held[k]]
    if cmd.opts["json"]:
        t.json(dict(obj, opened=[{"repo": co["repo"], "name": co["name"], "n": q["n"], "state": q["state"],
                                  "text": q["text"], "file": q["file"], "line": q["line"]} for co, q in opened]))
        return 0
    for i, (co, q) in enumerate(opened):
        if i:
            t.blank()
        t.table([(None, [term.name(co["name"]), t.text("inbox.open.title", n=q["n"], state=q["state"],
                                                        age=_asked(t, q["proposed"], now))], None)], indent=0)
        t.blank()
        for line in (q["text"] if isinstance(q["text"], str) else "").splitlines():
            t.line("inbox.open.line", text=line)
        t.blank()
        t.line("inbox.open.answer", file=_shown(q["file"]), line=_shown(q["line"]))
        t.line("inbox.open.sitting", name=co["name"])
    return 0
