"""`doctor`: the machine checked in one read, grouped by tool, the suite's group first.

The suite's checks, in order: the door (the first `agentik` on PATH that is a regular executable
file, its VERSION against the door this command ships), a shadow (an `agentik-<word>` on PATH
whose word the door would hand to it in place of the suite's verb), the user settings file, and
the setup plan's steps 1 to 6, one check a row. Then each listed tool's own checks: every one
is asked `doctor --json` at once, and a tool whose answer is not the contract's (§5) is asked
plain `doctor` in a second round, both under one deadline of DEADLINE seconds (row sc10). A check
is {name, status, detail, remedy}; the status is ok, note, warn or fail; exit 1 when one is fail,
else 0. The screen is a line a group, a row for each check that fails or warns, and a close that
names at most one command. It reads no cache, runs no `describe` and no `claude`, and writes
nothing itself; a tool's own doctor may write its state.

Each group carries `source`, the finder's row (row fk2b-reads), null for the suite. What a source
that is not the marketplace's own gives (its id, marketplace, folder, version) stands in no check's
name, detail or remedy: the `from`, `seen`, `runs` and `passed over` lines under a group are made
from `source` at print time, and the checks name a step by its tool.
"""
import json
import os
import re
import time

import agentik_install

from . import apply, plan, prog, settings, sources, status, tools

DEADLINE = 30.0
RESERVED = ("remove", "update", "init", "completion", "inbox")
STATE = {"ok": "ok", "todo": "warn", "blocked": "fail"}
STATUSES = ("ok", "note", "warn", "fail")
SCHEMA = "agentik.doctor/1"
KEYS = ("name", "status", "detail", "remedy")
FACT = {"setup.cmd.missing": "doctor.plan.path", "setup.path.missing": "doctor.plan.path",
        "setup.python.low": "doctor.plan.python", "setup.market.missing": "doctor.plan.market",
        "setup.plugin.missing": "doctor.plan.plugin", "setup.plugin.broken": "doctor.plan.broken",
        "setup.launcher.behind": "doctor.plan.behind", "setup.suite.behind": "doctor.plan.behind",
        "setup.launcher.unread": "doctor.plan.unread", "setup.suite.unread": "doctor.plan.unread",
        "setup.plugin.declared": "doctor.plan.declared", "setup.plugin.gone": "doctor.plan.gone",
        "setup.launcher.earlier": "doctor.plan.earlier", "setup.launcher.other": "doctor.plan.other"}
# A held row (fk2-plan R4) in doctor's words, whose remedy is the card that shows how to choose.
HELD = {"setup.plugin.held": "doctor.source.undecided", "setup.plugin.held.twice": "doctor.source.twice",
        "setup.plugin.held.repo": "doctor.source.repo"}
FACT.update(HELD)
# An ok row of a source not the marketplace's own whose plan words hold the source's version.
SOURCE_OK = {"setup.plugin.source": "doctor.plan.source", "setup.plugin.source.none": "doctor.plan.source",
             "setup.launcher.ok": "doctor.plan.launcher"}
SAID = ("value", "ignored", "self", "relative")  # the config read's warnings the doctor shows (R4)


class _Blank(dict):
    """The settings' summaries the doctor does not print: each is empty."""

    def __missing__(self, key):
        return ""


def _check(name, state, detail, remedy=None):
    return {"name": name, "status": state, "detail": detail, "remedy": remedy}


first_door = prog.first_door  # moved to prog, where the command's form reads it (row sc2)


