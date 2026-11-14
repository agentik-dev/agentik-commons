"""`issue`: a problem drafted on this machine and sent only by a person (hq design/22; packet
rp6-verb). It joins the four modules: `gather` reads the facts, `scrub` takes out what is
private, `form` writes the draft's bytes, and `send` shows them on the terminal device and files
them after the typed word.

The words: none (the drafts and their state), `new [TOOL]`, `show`, `strike WORD...`, `drop
SECTION...`, `edit`, `reword FILE`, `send` and `discard`. A draft is a folder of
${XDG_STATE_HOME:-~/.local/state}/agentik-suite/issues/, mode 0700: `issue.md`, the exact bytes,
and `draft.json`, its fields, repo, fingerprint and counts; `sent.json` once it is filed. Raw text
reaches no file, no message and no exception: only scrubbed values are written or printed. `new`
calls no network; `send` reads the one file once, and those bytes are what it checks, shows and
files.

Each refusal is sc4's two lines (`cmd.Refusal`): the cause, then `next:` and the line typed,
mended, where the suite would run it and it only reads; a word that writes or sends is never
offered, so the help of the verb stands in for it. Each word answers --json with one
`agentik.issue/1` object on stdout, and no key holds an absolute path (rp6 phase 2, review 1 F6).
"""
import difflib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

from . import form, gather, plan, scrub, send, term

WORDS = ("new", "show", "strike", "drop", "edit", "reword", "send", "discard")
WRITERS = ("new", "strike", "drop", "edit", "reword", "discard")  # each refuses --dry-run (review 2)
SCHEMA = "agentik.issue/1"
ID = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{4}\Z")
READ_CAP = 1 << 20  # bytes of a draft or a render read back
# The cut of a free value scrubbed again (A1), by its key: gather's bounds, the title's own.
CAPS = {"ran": gather.RAN, "expected": gather.EXPECTED, "happened": gather.LINE,
        "title": form.TITLE_BYTES, "name": gather.ROW_NAME, "detail": gather.ROW_DETAIL}
HIGHLIGHT = "7"  # a placeholder or an unsure span, on a terminal


def reads(nouns):
    """True where `issue` with these words only reads: bare, with --check, or `show`. Only such a
    line is offered behind `next:`; --dry-run makes no other word a read (phase 2)."""
    return not nouns or list(nouns) == ["show"]


def takes(o, nouns):
    """True where `issue` takes these words and flags, by its refusals that read no file."""
    if not nouns:
        return True
    word, rest = nouns[0], nouns[1:]
    if word not in WORDS or o["check"] or o["dry_run"] and word in WRITERS:
        return False
    if word == "new":
        return len(rest) <= 1 and (o["exit"] is None or _exit(o["exit"]) is not None)
    if word == "strike":
        return bool(rest)
    if word == "drop":
        return bool(rest) and all(r in form.SECTIONS for r in rest)
    if word == "reword":
        return len(rest) == 1
    return not rest and not (word == "send" and o["yes"])


def _exit(value):
    return int(value) if re.fullmatch(r"[0-9]{1,3}", value) and int(value) <= 255 else None


class _Buffer:
    """A stream the in-process doctor writes to."""

    def __init__(self):
        self.parts = []

    def write(self, text):
        self.parts.append(text)

    def flush(self):
        pass


def drafts_dir(env):
    state = env.get("XDG_STATE_HOME") or ""
    if not os.path.isabs(state):
        state = os.path.join(env.get("HOME") or os.path.expanduser("~"), ".local", "state")
    return os.path.join(state, "agentik-suite", "issues")


def _made(path):
    """When a draft folder was made, which orders two drafts of one second."""
    try:
        return os.lstat(path).st_ctime_ns
    except OSError:
        return 0


def _drafts(root):
    """Each draft folder, oldest first: {id, path, url (None unsent), meta}."""
    try:
        names = [n for n in os.listdir(root) if ID.match(n)]
        names.sort(key=lambda n: (n[:16], _made(os.path.join(root, n))))
    except OSError:
        return []
    found = []
    for name in names:
        path = os.path.join(root, name)
        sent = plan._read_json(os.path.join(path, "sent.json"))
        meta = plan._read_json(os.path.join(path, "draft.json"))
        url = sent.get("url") if isinstance(sent, dict) else None
        found.append({"id": name, "path": path, "url": url if isinstance(url, str) else None,
                      "meta": meta if isinstance(meta, dict) else {}})
    return found


