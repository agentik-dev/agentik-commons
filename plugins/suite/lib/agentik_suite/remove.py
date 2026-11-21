"""`remove` (row ak4-remove): setup's plan reversed, a tool taken off and every path it kept named.

The hold comes first, update's (R2): a runner's live run or an unattended run, or a process list that
cannot be read, holds the run, exit 2, nothing written; then each chosen tool's
`agentik_install.uninstall(dry=True)`, where a row `kept: held` holds it the same way, before any
`claude` command runs. A tool is taken off where the finder's row is `own` at the user's scope,
or where the plugin is absent and its launcher stands (R3); any other kind is a kept row with no
command, its launcher left. Its steps (R4): `claude plugin uninstall <name>@agentik --keep-data`
where it is installed, then `uninstall("agentik-<name>")`. With `--all`, after every tool (R5):
the suite's own plugin where it is listed at the user's scope, then the `agentik` marketplace
where it is the one setup adds, so every plugin goes before its marketplace (row rm1-leave-clean
R4), the suite's launcher, trees and the door, then the agentik cache folder by the install
module's own walk, which follows no link. Config and state folders, and Claude Code's data and
cache folders for each tool and the suite, are listed and kept (R7), each folder once. Step 5 may remove
the tree this code runs from (R6): every module is imported at the top, the catalogue is in
memory and each slot is filled before it, and after it nothing is read from the tree.
"""
import datetime
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys

import agentik_install

from . import apply, plan, settings, sources, term, tools, update

SCHEMA = "agentik.remove/1"
SUITE = "suite"
PARENTS = 32  # the most parents `spare` walks up
FAILS = {"err.setup.step": "err.remove.step", "err.setup.step.silent": "err.remove.step.silent",
         "err.setup.wall": "err.remove.wall", "err.setup.wall.silent": "err.remove.wall.silent",
         "err.setup.start": "err.remove.start", "err.setup.interrupted.idle": "err.remove.interrupted.idle"}
KIND = {"folder": "remove.kept.folder", "plugin": "remove.kept.plugin", "undecided": "remove.kept.undecided",
        "own": "remove.kept.scope"}