def door(cmd, on_path):
    t, home = cmd.t, cmd.env.get("HOME")
    setup = cmd.say("setup")
    path = first_door(cmd.env)
    if path is None:
        return _check("door", "warn", t.text("doctor.door.none"), setup)
    shown = plan.shown(path, home)
    want = (agentik_install.read_launcher(agentik_install._source()[2]) or {}).get("version")
    have = (agentik_install.read_launcher(path) or {}).get("version")
    a, b = agentik_install.order(have), agentik_install.order(want)
    if a is None or b is None:
        return _check("door", "warn", t.text("doctor.door.unread", path=shown, have=have or "none",
                                             want=want or "none"))
    if a >= b:
        return _check("door", "ok", t.text("doctor.door.ok", path=shown, have=have, want=want))
    if any(f["name"] == cmd.tool for f in on_path):
        return _check("door", "fail", t.text("doctor.door.behind", path=shown, have=have, want=want),
                      cmd.say("install-cli"))
    return _check("door", "warn", t.text("doctor.door.old", path=shown, have=have, want=want), setup)


def shadow(cmd, on_path):
    words = set(cmd.VERBS) | set(RESERVED)
    found = []
    for f in on_path:
        word = f["name"][len("agentik-"):]
        if word in words:
            found.append(_check("shadow", "fail", cmd.t.text("doctor.shadow.hit", path=f["path"],
                                                             word=word)))
    return found or [_check("shadow", "ok", cmd.t.text("doctor.shadow.ok"))]


def user_settings(cmd):
    home = cmd.env.get("HOME")
    try:
        path, found, unchecked = status.declared(cmd.env)
    except settings.Fault as f:
        fault = cmd.t.text("config.fault" if f.line else "config.fault.noline",
                           path=plan.shown(f.path, home), line=f.line, why=f.why)
        return [_check("settings", "fail", fault)]
    shown = plan.shown(path, home)
    if unchecked:
        return [_check("settings", "warn", cmd.t.text("doctor.settings.unchecked", name=name, path=shown))
                for name in unchecked]
    if not os.path.exists(path):
        return [_check("settings", "ok", cmd.t.text("doctor.settings.none", path=shown))]
    return [_check("settings", "ok", cmd.t.text("doctor.settings.ok", path=shown))]


def source_settings(cmd):
    """The warns of the `sources` lines (R4, R5): each config-read warning of a reason in SAID,
    with its file and line; and, while the user file holds a line and is on no gate list, the
    gate warn, the line to add kept under `add`, which --json cuts away. A file that does not
    parse is user_settings' fail, so nothing here."""
    t, env, home = cmd.t, cmd.env, cmd.env.get("HOME")
    try:
        cwd = os.getcwd()
    except OSError:
        cwd = None
    try:
        lines, _ = settings.declared(env)
        body = settings.resolve(env, cwd, _Blank())
    except settings.Fault:
        return []
    found = []
    for w in body["warnings"]:
        if w.get("reason") in SAID:
            at = plan.shown(str(w.get("path")), home)
            if w.get("line"):
                at = "%s:%s" % (at, w["line"])
            found.append(_check("settings", "warn", t.text("doctor.settings." + w["reason"],
                                                           key=w.get("key"), at=at)))
    if lines:
        config, user = sources.config_dir(env), settings.user_path(env)
        if apply.gated(config, home, t, user) == (None, None):
            c = _check("sources", "warn", t.text("doctor.sources.gate", path=plan.shown(user, home)))
            c["add"] = t.text("doctor.sources.add", path=plan.shown(user, home),
                              list=plan.shown(os.path.join(config, "edit-gates"), home))
            found.append(c)
    return found


def _tool_of(step, names):
    """The tool a step of steps 3 and 4 is about: step 3's are in the plan's order (`names`, an
    iterator), step 4's subject is `~/.local/bin/agentik-<tool>`."""
    if step["n"] == 3:
        return next(names, None)
    if step["n"] == 4:
        return os.path.basename(step["subject"])[len("agentik-"):]
    return None