def _slots(cmd):
    words = {w: cmd.say("issue", w) for w in WORDS}
    return dict(cmd.slots(), issue=cmd.say("issue"), check=cmd.say("issue", "--check"), **words)


def _usage(cmd, code, mid, remedy=None, exit_code=2, **values):
    """A refusal in sc4's two lines: the cause, then `next:` and `remedy`, a command from
    `cmd.offer` or `cmd.again` (each offers a line only where the suite would run it and it only
    reads, else the help of the verb), by default the help of the verb; False for no `next:`."""
    remedy = cmd.say("help", "issue") if remedy is None else remedy or None
    return cmd.Refusal(code, mid, remedy, exit_code, **dict(_slots(cmd), **values))


def _json(cmd, d, **more):
    cmd.t.json(dict({"schema": SCHEMA, "ok": True, "id": d["id"]}, **more))


# ---- the words ---------------------------------------------------------------------------

def do_issue(cmd, nouns):
    """The verb in the frame: a file of the drafts that cannot be read, written or removed is a
    refusal that names no path, never a traceback (review 1 F5)."""
    try:
        return _word(cmd, nouns)
    except BrokenPipeError:
        raise
    except (OSError, UnicodeError):
        raise _usage(cmd, "unreadable", "err.issue.io", cmd.offer(["issue"]))


def _word(cmd, nouns):
    o = cmd.opts
    word = nouns[0] if nouns else None
    if word is not None and word not in WORDS:
        near = difflib.get_close_matches(word, WORDS, n=1, cutoff=0.6)
        if near:
            raise _usage(cmd, "unknown_word", "err.issue.word.near", cmd.again({cmd.at[1]: near}),
                         word=word, near=near[0])
        raise _usage(cmd, "unknown_word", "err.issue.word", word=word)
    if word is None:
        return _read(cmd)
    if o["dry_run"] and word in WRITERS:  # send alone keeps it: nothing is read, made or removed
        raise _usage(cmd, "dry_run", "err.issue.dry", word=word)
    if o["check"]:
        raise _usage(cmd, "check_alone", "err.issue.check", cmd.again({i: [] for i in cmd.at[1:]}))
    return globals()["_" + word](cmd, nouns[1:])


def _read(cmd):
    t = cmd.t
    found = _drafts(drafts_dir(cmd.env))
    unsent = [d for d in found if not d["url"]]
    if cmd.opts["json"]:
        t.json({"schema": SCHEMA, "ok": True, "drafts": [
            {"id": d["id"], "path": d["path"], "tool": d["meta"].get("tool"), "sent": d["url"]}
            for d in found]})
        return 1 if cmd.opts["check"] and unsent else 0
    if cmd.opts["check"]:
        for d in unsent:
            t.line("issue.check.waits", id=d["id"], tool=d["meta"].get("tool") or "")
        return 1 if unsent else 0
    if not found:
        t.line("issue.list.none")
        return 0
    for d in found:
        if d["url"]:
            t.line("issue.list.sent", id=d["id"], url=d["url"])
        else:
            t.line("issue.list.unsent", id=d["id"], tool=d["meta"].get("tool") or "",
                   title=d["meta"].get("title") or "")
    if unsent:
        t.hint("hint.issue.read", _slots(cmd))
    return 0


def _target(cmd):
    """The draft a word acts on: `--draft ID`, else the newest unsent, else the newest. The
    drafts folder and the draft are each a real folder of this user's, open to no other, checked
    before anything is read, written or removed (review 1 F4, F5); a refusal names the draft by
    its id."""
    root = drafts_dir(cmd.env)
    if os.path.lexists(root):
        _private_path(cmd, root, True)
    found = _drafts(root)
    want = cmd.opts["draft"]
    if want is not None:
        d = ([d for d in found if d["id"] == want] or [None])[0]
        if d is None:
            raise _usage(cmd, "no_draft", "err.issue.draft", cmd.offer(["issue"]), id=want)
    else:
        unsent = [d for d in found if not d["url"]]
        if len(unsent) > 1:
            cmd.t.hint("hint.issue.which", _slots(cmd), id=unsent[-1]["id"], count=len(unsent))
        if not found:
            raise _usage(cmd, "no_draft", "err.issue.none", cmd.offer(["issue", "new"]))
        d = (unsent or found)[-1]
    _private_path(cmd, d["path"], True, d["id"])
    return d


