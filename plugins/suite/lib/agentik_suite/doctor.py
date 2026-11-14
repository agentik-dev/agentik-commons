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
"""
import json
import os
import re
import time

import agentik_install

from . import plan, prog, settings, status, tools

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
        "setup.launcher.unread": "doctor.plan.unread", "setup.suite.unread": "doctor.plan.unread"}


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


def plan_rows(cmd):
    """Steps 1 to 6, a check a row: an ok row keeps the plan's message, one not ok takes
    doctor's own fact (R6). Each keeps its step under `step`, which --json cuts away."""
    steps = plan.build(plan.default_set(cmd.lib), cmd.env, cmd.lib, cmd.tool, cmd.version)
    found = []
    for s in steps:
        if s["n"] > 6:
            continue
        state = STATE[s["state"]]
        remedy = None
        if state == "warn":
            remedy = s["command"] if s["n"] == 6 and s["command"] else cmd.say("setup")
        mid = s["mid"] if state == "ok" else FACT.get(s["mid"], "doctor.plan.placed")
        c = _check("%s %s" % (s["id"], s["subject"]), state, cmd.t.text(mid, **s["values"]), remedy)
        c["step"] = s
        found.append(c)
    return found


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
        group = {"name": name, "one": True, "nocmd": False, "exe": e["exe"]}
        groups.append(group)
        if not e["exe"]:
            group.update(nocmd=True, checks=[_check("doctor", "note", t.text("doctor.tool.nocmd"))])
            continue
        if name in answers:
            group.update(one=False, checks=answers[name])
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
        group["checks"] = [c]
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
    return any(c.get("step") and low <= c["step"]["n"] <= high and c["status"] != "ok" for c in checks)


def _closes(remedy):
    """A tool's remedy the close may name: a shell line with no word that answers a question for
    the person (cli.SKIPS) and not `remove` (row sc5 R8); a write such as install-cli is the fix."""
    from . import cli
    words = remedy.split() if _is_shell(remedy) else []
    return bool(words) and not any(w.partition("=")[0] in cli.SKIPS or w == "remove" for w in words)


def close_command(cmd, groups):
    """The one command the close names (R8), first match, or None. A tool's remedy that fails
    `_closes` stands on its check's line, and the close names the tool's own doctor, through the
    door where one reaches the suite (`tool_doctor`; review 1 F1: `doctor <tool>` takes no name)."""
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
            if _closes(remedy):
                return remedy
            return tool_doctor(cmd, g["name"], g["exe"])
    for i, g in enumerate(groups):
        for c in g["checks"]:
            if c["status"] == "warn" and _is_shell(c["remedy"]) \
                    and not (c.get("step") and c["step"]["n"] == 6):
                if i == 0 or _closes(c["remedy"]):
                    return c["remedy"]
                return tool_doctor(cmd, g["name"], g["exe"])
    return None


def _under(cmd, c, hint, left):
    """The one line under a row (R7), or None."""
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
        if c["status"] not in ("fail", "warn") or (group["one"] and s is None):
            continue
        if s is None:
            rows.append([c["status"], c["name"], _home(c["detail"], home), after])
            continue
        if (2 <= s["n"] <= 5 and s["state"] == "todo" and not s["command"]) \
                or (s["n"] == 5 and s["id"] == "door" and not door_ok):
            waiting += 1
            continue
        key = (s["id"], c["detail"])
        if key in folds:
            folds[key][1].append(s["subject"])
            continue
        row = [c["status"], s["id"], None, after]
        folds[key] = (row, [s["subject"]])
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


def screen(cmd, groups, failed, warned, total):
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
    own = [door(cmd, on_path)] + shadow(cmd, on_path) + user_settings(cmd) + plan_rows(cmd)
    groups = [{"name": entries[0]["name"], "checks": own, "one": False, "nocmd": False, "exe": None}]
    groups += own_doctors(cmd, entries[1:])
    checks = [c for g in groups for c in g["checks"]]
    failed = sum(c["status"] == "fail" for c in checks)
    warned = sum(c["status"] == "warn" for c in checks)
    if cmd.opts["json"]:
        cmd.t.json({"schema": SCHEMA, "ok": True, "failed": failed, "warned": warned,
                    "tools": [{"name": g["name"], "checks": [{k: c[k] for k in KEYS} for c in g["checks"]]}
                              for g in groups]})
    else:
        screen(cmd, groups, failed, warned, len(checks))
    return 1 if failed else 0
