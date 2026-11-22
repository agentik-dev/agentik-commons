"""setup applied (packet ak3-setup): the plan read, its first runnable row run, the plan read again.

A row is runnable when it is one of steps 2 to 5, `todo`, and names a command whose line is `run`.
Each command runs once, split by shlex with no shell, stdin the null device, both streams
captured, in its own process group under a wall (600 s for `claude`, 120 s else), the group killed
past it. A row that still names a command already run has failed, as has a non-zero exit, the wall
or a file that cannot start: the run stops there, exit 1, with no rollback. Step 6 is never
applied and step 7 never run. Before the first command setup asks on a terminal, counting what
a yes runs, Enter a no; it needs --yes off one, and off one refuses outright where step 2 or 3 would write a settings file the user's gate
list names, or where that list is there but cannot be read. An interrupt (SIGINT or SIGTERM) before
the first command, the question's included, declines, exit 2; during a command it stops the
command's group and ends the run, exit 130, the journal written. What each command wrote is found
by lstat over a fixed set of places; a run that ran a command appends one line to its journal,
through term.
"""
import datetime
import fnmatch
import json
import os
import shlex
import signal
import subprocess
import sys
import time

import agentik_install

from . import pick, plan, term, tools

CLAUDE_WALL = 600
WALL = 120
GRACE = 2  # seconds between an interrupted command's SIGTERM and its SIGKILL
INTERRUPTED = 130
JOURNAL = "setup" + ".jsonl"  # the verb's journal; a bare id-like literal would read as a message id
STATUS = {"ok": "ok", "todo": "note", "blocked": "warn", "warn": "warn"}  # warn: a need (ic2-needs)
JSON_KEYS = ("n", "id", "state", "subject", "detail", "command")


def runnable(steps):
    return [s for s in steps if 2 <= s["n"] <= 5 and s["state"] == "todo" and s["command"]
            and s["line"] == "run"]


def planned(steps):
    """The commands a yes would run, as the question counts them: the runnable rows, and one
    install-cli for each step 4 row that waits on step 3 (row sm1-setup-ask R3). A plugin that
    turns out to ship no command, or a door older than this one's, moves the true count by one.
    Another row with no command is nothing to do (row fk2-plan R7)."""
    waiting = [s for s in steps if s["n"] == 4 and s["state"] == "todo" and not s["command"]
               and s["mid"] == "setup.launcher.wait"]
    return len(runnable(steps)) + len(waiting)


def old_python(steps):
    """The values of step 1's python3 row where it is blocked, else None. The suite runs under that
    Python, so a blocked one is installed and under the floor, never missing (review 1 F2)."""
    for s in steps:
        if s["id"] == "prereqs" and s["subject"] == "python3" and s["state"] == "blocked":
            return s["values"]
    return None


def path_close(t, command):
    """The close where the door stands and only PATH lacks its folder: the reason, then the line
    that mends this terminal, a command that runs as printed (ic1-close review 1)."""
    t.flush()  # the plan's add line above it, where both streams share one pipe
    t.line("setup.path.why", err=True)
    t.hint("hint.setup.path", command=command)


def path_rows(cmd, command):
    """The report's two PATH rows (row sc8 R2), as `_tail` takes them: the reason and the login
    file, then the line itself. The dry run whose plan runs nothing closes on them too."""
    return [("setup.tail.path", cmd.t.text("setup.path.row", profile=profile(cmd.env)), False),
            (None, command, True)]


def page_close(steps):
    """The close where a page row is left and no step holds a command setup would run, or None
    (row fh13 R7): each such tool in the plan's order."""
    names = [s["values"]["name"] for s in steps if s["n"] == 4 and s["line"] == "page"]
    if not names or runnable(steps):
        return None
    return "hint.setup.page", {"names": ", ".join(names)}


def step_json(s):
    """A step as setup's JSON gives it; a page row adds its page (row fh13 R2)."""
    obj = {k: s[k] for k in JSON_KEYS}
    if s.get("page"):
        obj["page"] = s["page"]
    return obj


def _kill(group, sig=signal.SIGKILL):
    try:
        os.killpg(group, sig)
    except OSError:
        pass


