"""`update` (row ak4a-update): every installed tool and its command brought current in one call.

The hold comes first, before any other read or write (R3). The two tools it asks of are named by
the suite's table, never here: the runner, the tool whose status reads hold one named `run`, and
the tool whose status reads hold one named `unattended`. A runner's `run`, `gate` or `plan` in the
process list, read by the program's name and never by a path's or a value's text, or an
`unattended` read that answers other than `null` inside SESSION_WALL, holds the update, as does a
process list that cannot be read; then nothing runs and nothing is written. Then the plan of five
steps (R4): each marketplace once, `agentik` first; `claude plugin update T@M` for each tool the
finder gives a standing source of the user's (`own` or `plugin`), the suite last; setup's step 4
rows; setup's step 5 rows for the suite's own command and the door, where the suite stands, else
one note row and nothing written for it (R6); the doctor. Steps 1 and 2 always run, through
apply.execute; then the finder is read again and steps 3 and 4 are built from that read by
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
HOLDS = ("run", "gate", "plan")
ASSIGN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")  # where `ps -E` starts a process's environment
# setup's failure and ran-nothing lines, as update's own, so update's screen names the verb that
# ran (review 1 lead a); setup's own lines stay as they are
FAILS = {"err.setup.step": "err.update.step", "err.setup.step.silent": "err.update.step.silent",
         "err.setup.wall": "err.update.wall", "err.setup.wall.silent": "err.update.wall.silent",
         "err.setup.start": "err.update.start", "err.setup.todo": "err.update.todo",
         "err.setup.interrupted.idle": "err.update.interrupted.idle"}
PART = re.compile(r"[a-z0-9][a-z0-9-]*\Z")  # a plugin id's name and its marketplace (review 1 F2)


def reader(lib, read):
    """(the tool, the argv) of the suite's table whose status reads hold one named `read`, or None."""
    for name, row in sorted(tools.fallback(lib).items()):
        for r in row.get("status") or ():
            if isinstance(r, dict) and r.get("name") == read and isinstance(r.get("argv"), list):
                return name, [str(w) for w in r["argv"]]
    return None


def runner_pid(text, runner):
    """The pid of the first line whose program is the runner's (its name, its old `agent-` name or
    `agentik-` name) and whose words hold `run`, `gate` or `plan`, or `agentik <runner>` with one of
    them; the words stop at the first environment value, and a path's text is never a word (R3).
    The program is each prefix of the words in turn, joined by one space, so a runner under a path
    with a space holds (review 1 F3); where that reads an editor's two file words as a runner and
    its verb (`vim /x/<runner> run`), the update is held, the safe side. None when no line holds."""
    programs = (runner, "agent-" + runner, "agentik-" + runner)
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2 or not parts[0].isdigit():
            continue
        words = []
        for word in parts[1:]:
            if ASSIGN.match(word):
                break
            words.append(word)
        for k in range(1, len(words) + 1):
            program, rest = os.path.basename(" ".join(words[:k])), words[k:]
            if program in programs and any(w in HOLDS for w in rest):
                return parts[0]
            if program == "agentik" and rest[:1] == [runner] and len(rest) > 1 and rest[1] in HOLDS:
                return parts[0]
    return None


