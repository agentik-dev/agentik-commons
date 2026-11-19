"""The `config` and `describe` verbs: every tool's settings, found from one place.

`config` lists each tool with its state and counts; `config <tool>` its settings; `config
<tool>.<key>`, cut at the first dot, one setting's card: its value, where it is set, each
layer's value, and how to change it. `--changed` lists every setting that differs from its
default; `--user-files` each layer path marked `travels`. A tool answers through its own
`describe --json` and the config read it names there; the suite answers for itself in process,
and to other tools through `describe --json` and `describe config --json [KEY]`. Nothing here
writes a setting: the card prints the line, and the tool's own verb writes.

A tool's row carries `source`, the finder's row (row fk2b-reads), null for the suite; the `from`
word of a row and a title, and the card of a tool no source is declared for, are made from it.
Where the file that runs lies under the root of a source not the marketplace's own, `path` is
null: the source's folder stands under `source` alone (R1).
"""
import difflib
import json
import os
import re
import time

from . import doctor, plan, settings, sources, term, tools

NEAR = 0.6  # difflib's cutoff for a near verb, tool, flag or key (row sc4 R4)

SUITE_READ = {"kind": "config", "name": "settings", "argv": ["describe", "config", "--json"]}
GROUP_PAST = 20
# Why a tool gives no settings (`why`), and the line for it at the tool's level and a key's.
STATE_LINE = {"timed out": "config.state.timed_out", "unreadable": "config.state.unreadable",
              "no command": "config.state.no_command", "noread": "config.state.noread",
              "read timed out": "config.state.read_timed_out",
              "read unreadable": "config.state.read_unreadable", "read error": "config.state.read_error"}
KEY_LINE = {"timed out": "err.config.silent", "unreadable": "err.config.silent",
            "no command": "err.config.silent.command", "noread": "err.config.silent.noread",
            "read timed out": "err.config.read.timed_out",
            "read unreadable": "err.config.read.unreadable", "read error": "err.config.read.error"}
REASON = {"other": "config.reason.other", "unread": "config.reason.unread"}  # row ak9b R3
WARNED = {"unreadable": "config.warn.unreadable", "ignored": "config.warn.ignored"}  # row ak9c R7
CLAIM = {"suite": "config.claim.suite", "kept": "config.claim.kept", "market": "config.claim.market"}  # R4
READ_CELL = {"timed out": "config.read.timed_out", "unreadable": "config.read.unreadable",
             "error": "config.read.error"}
ANSWER_CELL = {"timed out": "config.answer.timed_out", "unreadable": "config.answer.unreadable"}  # sc6 R2
SUITE_SUMMARIES = ("checkouts", "kind", "watcher.match", "watcher.start", "watcher.beat",
                   "watcher.writer", "sources")


def shown_value(value):
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value if value else '""'
    return json.dumps(value, ensure_ascii=False)


def why(row):
    """Why a row gives no settings: its read's state, a tool that names no read, or its state."""
    if row["read_state"]:
        return "read " + row["read_state"]
    return "noread" if row["state"] == "answers" else row["state"]


def reason(t, row):
    """The words beside a state whose describe did not count (row ak9b R3), or None."""
    return t.text(REASON[row["reason"]]) if row.get("reason") else None


def asks(remedy):
    """A remedy that answers a question for the person (`--yes`, `-y`) or removes: it stands on
    its own line, never behind `next:` (row sc5 R8, ruled for config by ak9b review 1 lead 1),
    by doctor's one rule (NICE n197)."""
    return doctor.asks(remedy.split())


def silent(rows):
    """The tools whose settings were not read: each but those that answer and name no read."""
    return [row["name"] for row in rows if row["config"] is None and why(row) != "noread"]


def differs(s):
    return s.get("default") is not None and s.get("value") != s.get("default")