def plan_rows(cmd):
    """Steps 1 to 6, a check a row: an ok row keeps the plan's message, one not ok takes
    doctor's own fact (R6). A step of a source not the marketplace's own is named by its tool and
    holds no word of the source (row fk2b-reads R1); a held row's remedy is the source's card.
    Each keeps its step under `step`, which --json cuts away."""
    names = plan.default_set(cmd.lib)
    steps = plan.build(names, cmd.env, cmd.lib, cmd.tool, cmd.version)
    rows = tools.rows(cmd.env, cmd.lib, None, names=names)
    order, found = iter(names), []
    for s in steps:
        tool = _tool_of(s, order)
        if s["n"] > 6:
            continue
        row = rows.get(tool) if tool else None
        theirs = row is not None and row["kind"] not in ("own", "absent")
        state = STATE[s["state"]]
        remedy = None
        if state == "warn":
            if s["mid"] in HELD:
                remedy = cmd.say("config", "suite.sources." + tool)
            else:
                remedy = s["command"] if s["n"] == 6 and s["command"] else cmd.say("setup")
        if state == "ok":
            mid = SOURCE_OK.get(s["mid"], s["mid"]) if theirs else s["mid"]
        else:
            mid = FACT.get(s["mid"], "doctor.plan.placed")
        subject = tool if theirs and s["n"] == 3 else s["subject"]
        c = _check("%s %s" % (s["id"], subject), state, cmd.t.text(mid, **s["values"]), remedy)
        c["step"], c["shown"] = s, subject
        found.append(c)
    return found


def _ids(row):
    return list(dict.fromkeys(s["plugin"] for s in row["seen"]))


def source_checks(cmd, name, row):
    """The warns of a tool's source (R4): undecided, declared and not found, declared with another
    plugin of the name, a file the door would run that the suite passes over. Each is marked
    `source`, which --json cuts away; none names the source."""
    t, found = cmd.t, []
    if not row:
        return found
    kind, ids = row["kind"], _ids(row)
    if kind == "undecided":
        seen = row["seen"]
        if len(seen) == 1 and seen[0]["scope"] in ("project", "local"):
            mid = "doctor.source.repo"
        elif len(ids) == 1:
            mid = "doctor.source.twice"
        else:
            mid = "doctor.source.undecided"
        found.append(_check("source", "warn", t.text(mid, count=len(ids)),
                            cmd.say("config", "suite.sources." + name)))
    elif kind in ("plugin", "folder") and row["declared"]:
        if not row["found"]:
            found.append(_check("source", "warn", t.text("doctor.source.%s" % (
                "folder" if kind == "folder" else "declared"))))
        others = [i for i in ids if i != row["plugin"]]
        if others:
            found.append(_check("source", "warn", t.text("doctor.source.named", count=1 + len(others))))
    if row["passed_over"]:
        found.append(_check("source", "warn", t.text("doctor.source.passed")))
    for c in found:
        c["source"] = True
    return found


def source_notes(cmd, group, entries=()):
    """The lines under a group made from `source` at print time (R2, R3): `from`, `seen`, `runs`
    and `passed over`; for the suite's group, one `from` line for the tools of a mirror."""
    t, home, row = cmd.t, cmd.env.get("HOME"), group.get("source")
    if group is not None and group.get("suite"):
        names = [e["name"] for e in entries if e["source"] and e["source"]["kind"] == "own"
                 and e["source"]["mirror"]]
        return [t.text("doctor.from.mirror", names=", ".join(names))] if names else []
    if not row:
        return []
    notes, kind = [], row["kind"]

    def versioned(what, version):
        return what + (" " + version if isinstance(version, str) and version else "")

    if kind in ("plugin", "folder"):
        what = row["plugin"] if kind == "plugin" else plan.shown(row["root"] or "", home)
        at = row["declared"]
        if at:
            notes.append(t.text("doctor.from.declared", source=versioned(what, row["version"]),
                                at="%s:%s" % (plan.shown(at["path"], home), at["line"])))
        else:
            notes.append(t.text("doctor.from.only", source=versioned(what, row["version"])))
    others = [s for s in row["seen"] if kind == "undecided" or s["plugin"] != row["plugin"]]
    if others:
        pairs = list(dict.fromkeys(versioned(s["plugin"], s["version"]) for s in others))
        notes.append(t.text("doctor.seen", seen=", ".join(pairs)))
    runs = row["runs"]
    if kind in ("plugin", "folder", "undecided") and runs and runs["of"] != "source":
        mid = "doctor.runs.placed" if runs["of"] == "placed" else "doctor.runs.unknown"
        notes.append(t.text(mid, file=versioned(plan.shown(runs["path"], home), runs.get("version"))))
    passed = row["passed_over"]
    if passed:
        notes.append(t.text("doctor.passed", path=plan.shown(passed["path"], home), of=passed["of"]))
    return notes