def _unattended(path, argv, env):
    """True when the tool at `path` answers `argv` with JSON other than null inside SESSION_WALL,
    whatever its exit (review 1 lead c); absent, slow, or text that is no JSON is False."""
    try:
        p = subprocess.Popen([path] + argv, stdin=subprocess.DEVNULL,
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
    try:
        return json.loads(out.decode("utf-8")) is not None
    except (ValueError, UnicodeDecodeError):
        return False


def hold(cmd):
    """The held text, or None (R3). It starts the process list and, where the finder says a file
    runs for the `unattended` read's tool, that file; it reads nothing else."""
    env = cmd.env
    ps = shutil.which("ps", path=env.get("PATH", ""))  # none on PATH: a list that cannot be read
    text = agentik_install.processes(ps, timeout=PS_WALL)[0] if ps else None
    if text is None:
        return cmd.t.text("update.held.ps")
    runner = reader(cmd.lib, "run")
    pid = runner and runner_pid(text, runner[0])
    if pid:
        return cmd.t.text("update.held.run", tool=runner[0], pid=pid)
    found = reader(cmd.lib, "unattended")
    if not found:
        return None
    row = tools.rows(env, cmd.lib, cmd.cwd, names=[found[0]])[found[0]]
    path = (row["runs"] or {}).get("path")
    if path and _unattended(path, found[1], env):
        return cmd.t.text("update.held.unattended")
    return None


def _standing(row):
    """True where the finder gives a standing source of the user's own: `own`, or `plugin` (R2)."""
    return row["kind"] in ("own", "plugin") and bool(row["plugin"]) and row["scope"] == "user"


def _market(pid):
    return pid.rpartition("@")[2]


def plugin_id(pid):
    """True where the id is `name@market`, each part lowercase letters, digits and dashes that
    begins with a letter or a digit, so no word read from the file is ever a command's option
    (review 1 F2)."""
    name, at, market = pid.partition("@") if isinstance(pid, str) else ("", "", "")
    return bool(at and PART.match(name) and PART.match(market))


class Update:
    def __init__(self, cmd, nouns):
        self.cmd, self.t, self.env, self.o = cmd, cmd.t, cmd.env, cmd.opts
        self.nouns = list(dict.fromkeys(nouns))
        self.home = self.env.get("HOME") or ""
        self.config = self.env.get("CLAUDE_CONFIG_DIR") or os.path.join(self.home, ".claude")
        self.bindir = os.path.join(self.home, ".local", "bin")
        self.slots = dict(cmd.slots(), setup=cmd.say("update"))  # setup's lines name this verb
        self.names, self.tools, self.skips, self.shown, self.absent, self.gone = [], [], {}, [], [], []
        self.suite, self.order = None, []  # a held run's JSON reads no scope (review 1 F1)

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
            if _standing(row) and not plugin_id(row["plugin"]):
                self.skips[name] = plan._step(2, "skip", "todo", name, "update.skip.id",
                                              id=term.clean(row["plugin"]))
                self.shown.append(name)
            elif _standing(row):
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
        step 5 rows for the suite's own command and the door, and the doctor (R4, R5, R6). A tool
        the finder now reads absent is gone and gets no row here (review 1 F4); a step 3 row of
        setup's that is not ok is shown with its command and left for the person to run (F5)."""
        cmd = self.cmd
        read = tools.rows(self.env, cmd.lib, cmd.cwd, names=[e["name"] for e in self.order]) if self.order else {}
        self.gone = [e for e in self.order if read[e["name"]]["kind"] == "absent"]
        names = [e["name"] for e in self.tools if e not in self.gone]
        built = plan.build(names, self.env, cmd.lib, cmd.tool, cmd.version)
        self.prereqs = [s for s in built if s["n"] == 1]
        steps = [dict(s, n=3, left=True) for s in built if s["n"] == 3 and s["state"] != "ok"]
        steps += [dict(s, n=3) for s in built if s["n"] == 4]
        if self.suite and self.suite not in self.gone:
            row = read[SUITE]
            root, ver = row["root"], row["version"]
            if isinstance(root, str) and isinstance(ver, str) and ver:
                own = plan.build([], self.env, os.path.join(root, "lib"), cmd.tool, ver)
                steps += [dict(s, n=4) for s in own if s["n"] == 5]
        elif SUITE in self.names and SUITE not in self.skips:
            steps.append(plan._step(4, "suite", "ok", cmd.tool, "update.suite.checkout", version=cmd.version))
        steps.append(plan._step(5, "doctor", "todo", "doctor", "update.doctor", cmd.say("doctor")))
        if any(s["state"] == "blocked" for s in self.prereqs):
            for s in steps:
                s["command"] = None if s["id"] != "doctor" else s["command"]
        return steps

    def runnable(self, steps):
        return [s for s in steps if s["n"] in (1, 2, 3, 4) and s["state"] == "todo" and s["command"]
                and s["line"] == "run" and not s.get("left")]

    def title(self):
        if self.shown:
            self.t.line("update.plan.dry" if self.o["dry_run"] else "update.plan", names=", ".join(self.shown))
        elif self.absent:  # a name typed that is listed and not installed (review 1 lead b)
            self.t.line("update.plan.absent" if len(self.absent) == 1 else "update.plan.absent.many",
                        names=", ".join(self.absent))
        else:
            self.t.line("update.plan.none")

    # ---- the close (R6, R7, R8) -----------------------------------------------------------------

    def hints(self):
        if self.suite is None and SUITE in self.names and SUITE not in self.skips:
            listed = SUITE in tools.descriptions(self.env)
            self.t.hint("hint.update.suite" if listed else "hint.update.suite.pull", **self.slots)
        missing = self.absent + [e["name"] for e in self.gone]
        if missing:
            self.t.hint("hint.update.setup", command=self.cmd.say("setup", *missing), names=", ".join(missing))

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
            self.t.error("err.update.journal", path=plan.shown(path, self.home), why=e.strerror or str(e))
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
                raise self.cmd.Usage("blocked", "err.update.blocked", self.cmd.say("update", "--dry-run"),
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
                raise self.cmd.Usage("needs_yes", "err.update.yes", self.cmd.say("update", "--yes"), **self.slots)
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
            raise self.cmd.Usage("declined", "err.update.declined", self.cmd.say("update"), **self.slots)

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
        left = [] if failure else [s for s in self.detail(self.tail()) if s.get("left")]  # F4, F5
        if left or (self.gone and not failure):
            code = 1
        if ran:
            wrote = self.journal(ran, wrote, code)
        rows = tools.rows(self.env, self.cmd.lib, self.cmd.cwd, names=[e["name"] for e in self.order])
        after = {name: row["version"] for name, row in rows.items()}
        commands = [r["command"] for r in ran]
        if failure:
            mid = FAILS.get(failure[0], failure[0])
            message = t.text(mid, **dict(self.slots, **failure[1]))
            if self.o["json"]:
                self.json(False, steps, after, commands, wrote,
                          error={"code": "step_failed", "message": message, "remedy": self.cmd.say("update")})
            else:
                t.flush()
                t.error(mid, **dict(self.slots, **failure[1]))
            return code
        short = None
        if left:
            short = ("err.update.left" if left[0]["command"] else "err.update.left.none",
                     dict(self.slots, subject=left[0]["subject"], command=left[0]["command"] or ""))
        gone = [e["name"] for e in self.gone]
        groups, failed, warned, total, entries = doctor.read(self.cmd)
        if self.o["json"]:
            error = None
            if short:
                error = {"code": "step_todo", "message": t.text(short[0], **short[1]),
                         "remedy": left[0]["command"] or self.cmd.say("update")}
            elif gone:
                error = {"code": "not_installed", "message": self.gone_text(self.gone[0]),
                         "remedy": self.cmd.say("setup", *gone)}
            self.json(code == 0, steps, after, commands, wrote, checked={"failed": failed, "warned": warned},
                      error=error)
            return code
        moved = [e for e in self.order if e not in self.gone and after.get(e["name"]) != e["from"]]
        if not moved and not placed and not gone and not left:  # no row is left to do (F5)
            t.line("update.nothing")
        else:
            t.table([("fail", [self.gone_text(e)], None) if e in self.gone else
                     ("ok", [t.text("update.tool.moved", name=e["name"], old=e["from"], new=after.get(e["name"]))
                             if e in moved else
                             t.text("update.tool.same", name=e["name"], version=e["from"])], None)
                     for e in self.order])
        if left:
            apply.show(self.cmd, left)
        self.hints()
        doctor.screen(self.cmd, groups, failed, warned, total, entries)
        if short:
            t.flush()
            t.error(short[0], **short[1])
        return code

    def gone_text(self, e):
        return self.t.text("update.tool.gone", name=e["name"], version=e["from"] or "?")

    def root(self, row):
        name = row["subject"].rpartition("@")[0]
        found = tools.rows(self.env, self.cmd.lib, self.cmd.cwd, names=[name])[name]["root"]
        return found if isinstance(found, str) else None


def do_update(cmd, nouns):
    return Update(cmd, nouns).main()