class Reader:
    """The reads behind both verbs, for one command run."""

    def __init__(self, cmd):
        self.cmd, self.t, self.env = cmd, cmd.t, cmd.env
        self.suite = cmd.tool[len("agentik-"):] if cmd.tool.startswith("agentik-") else cmd.tool
        self.home = self.env.get("HOME") or ""
        self.deadline = None
        self.lines = {}  # each file's lines by dotted path, read once a run (R5)

    # ---- the suite itself -------------------------------------------------------------------

    def suite_config(self, key=None):
        """R5's object for the suite's own settings; a settings.Fault for a file outside the subset."""
        summaries = {k: self.t.text("setting." + k) for k in SUITE_SUMMARIES}
        try:
            cwd = os.getcwd()
        except OSError:  # a removed folder: no repo layer
            cwd = None
        body = settings.resolve(self.env, cwd, summaries)
        rows = body["settings"]
        if key is not None:
            rows = [s for s in rows if s["key"] == key]
        return {"schema": "agentik.config/1", "ok": True, "tool": self.suite,
                "layers": body["layers"], "settings": rows, "warnings": body["warnings"]}

    def suite_describe(self):
        cmd = self.cmd
        return {"schema": "agentik.describe/1", "ok": True, "tool": self.suite,
                "version": cmd.version, "summary": self.t.text("describe.summary"),
                "repo": plan.SOURCE, "plugin": "%s@%s" % (self.suite, plan.MARKETPLACE),
                "needs": [],
                "verbs": [{"name": v, "summary": self.t.text("verb." + v.replace("-", "_")), "top": True}
                          for v in cmd.VERBS],
                "reads": [dict(SUITE_READ)]}

    # ---- the others ---------------------------------------------------------------------------

    def entries(self):
        return tools.listed(self.suite, self.cmd._on_path(), self.env)

    def wall(self):
        """The one deadline, set at the first spawn, that every describe and read of the run shares."""
        if self.deadline is None:
            self.deadline = time.monotonic() + tools.WALL
        return self.deadline

    def survey(self, entries, with_config=True, key=None):
        """[{name, state, answer, config, read_state, fault, ...}]: every describe and config read
        at once, each read started as soon as its tool's answer is known, under one wall."""
        runnable = [e for e in entries if e["name"] != self.suite and e["exe"]]
        reasons = {}
        described, reads = tools.describe_all(runnable, self.env, read=with_config, key=key,
                                              deadline=self.wall(), reasons=reasons) \
            if runnable else ({}, {})
        rows = []
        for e in entries:
            row = {"name": e["name"], "exe": e["exe"], "answer": None, "config": None,
                   "fault": None, "read": None, "read_state": None, "source": e.get("source"),
                   "reason": reasons.get(e["name"]), "error": None, "claims": []}
            if e["name"] == self.suite:
                row["state"] = "answers"
                row["answer"] = self.suite_describe()
                try:
                    row["config"] = self.suite_config(key)
                except settings.Fault as f:
                    row["state"], row["fault"] = "unreadable", self.fault_text(f)
            elif not e["exe"]:
                row["state"] = "no command"
            else:
                row["state"], row["answer"] = described[e["name"]]
                row["read"] = tools.config_read(row["answer"]) if row["answer"] else None
                row["claims"] = [{k: c[k] for k in ("verb", "counts", "reason")}  # row ak9c R4
                                 for c in doctor.claims(self.cmd, [e], described)]
                if e["name"] in reads:
                    code, out, state = reads[e["name"]]
                    row["config"] = tools.counted_config(code, out) if state == "ran" else None
                    row["error"] = tools.config_error(out) if state == "ran" and row["config"] is None else None
                    if row["error"]:  # a counted error, whatever the exit (row ak9b R4)
                        row["read_state"] = "error"
                    elif row["config"] is None:
                        row["read_state"] = "timed out" if state == "timed out" else "unreadable"
            rows.append(row)
        return rows

    def read_one(self, row, key):
        """The tool's config object for one key (or all), or None; under the run's one wall."""
        if row["name"] == self.suite:
            return self.suite_config(key)
        argv = [row["exe"]] + row["read"]["argv"] + ([key] if key is not None else [])
        code, out, state = tools.run_all([("one", argv)], self.env, deadline=self.wall())["one"]
        return tools.counted_config(code, out) if state == "ran" else None

    def fault_text(self, f):
        return self.t.text("config.fault" if f.line else "config.fault.noline",
                           path=plan.shown(getattr(f, "path", ""), self.home), line=f.line, why=f.why)

    def user_file(self, cfg):
        for layer in (cfg or {}).get("layers") or ():
            if layer.get("name") == "user" and isinstance(layer.get("path"), str):
                return layer["path"]
        return None


def _nearest(word, names):
    near = difflib.get_close_matches(word, names, n=1, cutoff=NEAR)
    return near[0] if near else None


def _theirs(source):
    return bool(source) and source["kind"] not in ("own", "absent")


def _from(source, home):
    """The id or the folder of a source of kind `plugin` or `folder`, else None (R6): a line the
    config read passes over has no folder, so it gives none (review 1 F3)."""
    if source and source["kind"] == "plugin":
        return source["plugin"]
    if source and source["kind"] == "folder" and source["root"]:
        return plan.shown(source["root"], home)
    return None


def _shown_path(row):
    """`path` of a row in --json: none where the file lies under a source not the marketplace's own
    (R1). Its `version` is none for any such source, since that version stands under `source`
    (review 1 F1)."""
    if _theirs(row["source"]) and ((row["source"]["runs"] or {}).get("of") == "source"):
        return None
    return row["exe"]