def _stop(p):
    """The command's group stopped on an interrupt: SIGTERM, SIGKILL after GRACE, the head reaped."""
    _kill(p.pid, signal.SIGTERM)
    try:
        p.wait(timeout=GRACE)
    except subprocess.TimeoutExpired:
        pass
    _kill(p.pid)
    p.wait()


def _ignore():
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, signal.SIG_IGN)
        except ValueError:  # not the main thread
            pass


def _interrupt(signum, frame):
    """SIGINT or SIGTERM during a run: the next one is ignored, so the stop and the journal end."""
    _ignore()
    raise KeyboardInterrupt


def execute(command, env):
    """{exit, last, why, wall}: why is None, "wall" or "start"; exit is None unless it exited. An
    interrupt stops the command's group and goes on up."""
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
        try:
            data, _ = p.communicate(timeout=wall)
        except subprocess.TimeoutExpired as e:
            why, data = "wall", e.output or b""
            _kill(p.pid)
            try:
                data, _ = p.communicate(timeout=5)  # all it printed, what came before the kill too
            except subprocess.TimeoutExpired as again:  # a process outside the group holds the pipe
                data = again.output or data
                p.kill()
                p.wait()
    except BaseException:
        _stop(p)
        raise
    lines = [l.strip() for l in data.decode("utf-8", "replace").splitlines() if l.strip()]
    return {"exit": None if why else p.returncode, "last": lines[-1] if lines else "",
            "why": why, "wall": wall, "tail": lines[-TAIL:]}


def gated(config, home, t, target=None):
    """(path, why): `target` (Claude Code's settings file when None) when the user's gate list
    names it; the list itself, and why, when it is there but cannot be read, which refuses too
    (review 1 F4); else (None, None). A byte that is not UTF-8 is replaced, so it hides no line
    (F2). The doctor asks it of the suite's user file (row fk2b-reads R5): one reader of the list."""
    target = target or os.path.join(config, "settings.json")
    listing = os.path.join(config, "edit-gates")
    if not os.path.lexists(listing):
        return None, None
    if not os.path.isfile(listing):
        return listing, t.text("setup.gate.notfile")
    try:
        with open(listing, "rb") as fh:
            text = fh.read().decode("utf-8", "replace")
    except OSError as e:
        return listing, e.strerror or str(e)
    names = (target, os.path.realpath(target))
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("~/"):
            line = os.path.join(home, line[2:])
        if any(line == name or fnmatch.fnmatch(name, line) for name in names):
            return target, None
    return None, None


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


def install_root(env, key, cwd=None):
    """The root of the source that stands for `<name>@<marketplace>`'s name, as the finder says
    (row fk2-plan R7), and whether it is there."""
    name = key.rpartition("@")[0] or key
    root = tools.rows(env, None, cwd, names=[name])[name]["root"]
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
    """The plan's table, the dry run's and the run's; with `lines` false a page row still holds its
    page, which the close points to (row fh13 review 1 F1). A missing `claude` has the `get it:`
    line under its row (row sm2 R2, in the run too by row ic1-close R3)."""
    t, rows, last = cmd.t, [], None
    for s in steps:
        if s["n"] > upto:
            continue
        shown = s["command"] or s.get("page")  # a page is shown, never run (fh13 R6)
        keep = lines or s["line"] == "page"
        after = t.text("setup." + s["line"], command=shown) if keep and shown else None
        if s["id"] == "prereqs" and s["subject"] == "claude" and s["state"] == "blocked":
            after = t.text("setup.cmd.get")  # where Claude Code comes from
        n = str(s["n"]) if s["n"] != last else ""
        last = s["n"]
        subject = term.path(s["subject"]) if s["subject"].startswith(("~", "/")) else term.name(s["subject"])
        rows.append((STATUS[s["state"]], [n, subject, s["detail"]], after))
    t.table(rows, mark_at=1)


COVERED = ("setup.door.above", "setup.door.place", "setup.door.plugin")  # placed by another row's command
LABEL = 11  # the widest step label, `marketplace`
TAIL_LABEL = 5  # the widest of the report's labels
LEAD = 6  # a command that does not fit its row stands at this column on the line under it
TAIL = 5  # a failed command's own last lines shown under its row (row sc8 R6)


def undo(cmd):
    """The `undo` row's command, one row in the plan's `Yours, after:` and one in the report
    (design/23 §5, D23-3): None while setup's screens name no `remove`; a later row turns it on."""
    return None