def _public(cmd):
    try:
        return gather.load_public(cmd.lib)
    except ValueError:
        raise _usage(cmd, "no_table", "err.issue.public", cmd.offer(["doctor"]),
                     path=plan.shown(os.path.join(cmd.lib, gather.PUBLIC), cmd.env.get("HOME")))


def _machine(cmd, public, logins=()):
    try:
        return scrub.machine(cmd.env, cmd.cwd, public, logins)
    except scrub.PrivateUnreadable:
        raise _usage(cmd, "private_unreadable", "err.issue.private", False)


def _terminal(cmd):
    try:
        return sys.stdin.isatty() and cmd.t.err.tty
    except (AttributeError, ValueError, OSError):
        return False


def _ask(cmd, mid, **values):
    cmd.t.line(mid, err=True, **values)
    cmd.t.flush()
    try:
        return sys.stdin.readline().strip() or None
    except (OSError, ValueError, KeyboardInterrupt):
        return None


def _doctor(cmd):
    """This command's own `doctor --json`, in process over two buffers; None when unread."""
    from . import cli
    out, err = _Buffer(), _Buffer()
    cli.Command(["doctor", "--json"], dict(cmd.env), out, err).run()
    try:
        return json.loads("".join(out.parts))
    except ValueError:
        return None


# ---- layer 1 over the facts and the form (R4, A1) ------------------------------------------

def _joined(facts, fn):
    """map_free with the last lines as one text."""
    f = json.loads(json.dumps(facts))
    lines = f["output"]["lines"]
    f["output"]["lines"] = ["\n".join(lines)] if lines else []
    out = gather.map_free(f, fn)
    o = out["output"]
    o["lines"] = o["lines"][0].split("\n") if o["lines"] and isinstance(o["lines"][0], str) else []
    return out


class _Layer:
    """Layer 1 for one draft: one numbering, the unsure spans it marks, the machine's table."""

    def __init__(self, m, texts=()):
        self.m, self.st, self.unsure = m, scrub.numbering(texts), []

    def written(self):
        """Each placeholder this layer wrote, so a report names only what the scrub changed."""
        return set(self.st.values.values())

    def __call__(self, value):
        text, _counts, spans = scrub.scrub(value, self.m, state=self.st)
        for a, b, kind in spans:
            if kind == "unsure" and text[a:b] not in self.unsure:
                self.unsure.append(text[a:b])
        return text

    def dirty(self, value):
        return bool(scrub.detect(value, self.m))

    def facts(self, facts):
        """Scrubbed, bound, and each value that reads dirty after the bound scrubbed and bound
        once more, then `unreadable` (A1)."""
        b = gather.bound(_joined(facts, self))
        b = gather.bound(_joined(b, lambda v: self(v) if self.dirty(v) else v))
        out = _joined(b, lambda v: v if not self.dirty(v) else "\n".join(
            gather.UNREADABLE if self.dirty(l) else l for l in v.split("\n")))
        return _joined(out, lambda v: gather.UNREADABLE if self.dirty(v) else v)

    def form(self, fields, keys=None):
        """Each free value of the form (of `keys`, else all) through layer 1, cut to its bound,
        and `unreadable` when it still reads dirty."""
        for key, _line, value in list(form.free(fields)):
            if keys is not None and key not in keys:
                continue
            text = self(value)
            if key == "lines":
                text = "\n".join(gather._cut(l, gather.LINE) for l in text.split("\n"))
            else:
                text = gather._cut(text, CAPS.get(key.rsplit(".", 1)[-1], gather.LINE))
            if self.dirty(text):
                text = "\n".join(gather.UNREADABLE for _ in text.split("\n"))
            if text != value:
                fields = form.put(fields, key, text)
        return fields

    def guard(self, fields):
        """The last word of A1 on the form: a free value that reads dirty is `unreadable`."""
        for key, _line, value in list(form.free(fields)):
            if self.dirty(value):
                fields = form.put(fields, key, "\n".join(gather.UNREADABLE for _ in value.split("\n")))
        return fields