def _ids(source):
    """The plugins of the name: the standing one first, then the seen, each once."""
    first = [source["plugin"]] if source["kind"] in ("own", "plugin") and source["plugin"] \
        and source["kind"] != "undecided" else []
    return list(dict.fromkeys(first + [s["plugin"] for s in source["seen"]]))


def _titled(cmd, mid, origin, **values):
    """A title line; with `origin`, it ends `from <id or folder>` (R6)."""
    t = cmd.t
    if origin:
        t.line("config.titled", title=t.text(mid, **values).rstrip("."), source=origin)
    else:
        t.line(mid, **values)


def path(nouns):
    """The words after `config` are one path, joined by dots (row sc4 R5)."""
    return ".".join(nouns)


def _again(cmd, dotted):
    """`config` as typed with its words as the one path `dotted`, none where it is empty."""
    at = cmd.at[1:]
    swap = {i: [] for i in at[1:]}
    swap[at[0]] = [dotted] if dotted else []
    return cmd.again(swap)


def do_config(cmd, nouns):
    o, t, Refusal = cmd.opts, cmd.t, cmd.Refusal
    if o["changed"] and o["user_files"]:
        raise Refusal("two_answers", "err.config.both", cmd.say("config", "--changed"))
    if nouns and (o["changed"] or o["user_files"]):
        flag = "--changed" if o["changed"] else "--user-files"
        raise Refusal("extra_word", "err.extra", cmd.say("config", flag),
                      verb="config " + flag, word=nouns[0])
    r = Reader(cmd)
    entries = r.entries()
    if not nouns:
        rows = r.survey(entries)
        if o["changed"]:
            return _changed(cmd, r, rows)
        if o["user_files"]:
            return _user_files(cmd, rows)
        return _list(cmd, r, rows)
    name, dot, key = path(nouns).partition(".")
    if not name:
        raise Refusal("unknown_tool", "err.config.noname", cmd.say("config"))
    names = [e["name"] for e in entries]
    if name not in names:
        if not dot:  # one word that is no tool's name: a search, and a tool's name wins (sc7 R1)
            return _find(cmd, r, entries, name)
        near = _nearest(name, names)
        raise Refusal("unknown_tool", "err.config.tool", _again(cmd, near and near + dot + key),
                      name=name)
    entry = entries[names.index(name)]
    if dot and not key:
        raise Refusal("unknown_key", "err.config.nokey", _again(cmd, name), name=name)
    if not key and (entry.get("source") or {}).get("kind") == "undecided":
        return _source_card(cmd, r, name, entry["source"])
    row = r.survey([entry], key=key or None)[0]
    if row["fault"]:  # no command mends a file that does not parse (R7)
        raise Refusal("bad_file", "err.config.file", None, fault=row["fault"])
    table = tools.fallback(cmd.lib).get(name)
    cfg = row["config"]
    if cfg is None:
        if key:
            state = row["state"] + (": " + reason(t, row) if row.get("reason") else "")
            raise Refusal("no_answer", KEY_LINE[why(row)], _again(cmd, name), name=name, key=key,
                          state=state, message=(row["error"] or {}).get("message"), **cmd.slots())
        return _silent(cmd, r, row, table)
    if not key:
        return _tool(cmd, r, name, cfg, _from(row["source"], r.home), row["claims"], row["source"])
    found = [s for s in cfg["settings"] if s["key"] == key]
    if not found and name == r.suite and key.startswith("sources."):
        known = tools.rows(cmd.env, cmd.lib)
        if key[len("sources."):] in known:  # no line is written: the card that shows how (R6)
            return _source_card(cmd, r, key[len("sources."):], known[key[len("sources."):]], key=key)
    if not found:
        whole = r.suite_config() if row["name"] == r.suite else r.read_one(row, None)
        keys = [s["key"] for s in (whole or {}).get("settings") or ()]
        if any(k.startswith(key + ".") for k in keys):  # a prefix: its group, flat (R3)
            return _tool(cmd, r, name, whole, _from(row["source"], r.home), row["claims"], row["source"],
                         prefix=key)
        near = _nearest(key, keys)
        raise Refusal("unknown_key", "err.config.key", _again(cmd, name + "." + near if near else name),
                      name=name, key=key)
    return _card(cmd, r, name, cfg, found[0])


# ---- the three levels -------------------------------------------------------------------------

def _counts(row):
    cfg = row["config"]
    if not cfg:
        return None, None
    return len(cfg["settings"]), sum(1 for s in cfg["settings"] if differs(s))


