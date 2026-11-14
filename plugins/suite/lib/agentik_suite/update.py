"""`update` (row ak4a-update): every installed tool and its command brought current in one call.

The hold comes first, before any other read or write (R3): a relay `run`, `gate` or `plan` in
the process list, read by the program's name and never by a path's or a value's text, or a session
tool whose `unattended status --json` answers other than `null` inside SESSION_WALL, holds the
update, as does a process list that cannot be read; then nothing runs and nothing is written. Then
the plan of five steps (R4): each marketplace once, `agentik` first; `claude plugin update T@M` for
each tool the finder gives a standing source of the user's (`own` or `plugin`), the suite last;
setup's step 4 rows; setup's step 5 rows for the suite's own command and the door, where the suite
stands, else one note row and nothing written for it (R6); the doctor. Steps 1 and 2 always run,
through apply.execute; then the finder is read again and steps 3 and 4 are built from that read by
plan.build (R5). A failed command stops the run, exit 1, with no rollback. The doctor's read runs
once after step 4 and its rows close the screen; the exit is the update's (R7). It writes no gate
list's settings file itself: a plugin update moves installed_plugins.json alone (R9, hq measured).
"""
import datetime
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys

import agentik_install

from . import apply, doctor, plan, term, tools

SCHEMA = "agentik.update/1"
SESSION_WALL = 10
PS_WALL = 10
SUITE = "suite"
SESSION = "session"
RELAYS = ("relay", "agent" + "-relay", "agentik-relay")  # split: the scan reads the old name as renamed
HOLDS = ("run", "gate", "plan")
ASSIGN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")  # where `ps -E` starts a process's environment


def relay_pid(text):
    """The pid of the first line whose program is a relay's and whose words hold `run`, `gate` or
    `plan`, or `agentik relay` with one of them; the words stop at the first environment value, and
    a path's text is never a word (R3). None when no line holds."""
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2 or not parts[0].isdigit():
            continue
        words = []
        for word in parts[2:]:
            if ASSIGN.match(word):
                break
            words.append(word)
        program = os.path.basename(parts[1])
        if program in RELAYS and any(w in HOLDS for w in words):
            return parts[0]
        if program == "agentik" and words[:1] == ["relay"] and len(words) > 1 and words[1] in HOLDS:
            return parts[0]
    return None


def _unattended(path, env):
    """True when the session tool at `path` answers `unattended status --json` with JSON other than
    null, exit 0, inside SESSION_WALL; absent, slow or unreadable is False."""
    try:
        p = subprocess.Popen([path, "unattended", "status", "--json"], stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=dict(env),
                             start_new_session=True)
    except (OSError, ValueError):
        return False
    try:
        out, _ = p.communicate(timeout=SESSION_WALL)
    except subprocess.TimeoutExpired:
        apply._kill(p.pid)
        p.kill()
        p.communicate()
        return False
    if p.returncode != 0:
        return False
    try:
        return json.loads(out.decode("utf-8")) is not None
    except (ValueError, UnicodeDecodeError):
        return False


def hold(cmd):
    """The held text, or None (R3). It starts the process list and, where the finder says a file
    runs for the session tool, that file; it reads nothing else."""
    env = cmd.env
    ps = shutil.which("ps", path=env.get("PATH", ""))  # none on PATH: a list that cannot be read
    text = agentik_install.processes(ps, timeout=PS_WALL)[0] if ps else None
    if text is None:
        return cmd.t.text("update.held.ps")
    pid = relay_pid(text)
    if pid:
        return cmd.t.text("update.held.relay", pid=pid)
    row = tools.rows(env, cmd.lib, cmd.cwd, names=[SESSION])[SESSION]
    path = (row["runs"] or {}).get("path")
    if path and _unattended(path, env):
        return cmd.t.text("update.held.unattended")
    return None


def _standing(row):
    """True where the finder gives a standing source of the user's own: `own`, or `plugin` (R2)."""
    return row["kind"] in ("own", "plugin") and bool(row["plugin"]) and row["scope"] == "user"


def _market(pid):
    return pid.rpartition("@")[2]