def _counts(data, only=None):
    """{kind: {"n": distinct placeholders, "lines": [line...]}} of the draft's bytes; of the
    placeholders in `only` alone when it is given (review 1 F3)."""
    found = {}
    for n, line in enumerate(data.decode("utf-8").split("\n"), 1):
        for mt in scrub.PH.finditer(line):
            if only is not None and mt.group() not in only:
                continue
            kind = mt.group(1) or mt.group(3)
            k = found.setdefault(kind, {"names": [], "lines": []})
            if mt.group() not in k["names"]:
                k["names"].append(mt.group())
            if n not in k["lines"]:
                k["lines"].append(n)
    return {kind: {"n": len(v["names"]), "lines": v["lines"]} for kind, v in sorted(found.items())}


# ---- new (R4) ------------------------------------------------------------------------------

def _tool(cmd, public, named, found):
    tools = public["tools"]
    if named is not None:
        if named not in tools:
            raise _usage(cmd, "unknown_tool", "err.issue.tool", tool=named,
                         tools=", ".join(sorted(tools)))
        return named
    failing = []
    for g in (found or {}).get("tools") or []:
        if isinstance(g, dict) and g.get("name") in tools and any(
                isinstance(c, dict) and c.get("status") == "fail" for c in g.get("checks") or []):
            failing.append(g["name"])
    if len(failing) == 1:
        return failing[0]
    if _terminal(cmd):
        got = _ask(cmd, "issue.ask.tool", tools=", ".join(sorted(tools)))
        if got in tools:
            return got
    return "suite" if "suite" in tools else sorted(tools)[0]


def _new(cmd, nouns):
    o, t, env = cmd.opts, cmd.t, cmd.env
    if len(nouns) > 1:
        cmd._no_nouns(nouns[1:])
    root = drafts_dir(env)
    if os.path.lexists(root):  # a draft is never made through a link (review 1 F4's kind)
        _private_path(cmd, root, True)
    public = _public(cmd)
    m = _machine(cmd, public)
    exit_code = None
    if o["exit"] is not None:
        exit_code = _exit(o["exit"])
        if exit_code is None:
            raise _usage(cmd, "bad_exit", "err.issue.exit", value=o["exit"])
    if nouns and nouns[0] not in public["tools"]:
        _tool(cmd, public, nouns[0], None)
    found = _doctor(cmd)
    tool = _tool(cmd, public, nouns[0] if nouns else None, found)
    ran, expected = o["ran"], o["expected"]
    if ran is None and _terminal(cmd):
        ran = _ask(cmd, "issue.ask.ran")
    if expected is None and _terminal(cmd):
        expected = _ask(cmd, "issue.ask.expected")
    given = {"tool": tool, "ran": ran, "exit": exit_code, "output": o["output"], "expected": expected}
    facts = gather.facts(env, cmd.lib, given, lambda: found)
    # numbered past each placeholder the given values hold, so a typed <path-1> and a replaced
    # path never share a name (review 1 F3, design/22 item 4)
    texts = [facts["output"]["ran"], facts["words"]["expected"]] + facts["output"]["lines"] + \
        [r[k] for r in facts["checks"]["rows"] for k in ("name", "detail")]
    layer = _Layer(m, [t for t in texts if isinstance(t, str)])
    facts = layer.facts(facts)
    lines = [l for l in facts["output"]["lines"] if l.strip()]
    rows = [r for r in facts["checks"]["rows"] if r["status"] == "fail"]
    happened = lines[-1] if lines else rows[0]["detail"] if rows else ""
    launchers = {name: "agentik-" + name for name in public["tools"]}
    first = form.draft(facts, tool, happened, happened, "0" * 12)
    subject = form.subject(tool, first["ran"], first["exit"], first["rows"], launchers)
    parts = subject.split(":")
    verb = parts[2] if parts[0] in ("ran", "check") and parts[1] != "other" else ""
    fields = form.draft(facts, tool, form.title(verb, happened), happened,
                        form.fingerprint(tool, subject))
    fields, went = form.fit(layer.guard(fields))
    data = form.build(fields)
    path = _make(root)
    counts = _counts(data, layer.written())
    meta = {"schema": "agentik.issue-draft/1", "id": os.path.basename(path), "tool": tool,
            "repo": public["tools"][tool], "fingerprint": fields["fingerprint"],
            "title": fields["title"], "counts": counts, "unsure": layer.unsure, "fields": fields}
    term.keep(os.path.join(path, "issue.md"), data)
    term.keep(os.path.join(path, "draft.json"), (json.dumps(meta, indent=1) + "\n").encode("utf-8"))
    if o["json"]:
        t.json({"schema": SCHEMA, "ok": True, "id": meta["id"], "path": path, "tool": tool,
                "repo": meta["repo"], "size": len(data),
                "counts": {k: v["n"] for k, v in counts.items()}, "unsure": len(layer.unsure),
                "went": [list(w) for w in went]})
        return 0
    t.line("issue.new.done", tool=meta["tool"])
    _print_draft(cmd, data, layer.unsure)
    _report(cmd, data, counts, layer.unsure, m, went, meta["repo"])
    t.hint("hint.issue.new", _slots(cmd))
    return 0