def _list(cmd, r, rows):
    t = cmd.t
    table, words = tools.fallback(cmd.lib), None
    if cmd.opts["json"]:
        out = []
        for row in rows:
            n, d = _counts(row)
            item = {"name": row["name"], "state": row["state"], "path": _shown_path(row),
                    "settings": n, "differ": d, "user_file": r.user_file(row["config"]),
                    "version": None if _theirs(row["source"]) else (row["answer"] or {}).get("version"),
                    "summary": (row["answer"] or {}).get("summary")}
            if row["fault"]:
                item["fault"] = row["fault"]
            if row["read_state"]:
                item["read"] = row["read_state"]
            if row["error"]:
                item["error"] = row["error"]
            if row["reason"]:
                item["reason"] = row["reason"]
            if row["state"] != "answers" and row["name"] in table:
                words = words if words is not None else tools.descriptions(cmd.env)
                item["table"] = table[row["name"]]
                item["description"] = words.get(row["name"])
            item["source"] = row["source"]
            out.append(item)
        t.json({"schema": "agentik.config/1", "ok": True, "tools": out})
        return 0
    counted = [(row, *_counts(row)) for row in rows]
    t.line("config.title", changed=sum(d for _, n, d in counted if n is not None),
           total=sum(n for _, n, _ in counted if n is not None))
    t.blank()
    keys = {row["name"]: t.text("config.count.one" if n == 1 else "config.count", n=n)
            for row, n, _ in counted if n}
    room = max(map(term.columns, keys.values()), default=0)
    lines = []
    for row, n, d in counted:
        after, status, cells = row["fault"], None, [term.name(row["name"])]
        if n:  # its keys and how many changed, the counts aligned down the rows (R2)
            cells.append(keys[row["name"]] + " " * (room - term.columns(keys[row["name"]])) + "  "
                         + t.text("config.differ", n=d))
            user = r.user_file(row["config"])
            cells.append(term.path(plan.shown(user, r.home)) if user else "")
        elif row["fault"] or row["read_state"] or row["state"] in ("timed out", "unreadable"):
            status = "warn"  # a mark only where something is wrong (R2)
            note = t.text(READ_CELL[row["read_state"]]) if row["read_state"] else reason(t, row) or \
                (t.text(ANSWER_CELL[row["state"]]) if row["state"] in ANSWER_CELL else None)
            known = (table.get(row["name"]) or {}).get("user_file")  # the suite's table, where it has one
            cells += [t.text("config.silent"), term.path(plan.shown(str(known), r.home)) if known else note or ""]
        else:  # it answers with none, names no read, or ships no command: its file still shows
            user = r.user_file(row["config"]) or (table.get(row["name"]) or {}).get("user_file")
            cells += [t.text("config.nokeys"), term.path(plan.shown(str(user), r.home)) if user else ""]
        source, extra = row["source"], None
        if source and source["kind"] == "undecided":
            status, extra = "warn", t.text("config.undecided", count=len(_ids(source)))
        elif _from(source, r.home):
            extra = t.text("config.from", source=_from(source, r.home))
        lines.append((status, cells, after, extra))
    # the source's words end a row, in a column after every other row's cells (R6)
    wide = max(len(cells) for _, cells, _, _ in lines)
    marked = any(status for status, _, _, _ in lines)
    t.table([(status, cells + ([""] * (wide - len(cells)) + [extra] if extra else []), after)
             for status, cells, after, extra in lines], indent=0 if marked else 2)
    top = max((c for c in counted if c[1] is not None), key=lambda c: c[2], default=None)
    if top:  # the tool with the most changed keys, the first on a tie (R2)
        t.hint("hint.config", command=cmd.say("config", top[0]["name"]))
    return 0


def _silent(cmd, r, row, table):
    """A tool that gives no settings: its row of the fallback table, else its state."""
    t, name = cmd.t, row["name"]
    if cmd.opts["json"]:
        obj = {"schema": "agentik.config/1", "ok": True, "tool": name, "state": row["state"],
               "layers": [], "settings": []}
        if row["read_state"]:
            obj["read"] = row["read_state"]
        if row["error"]:
            obj["error"] = row["error"]
        if row["reason"]:
            obj["reason"] = row["reason"]
        if row["claims"]:
            obj["claims"] = row["claims"]
        if table:
            obj["table"] = table
            obj["description"] = tools.descriptions(cmd.env).get(name)
        cmd.t.json(obj)
        return 0
    _titled(cmd, STATE_LINE[why(row)], _from(row["source"], r.home), name=name,
            message=(row["error"] or {}).get("message"))
    if row["reason"]:
        t.line(REASON[row["reason"]], style="hint")
    remedy = (row["error"] or {}).get("remedy")
    held = bool(remedy) and asks(remedy)
    if held:  # the close names the read again (lead 1)
        close = ("hint.config.again", {"command": cmd.say("config", name)})
    else:
        close = ("hint.config.remedy", {"remedy": remedy}) if remedy else \
            ("hint.config.back", {"command": cmd.say("config")})  # a command alone (review 1 F1)
    if table:
        desc = tools.descriptions(cmd.env).get(name)
        t.line("config.table.title", name=name)
        if desc:
            t.line("config.table.description", description=desc, style="hint")
        rows = [("note", [t.text("config.label.run"), line], None)
                for line in table.get("lines") or () if isinstance(line, str)]
        if not rows:
            rows.append(("note", [t.text("config.label.run"), t.text("config.table.nocmd")], None))
        if table.get("user_file"):
            rows.append(("note", [t.text("config.label.file"), term.path(str(table["user_file"]))], None))
        for need in table.get("needs") or ():
            rows.append(("note", [t.text("config.label.needs"), str(need)], None))
        t.table(rows)
    _claims(cmd, name, row["claims"], row["source"])
    if held:
        t.line("config.remedy", remedy=remedy)
    t.hint(close[0], **close[1])
    return 0


