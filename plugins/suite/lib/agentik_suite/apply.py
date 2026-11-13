"""setup applied (packet ak3-setup): the plan read, its first runnable row run, the plan read again.

A row is runnable when it is one of steps 2 to 5, `todo`, and names a command whose line is `run`.
Each command runs once, split by shlex with no shell, stdin the null device, both streams
captured, in its own process group under a wall (600 s for `claude`, 120 s else), the group killed
past it. A row that still names a command already run has failed, as has a non-zero exit, the wall
or a file that cannot start: the run stops there, exit 1, with no rollback. Step 6 is never
applied and step 7 never run. Before the first command setup asks on a terminal, needs --yes off
one, and off one refuses outright where step 2 or 3 would write a settings file the user's gate
list names. What each command wrote is found by lstat over a fixed set of places; a run that ran a
command appends one line to its journal, through term.
"""
import datetime
import fnmatch
import json
import os
import shlex
import signal
import subprocess
import sys

from . import plan, term

CLAUDE_WALL = 600
WALL = 120
JOURNAL = "setup" + ".jsonl"  # the verb's journal; a bare id-like literal would read as a message id
STATUS = {"ok": "ok", "todo": "note", "blocked": "warn"}
JSON_KEYS = ("n", "id", "state", "subject", "detail", "command")


def runnable(steps):
    return [s for s in steps if 2 <= s["n"] <= 5 and s["state"] == "todo" and s["command"]
            and s["line"] == "run"]


def _kill(group):
    try:
        os.killpg(group, signal.SIGKILL)
    except OSError:
        pass


def execute(command, env):
    """{exit, last, why, wall}: why is None, "wall" or "start"; exit is None unless it exited."""
    try:
        words = shlex.split(command)
    except ValueError as e:
        return {"exit": None, "last": str(e), "why": "start", "wall": WALL}
    wall = CLAUDE_WALL if words and words[0] == "claude" else WALL
    if not words:
        return {"exit": None, "last": "", "why": "start", "wall": wall}
    try:
        p = subprocess.Popen(words, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, env=dict(env), start_new_session=True)
    except (OSError, ValueError) as e:
        return {"exit": None, "last": getattr(e, "strerror", None) or str(e), "why": "start",
                "wall": wall}
    why = None
    try:
        data, _ = p.communicate(timeout=wall)
    except subprocess.TimeoutExpired:
        why = "wall"
        _kill(p.pid)
        try:
            data, _ = p.communicate(timeout=5)
        except subprocess.TimeoutExpired:  # a process outside the group holds the pipe
            p.kill()
            p.wait()
            data = b""
    lines = [l.strip() for l in data.decode("utf-8", "replace").splitlines() if l.strip()]
    return {"exit": None if why else p.returncode, "last": lines[-1] if lines else "",
            "why": why, "wall": wall}


def gated(config, home):
    """The settings file Claude Code writes, when the user's gate list names it; else None."""
    target = os.path.join(config, "settings.json")
    listing = os.path.join(config, "edit-gates")
    if not os.path.isfile(listing):
        return None
    try:
        with open(listing, encoding="utf-8") as fh:
            text = fh.read()
    except (OSError, ValueError):
        return None
    names = (target, os.path.realpath(target))
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("~/"):
            line = os.path.join(home, line[2:])
        if any(line == name or fnmatch.fnmatch(name, line) for name in names):
            return target
    return None


def _entries(folder):
    try:
        return [os.path.join(folder, name) for name in sorted(os.listdir(folder))]
    except OSError:
        return []


