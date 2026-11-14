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
"""
import difflib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time

from . import form, gather, plan, scrub, send, term

WORDS = ("new", "show", "strike", "drop", "edit", "reword", "send", "discard")
SCHEMA = "agentik.issue/1"
ID = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{4}\Z")
READ_CAP = 1 << 20  # bytes of a draft or a render read back
# The cut of a free value scrubbed again (A1), by its key: gather's bounds, the title's own.
CAPS = {"ran": gather.RAN, "expected": gather.EXPECTED, "happened": gather.LINE,
        "title": form.TITLE_BYTES, "name": gather.ROW_NAME, "detail": gather.ROW_DETAIL}
HIGHLIGHT = "7"  # a placeholder or an unsure span, on a terminal


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
    return cmd.Usage(code, mid, remedy or cmd.say("issue", "--help"), exit_code,
                     **dict(_slots(cmd), **values))


# ---- the words ---------------------------------------------------------------------------

def do_issue(cmd, nouns):
    o = cmd.opts
    word = nouns[0] if nouns else None
    if word is not None and word not in WORDS:
        near = difflib.get_close_matches(word, WORDS, n=1, cutoff=0.6)
        if near:
            raise _usage(cmd, "unknown_word", "err.issue.word.near", cmd.say("issue", near[0]),
                         word=word, near=near[0])
        raise _usage(cmd, "unknown_word", "err.issue.word", word=word)
    if word is None:
        return _read(cmd)
    if o["check"]:
        raise _usage(cmd, "check_alone", "err.issue.check")
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
    """The draft a word acts on: `--draft ID`, else the newest unsent, else the newest."""
    found = _drafts(drafts_dir(cmd.env))
    want = cmd.opts["draft"]
    if want is not None:
        for d in found:
            if d["id"] == want:
                return d
        raise _usage(cmd, "no_draft", "err.issue.draft", cmd.say("issue"), id=want)
    unsent = [d for d in found if not d["url"]]
    if len(unsent) > 1:
        cmd.t.hint("hint.issue.which", _slots(cmd), id=unsent[-1]["id"], count=len(unsent))
    if unsent or found:
        return (unsent or found)[-1]
    raise _usage(cmd, "no_draft", "err.issue.none", cmd.say("issue", "new"))


def _public(cmd):
    try:
        return gather.load_public(cmd.lib)
    except ValueError:
        raise _usage(cmd, "no_table", "err.issue.public", cmd.say("doctor"),
                     path=os.path.join(cmd.lib, gather.PUBLIC))


def _machine(cmd, public, logins=()):
    try:
        return scrub.machine(cmd.env, cmd.cwd, public, logins)
    except scrub.PrivateUnreadable:
        raise _usage(cmd, "private_unreadable", "err.issue.private", cmd.say("issue"))


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


def _counts(data):
    """{kind: {"n": distinct placeholders, "lines": [line...]}} of the draft's bytes."""
    found = {}
    for n, line in enumerate(data.decode("utf-8").split("\n"), 1):
        for mt in scrub.PH.finditer(line):
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
            raise _usage(cmd, "unknown_tool", "err.issue.tool", cmd.say("issue", "new"), tool=named,
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
    public = _public(cmd)
    m = _machine(cmd, public)
    exit_code = None
    if o["exit"] is not None:
        if not re.fullmatch(r"[0-9]{1,3}", o["exit"]) or int(o["exit"]) > 255:
            raise _usage(cmd, "bad_exit", "err.issue.exit", value=o["exit"])
        exit_code = int(o["exit"])
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
    layer = _Layer(m)
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
    root = drafts_dir(env)
    path = _make(root)
    counts = _counts(data)
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
    t.line("issue.new.done", tool=tool)
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
    data = _read_file(cmd, os.path.join(d["path"], "issue.md"))
    try:
        return data, form.parse(data, public["tools"])
    except form.NotTheForm as e:
        raise _usage(cmd, "not_the_form", "err.issue.form", cmd.say("issue", "discard"), exit_code=1,
                     line=e.line)


def _read_file(cmd, path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        raise _usage(cmd, "unreadable", "err.issue.unreadable", path=plan.shown(path, cmd.env.get("HOME")))
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise _usage(cmd, "unreadable", "err.issue.unreadable",
                         path=plan.shown(path, cmd.env.get("HOME")))
        chunks, size = [], 0
        while size <= READ_CAP:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
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
    words = t.text("issue.count.word" if len(marks) == 1 else "issue.count.words", n=len(marks))
    where = t.text("issue.count.place" if places == 1 else "issue.count.places", n=places)
    if not places:
        t.line("issue.strike.none", words=words, places=where)
        return 0
    _save(cmd, d, fields)
    t.line("issue.strike.done", words=words, places=where,
           marks=", ".join("<struck-%s>" % p for p in marks))
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
        saved = _read_file(cmd, copy)
    finally:
        try:
            os.unlink(copy)
        except OSError:
            pass
    try:
        got = form.parse(saved, public["tools"])
    except form.NotTheForm as e:
        cmd.t.error("err.issue.edit.form", line=e.line)
        return 1
    layer = _Layer(m, [v for _, _, v in form.free(got)])
    got = layer.guard(layer.form(got))
    _save(cmd, d, got, list(d["meta"].get("unsure") or []) + layer.unsure)
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
        cmd.t.line("issue.reword.kept", kinds=", ".join(dict.fromkeys(k for k, _ in misses)))
        return 1
    added = form.added(render, fields)
    m = _machine(cmd, public)
    new = form.put(fields, "happened", render["happened"])
    if fields["expected"] is not None:
        new = form.put(new, "expected", render["expected"])
    layer = _Layer(m, [v for _, _, v in form.free(new)])
    new = layer.guard(layer.form(new, ("happened", "expected")))
    unsure = list(d["meta"].get("unsure") or []) + [w for w in added + layer.unsure]
    _save(cmd, d, new, list(dict.fromkeys(unsure)))
    cmd.t.line("issue.reword.done")
    if added:
        cmd.t.line("issue.reword.added", words=", ".join(added))
    return 0


# ---- send, show, discard (R6, R7) ----------------------------------------------------------

def _private_path(cmd, path, folder):
    """A link, the wrong kind, or one open to others: exit 2."""
    try:
        st = os.lstat(path)
    except OSError:
        raise _usage(cmd, "unsafe", "err.issue.unsafe", path=plan.shown(path, cmd.env.get("HOME")))
    kind = stat.S_ISDIR(st.st_mode) if folder else stat.S_ISREG(st.st_mode)
    if stat.S_ISLNK(st.st_mode) or not kind or st.st_mode & (0o077 if folder else 0o022) \
            or st.st_uid != os.getuid():
        raise _usage(cmd, "unsafe", "err.issue.unsafe", path=plan.shown(path, cmd.env.get("HOME")))


def _refused(cmd, r):
    raise _usage(cmd, r.mid.rsplit(".", 1)[-1], r.mid, cmd.say("issue", "send"), exit_code=r.code,
                 **r.values)


def _send(cmd, nouns):
    o, t, env = cmd.opts, cmd.t, cmd.env
    if o["yes"]:
        raise _usage(cmd, "no_yes", "err.issue.send.yes", cmd.say("issue", "send"))
    cmd._no_nouns(nouns)
    root = drafts_dir(env)
    if os.path.lexists(root):
        _private_path(cmd, root, True)
    d = _target(cmd)
    if d["url"]:
        raise _usage(cmd, "sent", "err.issue.sent", cmd.say("issue"), exit_code=1, url=d["url"])
    _private_path(cmd, d["path"], True)
    path = os.path.join(d["path"], "issue.md")
    _private_path(cmd, path, False)
    data = _read_file(cmd, path)
    public = _public(cmd)
    logins = [login for login, _ in send.accounts(env)]
    m = _machine(cmd, public, logins)
    found = send.check(data, m, public, form, scrub)
    if found:
        for line, kind in found:
            t.error("err.issue.send.line", line=line, kind=kind, **_slots(cmd))
        t.hint("hint.issue.mend", _slots(cmd))
        return 1
    repo = send.repo_of(data, public)
    fingerprint = send.marker(data)[2]
    road = send.account(env, o["as_login"])
    if road["road"] == "refuse":
        raise _usage(cmd, "account", road["why"], cmd.say("issue", "send"), **road["values"])
    web = o["web"] or road["road"] == "web"
    notes = []
    if not web:
        state, matches = send.search(env, repo, fingerprint)
        if state == "open" and not o["not_a_duplicate"]:
            raise _usage(cmd, "duplicate", "err.issue.send.open", cmd.say("issue", "send"),
                         exit_code=1, url=matches[0].get("url", ""))
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
        t.line("issue.send.kept", err=True)
        return 1
    if web:
        found, new = send.web(approved.data, repo, fingerprint)
        t.line("issue.send.web.path", path=path)
        t.line("issue.send.web.search", url=found)
        t.line("issue.send.web.new", url=new)
        return 0
    if o["dry_run"]:
        t.line("issue.send.dry", err=True)
        return 0
    try:
        url = send._file(approved, repo, env)
    except send.Refusal as r:
        _refused(cmd, r)
    term.keep(os.path.join(d["path"], "sent.json"), (json.dumps(
        {"url": url, "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "sha256": approved.sha256}) + "\n").encode("utf-8"))
    t.line("issue.send.url", url=url)
    return 0


def _show(cmd, nouns):
    cmd._no_nouns(nouns)
    d = _target(cmd)
    data = _read_file(cmd, os.path.join(d["path"], "issue.md"))
    for line in data.decode("utf-8", "replace").split("\n")[:-1]:
        cmd.t.marked(line, [])
    return 0


def _discard(cmd, nouns):
    cmd._no_nouns(nouns)
    d = _target(cmd)
    shutil.rmtree(d["path"])
    cmd.t.line("issue.discard.done", id=d["id"])
    return 0