def _claims(cmd, name, claims, source):
    """One line a claim that does not count, under the list: the word, and why `agentik W` does
    not run it (R4). A file on PATH that the finder knows no source for gets none on the screen,
    only in --json and in `agentik W`'s `next:`, so its list keeps the pin's lines."""
    for c in claims if source else ():
        if not c["counts"]:
            cmd.t.line(CLAIM[c["reason"]], name=name, verb=c["verb"], run=cmd.say(c["verb"]))


def _tool(cmd, r, name, cfg, origin=None, claims=(), source=None, prefix=None):
    """Step 2 (R3): the changed keys first, each where it is set; past GROUP_PAST keys on a
    terminal one line a group, else, off one, with --all or for a prefix, every key flat."""
    t, rows = cmd.t, cfg["settings"]
    if prefix:
        rows = [s for s in rows if s["key"].startswith(prefix + ".")]
    if cmd.opts["json"]:
        obj = {"schema": "agentik.config/1", "ok": True, "tool": name, "layers": cfg["layers"],
               "settings": rows, "warnings": cfg.get("warnings") or []}
        if claims:
            obj["claims"] = list(claims)
        t.json(obj)
        return 0
    changed = [s for s in rows if differs(s)]
    named = {s["source"].get("layer") for s in rows} | {v.get("layer") for s in rows for v in s.get("values") or ()}
    layers = [layer["name"] for layer in cfg.get("layers") or ()
              if isinstance(layer.get("name"), str) and (layer.get("present") or layer["name"] in named)]
    layers = layers if "default" in layers else ["default"] + layers  # the lowest, always (R3)
    _titled(cmd, "config.tool.title" if changed else "config.tool.title.none", origin,
            name=name + "." + prefix if prefix else name, changed=len(changed),
            layers=", ".join(layers),
            settings=t.text("config.count.one" if len(rows) == 1 else "config.count", n=len(rows)))
    t.blank()

    def row(s):
        layer = str(s["source"].get("layer") or "default")
        where = _set_at(r, name, s) if layer != "default" else None
        return (None, (["*" if differs(s) else ""] if changed else [])
                + [term.name(s["key"]), shown_value(s.get("value")), layer, term.path(where) if where else ""],
                None)

    indent = 0 if changed else 2
    if prefix or cmd.opts["config_all"] or not t.out.tty or len(rows) <= GROUP_PAST:
        t.table([row(s) for s in changed] + [row(s) for s in rows if not differs(s)], indent=indent)
    else:
        if changed:
            t.table([row(s) for s in changed], indent=indent)
            t.blank()
        heads = {}
        for s in rows:
            heads.setdefault(s["key"].split(".", 1)[0], []).append(s)
        groups = [(term.name(head), members) for head, members in heads.items()
                  if len(members) > 1 or "." in members[0]["key"]]
        rest = [members[0] for head, members in heads.items() if len(members) == 1 and "." not in members[0]["key"]]
        if rest:
            groups.append((t.text("config.group.rest"), rest))

        def word(s, head):
            short = s["key"][len(head) + 1:] if head and s["key"].startswith(head + ".") else s["key"]
            return short + ("*" if differs(s) else "")

        t.table([(None, [label, str(len(members)),
                         " ".join(word(s, label[0] if isinstance(label, tuple) else "") for s in members)], None)
                 for label, members in groups])
    for w in cfg.get("warnings") or ():
        if prefix and w.get("key") and not str(w["key"]).startswith(prefix + "."):  # review 1 F3
            continue
        # a file skipped, a key not taken from it (row ak9c R7); a reason that is no string reads
        # as an unknown key, as at the pin (review 1 F2)
        if isinstance(w.get("reason"), str) and w["reason"] in WARNED:
            where = _where(w, r.home)
            t.table([("warn", [t.text(WARNED[w["reason"]], name=name, key=w.get("key"))]
                      + ([term.path(where)] if where else []), None)])
            continue
        said = t.text("config.badvalue", key=w.get("key"), value=shown_value(w.get("value"))) \
            if w.get("reason") == "choice" else t.text("config.unknown", key=w.get("key"))
        t.table([("warn", [said,
                           term.path("%s:%s" % (plan.shown(str(w.get("path")), r.home), w.get("line")))],
                  None)])
    _claims(cmd, name, claims, source)
    if rows:  # the first changed key, else the first key (R3)
        t.hint("hint.config.tool", command=cmd.say("config", name + "." + (changed or rows)[0]["key"]))
    return 0


