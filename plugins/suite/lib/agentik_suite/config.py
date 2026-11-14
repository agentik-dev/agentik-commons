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
import time

from . import plan, settings, sources, term, tools

NEAR = 0.6  # difflib's cutoff for a near verb, tool, flag or key (row sc4 R4)

SUITE_READ = {"kind": "config", "name": "settings", "argv": ["describe", "config", "--json"]}
GROUP_PAST = 20
STATUS = {"answers": "ok", "timed out": "warn", "unreadable": "warn", "no command": "note"}
# Why a tool gives no settings (`why`), and the line for it at the tool's level and a key's.
STATE_LINE = {"timed out": "config.state.timed_out", "unreadable": "config.state.unreadable",
              "no command": "config.state.no_command", "noread": "config.state.noread",
              "read timed out": "config.state.read_timed_out",
              "read unreadable": "config.state.read_unreadable"}
KEY_LINE = {"timed out": "err.config.silent", "unreadable": "err.config.silent",
            "no command": "err.config.silent.command", "noread": "err.config.silent.noread",
            "read timed out": "err.config.read.timed_out",
            "read unreadable": "err.config.read.unreadable"}
READ_CELL = {"timed out": "config.read.timed_out", "unreadable": "config.read.unreadable"}
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
        described, reads = tools.describe_all(runnable, self.env, read=with_config, key=key,
                                              deadline=self.wall()) if runnable else ({}, {})
        rows = []
        for e in entries:
            row = {"name": e["name"], "exe": e["exe"], "answer": None, "config": None,
                   "fault": None, "read": None, "read_state": None, "source": e.get("source")}
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
                if e["name"] in reads:
                    code, out, state = reads[e["name"]]
                    row["config"] = tools.counted_config(code, out) if state == "ran" else None
                    if row["config"] is None:
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
            raise Refusal("no_answer", KEY_LINE[why(row)], _again(cmd, name),
                          name=name, key=key, state=row["state"])
        return _silent(cmd, r, row, table)
    if not key:
        return _tool(cmd, r, name, cfg, _from(row["source"], r.home))
    found = [s for s in cfg["settings"] if s["key"] == key]
    if not found and name == r.suite and key.startswith("sources."):
        known = tools.rows(cmd.env, cmd.lib)
        if key[len("sources."):] in known:  # no line is written: the card that shows how (R6)
            return _source_card(cmd, r, key[len("sources."):], known[key[len("sources."):]], key=key)
    if not found:
        whole = r.suite_config() if row["name"] == r.suite else r.read_one(row, None)
        keys = [s["key"] for s in (whole or {}).get("settings") or ()]
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
            if row["state"] != "answers" and row["name"] in table:
                words = words if words is not None else tools.descriptions(cmd.env)
                item["table"] = table[row["name"]]
                item["description"] = words.get(row["name"])
            item["source"] = row["source"]
            out.append(item)
        t.json({"schema": "agentik.config/1", "ok": True, "tools": out})
        return 0
    t.line("config.title", count=len(rows))
    lines = []
    for row in rows:
        n, d = _counts(row)
        after = row["fault"]
        if n is not None:
            cells = [term.name(row["name"]), row["state"],
                     t.text("config.count.one" if n == 1 else "config.count", n=n),
                     t.text("config.differ", n=d)]
            user = r.user_file(row["config"])
            if user:
                cells.append(term.path(plan.shown(user, r.home)))
        elif row["read_state"]:
            cells = [term.name(row["name"]), row["state"], t.text(READ_CELL[row["read_state"]])]
        elif row["name"] in table and row["state"] != "answers":
            words = words if words is not None else tools.descriptions(cmd.env)
            cells = [term.name(row["name"]), row["state"], t.text("config.from_table"), "",
                     term.path(str(table[row["name"]].get("user_file") or ""))]
            after = words.get(row["name"])
        else:
            cells = [term.name(row["name"]), row["state"]]
        status = "warn" if row["read_state"] else STATUS.get(row["state"], "warn")
        source, extra = row["source"], None
        if source and source["kind"] == "undecided":
            status, extra = "warn", t.text("config.undecided", count=len(_ids(source)))
        elif _from(source, r.home):
            extra = t.text("config.from", source=_from(source, r.home))
        lines.append((status, cells, after, extra))
    # the source's words end a row, in a column after every other row's cells (R6)
    wide = max(len(cells) for _, cells, _, _ in lines)
    t.table([(status, cells + ([""] * (wide - len(cells)) + [extra] if extra else []), after)
             for status, cells, after, extra in lines])
    t.hint("hint.config", **cmd.slots())
    return 0