def read_answer(out, failed):
    """The checks of a `doctor --json` answer that counts (R1), else None: one object whose
    schema is SCHEMA and whose checks are the contract's shape; the exit, `failed` and `warned`
    are not read. Such an object with ok false is one fail check, `doctor`, with the error's
    message (else `failed`) and remedy."""
    try:
        obj = json.loads(out.decode("utf-8", "replace"))
    except (ValueError, RecursionError):
        return None
    if not isinstance(obj, dict) or obj.get("schema") != SCHEMA:
        return None
    if obj.get("ok") is False:
        error = obj.get("error") if isinstance(obj.get("error"), dict) else {}
        message, remedy = error.get("message"), error.get("remedy")
        return [_check("doctor", "fail", message if isinstance(message, str) and message else failed,
                       remedy if isinstance(remedy, str) and remedy else None)]
    checks = obj.get("checks")
    if not isinstance(checks, list):
        return None
    found = []
    for c in checks:
        if not (isinstance(c, dict) and isinstance(c.get("name"), str) and c.get("status") in STATUSES
                and isinstance(c.get("detail"), str)
                and (c.get("remedy") is None or isinstance(c.get("remedy"), str))):
            return None
        found.append({k: c.get(k) for k in KEYS})
    return found


def tool_doctor(cmd, name, exe):
    """The command that runs a tool's own doctor: through the door where one reaches the suite,
    else the tool's file."""
    if prog.form(cmd.env, cmd.tool)[0] == prog.DOOR:
        return cmd.say(name, "doctor")
    return "%s doctor" % prog.shown(exe, cmd.env.get("HOME"), full=cmd.opts["json"])


def own_doctors(cmd, entries):
    """[group] for each listed tool but the suite, in the list's order. A group is {name,
    checks, one, nocmd, exe}; `one` marks a group of a single check the suite wrote (R2)."""
    t = cmd.t
    exes = {e["name"]: e["exe"] for e in entries if e["exe"]}
    jobs = [((name, 1), [exe, "doctor", "--json"]) for name, exe in exes.items()]
    answers = {}

    def then(key, result):
        name, round_ = key
        code, out, state = result
        if round_ != 1 or state != "ran":
            return ()
        got = read_answer(out, t.text("doctor.tool.failed"))
        if got is None:
            return [((name, 2), [exes[name], "doctor"])]
        answers[name] = got
        return ()

    results = tools.run_all(jobs, cmd.env, then=then,
                            deadline=time.monotonic() + DEADLINE) if jobs else {}
    groups = []
    for e in entries:
        name = e["name"]
        group = {"name": name, "one": True, "nocmd": False, "exe": e["exe"], "source": e["source"]}
        groups.append(group)
        lead = source_checks(cmd, name, e["source"])
        if lead:
            group["lead"] = lead[0]
        if not e["exe"]:
            group.update(nocmd=True, checks=lead + [_check("doctor", "note", t.text("doctor.tool.nocmd"))])
            continue
        if name in answers:
            group.update(one=False, checks=lead + answers[name])
            continue
        again = tool_doctor(cmd, name, e["exe"])
        code, out, state = results[(name, 1)]
        if state == "ran":
            code, out, state = results.get((name, 2), (None, b"", "timed out"))
        if state == "timed out":
            c = _check("doctor", "warn", t.text("doctor.tool.slow", secs="%g" % DEADLINE), again)
        elif state != "ran":
            c = _check("doctor", "warn", t.text("doctor.tool.unreadable"), again)
        elif code == 0:
            c = _check("doctor", "ok", t.text("doctor.tool.passed"))
        elif out.strip():
            c = _check("doctor", "fail", t.text("doctor.tool.failed"), again)
        else:
            c = _check("doctor", "fail", t.text("doctor.tool.silent"), again)
        group["checks"] = lead + [c]
    return groups