def _where(row, home):
    """A row's file as the card's set-by line shows one, `~` for the home, one line, its `line`
    after a colon where one is given; None where the row names no file (row ak9c R7, R8)."""
    path = row.get("path")
    if not isinstance(path, str) or not path:
        return None
    shown = tools.one_line(plan.shown(path, home))
    line = row.get("line")
    return "%s:%s" % (shown, line) if isinstance(line, int) and not isinstance(line, bool) else shown


def _a_line(n):
    return isinstance(n, int) and not isinstance(n, bool) and n > 0


def _line_in(r, path, keys):
    """The 1-based line of the first of `keys` (dotted paths) in the file at `path`, read in the
    strict subset; None where the file is absent, does not parse, or holds none of them (R5)."""
    cache = r.lines
    if path not in cache:
        try:
            cache[path] = settings.read(path)[2]
        except (settings.Fault, OSError, ValueError, UnicodeError):
            cache[path] = {}
    return next((cache[path][k] for k in keys if k in cache[path]), None)


def _set_at(r, name, s):
    """`path:line` of the file a key's value comes from, its source's or, where that names none,
    its layer's value's: the line the tool gives, else the line of its dotted path in that file
    (`<tool>.<key>` alone in the repo and local layers, whose file holds a section a tool), else
    the path alone; None where the tool names no file (R5)."""
    src = s["source"]
    path, line = src.get("path"), src.get("line")
    if not isinstance(path, str) or not path:  # the file of the value its layer gives (ak9c R8)
        held = [v for v in s.get("values") or () if v.get("layer") == src.get("layer")
                and isinstance(v.get("path"), str) and v["path"]]
        if not held:
            return None
        path, line = held[-1]["path"], held[-1].get("line")
    if not _a_line(line):
        # a repo or local file holds a section a tool: there only `<tool>.<key>` (review 1 F2)
        line = _line_in(r, path, [name + "." + s["key"]] if src.get("layer") in ("repo", "local") else [s["key"]])
    shown = tools.one_line(plan.shown(path, r.home))
    return "%s:%d" % (shown, line) if _a_line(line) else shown


def _edit_at(r, s, change):
    """`path:line` of the file a hand edit goes to: the line of the block's last key in it, else
    the path alone (R5)."""
    path = str(change["path"])
    try:
        found = settings.parse(str(change.get("block") or ""))[1]
    except (settings.Fault, ValueError):
        found = {}
    keys = [max(found, key=found.get)] if found else [s["key"]]
    line = _line_in(r, path, keys)
    shown = tools.one_line(plan.shown(path, r.home))
    return "%s:%d" % (shown, line) if _a_line(line) else shown


def _card(cmd, r, name, cfg, s):
    """Step 3 (R4): the key, its value and default; the summary; where it is set, each layer's
    value, the choices, the one change and when it applies. No `next:`: `change` is the step."""
    t, src, change = cmd.t, s["source"], s["change"]
    if cmd.opts["json"]:
        t.json({"schema": "agentik.config/1", "ok": True, "tool": name, "key": s["key"],
                "layers": cfg["layers"], "setting": s})
        return 0
    if s.get("default") is not None:
        t.line("config.card.key.default", name=name, key=s["key"], value=shown_value(s.get("value")),
               default=shown_value(s["default"]))
    else:
        t.line("config.card.key", name=name, key=s["key"], value=shown_value(s.get("value")))
    if s.get("summary"):
        t.line("config.card.summary", summary=str(s["summary"]))
    t.blank()
    label = lambda mid: term.name(t.text("config.label." + mid))  # noqa: E731
    layer = str(src.get("layer") or "default")
    where = _set_at(r, name, s)
    rows = [(None, [label("set_in"), term.path(t.text("config.set_in", where=where, layer=layer))
                    if where else layer], None)]
    values = [(v.get("layer"), v.get("value")) for v in s.get("values") or ()]
    if s.get("default") is not None and "default" not in [v[0] for v in values]:
        values.insert(0, ("default", s["default"]))
    if values:
        rows.append((None, [label("layers"), ", ".join(t.text("config.layers.item", layer=v[0],
                                                               value=shown_value(v[1])) for v in values)], None))
    if s.get("choices"):
        rows.append((None, [label("choices"), " ".join(shown_value(c) for c in s["choices"])], None))
    kind = change.get("kind")
    if kind == "command" and change.get("command"):
        rows.append((None, [label("change"), str(change["command"])], None))
    elif kind == "launch" and change.get("command"):
        rows.append((None, [label("change"), t.text("config.change.launch", command=str(change["command"]))], None))
    elif kind == "edit" and change.get("path"):
        rows.append((None, [label("change"), term.path(t.text("config.change.edit", where=_edit_at(r, s, change)))],
                     None))
        for line in str(change.get("block") or "").splitlines():
            rows.append((None, ["", line], None))
    else:
        rows.append((None, [label("change"), t.text("config.change.fixed")], None))
    if change.get("note"):
        rows.append((None, [label("note"), str(change["note"])], None))
    rows.append((None, [label("applies"), t.text("config.live" if s.get("live") else "config.later")], None))
    t.table(rows)
    return 0