def profile(env):
    """The login shell's own file, as a person reads it (row sc8 R2)."""
    shell = os.path.basename(env.get("SHELL") or "")
    if shell == "zsh":
        return "~/.zshrc"
    if shell == "bash":
        return "~/.bash_profile" if sys.platform == "darwin" else "~/.bashrc"
    return "~/.profile"


def _say(stream, text, indent=0, first=""):
    """`first`, then `text`: on a terminal wrapped at its width, each next line at `indent`; off
    one a single line, so a pipe is searched by line."""
    if not stream.tty:  # off a terminal one row is one line, as sc3's table (build 2's ruling)
        stream.put((first + term.clean(text)).rstrip(" ") + "\n")
        return
    room = max(stream.width() - max(indent, term.columns(first)), 20)
    lines = term._wrap(term.clean(text), room) if text else [""]
    stream.put((first + lines[0]).rstrip(" ") + "\n")
    for more in lines[1:]:
        stream.put(" " * indent + more + "\n")


def _rows(t, rows, err=False):
    """Setup's rows (row sc8 R1, R6, R7): (status or None, step or "", label, text, whole).
    The mark column is as wide as the widest mark shown; a `whole` text is a command, never
    broken: on a terminal, where it does not fit after its head it stands on the next line at LEAD,
    and other text wraps under its own column; off one a row is one line (sc3's table, R9)."""
    stream = t._stream(err)
    width = max((term.columns(stream.mark(r[0])[0]) for r in rows if r[0]), default=1)
    for status, n, label, text, whole in rows:
        shown, painted = stream.mark(status) if status else ("", "")
        step = str(n) or " "
        head = "  %s%s %s %s  " % (painted, " " * (width - term.columns(shown)), step,
                                   term.clean(label).ljust(LABEL))
        room = 2 + width + 1 + len(step) + 1 + LABEL + 2
        text = term.clean(text)
        if not whole:
            _say(stream, text, room, head)
        elif not stream.tty or room + term.columns(text) <= stream.width():
            stream.put(head + text + "\n")
        else:
            if n or label or status:
                stream.put(head.rstrip(" ") + "\n")
            stream.put(" " * LEAD + text + "\n")


def _summary(n, group):
    """The one line of a step whose rows all read ok: the names it holds."""
    if n == 6:
        return group[0]["subject"]
    names = []
    for s in group:
        subject = s["subject"]
        if n in (4, 5) or subject.startswith(("~", "/")):
            subject = os.path.basename(subject)
        elif n == 3:
            subject = subject.rpartition("@")[0] or subject
        if s["id"] == "prereqs" and subject == "python3" and s["values"].get("version"):
            subject += " " + str(s["values"]["version"])
        names.append(subject)
    return ", ".join(names)


def plan_screen(cmd, steps, names, dry=False):
    """The plan (row sc8 R1; design/23 §5): its title; one marked line a step whose rows all read
    ok; each row that needs a word of its own, marked; `Would run, in this order:` over every
    command a yes runs and no other, step 4's count of the commands step 3 brings; `Yours,
    after:` over what setup never runs."""
    t = cmd.t

    def label(n):
        return t.text("setup.step.%d" % n)

    if names:
        title = t.text("setup.title.dry" if dry else "setup.title", plugins=", ".join(names))
    else:
        title = t.text("setup.title.none.dry" if dry else "setup.title.none")
    _say(t.out, title)
    t.blank()
    runs = runnable(steps)
    top, would, yours = [], [], []
    for n in range(1, 7):
        group = [s for s in steps if s["n"] == n]
        if group and all(s["state"] == "ok" for s in group):
            top.append(("ok", n, label(n), _summary(n, group), False))
            continue
        for s in group:
            if s in runs or s["state"] == "ok" or s["mid"] in COVERED or s["mid"] == "setup.launcher.wait":
                continue
            if n == 6 and s["state"] == "todo" and s["line"] == "add":
                yours.append((None, 6, label(6), t.text("setup.yours.path"), False))
                continue
            top.append((STATUS[s["state"]], n, label(n), "%s: %s" % (s["subject"], s["detail"]), False))
            if s["id"] == "prereqs" and s["subject"] == "claude" and s["state"] == "blocked":
                top.append((None, "", "", t.text("setup.cmd.get"), True))  # where Claude Code comes from
            if s["line"] == "page" and s.get("page"):
                top.append((None, "", "", t.text("setup.page", command=s["page"]), True))  # whole, as a command
    waiting = [s for s in steps if s["n"] == 4 and s["state"] == "todo" and not s["command"]
               and s["mid"] == "setup.launcher.wait"]
    shown = set()
    for n in (2, 3, 4, 5):
        for s in [r for r in runs if r["n"] == n]:
            would.append((None, "" if n in shown else n, "" if n in shown else label(n), s["command"], True))
            shown.add(n)
        if n == 4 and waiting:
            text = t.text("setup.waiting.one") if len(waiting) == 1 else t.text("setup.waiting", count=len(waiting))
            would.append((None, "" if 4 in shown else 4, "" if 4 in shown else label(4), text, False))
    yours.append((None, 7, label(7), cmd.slots()["doctor"], True))
    if undo(cmd):
        yours.append((None, "", t.text("setup.tail.undo"), undo(cmd), True))
    _rows(t, top)
    if would:
        t.line("setup.would")
        _rows(t, would)
    t.line("setup.yours")
    _rows(t, yours)