class Update:
    def __init__(self, cmd, nouns):
        self.cmd, self.t, self.env, self.o = cmd, cmd.t, cmd.env, cmd.opts
        self.nouns = list(dict.fromkeys(nouns))
        self.home = self.env.get("HOME") or ""
        self.config = self.env.get("CLAUDE_CONFIG_DIR") or os.path.join(self.home, ".claude")
        self.bindir = os.path.join(self.home, ".local", "bin")
        self.slots = dict(cmd.slots(), setup=cmd.say("update"))  # setup's lines name this verb

    # ---- the scope (R2) ---------------------------------------------------------------------

    def scope(self):
        known = tools.known(self.env, self.cmd.lib)
        for name in self.nouns:
            if name not in known and name != SUITE:
                raise self.cmd.Refusal("bad_name", "err.setup.name", self.cmd.say("update", "--dry-run"),
                                       name=name)
        names = self.nouns or [n for n in known if n != SUITE] + [SUITE]
        self.names = [n for n in names if n != SUITE] + ([SUITE] if SUITE in names else [])
        rows = tools.rows(self.env, self.cmd.lib, self.cmd.cwd, names=self.names)
        self.tools, self.skips, self.shown, self.absent = [], {}, [], []
        self.suite = None
        for name in self.names:
            row = rows[name]
            if _standing(row):
                entry = {"name": name, "plugin": row["plugin"], "from": row["version"]}
                if name == SUITE:
                    self.suite = entry
                else:
                    self.tools.append(entry)
                self.shown.append(name)
            elif name == SUITE:
                self.shown.append(name)
            elif row["kind"] == "absent":
                if name in self.nouns:
                    self.absent.append(name)
            elif row["kind"] == "folder":
                self.skips[name] = plan._step(2, "skip", "todo", name, "update.skip.folder", name=name)
                self.shown.append(name)
            else:
                step = plan._plugin_row(2, name, row, self.home)[0]
                step["command"] = None
                self.skips[name] = step
                self.shown.append(name)
        self.order = self.tools + ([self.suite] if self.suite else [])

    # ---- the plan (R4) ------------------------------------------------------------------------

    def detail(self, steps):
        for s in steps:
            s["detail"] = self.t.text(s["mid"], **dict(self.slots, **s["values"]))
        return steps

    def head(self):
        """Steps 1 and 2, and the step 1 rows of setup's plan where one is blocked."""
        markets = list(dict.fromkeys(_market(e["plugin"]) for e in self.order))
        markets.sort(key=lambda m: m != plan.MARKETPLACE)  # agentik first, the rest as met
        steps = [plan._step(1, "marketplace", "todo", m, "update.market",
                            "claude plugin marketplace update %s" % shlex.quote(m)) for m in markets]
        updates = {e["name"]: plan._step(2, "plugin", "todo", e["plugin"], "update.plugin",
                                         "claude plugin update %s" % shlex.quote(e["plugin"]),
                                         version=e["from"] or "?") for e in self.order}
        for name in self.names:
            if name in updates:
                steps.append(updates[name])
            elif name in self.skips:
                steps.append(self.skips[name])
        return steps

    def tail(self):
        """Steps 3 to 5, from the finder as it reads now: setup's step 4 rows for each tool, its
        step 5 rows for the suite's own command and the door, and the doctor (R4, R5, R6)."""
        cmd = self.cmd
        names = [e["name"] for e in self.tools]
        built = plan.build(names, self.env, cmd.lib, cmd.tool, cmd.version)
        self.prereqs = [s for s in built if s["n"] == 1]
        steps = [dict(s, n=3) for s in built if s["n"] == 4]
        if self.suite:
            row = tools.rows(self.env, cmd.lib, cmd.cwd, names=[SUITE])[SUITE]
            root, ver = row["root"], row["version"]
            if isinstance(root, str) and isinstance(ver, str) and ver:
                own = plan.build([], self.env, os.path.join(root, "lib"), cmd.tool, ver)
                steps += [dict(s, n=4) for s in own if s["n"] == 5]
        elif SUITE in self.names:
            steps.append(plan._step(4, "suite", "ok", cmd.tool, "update.suite.checkout", version=cmd.version))
        steps.append(plan._step(5, "doctor", "todo", "doctor", "update.doctor", cmd.say("doctor")))
        if any(s["state"] == "blocked" for s in self.prereqs):
            for s in steps:
                s["command"] = None if s["id"] != "doctor" else s["command"]
        return steps

    def runnable(self, steps):
        return [s for s in steps if s["n"] in (1, 2, 3, 4) and s["state"] == "todo" and s["command"]
                and s["line"] == "run"]

    def title(self):
        if self.shown:
            self.t.line("update.plan.dry" if self.o["dry_run"] else "update.plan", names=", ".join(self.shown))
        else:
            self.t.line("update.plan.none")

    # ---- the close (R6, R7, R8) -----------------------------------------------------------------

    def hints(self):
        if self.suite is None and SUITE in self.names:
            listed = SUITE in tools.descriptions(self.env)
            self.t.hint("hint.update.suite" if listed else "hint.update.suite.pull", **self.slots)
        if self.absent:
            self.t.hint("hint.update.setup", command=self.cmd.say("setup", *self.absent),
                        names=", ".join(self.absent))

    def launcher(self, name):
        found = agentik_install.read_launcher(os.path.join(self.bindir, "agentik-" + name))
        return (found or {}).get("version")

    def tool_json(self, after):
        return [{"name": e["name"], "plugin": e["plugin"], "from": e["from"],
                 "to": after.get(e["name"]) if after is not None else None,
                 "launcher": self.launcher(e["name"])} for e in self.order]

    def skipped_json(self, steps):
        found = [{"name": name, "why": s["detail"]} for name, s in self.skips.items()]
        found += [{"name": SUITE, "why": s["detail"]} for s in steps if s["mid"] == "update.suite.checkout"]
        return found

    def json(self, ok, steps, after=None, ran=(), wrote=(), checked=None, error=None, held=None):
        obj = {"schema": SCHEMA, "ok": ok, "held": held, "dry_run": bool(self.o["dry_run"]),
               "tools": self.tool_json(after), "skipped": self.skipped_json(steps),
               "ran": list(ran), "wrote": list(wrote), "doctor": checked}
        if self.o["dry_run"]:
            obj["steps"] = [apply.step_json(s) for s in steps]
        if error:
            obj["error"] = error
        self.t.json(obj)

    def journal(self, ran, wrote, code):
        path = apply.journal_path(self.env, self.home)
        entry = {"at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "verb": "update", "version": self.cmd.version, "plugins": self.names,
                 "ran": [{k: r[k] for k in ("n", "command", "exit")} for r in ran],
                 "wrote": wrote + [path], "exit": code}
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            term.append(path, json.dumps(entry) + "\n")
        except OSError as e:
            self.t.error("err.setup.journal", path=plan.shown(path, self.home), why=e.strerror or str(e))
            return wrote
        return wrote + [path]

    # ---- the verb ---------------------------------------------------------------------------

    def held(self, what):
        if self.o["json"]:
            self.json(False, [], held=what)
        else:
            self.t.error("err.update.held", what=what)
            again = self.cmd.say("update", *(self.nouns + (["--dry-run"] if self.o["dry_run"] else [])))
            self.t.hint("hint.update.held", command=again)
        return 2

    def main(self):
        for name in self.nouns:
            if not tools.NAME.match(name):
                raise self.cmd.Refusal("bad_name", "err.setup.name", self.cmd.say("update", "--dry-run"),
                                       name=name)
        what = hold(self.cmd)
        if what:
            return self.held(what)
        self.scope()
        steps = self.detail(self.head() + self.tail())
        blocked = [s for s in self.prereqs if s["state"] == "blocked"]
        if blocked:
            steps = self.detail(blocked) + steps
        t, o = self.t, self.o
        if o["dry_run"]:
            if o["json"]:
                self.json(True, steps)
                return 0
            self.title()
            apply.show(self.cmd, steps)
            self.hints()
            return 0
        if blocked:
            missing = ", ".join(s["subject"] for s in blocked)
            if o["json"]:
                raise self.cmd.Usage("blocked", "err.setup.blocked", self.cmd.say("update", "--dry-run"),
                                     missing=missing, **self.slots)
            self.title()
            apply.show(self.cmd, steps)
            t.hint("hint.setup.blocked", missing=missing, **self.slots)
            return 2
        if not o["json"]:
            self.title()
            apply.show(self.cmd, steps)
        todo = self.runnable(steps)
        if todo and not o["yes"]:
            if not apply._terminal(self.cmd) or o["json"]:
                raise self.cmd.Usage("needs_yes", "err.setup.yes", self.cmd.say("update", "--yes"), **self.slots)
            self.ask(len(todo))
        return self.run(steps)

    def ask(self, count):
        t = self.t
        t.line("setup.ask.one" if count == 1 else "setup.ask", err=True, count=count)
        t.flush()
        try:
            answer = sys.stdin.readline()
        except (OSError, ValueError):
            answer = ""
        except KeyboardInterrupt:
            answer = None
            t.blank(err=True)
        if (answer or "").strip().lower() not in ("y", "yes"):
            raise self.cmd.Usage("declined", "err.setup.declined", self.cmd.say("update"), **self.slots)

    def execute(self, row, ran, wrote):
        """One command, as setup runs one; its result."""
        if not self.t.quiet:
            self.t.line("setup.running", err=True, command=row["command"])
            self.t.flush()
        before = apply.look(self.home, self.config)
        result = apply.execute(row["command"], self.env)
        after = apply.look(self.home, self.config)
        wrote.extend(p for p in sorted(after) if after[p] != before.get(p) and p not in wrote)
        ran.append({"n": row["n"], "command": row["command"], "exit": result["exit"]})
        return result

    def run(self, steps):
        saved = {}
        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                saved[sig] = signal.signal(sig, apply._interrupt)
        except ValueError:  # not the main thread
            pass
        try:
            return self._run(steps)
        finally:
            for sig, handler in saved.items():
                signal.signal(sig, handler)

    def _run(self, steps):
        t, ran, wrote, failure, placed = self.t, [], [], None, False
        try:
            for row in [s for s in steps if s["n"] in (1, 2) and s["command"]]:  # always run (R5)
                old = self.root(row) if row["n"] == 2 else None
                result = self.execute(row, ran, wrote)
                if result["why"] or result["exit"] != 0:
                    failure = apply._failure(row["command"], result)
                    break
                new = self.root(row) if row["n"] == 2 else None
                if new and new != old and new not in wrote:
                    wrote.append(new)
            done = set()
            while failure is None:  # steps 3 and 4 from the finder read again, after each command
                rows = self.runnable(self.detail(self.tail()))
                if not rows:
                    break
                if rows[0]["command"] in done:
                    failure = ("err.setup.todo", {"command": rows[0]["command"], "n": rows[0]["n"]})
                    break
                done.add(rows[0]["command"])
                placed = True
                result = self.execute(rows[0], ran, wrote)
                if result["why"] or result["exit"] != 0:
                    failure = apply._failure(rows[0]["command"], result)
        except KeyboardInterrupt:
            apply._ignore()
            failure = ("err.setup.interrupted.idle", {}, apply.INTERRUPTED)
        apply._ignore()
        code = (failure[2] if len(failure) > 2 else 1) if failure else 0
        if ran:
            wrote = self.journal(ran, wrote, code)
        rows = tools.rows(self.env, self.cmd.lib, self.cmd.cwd, names=[e["name"] for e in self.order])
        after = {name: row["version"] for name, row in rows.items()}
        commands = [r["command"] for r in ran]
        if failure:
            message = t.text(failure[0], **dict(self.slots, **failure[1]))
            if self.o["json"]:
                self.json(False, steps, after, commands, wrote,
                          error={"code": "step_failed", "message": message, "remedy": self.cmd.say("update")})
            else:
                t.flush()
                t.error(failure[0], **dict(self.slots, **failure[1]))
            return code
        groups, failed, warned, total, entries = doctor.read(self.cmd)
        if self.o["json"]:
            self.json(True, steps, after, commands, wrote, checked={"failed": failed, "warned": warned})
            return 0
        moved = [e for e in self.order if after.get(e["name"]) != e["from"]]
        if not moved and not placed:
            t.line("update.nothing")
        else:
            t.table([("ok", [t.text("update.tool.moved", name=e["name"], old=e["from"], new=after.get(e["name"]))
                             if e in moved else
                             t.text("update.tool.same", name=e["name"], version=e["from"])], None)
                     for e in self.order])
        self.hints()
        doctor.screen(self.cmd, groups, failed, warned, total, entries)
        return 0

    def root(self, row):
        name = row["subject"].rpartition("@")[0]
        found = tools.rows(self.env, self.cmd.lib, self.cmd.cwd, names=[name])[name]["root"]
        return found if isinstance(found, str) else None


def do_update(cmd, nouns):
    return Update(cmd, nouns).main()