# ---- the screen (R5 to R8, R10) ------------------------------------------------------------

def _is_slash(remedy):
    """A slash command, `/demo:install-cli`: a first word that starts with `/` and holds no
    other `/`, which a path to run (`/opt/bin/demo setup`) always does."""
    first = remedy.split()[0] if remedy and remedy.split() else ""
    return first.startswith("/") and "/" not in first[1:]


def _is_shell(remedy):
    """A line to paste in a shell: not blank after strip(), and no slash command."""
    return bool(remedy and remedy.strip()) and not _is_slash(remedy)


def _left(checks, low, high):
    """A step of `low` to `high` that setup has left, a held row aside: its remedy is its card."""
    return any(c.get("step") and low <= c["step"]["n"] <= high and c["status"] != "ok"
               and c["step"]["mid"] not in HELD for c in checks)


def close_command(cmd, groups):
    """The one command the close names (R8), first match, or None."""
    suite = groups[0]["checks"]
    for c in suite:
        if c["status"] == "fail" and c["remedy"] and c["remedy"].strip():
            return c["remedy"]
    if _left(suite, 1, 5):
        return cmd.say("setup")
    for g in groups[1:]:
        fails = [c for c in g["checks"] if c["status"] == "fail"]
        if fails:
            remedy = fails[0]["remedy"]
            return remedy if _is_shell(remedy) else tool_doctor(cmd, g["name"], g["exe"])
    for g in groups:
        for c in g["checks"]:
            if c["status"] == "warn" and _is_shell(c["remedy"]) \
                    and not (c.get("step") and c["step"]["n"] == 6):
                return c["remedy"]
    return None


def _under(cmd, c, hint, left):
    """The one line under a row (R7), or None."""
    if c.get("add"):
        return c["add"]
    s = c.get("step")
    if s and s["line"] != "run":
        if left or not s["command"]:
            return None
        return cmd.t.text("setup." + s["line"], command=s["command"])
    remedy = c["remedy"]
    if not remedy or not remedy.strip():
        return None
    if _is_slash(remedy):
        return cmd.t.text("doctor.slash", command=remedy)
    return None if remedy == hint else cmd.t.text("doctor.fix", command=remedy)


def _home(text, home):
    """HOME's path read as `~` in a row's detail."""
    top = (home or "").rstrip("/")
    if not top:
        return text
    return re.sub(re.escape(top) + r"(?=$|[/\s:;,)'\"`])", "~", text)


def _rows(cmd, group, hint, every):
    """(rows, waiting) under a group line: every check with `every`, else each fail and warn,
    a plan's rows of one id and one fact folded into one, the rows that only wait counted."""
    checks, home = group["checks"], cmd.env.get("HOME")
    left = _left(checks, 2, 5)
    door_ok = all(c["status"] == "ok" for c in checks if c["name"] == "door" and not c.get("step"))
    rows, folds, waiting = [], {}, 0
    for c in checks:
        after = _under(cmd, c, hint, left)
        s = c.get("step")
        if every:
            rows.append([c["status"], c["name"], _home(c["detail"], home), after])
            continue
        if c["status"] not in ("fail", "warn") or c is group.get("lead") \
                or (group["one"] and s is None and not c.get("source") and not group.get("lead")):
            continue
        if s is None:
            rows.append([c["status"], c["name"], _home(c["detail"], home), after])
            continue
        if (2 <= s["n"] <= 5 and s["state"] == "todo" and not s["command"] and s["mid"] not in HELD) \
                or (s["n"] == 5 and s["id"] == "door" and not door_ok):
            waiting += 1
            continue
        key = (s["id"], c["detail"])
        if key in folds:
            folds[key][1].append(c.get("shown", s["subject"]))
            continue
        row = [c["status"], s["id"], None, after]
        folds[key] = (row, [c.get("shown", s["subject"])])
        rows.append(row)
    for (sid, fact), (row, subjects) in folds.items():
        row[2] = cmd.t.text("doctor.fold", fact=fact, subjects=", ".join(subjects))
    return rows, waiting