def _make(root):
    """A new draft folder, each folder this makes 0700."""
    state = os.path.dirname(os.path.dirname(root))
    os.makedirs(state, exist_ok=True)
    for folder in (os.path.dirname(root), root):
        if not os.path.isdir(folder):
            os.mkdir(folder, 0o700)
            os.chmod(folder, 0o700)
    while True:
        name = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + os.urandom(2).hex()
        path = os.path.join(root, name)
        try:
            os.mkdir(path, 0o700)
        except FileExistsError:
            continue
        os.chmod(path, 0o700)
        return path


def _print_draft(cmd, data, unsure):
    """The draft's lines as the file holds them, one a line; each placeholder and unsure span
    painted on a terminal, and listed under the text off one."""
    t, marks = cmd.t, []
    for n, line in enumerate(data.decode("utf-8").split("\n")[:-1], 1):
        spans = [(mt.start(), mt.end()) for mt in scrub.PH.finditer(line)]
        for word in unsure:
            at = line.find(word)
            while word and at >= 0:
                spans.append((at, at + len(word)))
                at = line.find(word, at + len(word))
        t.marked(line, spans, HIGHLIGHT)
        if spans:
            marks.append((n, sorted(spans)))
    if not t.out.colour:
        lines = data.decode("utf-8").split("\n")
        for n, spans in marks:
            t.line("issue.new.mark", line=n, marks=", ".join(lines[n - 1][a:b] for a, b in spans))


def _report(cmd, data, counts, unsure, m, went, repo):
    t = cmd.t
    t.blank()
    for kind, c in counts.items():
        t.line("issue.new.replaced", n=c["n"], kind=kind, lines=", ".join(map(str, c["lines"])))
    t.line("issue.new.unsure", n=len(unsure))
    weak = scrub.weak(m)
    if weak:
        t.line("issue.new.weak", kinds=", ".join(weak))
    shown = [(w, n) for w, n in went if w != "over"]
    if shown:
        t.line("issue.new.went", went=", ".join("%s %d" % w for w in shown))
    t.line("issue.new.size", size=len(data), ceiling=form.CEILING)
    over = [n for w, n in went if w == "over"]
    if over:
        t.line("issue.new.over", size=over[0], over=over[0] - form.CEILING, **_slots(cmd))
    t.line("issue.new.repo", repo=repo)
    t.line("issue.new.warning")


# ---- the user's removals (R5) --------------------------------------------------------------

def _load(cmd, d, public):
    data = _read_file(cmd, os.path.join(d["path"], "issue.md"), d["id"])
    try:
        return data, form.parse(data, public["tools"])
    except form.NotTheForm as e:
        raise _usage(cmd, "not_the_form", "err.issue.form", _show_line(cmd, d), exit_code=1,
                     line=e.line, id=d["id"])


def _show_line(cmd, d):
    return cmd.offer(["issue", "show"] + (["--draft", d["id"]] if cmd.opts["draft"] else []))