def _note(t, mid, **values):
    """A note line on stderr: the note mark, then the text (row sc8 R5)."""
    t.flush()
    stream = t.err
    stream.put(stream.mark("note")[1] + term.GAP + t.text(mid, **values) + "\n")


def _tail(t, rows):
    """The report's labelled rows (row sc8 R2): (label id or None, text, whole); a whole text that
    does not fit stands under its label at LEAD."""
    stream = t.out
    room = 2 + TAIL_LABEL + 2
    for mid, text, whole in rows:
        head = "  " + t.text(mid).ljust(TAIL_LABEL) + "  " if mid else " " * room
        text = term.clean(text)
        if not whole:
            _say(stream, text, room, head)
        elif not stream.tty or room + term.columns(text) <= stream.width():
            stream.put(head + text + "\n")
        else:
            if mid:
                stream.put(head.rstrip(" ") + "\n")
            stream.put(" " * LEAD + text + "\n")


def _ended(cmd, row, result, seconds):
    """A command that ended (row sc8 R7): one row, a second where it does not fit; a failed one's
    last lines whole under it, five at most (R6)."""
    t = cmd.t
    why = result["why"]
    failed = bool(why) or result["exit"] != 0
    if t.quiet and not failed:
        return
    if why == "interrupted":
        after = t.text("setup.stopped", seconds=seconds)
    elif why == "wall":
        after = t.text("setup.failed.wall", wall=result["wall"])
    elif why == "start":
        after = t.text("setup.failed.start")
        result = dict(result, tail=[result["last"]] if result["last"] else [])
    elif failed:
        after = t.text("setup.failed" if result.get("tail") else "setup.failed.silent", seconds=seconds)
    else:
        after = t.text("setup.took", seconds=seconds)
    t.out.flush()
    _rows(t, [("fail" if failed else "ok", row["n"], t.text("setup.step.%d" % row["n"]),
               row["command"] + " " + after, True)], err=True)
    if failed and why != "interrupted":
        for line in result.get("tail") or []:
            t.err.put(" " * LEAD + term.clean(line) + "\n")


def run(cmd, names):
    """setup without --dry-run. SIGINT and SIGTERM raise KeyboardInterrupt while it runs."""
    saved = {}
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            saved[sig] = signal.signal(sig, _interrupt)
    except ValueError:  # not the main thread: the default handlers stay
        pass
    try:
        return _run(cmd, names)
    finally:
        for sig, handler in saved.items():
            signal.signal(sig, handler)