def spare(env, pid=None):
    """This process and its parents, by `ps -o ppid=`; a walk that cannot read a parent stops."""
    pid = pid or os.getpid()
    found = [str(pid), str(os.getppid())]
    ps = shutil.which("ps", path=env.get("PATH", ""))
    here = os.getppid()
    while ps and here > 1 and len(found) < PARENTS:
        try:
            p = subprocess.Popen([ps, "-o", "ppid=", "-p", str(here)], stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except (OSError, ValueError):
            break
        try:
            out = p.communicate(timeout=update.PS_WALL)[0].decode("ascii", "replace").split()
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()
            break
        if len(out) != 1 or not out[0].isdigit():
            break
        here = int(out[0])
        found.append(str(here))
    return list(dict.fromkeys(found))


def held_of(rows):
    """What holds the first `kept: held` row of uninstall's rows, or None."""
    for _, _, fate in rows:
        if fate.startswith("kept: held"):
            return fate[len("kept: held, "):] or fate
    return None


def guarded(env, home, keep=()):
    """What the cache folder's walk may never reach (review 1's F1): the config home and the state
    home as the suite resolves them, Claude Code's folder (`CLAUDE_CONFIG_DIR` and `~/.claude`
    both, review 2's G1), and each path of `keep`."""
    config = env.get("XDG_CONFIG_HOME") or ""
    found = [config if os.path.isabs(config) else os.path.join(home, ".config"),
             os.path.dirname(os.path.dirname(apply.journal_path(env, home))), sources.config_dir(env),
             os.path.join(home, ".claude") if home else ""]
    return [p for p in found + list(keep) if p]


def user_path(home, user):
    """A catalogue entry's `user_file` as a path, `~/` read as the home; None where it names none."""
    if not isinstance(user, str) or not user:
        return None
    return os.path.join(home, user[2:]) if user.startswith("~/") else user


def once(found):
    """(path, why) pairs, a folder once: keyed on its real path, its first path kept as given, so it
    is tested and shown there (rm1 R5; its review 1, F3: `..` after a link, normalised, names another
    folder)."""
    out = {}
    for p, why in found:
        out.setdefault(os.path.realpath(p), (p, why))
    return list(out.values())


def cache_fate(env, home, guard=(), acted=()):
    """(the agentik cache folder, None where it goes or the reason it stays, the root its walk may
    remove under, the guarded path it would have reached or None). It goes only where it is a real
    folder, no link, at the cache home's real path plus `agentik`, the cache home is neither `/`
    nor the home folder (R5), its real path is no home and holds none, and it is not, does not lie
    under and does not hold any path of `guard` (F1, F2), nor of `acted`, the bin and share folders
    steps 2 and 5 act on (G4), which is read before the link check, since the door is a link or a
    file. A relative `XDG_CACHE_HOME` is ignored."""
    base = env.get("XDG_CACHE_HOME") or ""
    if not os.path.isabs(base):
        base = os.path.join(home, ".cache")
    path = os.path.join(base, "agentik")
    real = os.path.realpath(base)
    root = os.path.join(real, "agentik")
    if not os.path.lexists(path):
        return path, "", root, None
    homes = agentik_install._homes(env)
    if real == "/" or real in homes:
        return path, "remove.cache.home", root, None
    for found in acted:
        real_found = os.path.realpath(found)
        if agentik_install._under(root, real_found) or agentik_install._under(real_found, root):
            return path, "remove.cache.acted", root, found
    if not agentik_install._real_dir(path):
        return path, "remove.cache.link", root, None
    if os.path.realpath(path) != root:
        return path, "remove.cache.place", root, None
    for found in sorted(homes):
        if agentik_install._under(found, root):
            return path, "remove.cache.guard", root, found
    for found in guard:
        real_found = os.path.realpath(found)
        if agentik_install._under(root, real_found) or agentik_install._under(real_found, root):
            return path, "remove.cache.guard", root, found
    return path, None, root, None


class Remove:
    def __init__(self, cmd, nouns):
        self.cmd, self.t, self.env, self.o = cmd, cmd.t, cmd.env, cmd.opts
        self.nouns = list(dict.fromkeys(nouns))
        self.all = bool(self.o["remove_all"])
        self.home = self.env.get("HOME") or ""
        self.config = sources.config_dir(self.env)
        self.prefix = os.path.join(self.home, ".local")
        self.bindir = os.path.join(self.prefix, "bin")
        self.slots = dict(cmd.slots(), setup=cmd.say("remove"))
        self.tools, self.others, self.extra, self.keep = [], [], [], []
        self.spare, self.suite_rows, self.cache, self.cache_root = (), [], (None, ""), None
        self.user_files = {}  # {tool: the `user` layer its config read names, or None} (ak10c5 R6)
        self.guard = []  # every path R7 names, standing or not: the cache walk reaches none (F1)
        self.soft = set()  # kept rows named only where they stand: gone after the run, no fault
        self.remedy = cmd.say("remove")  # every word the close prints, filled before step 5 (R6)

    # ---- which tools (R3), what they keep (R7) ------------------------------------------------

    def shown(self, path):
        return plan.shown(path, self.home)

    def launcher(self, name):
        return os.path.join(self.bindir, "agentik-" + name)

    def scope(self):
        known = tools.known(self.env, self.cmd.lib)
        for name in self.nouns:
            if name not in known and name != SUITE and not os.path.lexists(self.launcher(name)):
                raise self.cmd.Refusal("bad_name", "err.setup.name", self.cmd.say("remove", "--all", "--dry-run"),
                                       name=name)
        names = [n for n in known if n != SUITE] if self.all else self.nouns
        rows = tools.rows(self.env, self.cmd.lib, self.cmd.cwd, names=[n for n in names if n != SUITE])
        # each tool's user file, from the `user` layer of its config read, asked before anything is
        # removed; a tool that gives no answer has none (row ak10c5-table-gone R6)
        configs = tools.answered(self.env, rows, read=True)[1]
        self.user_files.update({n: tools.user_layer(tools.counted_config(*configs[n][:2]))
                                for n in configs if configs[n][2] == "ran"})
        for name in names:
            if name == SUITE:
                self.others.append(plan._step(1, "kept", "ok", name, "remove.kept.suite"))
                continue
            row = rows[name]
            own = row["kind"] == "own" and row["scope"] == "user" and row["plugin"] == name + "@agentik"
            if own or (row["kind"] == "absent" and os.path.lexists(self.launcher(name))):
                self.tools.append({"name": name, "plugin": row["plugin"] if own else None,
                                   "keep": self.kept(name, row, self.user_files.get(name))})
            elif row["kind"] != "absent":
                self.others.append(plan._step(1, "kept", "ok", name, KIND.get(row["kind"], "remove.kept.plugin"),
                                              name=name, id=term.clean(row["plugin"] or name),
                                              scope=row["scope"] or "?"))

    def old_state(self, name, row):
        """The tool's old state folder name, from its frozen tree's conf, else its plugin's."""
        found = agentik_install.read_launcher(self.launcher(name)) or {}
        for lib in (found.get("tree"), os.path.join(row["root"], "lib") if isinstance(row["root"], str) else None):
            if not lib:
                continue
            try:
                conf = agentik_install.names(lib)
            except (OSError, ValueError):
                continue
            if conf.get("tool_name") == "agentik-" + name:
                return conf.get("old_state") or ""
        return ""

    def kept(self, name, row, user_file):
        state = os.path.dirname(os.path.dirname(apply.journal_path(self.env, self.home)))
        base = os.path.dirname(os.path.dirname(settings.user_path(self.env)))
        found = [(os.path.join(base, name), "remove.keep.config")]
        user = user_path(self.home, user_file)
        if user:
            found.append((user, "remove.keep.config"))
        found.append((os.path.join(state, "agentik-" + name), "remove.keep.state"))
        old = self.old_state(name, row)
        if old and "/" not in old:
            found.append((os.path.join(state, old), "remove.keep.state"))
        found += [(os.path.join(self.config, "plugins", "data", name + "@agentik"), "remove.keep.data"),
                  (os.path.join(self.config, "plugins", "cache", "agentik", name), "remove.keep.cache")]
        self.guard += [p for p, _ in found]
        return once([(p, why) for p, why in found if os.path.lexists(p)])  # `a/` and `a`: one folder (rm1 R5)

    # ---- the plan (R4, R5) ---------------------------------------------------------------------

    def uninstall(self, tool, door=False, dry=True):
        try:
            return agentik_install.uninstall(tool, self.prefix, door=door, dry=dry, spare=self.spare)
        except ValueError as e:
            return [(self.launcher(tool[len("agentik-"):]), "launcher", "kept: " + str(e))]

    def market(self):
        known = plan._read_json(os.path.join(self.config, "plugins", "known_marketplaces.json"))
        entry = known.get(plan.MARKETPLACE) if isinstance(known, dict) else None
        if not isinstance(entry, dict):
            return None
        source = entry.get("source") if isinstance(entry.get("source"), dict) else {}
        return source.get("repo") == plan.SOURCE, term.clean(source.get("repo") or source.get("path")
                                                               or source.get("url") or "?")

    def suite_listed(self):
        return any(e["plugin"] == SUITE + "@" + plan.MARKETPLACE and (e["scope"] or "user") == "user"
                   for e in sources.entries(self.env))

    def rows_steps(self, n, rows):
        return [plan._step(n, "path", "todo" if fate == "would remove" else "ok", self.shown(path), "remove.row",
                           what=what, fate=fate) for path, what, fate in rows]

    def build(self):
        """The plan's steps, and the held text where a row is held (R2)."""
        steps, held = list(self.others), None
        for e in self.tools:
            if e["plugin"]:
                steps.append(plan._step(1, "plugin", "todo", e["plugin"], "remove.plugin",
                                        "claude plugin uninstall %s --keep-data" % shlex.quote(e["plugin"])))
            e["rows"] = self.uninstall("agentik-" + e["name"])
            steps += self.rows_steps(2, e["rows"])
            self.keep += e["keep"]
        if self.all:
            if self.suite_listed():  # every plugin before its marketplace (rm1 R4)
                steps.append(plan._step(3, "plugin", "todo", SUITE + "@" + plan.MARKETPLACE, "remove.suite",
                                        "claude plugin uninstall %s@%s --keep-data" % (SUITE, plan.MARKETPLACE)))
            found = self.market()
            command = "claude plugin marketplace remove " + plan.MARKETPLACE
            if found and found[0]:
                steps.append(plan._step(4, "market", "todo", plan.MARKETPLACE, "remove.market", command))
            elif found:
                steps.append(plan._step(4, "market", "ok", plan.MARKETPLACE, "remove.kept.market", command,
                                        line="later", source=found[1]))
            self.suite_rows = self.door_fate(self.uninstall("agentik-suite", door=True))
            steps += self.rows_steps(5, self.suite_rows)
            state = os.path.dirname(apply.journal_path(self.env, self.home))
            self.guard += [settings.user_path(self.env), state]
            self.guard += [p for p in (user_path(self.home, u)  # every tool's that answered, taken off or not (G1)
                                       for u in self.user_files.values()) if p]
            self.keep += [(p, "remove.keep.config") for p in [settings.user_path(self.env)] if os.path.lexists(p)]
            self.keep += [(state, "remove.keep.state")] if os.path.lexists(state) else []
            cache = os.path.join(self.config, "plugins", "cache", plan.MARKETPLACE, SUITE)  # rm1 R5
            self.guard.append(cache)
            if os.path.lexists(cache):
                self.keep.append((cache, "remove.keep.cache"))
                self.soft.add(cache)
            path, why, self.cache_root, reach = cache_fate(self.env, self.home, self.guards(), self.acted())
            if why == "remove.cache.acted" and self.a_row(path):
                why = ""  # a row of step 2 or 5, the door say: that row is its one fate (G4)
            self.cache = (path, why, reach)
            if why is None:
                steps.append(plan._step(6, "cache", "todo", self.shown(path), "remove.cache"))
            elif why:
                steps.append(plan._step(6, "cache", "ok", self.shown(path), why, reach=self.shown(reach or "")))
        self.keep = once(self.keep)  # a folder named once (rm1 R5)
        steps += [plan._step(7, "keep", "ok", self.shown(p), why) for p, why in self.keep]
        rows = [r for e in self.tools for r in e["rows"]] + (self.suite_rows if self.all else [])
        return steps, held_of(rows)

    def door_fate(self, rows):
        """The suite's dry rows, the door's `kept: <entry> stands` read `would remove` where every
        entry that keeps it has a `would remove` row in this plan: step 2 takes them first (F3);
        else it names the first entry no row removes, the one the run finds standing (rm1 R2)."""
        going = {os.path.basename(p) for p, _, fate in [r for e in self.tools for r in e["rows"]] + list(rows)
                 if fate == "would remove" and os.path.dirname(p) == self.bindir}
        out = []
        for path, what, fate in rows:
            if what == "door" and fate.startswith("kept: ") and fate.endswith(" stands") \
                    and not fate.startswith("kept: held"):
                try:
                    entries = sorted(os.listdir(self.bindir))
                except OSError:
                    entries = None
                keeps = [n for n in entries or () if n not in (agentik_install.DOOR, "agentik-" + SUITE) and (
                    agentik_install._TOOL.match(n) or agentik_install._launcher_form(os.path.join(self.bindir, n), n))]
                stays = [n for n in keeps if n not in going]
                if keeps and not stays:
                    fate = "would remove"
                elif stays:
                    fate = "kept: %s stands" % agentik_install._ascii(stays[0])
            out.append((path, what, fate))
        return out

    def guards(self):
        return guarded(self.env, self.home, self.guard)

    def acted(self):
        """The folders steps 2 and 5 act on: the prefix's bin and share (G4)."""
        return [self.bindir, os.path.join(self.prefix, "share")]

    def a_row(self, path):
        """Whether `path` is a row of step 2 or 5, each read with its folder's real path."""
        def same(p):
            return os.path.join(os.path.realpath(os.path.dirname(p)), os.path.basename(p))
        rows = [r for e in self.tools for r in e["rows"]] + list(self.suite_rows)
        return same(path) in {same(p) for p, _, _ in rows}

    def todo(self, steps):
        return [s for s in steps if s["state"] == "todo"]

    # ---- the verb ----------------------------------------------------------------------------

    def detail(self, steps):
        for s in steps:
            s["detail"] = self.t.text(s["mid"], **dict(self.slots, **s["values"]))
        return steps

    def json(self, ok, steps, held=None, ran=(), removed=(), wrote=(), error=None):
        obj = {"schema": SCHEMA, "ok": ok, "held": held, "dry_run": bool(self.o["dry_run"]),
               "tools": [{"name": e["name"], "plugin": e["plugin"],
                          "rows": [{"path": p, "what": w, "fate": f} for p, w, f in e.get("rows", ())]}
                         for e in self.tools],
               "kept": [{"path": p, "why": self.t.text(why)} for p, why in self.keep],
               "ran": list(ran), "removed": list(removed), "wrote": list(wrote)}
        if self.o["dry_run"]:
            obj["steps"] = [apply.step_json(s) for s in steps]
        if error:
            obj["error"] = error
        self.t.json(obj)

    def again(self, dry=False):
        """The line that runs this remove again."""
        words = self.nouns + (["--all"] if self.all else []) + (["--dry-run"] if dry and self.o["dry_run"] else [])
        return self.cmd.say("remove", *words)

    def held(self, what, steps=(), unread=False):
        if self.o["json"]:
            self.json(False, list(steps), held=what)
        else:
            self.t.error("err.remove.held", what=what)
            self.t.hint("hint.remove.held.ps" if unread else "hint.remove.held", command=self.again(dry=True))
        return 2

    def said(self, what):
        """(the held text, whether it is a list that cannot be read) of uninstall's hold: one that
        names no pid is processes' why, said in update's words (row lx1-ps-linux R3)."""
        if what is None or what.startswith("pid "):
            return what, False
        return self.t.text("update.held.ps", why=what), True

    def title(self):
        names = ", ".join([e["name"] for e in self.tools] + [s["subject"] for s in self.others])
        if self.o["dry_run"]:
            self.t.line("remove.plan.dry", names=names or "-")
        else:
            self.t.line("remove.plan", names=names or "-")

    def main(self):
        cmd = self.cmd
        if bool(self.nouns) == self.all:
            raise cmd.Refusal("usage", "err.remove.usage", cmd.say("remove", "--all", "--dry-run"), **self.slots)
        for name in self.nouns:
            if not tools.NAME.match(name):
                raise cmd.Refusal("bad_name", "err.setup.name", cmd.say("remove", "--all", "--dry-run"), name=name)
        what, unread = update.holding(cmd)
        if what:
            return self.held(what, unread=unread)
        self.spare = spare(self.env)
        self.scope()
        steps, what = self.build()
        if what:
            what, unread = self.said(what)
            return self.held(what, self.detail(steps), unread)
        steps = self.detail(steps)
        todo = self.todo(steps)
        o, t = self.o, self.t
        if o["dry_run"] or not todo:
            if o["json"]:
                self.json(True, steps)
                return 0
            self.title()
            apply.show(cmd, steps)
            if not todo:
                t.line("remove.nothing")
            return 0
        if not o["json"]:
            self.title()
            apply.show(cmd, steps)
        terminal = apply._terminal(cmd)
        if not terminal and any(s["command"] and s["state"] == "todo" for s in steps):
            gate, why = apply.gated(self.config, self.home, t)  # both commands write it (R8)
            if why:
                raise cmd.Usage("gate_unread", "err.remove.gate_unread", cmd.say("remove"),
                                path=self.shown(gate), why=why, **self.slots)
            if gate:
                raise cmd.Usage("gated", "err.remove.gated", cmd.say("remove"), path=self.shown(gate), **self.slots)
        if not o["yes"]:
            if not terminal or o["json"]:
                raise cmd.Usage("needs_yes", "err.remove.yes", cmd.say("remove", "--yes"), **self.slots)
            self.ask(len(todo))
        saved = {}
        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                saved[sig] = signal.signal(sig, apply._interrupt)
        except ValueError:  # not the main thread
            pass
        try:
            return self.run(steps)
        finally:
            for sig, handler in saved.items():
                signal.signal(sig, handler)

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
            raise self.cmd.Usage("declined", "err.remove.declined", self.cmd.say("remove"), **self.slots)

    def execute(self, command, n, ran, wrote):
        if not self.t.quiet:
            self.t.line("setup.running", err=True, command=command)
            self.t.flush()
        before = apply.look(self.home, self.config)
        result = apply.execute(command, self.env)
        after = apply.look(self.home, self.config)
        wrote.extend(p for p in sorted(after) if after[p] != before.get(p) and p not in wrote)
        ran.append({"n": n, "command": command, "exit": result["exit"]})
        if result["why"] or result["exit"] != 0:
            return apply._failure(command, result)
        return None

    def take(self, rows, removed, kept, name=SUITE):
        """uninstall's rows into the close; the first `kept: partly removed` or `kept: held` (F4),
        each a stop, or None."""
        partly = None
        for path, what, fate in rows:
            if fate == "removed":
                removed.append(path)
            else:
                kept.append((path, fate))
                if fate.startswith("kept: partly removed") and partly is None:
                    partly = ("err.remove.partly", {"path": self.shown(path), "why": fate})
                elif fate.startswith("kept: held") and partly is None:
                    said, unread = self.said(held_of([(path, what, fate)]))
                    partly = ("err.remove.held.run.ps" if unread else "err.remove.held.run",
                              {"what": said, "name": name, "command": self.again()})
        return partly

    def run(self, steps):
        """R4 and R5 in order; a failed step stops, with no rollback (R8). Before step 5 the
        journal's path, the slots and every text the close needs are in memory (R6)."""
        ran, wrote, removed, kept, red, stands, failure = [], [], [], [], [], [], None
        journal = apply.journal_path(self.env, self.home)
        texts = {mid: self.t.text(mid) for mid in set(why for _, why in self.keep)}
        gone = self.t.text("remove.gone")
        agentik_install._homes(self.env)  # its lazy import, loaded before step 5 can take the tree (R6)
        try:
            for e in self.tools:
                if e["plugin"]:
                    again = self.uninstall("agentik-" + e["name"])  # the hold read again, right before step 1 (F4)
                    if held_of(again) and not ran and not removed:
                        what, unread = self.said(held_of(again))
                        return self.held(what, unread=unread)
                    if held_of(again):
                        e["rows"] = again
                        failure = self.take(again, removed, kept, e["name"])
                        break
                    failure = self.execute("claude plugin uninstall %s --keep-data" % shlex.quote(e["plugin"]),
                                           1, ran, wrote)
                    if failure:
                        break
                e["rows"] = self.uninstall("agentik-" + e["name"], dry=False)
                failure = self.take(e["rows"], removed, kept, e["name"])
                if failure:
                    break
            if self.all and failure is None:
                folder = os.path.join(self.config, "plugins", "marketplaces", plan.MARKETPLACE)
                claude = [s for s in steps if s["n"] in (3, 4) and s["state"] == "todo"]
                again = self.door_fate(self.uninstall("agentik-suite", door=True)) if claude else []
                if held_of(again) and not ran and not removed:  # the suite's hold read again before step 3 (G2)
                    what, unread = self.said(held_of(again))
                    return self.held(what, unread=unread)
                if held_of(again):
                    self.suite_rows = again
                    failure = self.take(again, removed, kept)
                    claude = []
                for s in claude:
                    stood = os.path.lexists(folder)
                    failure = self.execute(s["command"], s["n"], ran, wrote)
                    if failure:
                        break
                    if s["id"] == "market" and os.path.lexists(folder):  # removed only where an lstat finds it gone (F6)
                        stands.append((folder, self.t.text("remove.market.stands")))  # to go, and stands (G5)
                    elif s["id"] == "market" and stood:
                        removed.append(folder)
                if failure is None:
                    self.suite_rows = self.uninstall("agentik-suite", door=True, dry=False)  # R6: the tree may go
                    failure = self.take(self.suite_rows, removed, kept)
                if failure is None:
                    failure = self.drop_cache(removed, kept)
        except KeyboardInterrupt:
            apply._ignore()
            failure = ("err.remove.interrupted.idle", {}, apply.INTERRUPTED)
        apply._ignore()
        code = (failure[2] if len(failure) > 2 else 1) if failure else 0
        soft = {p for p in self.soft if not os.path.lexists(p)}  # gone, and named only where it stood
        kept += [(p, texts[why]) for p, why in self.keep if p not in soft]
        if self.cache[0] and self.cache[1]:
            red += [] if os.path.lexists(self.cache[0]) else [(self.cache[0], gone)]
        red += [(p, gone) for p, why in self.keep if not os.path.lexists(p) and p not in self.soft]  # by lstat (F1)
        kept = [(p, why) for p, why in kept if p not in {r[0] for r in red}]
        code = code or (1 if red or stands else 0)
        wrote = wrote + [p for p in removed if p not in wrote]
        wrote = self.journal(journal, ran, wrote, code)
        return self.close(code, failure, ran, removed, kept, wrote, steps, red, stands)

    def drop_cache(self, removed, kept):
        path, why, reach = self.cache
        if why:
            kept.append((path, self.t.text(why, reach=self.shown(reach or ""))))
        if why is not None:
            return None
        again = cache_fate(self.env, self.home, self.guards(), self.acted())
        if again[1] is not None or again[2] != self.cache_root:
            kept.append((path, self.t.text(again[1] or "remove.cache.place", reach=self.shown(again[3] or ""))))
            return None
        root, done = self.cache_root, [0]
        try:
            agentik_install._take(path, lambda p: agentik_install._under(p, root), done)
        except OSError as e:
            why = term.clean(e.strerror or str(e))
            kept.append((path, ("kept: partly removed, " if done[0] else "kept: ") + why))
            return ("err.remove.cache.partly", {"path": self.shown(path), "why": why}) if done[0] else None
        removed.append(path)
        return None

    def journal(self, path, ran, wrote, code):
        if not ran and not wrote:
            return wrote
        entry = {"at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "verb": "remove", "version": self.cmd.version,
                 "plugins": [e["name"] for e in self.tools] + ([SUITE] if self.all else []),
                 "ran": [{k: r[k] for k in ("n", "command", "exit")} for r in ran],
                 "wrote": wrote + [path], "exit": code}
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            term.append(path, json.dumps(entry) + "\n")
        except OSError as e:
            self.t.error("err.remove.journal", path=self.shown(path), why=e.strerror or str(e))
            return wrote
        return wrote + [path]

    def close(self, code, failure, ran, removed, kept, wrote, steps, red=(), stands=()):
        """`red`: what was to stand and is gone; `stands`: what was to go and stands (G5)."""
        t, commands = self.t, [r["command"] for r in ran]
        message = None
        lines = [(mid, ", ".join(self.shown(p) for p, _ in found))
                 for mid, found in (("err.remove.red", red), ("err.remove.stands", stands)) if found]
        if failure:
            mid = FAILS.get(failure[0], failure[0])
            message = t.text(mid, **dict(self.slots, **failure[1]))
        if self.o["json"]:
            remedy = None if failure and failure[0] == "err.remove.cache.partly" else self.remedy  # F5: no verb is left
            error = {"code": "step_failed", "message": message, "remedy": remedy} if failure else None
            if lines and not error:
                error = {"code": "red", "message": " ".join(t.text(mid, paths=paths) for mid, paths in lines),
                         "remedy": None}
            obj = {"schema": SCHEMA, "ok": code == 0, "held": None, "dry_run": False,
                   "tools": [{"name": e["name"], "plugin": e["plugin"],
                              "rows": [{"path": p, "what": w, "fate": f} for p, w, f in e.get("rows", ())]}
                             for e in self.tools],
                   "kept": [{"path": p, "why": why} for p, why in kept],
                   "ran": commands, "removed": removed, "wrote": wrote}
            if error:
                obj["error"] = error
            t.json(obj)
            return code
        t.line("remove.close")
        rows = [("ok", [t.text("remove.ran", command=c)], None) for c in commands]
        rows += [("ok", [self.shown(p), t.text("remove.removed")], None) for p in removed]
        rows += [("note", [self.shown(p), why], None) for p, why in kept]
        rows += [("fail", [self.shown(p), why], None) for p, why in list(red) + list(stands)]
        t.table(rows)
        if failure:
            t.flush()
            t.error(FAILS.get(failure[0], failure[0]), **dict(self.slots, **failure[1]))
        elif lines:
            t.flush()
            for mid, paths in lines:
                t.error(mid, paths=paths)
        return code


def do_remove(cmd, nouns):
    return Remove(cmd, nouns).main()