def _source_card(cmd, r, name, source, key=None):
    """The card of a tool's source while no line is written (R6): how many plugins have the name,
    each seen, and the block the user file takes; `key` is the suite's `sources.<name>`."""
    t, ids = cmd.t, _ids(source)
    user = settings.user_path(cmd.env)
    pick = "%s@%s" % (name, plan.MARKETPLACE)
    block = "sources:\n  %s: %s" % (name, pick if pick in ids or not ids else ids[0])
    if cmd.opts["json"]:
        t.json({"schema": "agentik.config/1", "ok": True, "tool": r.suite if key else name, "key": key,
                "source": source, "change": {"kind": "edit", "path": user, "block": block}})
        return 0
    if source["kind"] == "undecided":
        mid = "config.source.undecided"
    else:
        mid = {0: "config.source.none", 1: "config.source.one"}.get(len(ids), "config.source.count")
    if key:
        t.line("config.card.title", name=r.suite, key=key)
        t.line(mid, count=len(ids), name=name)
    else:
        t.line("config.source.title", name=name, words=t.text(mid, count=len(ids)))
    label = lambda mid: term.name(t.text("config.label." + mid))  # noqa: E731
    plugins = [source] if source["kind"] in ("own", "plugin") and source["plugin"] else []
    seen = list(dict.fromkeys("%s %s" % (s["plugin"], s["version"]) if s.get("version") else s["plugin"]
                              for s in plugins + source["seen"]))
    rows = [(None, [label("seen"), ", ".join(seen)], None)] if seen else []
    rows.append((None, [label("edit"), term.path(plan.shown(user, r.home))], None))
    rows += [(None, ["", line], None) for line in block.splitlines()]
    rows.append((None, [label("holds"), t.text("config.live")], None))
    t.table(rows)
    t.hint("hint.config.card", **cmd.slots())
    return 0


def _words(text):
    """The words of a summary, case folded: each run of letters, digits or `_` (sc7 R1)."""
    return re.findall(r"\w+", str(text or "").casefold())


def _no_answer(row):
    """Step 1's marked row: a file that does not parse, a describe that failed or ran past its
    wall, or a read that did."""
    return bool(row["fault"] or row["read_state"] or row["state"] in ("timed out", "unreadable"))


def _find(cmd, r, entries, word):
    """`config <word>` (sc7 R1 to R3): every key of every tool that answers whose dotted segment
    or summary word is the word, case folded; one row a match, then one `!` line a tool that did
    not answer. No match is the refusal of an unknown tool, its `next:` the near tool, else the
    near key."""
    t, folded = cmd.t, word.casefold()
    rows = r.survey(entries)
    matches, segments = [], {}
    for row in rows:
        for s in (row["config"] or {}).get("settings") or ():
            key = str(s.get("key"))
            parts = key.casefold().split(".")
            for part in parts:  # the first key that holds each segment, for R3's near key
                segments.setdefault(part, row["name"] + "." + key)
            if folded in parts or folded in _words(s.get("summary")):
                matches.append((row["name"], key, s))
    silent = [row["name"] for row in rows if row["config"] is None and _no_answer(row)]
    if not matches:
        if not cmd.opts["json"]:  # the refusal explained (R2)
            for name in silent:
                t.table([("warn", [t.text("config.find.silent", name=name)], None)], err=True, indent=0)
        near = _nearest(word, [e["name"] for e in entries])
        if not near:
            seg = _nearest(folded, list(segments))
            near = segments[seg] if seg else None
        raise cmd.Refusal("unknown_tool", "err.config.tool", _again(cmd, near), name=word)
    if cmd.opts["json"]:
        t.json({"schema": "agentik.config/1", "ok": True, "word": word,
                "matches": [{"tool": name, "key": key, "value": s.get("value"), "summary": s.get("summary")}
                            for name, key, s in matches],
                "silent": silent})
        return 0
    t.line("config.find.title", word=word, count=len(matches))
    t.blank()
    t.table([(None, [term.name(name + "." + key), shown_value(s.get("value")),
                     term.cut(str(s.get("summary") or ""))], None)
             for name, key, s in matches])
    for name in silent:
        t.table([("warn", [t.text("config.find.silent", name=name)], None)], indent=0)
    t.hint("hint.config.tool", command=cmd.say("config", matches[0][0] + "." + matches[0][1]))
    return 0