def _before(cmd, names, build, the_plan, home, config):
    """The reads and the asking before the first command: the steps, or the run's exit."""
    t, o = cmd.t, cmd.opts
    steps = build()
    blocked = [s["subject"] for s in steps if s["state"] == "blocked"]
    old = old_python(steps)
    if old and o["json"]:  # no command of ours mends it, so the remedy is null (review 1 F2)
        raise cmd.Usage("blocked", "err.setup.blocked.old", None, version=old["version"],
                        floor=old["floor"], **cmd.slots())
    if old:
        the_plan(steps)
        t.flush()
        t.line("hint.setup.blocked.old", err=True, version=old["version"], floor=old["floor"])
        return 2
    if blocked:
        if o["json"]:
            raise cmd.Refusal("blocked", "err.setup.blocked", cmd.say("setup", "--dry-run"),
                            missing=", ".join(blocked), **cmd.slots())
        the_plan(steps)  # the close names the command typed, never a dry run (row ic1-close R3)
        t.hint("hint.setup.next", command=cmd.say("setup", *dict.fromkeys(cmd.words[1:])))
        return 2
    if not runnable(steps):
        return report(cmd, names, steps, [], [], None, None, home)
    # CI set: a pty there has nobody at it, on setup's path alone (row sc15-setup-pick R2,
    # review 1 F1); remove and update read `_terminal` as at the pin until they ask through pick
    terminal = _terminal(cmd) and not cmd.env.get("CI")
    if not terminal and any(s["n"] in (2, 3) and s["state"] == "todo" for s in steps):
        gate, why = gated(config, home, t)
        if why:
            raise cmd.Refusal("gate_unread", "err.setup.gate_unread", cmd.say("setup"),
                            path=plan.shown(gate, home), why=why, **cmd.slots())
        if gate:
            raise cmd.Refusal("gated", "err.setup.gated", cmd.say("setup"),
                            path=plan.shown(gate, home), **cmd.slots())
    the_plan(steps)  # under --yes too: the run's first screen (row sc8 R1; design/23 §5's sum)
    if not o["yes"]:
        if not (terminal and not o["json"]):
            raise cmd.Refusal("needs_yes", "err.setup.yes", cmd.say("setup", "--yes"), **cmd.slots())
        count = planned(steps)
        one = count == 1
        t.flush()  # the plan whole above the question, where stdout is a pipe (row ic1-close R4)
        try:  # the selector resting on no, else sm1's typed question (row sc15-setup-pick R1, R2)
            yes = pick.confirm(t, "setup.confirm.one" if one else "setup.confirm",
                               "setup.confirm.yes.one" if one else "setup.confirm.yes",
                               "setup.confirm.no", "setup.ask.one" if one else "setup.ask", count=count)
        except pick.NoTerminal:
            raise cmd.Refusal("needs_yes", "err.setup.yes", cmd.say("setup", "--yes"), **cmd.slots())
        except pick.Cancelled:
            yes = False
        except KeyboardInterrupt:  # a decline too, the terminal's ^C left on the line
            return declined(cmd, interrupted=True)
        if not yes:
            return declined(cmd)
    return steps


def declined(cmd, interrupted=False):
    """After a no (row sc8 R5; design/23 §5): a note that nothing ran, with no failure mark; the
    selector of plugins after a bare run, on a terminal (sc15 R4); `next:` setup. Exit 2."""
    t = cmd.t
    if interrupted:
        t.blank(err=True)
    _note(t, "setup.declined.interrupted" if interrupted else "setup.declined")
    if not interrupted and not cmd.words[1:] and not cmd.opts.get("pick"):
        t.line("setup.other", err=True, command=cmd.say("setup", "--pick"))
    t.hint("hint.setup.next", command=cmd.say("setup"))
    return 2


def _offered(env, lib):
    """{name: description} for each plugin of the agentik marketplace read with no network (R5):
    a clone's own marketplace file three folders over the package's lib, the file of the
    marketplace Claude Code knows, then public.json's names, with no description."""
    found = {}
    files = [] if agentik_install.is_frozen(lib) else [
        os.path.join(lib, os.pardir, os.pardir, os.pardir, ".claude-plugin", "marketplace.json")]
    for path in files:
        market = plan._read_json(path)
        if isinstance(market, dict) and market.get("name") == plan.MARKETPLACE:
            for p in market.get("plugins") or ():
                if isinstance(p, dict) and isinstance(p.get("name"), str):
                    found[p["name"]] = p.get("description") if isinstance(p.get("description"), str) else ""
    found.update(tools.descriptions(env))
    for name in tools.public(lib)["tools"]:
        found.setdefault(name, "")
    suite = plan.manifest(lib).get("name") or "suite"
    return {n: d for n, d in found.items() if tools.NAME.match(n) and n != suite}