def _mark(group):
    states = [c["status"] for c in group["checks"]]
    if "fail" in states:
        return "fail"
    if "warn" in states:
        return "warn"
    return "note" if group["nocmd"] else "ok"


def _summary(t, group, waiting):
    checks = group["checks"]
    if group.get("lead"):
        return group["lead"]["detail"] + (" " + t.text("doctor.part.waiting", n=waiting) if waiting else "")
    if group["one"]:
        return checks[0]["detail"]
    failed = sum(c["status"] == "fail" for c in checks)
    warned = sum(c["status"] == "warn" for c in checks)
    if not failed and not warned:
        text = t.text("doctor.group.one") if len(checks) == 1 else \
            t.text("doctor.group.ok", count=len(checks))
    else:
        parts = [("doctor.part.failed", failed), ("doctor.part.warned", warned),
                 ("doctor.part.ok", len(checks) - failed - warned)]
        text = ", ".join(t.text(mid, n=n) for mid, n in parts if n)
    return text + (" " + t.text("doctor.part.waiting", n=waiting) if waiting else "")


def screen(cmd, groups, failed, warned, total, entries=()):
    t = cmd.t
    hint = close_command(cmd, groups)
    closed = None if t.quiet else hint  # -q prints no close, so each row keeps its fix: line
    wide = max(len(g["name"]) for g in groups)
    marks = {g["name"]: _mark(g) for g in groups}
    mark_w = max(len(t.out.mark(m)[0]) for m in marks.values())
    for g in groups:
        rows, waiting = _rows(cmd, g, closed, cmd.opts["all"])
        mark = marks[g["name"]]
        pad = " " * (mark_w - len(t.out.mark(mark)[0]))
        t.table([(mark, [(pad + g["name"].ljust(wide), "name"), _summary(t, g, waiting)], None)],
                indent=0)
        t.table([(None, [(note, "hint")], None) for note in source_notes(cmd, g, entries)], indent=4)
        t.table([(status, [name, detail], after) for status, name, detail, after in rows], indent=4)
    if failed or warned:
        t.line("doctor.total", failed=failed, warned=warned, ok=total - failed - warned)
    else:
        t.line("doctor.done")
    if hint:
        t.hint("hint.doctor.next", command=hint)


def do_doctor(cmd, nouns):
    cmd._no_nouns(nouns)
    on_path = cmd._on_path()
    suite = cmd.tool[len("agentik-"):] if cmd.tool.startswith("agentik-") else cmd.tool
    entries = tools.listed(suite, on_path, cmd.env)
    own = [door(cmd, on_path)] + shadow(cmd, on_path) + user_settings(cmd) + source_settings(cmd) \
        + plan_rows(cmd)
    groups = [{"name": entries[0]["name"], "checks": own, "one": False, "nocmd": False, "exe": None,
               "source": None, "suite": True}]
    groups += own_doctors(cmd, entries[1:])
    checks = [c for g in groups for c in g["checks"]]
    failed = sum(c["status"] == "fail" for c in checks)
    warned = sum(c["status"] == "warn" for c in checks)
    if cmd.opts["json"]:
        cmd.t.json({"schema": SCHEMA, "ok": True, "failed": failed, "warned": warned,
                    "tools": [{"name": g["name"], "checks": [{k: c[k] for k in KEYS} for c in g["checks"]],
                               "source": g["source"]} for g in groups]})
    else:
        screen(cmd, groups, failed, warned, len(checks), entries)
    return 1 if failed else 0