def _read_file(cmd, path, draft=None):
    """The bytes of the regular file at `path`, never followed through a link at its last part
    and never cut: past READ_CAP it is refused. `draft`, the id of the draft whose file it is,
    names it in a refusal; else the path as the person gave it."""
    if draft is None:
        why = dict(mid="err.issue.unreadable", path=plan.shown(path, cmd.env.get("HOME")))
    else:
        why = dict(mid="err.issue.unreadable.draft", id=draft, name=os.path.basename(path))
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        raise _usage(cmd, "unreadable", **why)
    try:
        if _kind(os.fstat(fd).st_mode) != _FILE:
            raise _usage(cmd, "unreadable", **why)
        chunks, size = [], 0
        while size <= READ_CAP:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
        if size > READ_CAP:
            raise _usage(cmd, "unreadable", **why)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _save(cmd, d, fields, unsure=None):
    data = form.build(fields)
    term.keep(os.path.join(d["path"], "issue.md"), data)
    meta = dict(d["meta"], fields=fields, title=fields["title"], counts=_counts(data))
    if unsure is not None:
        meta["unsure"] = unsure
    term.keep(os.path.join(d["path"], "draft.json"), (json.dumps(meta, indent=1) + "\n").encode("utf-8"))
    return data


def _strike(cmd, nouns):
    if not nouns:
        raise _usage(cmd, "no_word", "err.issue.strike")
    d, public = _target(cmd), _public(cmd)
    data, fields = _load(cmd, d, public)
    free = list(form.free(fields))
    joined = "\x00".join(v for _, _, v in free)
    struck, places = scrub.strike(joined, nouns)
    parts = struck.split("\x00")
    for (key, _line, value), new in zip(free, parts):
        if new != value:
            fields = form.put(fields, key, new)
    marks = [p for p in dict.fromkeys(scrub.STRUCK.findall(struck)) if "<struck-%s>" % p not in joined]
    t = cmd.t
    if places:
        _save(cmd, d, fields)
    marks = ["<struck-%s>" % p for p in marks]
    if cmd.opts["json"]:
        _json(cmd, d, words=len(marks), places=places, struck=marks)
        return 0
    words = t.text("issue.count.word" if len(marks) == 1 else "issue.count.words", n=len(marks))
    where = t.text("issue.count.place" if places == 1 else "issue.count.places", n=places)
    if not places:
        t.line("issue.strike.none", words=words, places=where)
        return 0
    t.line("issue.strike.done", words=words, places=where, marks=", ".join(marks))
    return 0


def _drop(cmd, nouns):
    if not nouns:
        raise _usage(cmd, "no_section", "err.issue.drop.none", sections=", ".join(form.SECTIONS))
    for noun in nouns:
        if noun not in form.SECTIONS:
            raise _usage(cmd, "no_section", "err.issue.drop", section=noun,
                         sections=", ".join(form.SECTIONS))
    d, public = _target(cmd), _public(cmd)
    _data, fields = _load(cmd, d, public)
    _save(cmd, d, form.drop(fields, *nouns))
    if cmd.opts["json"]:
        _json(cmd, d, dropped=list(dict.fromkeys(nouns)))
        return 0
    cmd.t.line("issue.drop.done", sections=", ".join(dict.fromkeys(nouns)))
    return 0


def _edit(cmd, nouns):
    cmd._no_nouns(nouns)
    if not _terminal(cmd):
        raise _usage(cmd, "no_terminal", "err.issue.edit.tty")
    editor = cmd.env.get("VISUAL") or cmd.env.get("EDITOR")
    if not editor:
        raise _usage(cmd, "no_editor", "err.issue.edit.none")
    d, public = _target(cmd), _public(cmd)
    data, fields = _load(cmd, d, public)
    m = _machine(cmd, public)
    fd, copy = tempfile.mkstemp(dir=d["path"], prefix=".edit-", suffix=".md")
    os.close(fd)
    try:
        term.keep(copy, data)
        try:
            subprocess.run(shlex.split(editor) + [copy], env=cmd.env)
        except (OSError, ValueError):
            raise _usage(cmd, "no_editor", "err.issue.edit.none")
        saved = _read_file(cmd, copy, d["id"])
    finally:
        try:
            os.unlink(copy)
        except OSError:
            pass
    try:
        got = form.parse(saved, public["tools"])
    except form.NotTheForm as e:
        raise _usage(cmd, "not_the_form", "err.issue.edit.form", False, exit_code=1, line=e.line)
    layer = _Layer(m, [v for _, _, v in form.free(got)])
    got = layer.guard(layer.form(got))
    data = _save(cmd, d, got, list(d["meta"].get("unsure") or []) + layer.unsure)
    if cmd.opts["json"]:
        _json(cmd, d, size=len(data), unsure=len(layer.unsure))
        return 0
    cmd.t.line("issue.edit.done")
    return 0