def pick_names(cmd, nouns):
    """`setup --pick` (row sc15-setup-pick R5): the names to plan, as if typed after setup. One
    `many` over the marketplace's plugins, the default set first, `least` 1; with no terminal,
    or under --json, the names given, as with no --pick. Esc and Ctrl-C decline."""
    t, o, env, lib = cmd.t, cmd.opts, cmd.env, cmd.lib
    given = list(dict.fromkeys(nouns))
    if o["json"]:
        return given
    known = set(plan.known(env, lib))  # a row only for a name setup takes (review 1 F2)
    default = [n for n in plan.default_set(lib) if n in known]
    notes = {n: d for n, d in _offered(env, lib).items() if n in known}
    names = list(dict.fromkeys(default + sorted(n for n in notes if n not in default)
                               + [n for n in given if n not in notes and n not in default]))
    own = set(tools._own(env))
    options = [{"value": n, "label": n, "note": "; ".join(
        x for x in (t.text("setup.pick.installed") if n in own else "", notes.get(n, "")) if x)}
        for n in names]

    def check(text):
        return "" if tools.NAME.match(text) else t.text("err.setup.name", name=text)

    home = env.get("HOME") or ""
    flags = [f for f, key in (("--dry-run", "dry_run"), ("--yes", "yes")) if o[key]]

    def command(answers):  # the hint's words split, as an argv: a `~/` word is given whole
        line = cmd.say("setup", *(flags + [str(a) for a in answers["plugins"]]))
        return [os.path.join(home, w[2:]) if w.startswith("~/") and home else w for w in shlex.split(line)]

    question = {"id": "plugins", "prompt": "setup.pick", "kind": "many", "options": options,
                "default": given or default, "least": 1,
                "other": {"label": t.text("setup.pick.other"), "note": t.text("setup.pick.other.note"),
                          "check": check}}
    try:
        got = pick.ask(t, [question], command)
    except pick.NoTerminal:
        return given
    except (pick.Cancelled, KeyboardInterrupt) as e:
        if isinstance(e, KeyboardInterrupt):
            t.blank(err=True)
        raise cmd.Refusal("declined", "err.setup.declined", cmd.say("setup"), **cmd.slots())
    return list(dict.fromkeys(str(a) for a in got["plugins"]))


def _run(cmd, names):
    t, o, env, tool = cmd.t, cmd.opts, cmd.env, cmd.tool
    home = env.get("HOME") or ""
    config = env.get("CLAUDE_CONFIG_DIR") or os.path.join(home, ".claude")

    slots = cmd.slots()  # a held row names the config line (row fk2-plan R4)

    def build():
        steps = plan.build(names, env, cmd.lib, tool, cmd.version)
        for s in steps:
            s["detail"] = t.text(s["mid"], **dict(slots, **s["values"]))
        return steps

    def the_plan(steps):
        if not o["json"]:
            plan_screen(cmd, steps, names)

    try:
        steps = _before(cmd, names, build, the_plan, home, config)
    except KeyboardInterrupt:  # an interrupt before the first command declines, as at the question
        _ignore()
        return declined(cmd, interrupted=True)
    if isinstance(steps, int):
        return steps
    ran, wrote, done, failure, current = [], [], set(), None, None
    began = time.time()

    def record(row, before, old, result):
        after = look(home, config)
        new = [p for p in sorted(after) if after[p] != before.get(p)]
        if old is not None:
            root, there = install_root(env, row["subject"], getattr(cmd, "cwd", None))
            if there and (root != old[0] or not old[1]):
                new.append(root)
        wrote.extend(p for p in new if p not in wrote)
        ran.append({"n": row["n"], "command": row["command"], "exit": result["exit"], "result": result})
        if not o["json"]:
            _ended(cmd, row, result, int(round(time.time() - started)))

    try:
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
            started = time.time()
            before = look(home, config)
            old = install_root(env, row["subject"], getattr(cmd, "cwd", None)) if row["n"] == 3 else None
            current = (row, before, old)
            result = execute(command, env)
            current = None
            record(row, before, old, result)
            if result["why"] or result["exit"] != 0:
                failure = _failure(command, result)
                break
            steps = build()
    except KeyboardInterrupt:
        if current:
            row = current[0]
            record(*current, {"exit": None, "last": "", "why": "interrupted", "wall": None})
            failure = ("err.setup.interrupted", {"command": row["command"]}, INTERRUPTED, "interrupted")
        else:
            failure = ("err.setup.interrupted.idle", {}, INTERRUPTED, "interrupted")
    _ignore()  # from here the report and the journal end
    steps = build()
    return report(cmd, names, steps, ran, wrote, failure, journal_path(env, home), home,
                  int(round(time.time() - began)))