def _changed(cmd, r, rows):
    t, found, gone = cmd.t, [], silent(rows)
    for row in rows:
        for s in (row["config"] or {}).get("settings") or ():
            if differs(s):
                found.append((row["name"], s))
    if cmd.opts["json"]:
        t.json({"schema": "agentik.config/1", "ok": True,
                "changed": [{"tool": n, "key": s["key"], "value": s.get("value"),
                             "default": s.get("default"), "source": s["source"]} for n, s in found],
                "silent": gone})
        return 0
    if not found:
        t.line("config.changed.none")
    else:
        t.line("config.changed.title", count=len(found))
        t.table([(None, [term.name("%s.%s" % (n, s["key"])), shown_value(s.get("value")),
                         t.text("config.was", default=shown_value(s.get("default"))),
                         str(s["source"].get("layer") or "default")], None) for n, s in found])
    if gone:
        t.line("config.changed.silent", names=", ".join(gone))
    t.hint("hint.config.changed", **cmd.slots())
    return 0


def _user_files(cmd, rows):
    t, paths, gone = cmd.t, [], silent(rows)
    for row in rows:
        for layer in (row["config"] or {}).get("layers") or ():
            if layer.get("travels") is True and isinstance(layer.get("path"), str) \
                    and layer["path"] not in paths:
                paths.append(layer["path"])
    if cmd.opts["json"]:
        t.json({"schema": "agentik.config/1", "ok": True, "user_files": paths, "silent": gone})
        return 0
    for p in paths:
        t.line("config.file", path=p)
    if not paths:
        t.line("config.files.none", err=True)
    if gone:
        t.line("config.files.silent", err=True, names=", ".join(gone))
    return 0


# ---- describe ---------------------------------------------------------------------------------

def do_describe(cmd, nouns):
    Refusal, r = cmd.Refusal, Reader(cmd)
    if not cmd.opts["json"]:
        raise Refusal("needs_json", "err.describe.json", cmd.again({}, tail=["--json"]))
    if not nouns:
        cmd.t.json(r.suite_describe())
        return 0
    if nouns[0] == "sources":
        return _describe_sources(cmd, r, nouns[1:])
    if nouns[0] != "config":
        raise Refusal("extra_word", "err.extra", cmd.say("help", "describe"), verb="describe",
                      word=nouns[0])
    if len(nouns) > 2:
        cmd._no_nouns(nouns[2:])
    key = nouns[1] if len(nouns) > 1 else None
    try:
        cfg = r.suite_config(key)
    except settings.Fault as f:
        raise Refusal("bad_file", "err.config.file", None, fault=r.fault_text(f))
    if key is not None and not cfg["settings"]:
        keys = [s["key"] for s in r.suite_config()["settings"]]
        near = _nearest(key, keys)
        raise Refusal("unknown_key", "err.config.key",
                      cmd.mend(cmd.at[2], near) if near else cmd.say("config", r.suite),
                      name=r.suite, key=key)
    cmd.t.json(cfg)
    return 0


def _describe_sources(cmd, r, nouns):
    """`describe sources --json [TOOL]` (row fk1-sources R7): the finder's rows, one for TOOL, or
    each name the suite knows less itself, then each declared name."""
    if len(nouns) > 1:
        cmd._no_nouns(nouns[1:])
    try:
        cwd = os.getcwd()
    except OSError:  # a removed folder: no repo's entries
        cwd = None
    if nouns:
        names, more = [nouns[0]], False
    else:
        names, more = [n for n in tools.plugin_names(cmd.env, cmd.lib) if n != r.suite], True
    try:
        rows = sources.read(cmd.env, cwd, names, more=more)
    except settings.Fault as f:
        raise cmd.Refusal("bad_file", "err.config.file", None, fault=r.fault_text(f))
    cmd.t.json({"schema": sources.SCHEMA, "ok": True, "tools": rows})
    return 0