REWORD = re.compile(r"(Happened|Expected): ?(.*)\Z")


def _reword(cmd, nouns):
    if len(nouns) != 1:
        raise _usage(cmd, "no_file", "err.issue.reword.file")
    d, public = _target(cmd), _public(cmd)
    _data, fields = _load(cmd, d, public)
    try:
        text = _read_file(cmd, nouns[0]).decode("utf-8")
    except UnicodeDecodeError:
        raise _usage(cmd, "no_file", "err.issue.reword.file")
    render = {}
    for line in text.splitlines():
        mt = REWORD.match(line.strip())
        if mt:
            render[mt.group(1).lower()] = mt.group(2).strip()
    if set(render) != {"happened", "expected"}:
        raise _usage(cmd, "no_file", "err.issue.reword.file")
    if fields["expected"] is None:
        render["expected"] = ""
    misses = form.nothing_new(render, fields)
    if misses:
        kinds = list(dict.fromkeys(k for k, _ in misses))
        if cmd.opts["json"]:
            _json(cmd, d, reworded=False, kept=kinds)
        else:
            cmd.t.line("issue.reword.kept", kinds=", ".join(kinds))
        return 1
    m = _machine(cmd, public)
    new = form.put(fields, "happened", render["happened"])
    if fields["expected"] is not None:
        new = form.put(new, "expected", render["expected"])
    layer = _Layer(m, [v for _, _, v in form.free(new)])
    new = layer.guard(layer.form(new, ("happened", "expected")))
    # the words the render added, read from what the layer made of it: nothing of a render is
    # printed or saved before the scrub (review 1 F2, design/22 item 14)
    added = form.added({"happened": new["happened"], "expected": new["expected"] or ""}, fields)
    unsure = list(d["meta"].get("unsure") or []) + added + layer.unsure
    _save(cmd, d, new, list(dict.fromkeys(unsure)))
    if cmd.opts["json"]:
        _json(cmd, d, reworded=True, added=added)
        return 0
    cmd.t.line("issue.reword.done")
    if added:
        cmd.t.line("issue.reword.added", words=", ".join(added))
    return 0


# ---- send, show, discard (R6, R7) ----------------------------------------------------------

# The file-type bits of a mode (the stat module's S_IFMT, S_IFREG, S_IFDIR), so the package keeps
# to the modules its layout test allows; a link is neither kind and is refused as one.
_KIND, _FILE, _FOLDER = 0o170000, 0o100000, 0o040000


def _kind(mode):
    return mode & _KIND


def _private_path(cmd, path, folder, draft=None):
    """A link, the wrong kind, or one open to others: exit 2, naming the drafts folder, the
    draft by its id, or a file of the draft by its name and the draft's id; never a path."""
    if draft is None:
        why = dict(mid="err.issue.unsafe.root")
    elif folder:
        why = dict(mid="err.issue.unsafe", id=draft)
    else:
        why = dict(mid="err.issue.unsafe.file", id=draft, name=os.path.basename(path))
    try:
        st = os.lstat(path)
    except OSError:
        raise _usage(cmd, "unsafe", remedy=False, **why)
    if _kind(st.st_mode) != (_FOLDER if folder else _FILE) or st.st_mode & (0o077 if folder else 0o022) \
            or st.st_uid != os.getuid():
        raise _usage(cmd, "unsafe", remedy=False, **why)


def _refused(cmd, r):
    """send.py's refusal in the verb's frame; its `next:` is the help, never a line that sends."""
    raise _usage(cmd, r.mid.rsplit(".", 1)[-1], r.mid, exit_code=r.code, **r.values)