def _failure(command, result):
    values = {"command": command, "exit": result["exit"], "last": result["last"],
              "wall": result["wall"]}
    if result["why"] == "wall":
        return ("err.setup.wall" if result["last"] else "err.setup.wall.silent"), values
    if result["why"] == "start":
        return "err.setup.start", values
    return ("err.setup.step" if result["last"] else "err.setup.step.silent"), values


def report(cmd, names, steps, ran, wrote, failure, journal, home, seconds=0):
    t = cmd.t
    failure = failure and (tuple(failure) + (1, "step_failed"))[:4]  # (id, values, exit, JSON code)
    code = failure[2] if failure else 0
    journal_error = None
    if ran:
        wrote = wrote + ([journal] if journal not in wrote else [])
        entry = {"at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "verb": "setup", "version": cmd.version, "plugins": names,
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
               "steps": [step_json(s) for s in steps],
               "ran": [{k: r[k] for k in ("n", "command", "exit")} for r in ran],
               "wrote": wrote, "nothing": not ran, "journal": journal}
        if failure:
            mid, values = _closing(t, failure, ran)
            message = t.text(mid, **values)
            if failure[1].get("last"):  # the command's own last line, which the screen prints under its row
                message = t.text("err.setup.last", message=message, last=failure[1]["last"])
            obj["error"] = {"code": failure[3], "message": message, "remedy": cmd.say("setup")}
        t.json(obj)
        return code
    closing = failure and _closing(t, failure, ran)
    if not ran:
        done = all(s["state"] == "ok" for s in steps if s["n"] <= 5)
        t.line("setup.nothing" if done else "setup.nothing.left")
        if not failure and page_close(steps):  # the close's page stands above it (fh13 review 1 F1)
            show(cmd, [s for s in steps if s["line"] == "page"], lines=False)
    elif not failure:
        count = len(ran)
        t.line("setup.done.one" if count == 1 else "setup.done", count=count, seconds=seconds)
    rows = []
    if ran and wrote:
        rows.append(("setup.tail.wrote", t.text("setup.wrote.one") if len(wrote) == 1
                     else t.text("setup.wrote.count", count=len(wrote)), False))
    if ran and journal and not failure:
        rows.append(("setup.tail.log", plan.shown(journal, home), True))
    if not failure:
        rows.append(("setup.tail.check", cmd.slots()["doctor"], True))
        if undo(cmd):
            rows.append(("setup.tail.undo", undo(cmd), True))
        if add:  # only while ~/.local/bin is off PATH (row sc8 R2; D23-4)
            rows.extend(path_rows(cmd, add[0]["command"]))
    if rows:
        if not failure:
            t.blank()
        _tail(t, rows)
    if journal_error:
        t.error("err.setup.journal", path=plan.shown(journal_path(cmd.env, home), home), why=journal_error)
    if failure:
        t.flush()
        t.error(closing[0], cmd.say("setup"), **closing[1])
        return code
    if page_close(steps):  # fh13 R7: a note, since its line is no command
        _note(t, *page_close(steps)[:1], **page_close(steps)[1])
    t.hint("hint.setup.done")  # next: claude (row sc8 R3; D23-1)
    return code


def _closing(t, failure, ran):
    """The closing line of a run that stopped (row sc8 R6): (id, values), its step and what stands."""
    mid, values = failure[0], dict(failure[1])
    n = values.get("n") or (ran[-1]["n"] if ran else None)
    if mid in ("err.setup.step", "err.setup.step.silent", "err.setup.start"):
        if n == 2:
            return "err.setup.step.one", {"n": n}
        return "err.setup.step", {"n": n, "done": "1 and 2" if n == 3 else "1 to %d" % (n - 1)}
    if mid in ("err.setup.wall", "err.setup.wall.silent"):
        return "err.setup.wall", {"n": n, "wall": values["wall"]}
    if mid == "err.setup.interrupted":
        return mid, {"n": n}
    return mid, {k: v for k, v in values.items() if k == "n"}