def look(home, config):
    """{path: its lstat} over R7's places: what a command may write."""
    places = [os.path.join(home, ".claude.json"), os.path.join(config, "settings.json"),
              os.path.join(config, "plugins", "known_marketplaces.json"),
              os.path.join(config, "plugins", "installed_plugins.json")]
    places += _entries(os.path.join(home, ".local", "bin"))
    for share in _entries(os.path.join(home, ".local", "share")):
        if os.path.basename(share).startswith("agentik-"):
            places += _entries(share)
    seen = {}
    for path in places:
        try:
            st = os.lstat(path)
        except OSError:
            continue
        seen[path] = (st.st_mode, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
    return seen


def install_root(config, key):
    """The installPath Claude Code lists for `<name>@<marketplace>`, and whether it is there."""
    found = plan._read_json(os.path.join(config, "plugins", "installed_plugins.json"))
    table = found.get("plugins") if isinstance(found, dict) else None
    entry = table.get(key) if isinstance(table, dict) else None
    entry = entry[0] if isinstance(entry, list) and entry and isinstance(entry[0], dict) else {}
    root = entry.get("installPath")
    return (root, os.path.isdir(root)) if isinstance(root, str) and root else (None, False)


def journal_path(env, home):
    state = env.get("XDG_STATE_HOME") or ""
    if not os.path.isabs(state):
        state = os.path.join(home, ".local", "state")
    return os.path.join(state, "agentik-suite", JOURNAL)


def _terminal(cmd):
    try:
        stdin = sys.stdin is not None and sys.stdin.isatty()
    except (AttributeError, ValueError, OSError):
        stdin = False
    return stdin and cmd.t.err.tty


def show(cmd, steps, upto=7, lines=True):
    t, rows, last = cmd.t, [], None
    for s in steps:
        if s["n"] > upto:
            continue
        after = t.text("setup." + s["line"], command=s["command"]) if lines and s["command"] else None
        n = str(s["n"]) if s["n"] != last else ""
        last = s["n"]
        subject = term.path(s["subject"]) if s["subject"].startswith(("~", "/")) else term.name(s["subject"])
        rows.append((STATUS[s["state"]], [n, subject, s["detail"]], after))
    t.table(rows, mark_at=1)


def run(cmd, names):
    t, o, env, tool = cmd.t, cmd.opts, cmd.env, cmd.tool
    home = env.get("HOME") or ""
    config = env.get("CLAUDE_CONFIG_DIR") or os.path.join(home, ".claude")

    def build():
        steps = plan.build(names, env, cmd.lib, tool, cmd.version)
        for s in steps:
            s["detail"] = t.text(s["mid"], **s["values"])
        return steps

    def the_plan(steps):
        if not o["json"]:
            t.line("setup.title", plugins=", ".join(names)) if names else t.line("setup.title.none")
            show(cmd, steps)

    steps = build()
    blocked = [s["subject"] for s in steps if s["state"] == "blocked"]
    if blocked:
        if o["json"]:
            raise cmd.Usage("blocked", "err.setup.blocked", "%s setup --dry-run" % tool,
                            missing=", ".join(blocked), tool=tool)
        the_plan(steps)
        t.hint("hint.setup.blocked", missing=", ".join(blocked), tool=tool)
        return 2
    if not runnable(steps):
        return report(cmd, names, steps, [], [], None, None, home)
    terminal = _terminal(cmd)
    if not terminal and any(s["n"] in (2, 3) and s["state"] == "todo" for s in steps):
        gate = gated(config, home)
        if gate:
            raise cmd.Usage("gated", "err.setup.gated", "%s setup" % tool,
                            path=plan.shown(gate, home), tool=tool)
    if not o["yes"]:
        the_plan(steps)
        if not (terminal and not o["json"]):
            raise cmd.Usage("needs_yes", "err.setup.yes", "%s setup --yes" % tool, tool=tool)
        t.line("setup.ask", err=True)
        t.flush()
        try:
            answer = sys.stdin.readline()
        except (OSError, ValueError):
            answer = ""
        if answer.strip().lower() not in ("y", "yes"):
            raise cmd.Usage("declined", "err.setup.declined", "%s setup" % tool, tool=tool)

    ran, wrote, done, failure = [], [], set(), None
    while True:
        rows = runnable(steps)
        if not rows:
            break
        again = [s for s in rows if s["command"] in done]
        if again:
            failure = ("err.setup.todo", {"command": again[0]["command"], "n": again[0]["n"]})
            break
        row = rows[0]
        command = row["command"]
        done.add(command)
        if not t.quiet:
            t.line("setup.running", err=True, command=command)
            t.flush()
        before = look(home, config)
        old = install_root(config, row["subject"]) if row["n"] == 3 else None
        result = execute(command, env)
        after = look(home, config)
        new = [p for p in sorted(after) if after[p] != before.get(p)]
        if old is not None:
            root, there = install_root(config, row["subject"])
            if there and (root != old[0] or not old[1]):
                new.append(root)
        wrote += [p for p in new if p not in wrote]
        ran.append({"n": row["n"], "command": command, "exit": result["exit"], "result": result})
        if result["why"] or result["exit"] != 0:
            failure = _failure(command, result)
            break
        steps = build()
    steps = build()
    return report(cmd, names, steps, ran, wrote, failure, journal_path(env, home), home)


def _failure(command, result):
    values = {"command": command, "exit": result["exit"], "last": result["last"],
              "wall": result["wall"]}
    if result["why"] == "wall":
        return "err.setup.wall", values
    if result["why"] == "start":
        return "err.setup.start", values
    return ("err.setup.step" if result["last"] else "err.setup.step.silent"), values


def report(cmd, names, steps, ran, wrote, failure, journal, home):
    t, tool = cmd.t, cmd.tool
    code = 1 if failure else 0
    journal_error = None
    if ran:
        wrote = wrote + ([journal] if journal not in wrote else [])
        entry = {"at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "version": cmd.version, "plugins": names,
                 "ran": [{k: r[k] for k in ("n", "command", "exit")} for r in ran],
                 "wrote": wrote, "exit": code}
        try:
            os.makedirs(os.path.dirname(journal), exist_ok=True)
            term.append(journal, json.dumps(entry) + "\n")
        except OSError as e:
            journal_error = e.strerror or str(e)
            wrote = [p for p in wrote if p != journal]
            journal = None
    else:
        journal = None
    add = [s for s in steps if s["n"] == 6 and s["state"] == "todo" and s["command"]]
    if cmd.opts["json"]:
        obj = {"schema": "agentik.setup/1", "ok": not failure, "dry_run": False, "plugins": names,
               "steps": [{k: s[k] for k in JSON_KEYS} for s in steps],
               "ran": [{k: r[k] for k in ("n", "command", "exit")} for r in ran],
               "wrote": wrote, "nothing": not ran, "journal": journal}
        if failure:
            obj["error"] = {"code": "step_failed", "message": t.text(failure[0], tool=tool, **failure[1]),
                            "remedy": "%s setup" % tool}
        t.json(obj)
        return code
    if not ran:
        t.line("setup.nothing")
    else:
        t.line("setup.after")
        show(cmd, steps, upto=6, lines=False)
        for r in ran:
            why = r["result"]["why"]
            if why == "wall":
                t.line("setup.ran.wall", command=r["command"], wall=r["result"]["wall"])
            elif why == "start":
                t.line("setup.ran.start", command=r["command"])
            else:
                t.line("setup.ran", command=r["command"], exit=r["exit"])
        for path in wrote:
            t.line("setup.wrote", path=plan.shown(path, home))
    for s in add:
        t.line("setup.add", command=s["command"])
    if journal_error:
        t.error("err.setup.journal", path=plan.shown(journal_path(cmd.env, home), home), why=journal_error)
    if failure:
        t.flush()
        t.error(failure[0], tool=tool, **failure[1])
    else:
        t.hint("hint.setup.doctor", tool=tool)
    return code