def _send(cmd, nouns):
    o, t, env = cmd.opts, cmd.t, cmd.env
    if o["yes"]:
        raise _usage(cmd, "no_yes", "err.issue.send.yes")
    cmd._no_nouns(nouns)
    d = _target(cmd)
    if d["url"]:
        raise _usage(cmd, "sent", "err.issue.sent", cmd.offer(["issue"]), exit_code=1, url=d["url"])
    path = os.path.join(d["path"], "issue.md")
    _private_path(cmd, path, False, d["id"])
    data = _read_file(cmd, path, d["id"])
    public = _public(cmd)
    logins = [login for login, _ in send.accounts(env)]
    m = _machine(cmd, public, logins)
    found = send.check(data, m, public, form, scrub)
    if found:
        if o["json"]:
            first = t.text("err.issue.send.line", line=found[0][0], kind=found[0][1])
            t.json({"schema": SCHEMA, "ok": False, "id": d["id"],
                    "error": {"code": "check", "message": first, "remedy": cmd.say("help", "issue")},
                    "lines": [{"line": line, "kind": kind} for line, kind in found]})
            return 1
        for line, kind in found:
            t.error("err.issue.send.line", line=line, kind=kind)
        t.hint("hint.issue.mend", _slots(cmd))
        return 1
    repo = send.repo_of(data, public)
    fingerprint = send.marker(data)[2]
    road = send.account(env, o["as_login"])
    if road["road"] == "refuse":
        raise _usage(cmd, "account", road["why"], **road["values"])
    web = o["web"] or road["road"] == "web"
    notes = []
    if not web:
        state, matches = send.search(env, repo, fingerprint)
        if state == "open" and not o["not_a_duplicate"]:
            raise _usage(cmd, "duplicate", "err.issue.send.open", exit_code=1,
                         url=matches[0].get("url", ""))
        if state == "none":
            t.line("issue.send.none", err=True, repo=repo, fingerprint=fingerprint)
        notes = send.notes(state, matches)
    elif road["road"] == "web":
        t.line(road["why"], err=True, **road["values"])
    login = t.text("issue.send.browser") if web else road["login"]
    try:
        approved = send.approve(data, repo, login, notes, env, t)
    except send.Refusal as r:
        _refused(cmd, r)
    if approved is None:
        if o["json"]:
            _json(cmd, d, filed=False)
        t.line("issue.send.kept", err=True)
        return 1
    if web:
        found, new = send.web(approved.data, repo, fingerprint)
        if o["json"]:
            _json(cmd, d, filed=False, search=found, new=new)
            return 0
        t.line("issue.send.web.path", path=path)
        t.line("issue.send.web.search", url=found)
        t.line("issue.send.web.new", url=new)
        return 0
    if o["dry_run"]:
        if o["json"]:
            _json(cmd, d, filed=False, dry_run=True)
        t.line("issue.send.dry", err=True)
        return 0
    try:
        url = send._file(approved, repo, env)
    except send.Refusal as r:
        _refused(cmd, r)
    try:  # filed: the URL is said whatever becomes of the record
        term.keep(os.path.join(d["path"], "sent.json"), (json.dumps(
            {"url": url, "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "sha256": approved.sha256}) + "\n").encode("utf-8"))
        kept = True
    except OSError:
        kept = False
    if o["json"]:
        _json(cmd, d, filed=True, url=url, recorded=kept)
    else:
        t.line("issue.send.url", url=url)
    if not kept:
        t.error("err.issue.sent.unkept", id=d["id"])
        return 1
    return 0


def _show(cmd, nouns):
    cmd._no_nouns(nouns)
    d = _target(cmd)
    data = _read_file(cmd, os.path.join(d["path"], "issue.md"), d["id"])
    text = data.decode("utf-8", "replace")
    if cmd.opts["json"]:
        _json(cmd, d, text=text)
        return 0
    for line in text.split("\n")[:-1]:
        cmd.t.marked(line, [])
    return 0


def _discard(cmd, nouns):
    """One draft removed: `_target` has found the drafts folder and the draft each a real folder
    of this user's of mode 0700 at most, so nothing outside the drafts goes (review 1 F4, F5)."""
    cmd._no_nouns(nouns)
    d = _target(cmd)
    shutil.rmtree(d["path"])
    if cmd.opts["json"]:
        _json(cmd, d, discarded=True)
        return 0
    cmd.t.line("issue.discard.done", id=d["id"])
    return 0

