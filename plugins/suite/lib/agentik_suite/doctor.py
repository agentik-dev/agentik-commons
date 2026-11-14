"""`doctor`: the machine checked in one read, grouped by tool, the suite's group first.

The suite's checks, in order: the door (the first `agentik` on PATH that is a regular executable
file, its VERSION against the door this command ships), a shadow (an `agentik-<word>` on PATH
whose word the door would hand to it in place of the suite's verb), the user settings file, and
the setup plan's steps 1 to 6, one check a row. Then each listed tool's own `doctor`, every one
at once under one deadline of DEADLINE seconds. A check is {name, status, detail, remedy}; the
status is ok, note, warn or fail; exit 1 when one is fail, else 0. It reads no cache, runs no
`describe` and no `claude`, and writes nothing itself; a tool's own doctor may write its state.
"""
import os
import time

import agentik_install

from . import plan, prog, settings, status, term, tools

DEADLINE = 30.0
RESERVED = ("remove", "update", "init", "completion", "inbox")
STATE = {"ok": "ok", "todo": "warn", "blocked": "fail"}


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
    steps = plan.build(plan.default_set(cmd.lib), cmd.env, cmd.lib, cmd.tool, cmd.version)
    found = []
    for s in steps:
        if s["n"] > 6:
            continue
        state = STATE[s["state"]]
        remedy = None
        if state == "warn":
            remedy = s["command"] if s["n"] == 6 and s["command"] else cmd.say("setup")
        found.append(_check("%s %s" % (s["id"], s["subject"]), state,
                            cmd.t.text(s["mid"], **s["values"]), remedy))
    return found


def _last_line(out):
    for line in reversed(out.decode("utf-8", "replace").splitlines()):
        if line.strip():
            return line.strip()
    return None


def own_doctors(cmd, entries):
    """[(name, [check])] for each listed tool but the suite, in the list's order."""
    jobs = [(e["name"], [e["exe"], "doctor"]) for e in entries if e["exe"]]
    results = tools.run_all(jobs, cmd.env, deadline=time.monotonic() + DEADLINE) if jobs else {}
    groups = []
    for e in entries:
        if not e["exe"]:
            groups.append((e["name"], [_check("doctor", "note", cmd.t.text("doctor.tool.nocmd"))]))
            continue
        code, out, state = results[e["name"]]
        exe = os.path.basename(e["exe"])
        again = "%s doctor" % exe
        if state == "timed out":
            c = _check("doctor", "warn", cmd.t.text("doctor.tool.slow", secs="%g" % DEADLINE),
                       again)
        elif state != "ran":
            c = _check("doctor", "warn", cmd.t.text("doctor.tool.unreadable"), again)
        elif code == 0:
            c = _check("doctor", "ok", cmd.t.text("doctor.tool.ok"))
        else:
            c = _check("doctor", "fail", _last_line(out) or cmd.t.text("doctor.tool.silent",
                                                                         code=code), again)
        groups.append((e["name"], [c]))
    return groups


def _hint(cmd, checks):
    states = [c["status"] for c in checks]
    setup = cmd.say("setup")
    if "fail" in states:
        return "hint.doctor.fail"
    if any(c["status"] == "warn" and c["remedy"] == setup for c in checks):
        return "hint.doctor.setup"
    if "warn" in states:
        return "hint.doctor.warn"
    return "hint.doctor.done"


def do_doctor(cmd, nouns):
    cmd._no_nouns(nouns)
    t = cmd.t
    on_path = cmd._on_path()
    suite = cmd.tool[len("agentik-"):] if cmd.tool.startswith("agentik-") else cmd.tool
    entries = tools.listed(suite, on_path, cmd.env)
    own = [door(cmd, on_path)] + shadow(cmd, on_path) + user_settings(cmd) + plan_rows(cmd)
    groups = [(entries[0]["name"], own)] + own_doctors(cmd, entries[1:])
    checks = [c for _, found in groups for c in found]
    failed = sum(c["status"] == "fail" for c in checks)
    warned = sum(c["status"] == "warn" for c in checks)
    if cmd.opts["json"]:
        t.json({"schema": "agentik.doctor/1", "ok": True, "failed": failed, "warned": warned,
                "tools": [{"name": name, "checks": found} for name, found in groups]})
    else:
        t.line("doctor.title", **cmd.slots())
        for name, found in groups:
            t.blank()
            t.line("doctor.group", style="name", name=name)
            t.table([(c["status"], [term.name(c["name"]), c["detail"]],
                      t.text("doctor.run", command=c["remedy"]) if c["remedy"] else None)
                     for c in found])
        t.hint(_hint(cmd, checks), **cmd.slots())
    return 1 if failed else 0