def _silent(cmd, r, row, table):
    """A tool that gives no settings: its row of the fallback table, else its state."""
    t, name = cmd.t, row["name"]
    if cmd.opts["json"]:
        obj = {"schema": "agentik.config/1", "ok": True, "tool": name, "state": row["state"],
               "layers": [], "settings": []}
        if row["read_state"]:
            obj["read"] = row["read_state"]
        if table:
            obj["table"] = table
            obj["description"] = tools.descriptions(cmd.env).get(name)
        cmd.t.json(obj)
        return 0
    _titled(cmd, STATE_LINE[why(row)], _from(row["source"], r.home), name=name)
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
        t.hint("hint.config.back", **cmd.slots())
        return 0
    t.hint("hint.config.back", **cmd.slots())
    return 0


def _tool(cmd, r, name, cfg, origin=None):
    t, rows = cmd.t, cfg["settings"]
    if cmd.opts["json"]:
        t.json({"schema": "agentik.config/1", "ok": True, "tool": name, "layers": cfg["layers"],
                "settings": rows, "warnings": cfg.get("warnings") or []})
        return 0
    changed = sum(1 for s in rows if differs(s))
    _titled(cmd, "config.tool.title", origin, name=name, changed=changed,
            settings=t.text("config.count.one" if len(rows) == 1 else "config.count", n=len(rows)))

    def row(s, key):
        cells = [term.name(key), shown_value(s.get("value")),
                 str(s["source"].get("layer") or "default")]
        if differs(s):
            cells.append(t.text("config.changed"))
        return ("ok" if differs(s) else None, cells, None)

    if len(rows) > GROUP_PAST:
        groups = {}
        for s in rows:
            groups.setdefault(s["key"].split(".", 1)[0], []).append(s)
        for head, members in groups.items():
            t.line("config.group", group=head, style="name")
            t.table([row(s, s["key"]) for s in members], indent=4)
    else:
        t.table([row(s, s["key"]) for s in rows])
    for w in cfg.get("warnings") or ():
        said = t.text("config.badvalue", key=w.get("key"), value=shown_value(w.get("value"))) \
            if w.get("reason") == "choice" else t.text("config.unknown", key=w.get("key"))
        t.table([("warn", [said,
                           term.path("%s:%s" % (plan.shown(str(w.get("path")), r.home), w.get("line")))],
                  None)])
    t.hint("hint.config.tool", **cmd.slots(), name=name)
    return 0


def _card(cmd, r, name, cfg, s):
    t, src, change = cmd.t, s["source"], s["change"]
    if cmd.opts["json"]:
        t.json({"schema": "agentik.config/1", "ok": True, "tool": name, "key": s["key"],
                "layers": cfg["layers"], "setting": s})
        return 0
    t.line("config.card.title", name=name, key=s["key"])
    label = lambda mid: term.name(t.text("config.label." + mid))  # noqa: E731
    rows = [(None, [label("value"), shown_value(s.get("value"))], None)]
    if s.get("summary"):
        rows.append((None, [label("summary"), str(s["summary"])], None))
    if s.get("default") is not None:
        rows.append((None, [label("default"), shown_value(s["default"])], None))
    if s.get("choices"):
        rows.append((None, [label("choices"), ", ".join(shown_value(c) for c in s["choices"])], None))
    if src.get("path"):
        where = "%s:%s" % (plan.shown(str(src["path"]), r.home), src.get("line")) \
            if src.get("line") else plan.shown(str(src["path"]), r.home)
        rows.append((None, [label("set_by"), t.text("config.set_by", layer=src.get("layer"), where=where)],
                     None))
    else:
        rows.append((None, [label("set_by"), str(src.get("layer") or "default")], None))
    for v in s.get("values") or ():
        rows.append((None, [label("layer"), t.text("config.layer", layer=v.get("layer"),
                                                     value=shown_value(v.get("value")))], None))
    kind = change.get("kind")
    if kind in ("command", "launch") and change.get("command"):
        rows.append((None, [label(kind), str(change["command"])], None))
    elif kind == "edit" and change.get("path"):
        rows.append((None, [label("edit"), term.path(plan.shown(str(change["path"]), r.home))], None))
        for line in str(change.get("block") or "").splitlines():
            rows.append((None, ["", line], None))
    else:
        rows.append((None, [label("fixed"), str(change.get("note") or t.text("config.fixed"))], None))
    if kind != "fixed" and change.get("note"):
        rows.append((None, [label("note"), str(change["note"])], None))
    rows.append((None, [label("holds"), t.text("config.live" if s.get("live") else "config.later")], None))
    t.table(rows)
    t.hint("hint.config.card", **cmd.slots())
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
