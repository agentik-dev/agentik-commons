"""The issue's form, schema agentik-issue/1 (hq design/22 section 3, items 7, 10 and 11; packet
rp4-form): one dict of fields, written as bytes and read back to the same bytes; the subject and
the fingerprint of the marker line; the ceiling; and the nothing-new check of a rendered text.

The labels below are the form's grammar, constants of this module and not catalogue messages, so
a reworded catalogue cannot change what the reader reads. A free value is known only by the
reader: outside the fence each stands in a code span of its own, so no mention, reference or
tag in it is live and no value can close its span or the fold. It prints nothing."""
import hashlib
import re

SCHEMA = "agentik-issue/1"
CEILING = 4096
TITLE_BYTES = 72
EMPTY = "(empty)"
RAN = "**Ran:** "
EXIT = ", exit "
UNKNOWN = "unknown"
HAPPENED = "**Happened:** "
EXPECTED = "**Expected:** "
VERSIONS = "**Versions:** "
FOLD = "<details><summary>"
FOLD_END = "</summary>"
DIAGNOSIS = "Diagnosis"
COUNTS = "Diagnosis: %d failed, %d warned, %d passed"
HEAD = "| tool | status | check | detail |"
RULE = "|---|---|---|---|"
PLUGINS = "Plugins: "
OTHERS = "and %d other"
LAST = "Last lines:"
CLOSE = "</details>"
STATUS = ("fail", "warn")

KEYS = ("tool", "title", "ran", "exit", "happened", "expected", "versions", "system", "counts",
        "rows", "plugins", "others", "lines", "version", "fingerprint")
SECTIONS = {"checks": ("rows", "counts"), "plugins": ("plugins", "others"), "system": ("system",),
            "output": ("ran", "exit", "lines"), "words": ("expected",)}
SINGLE = ("title", "ran", "happened", "expected")

_VER = r"[0-9]+\.[0-9]+\.[0-9]+(?:-(?:alpha|beta|rc)\.[0-9]+)?"
_VERU = r"(?:%s|unreadable)" % _VER
_NAME = r"[a-z][a-z0-9-]*"
NAME = re.compile(_NAME)
VERSION = re.compile(_VERU)
FINGERPRINT = re.compile(r"[0-9a-f]{12}")
VERSION_ITEM = re.compile(r"(%s) %s(?: \((?:[0-9a-f]{12}|unreadable)\))?(?: launcher %s)?"
                          % (_NAME, _VERU, _VERU))
SYSTEM_ITEM = re.compile(r"Claude Code %s|(?:Darwin|Linux|other) (?:[0-9.]+|unreadable) "
                         r"(?:arm64|x86_64|aarch64|other)|Python (?:[0-9]+\.[0-9]+\.[0-9]+|unreadable)"
                         r"|in Claude Code|at a terminal" % _VERU)
PLUGIN_ITEM = re.compile(r"(%s) %s" % (_NAME, _VERU))
BREAKS = re.compile("[\n\r\x0b\x0c\x1c\x1d\x1e\x85  ]")
PLACEHOLDER = re.compile(r"<[a-z]+(?:-[0-9]+)?>")
TICKS = re.compile("`+")


class NotTheForm(ValueError):
    """The bytes do not read back as the form; `line` is the 1-based line the reader stopped at."""

    def __init__(self, line, why):
        ValueError.__init__(self, "line %d: %s" % (line, why))
        self.line = line
        self.why = why


def _copy(value):
    if isinstance(value, dict):
        return {k: _copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_copy(v) for v in value]
    return value


def _is_int(value, low, high=None):
    return (isinstance(value, int) and not isinstance(value, bool) and value >= low
            and (high is None or value <= high))


def _check(f):
    """A ValueError naming the first key whose value the form cannot hold; never the value."""
    if not isinstance(f, dict) or set(f) != set(KEYS):
        raise ValueError("the fields are not the form's keys")

    def bad(key):
        raise ValueError("field %s" % key)

    def text(key, value, optional=False):
        if value is None and optional:
            return
        if not isinstance(value, str):
            bad(key)
        if BREAKS.search(value):
            raise ValueError("field %s holds a line break" % key)

    def items(key, value, pattern, optional=False):
        if value is None and optional:
            return
        if not isinstance(value, list) or not all(isinstance(v, str) and pattern.fullmatch(v) for v in value):
            bad(key)

    if not isinstance(f["tool"], str) or not NAME.fullmatch(f["tool"]):
        bad("tool")
    text("title", f["title"])
    if not f["title"] or f["title"] != f["title"].strip():
        bad("title")
    if len(("%s %s" % (f["tool"], f["title"])).encode("utf-8", "surrogatepass")) > TITLE_BYTES:
        bad("title")
    text("ran", f["ran"], True)
    if f["exit"] is not None and (f["ran"] is None or not _is_int(f["exit"], 0, 255)):
        bad("exit")
    text("happened", f["happened"])
    text("expected", f["expected"], True)
    items("versions", f["versions"], VERSION_ITEM)
    if not f["versions"]:
        bad("versions")
    items("system", f["system"], SYSTEM_ITEM, True)
    if f["system"] == []:
        bad("system")
    if (f["rows"] is None) != (f["counts"] is None):
        bad("counts")
    if f["rows"] is not None:
        if not isinstance(f["counts"], list) or len(f["counts"]) != 3 or not all(_is_int(n, 0) for n in f["counts"]):
            bad("counts")
        if not isinstance(f["rows"], list):
            bad("rows")
        for i, row in enumerate(f["rows"]):
            if not isinstance(row, list) or len(row) != 4 or not isinstance(row[0], str) \
                    or not NAME.fullmatch(row[0]) or row[1] not in STATUS:
                bad("rows.%d" % i)
            text("rows.%d.name" % i, row[2])
            text("rows.%d.detail" % i, row[3])
    if (f["plugins"] is None) != (f["others"] is None):
        bad("others")
    if f["plugins"] is not None:
        items("plugins", f["plugins"], PLUGIN_ITEM)
        if not _is_int(f["others"], 0):
            bad("others")
    if f["lines"] is not None:
        if not isinstance(f["lines"], list) or not f["lines"]:
            bad("lines")
        for i, line in enumerate(f["lines"]):
            text("lines", line)
    if not isinstance(f["version"], str) or not VERSION.fullmatch(f["version"]):
        bad("version")
    if not isinstance(f["fingerprint"], str) or not FINGERPRINT.fullmatch(f["fingerprint"]):
        bad("fingerprint")


def _span(value, cell=False):
    """A free value as a code span of its own, or the empty word outside one."""
    if value == "":
        return EMPTY
    if cell:
        value = value.replace("|", "\\|")
    tick = "`" * (max([len(r) for r in TICKS.findall(value)] or [0]) + 1)
    if value[0] == "`" or value[-1] == "`" or (value[0] == " " and value[-1] == " " and value.strip(" ")):
        value = " " + value + " "
    return tick + value + tick


def _take_span(line, i, cell=False):
    """(value, end) of the span or empty word at line[i:]; ValueError when there is none."""
    if line.startswith(EMPTY, i):
        return "", i + len(EMPTY)
    opening = TICKS.match(line, i)
    if not opening:
        raise ValueError("no span")
    n = len(opening.group())
    for closing in TICKS.finditer(line, opening.end()):
        if len(closing.group()) == n:
            value = line[opening.end():closing.start()]
            if value[:1] == " " and value[-1:] == " " and value.strip(" "):
                value = value[1:-1]
            if cell:
                value = value.replace("\\|", "|")
            return value, closing.end()
    raise ValueError("an open span")


def _fence(lines):
    return "`" * max([3] + [len(r) + 1 for line in lines for r in TICKS.findall(line)])


def _render(f):
    """The form's lines and each free value's (key, line, value), in the form's order."""
    _check(f)
    out, frees = [], []

    def add(line, key=None, value=None):
        out.append(line)
        if key is not None:
            frees.append((key, len(out), value))

    add("%s %s" % (f["tool"], f["title"]), "title", f["title"])
    add("")
    if f["ran"] is not None:
        code = UNKNOWN if f["exit"] is None else str(f["exit"])
        add(RAN + _span(f["ran"]) + EXIT + code, "ran", f["ran"])
    add(HAPPENED + _span(f["happened"]), "happened", f["happened"])
    if f["expected"] is not None:
        add(EXPECTED + _span(f["expected"]), "expected", f["expected"])
    add(VERSIONS + ", ".join(f["versions"] + (f["system"] or [])))
    add("")
    if f["rows"] is not None or f["plugins"] is not None or f["lines"] is not None:
        add(FOLD + (DIAGNOSIS if f["counts"] is None else COUNTS % tuple(f["counts"])) + FOLD_END)
        add("")
        if f["rows"] is not None:
            add(HEAD)
            add(RULE)
            for i, (tool, status, name, detail) in enumerate(f["rows"]):
                add("| %s | %s | %s | %s |" % (tool, status, _span(name, True), _span(detail, True)),
                    "rows.%d.name" % i, name)
                frees.append(("rows.%d.detail" % i, len(out), detail))
            add("")
        if f["plugins"] is not None:
            add(PLUGINS + ", ".join(f["plugins"] + [OTHERS % f["others"]]))
            add("")
        if f["lines"] is not None:
            fence = _fence(f["lines"])
            add(LAST)
            add(fence)
            frees.append(("lines", len(out) + 1, "\n".join(f["lines"])))
            out.extend(f["lines"])
            add(fence)
            add("")
        add(CLOSE)
        add("")
    add(" ".join((SCHEMA, f["tool"], f["version"], f["fingerprint"])))
    return out, frees


def build(fields):
    """The form's bytes; a ValueError when a value cannot stand in it (fold a line break first)."""
    return ("\n".join(_render(fields)[0]) + "\n").encode("utf-8")


def free(fields):
    """[(key, line, value)]: every free value in the form's order, `line` its first line."""
    return _render(fields)[1]


def put(fields, key, value):
    """A copy of the fields with the one free value `key` replaced."""
    f = _copy(fields)
    if key in SINGLE:
        f[key] = value
    elif key == "lines":
        f["lines"] = value.split("\n")
    else:
        m = re.fullmatch(r"rows\.([0-9]+)\.(name|detail)", key)
        if not m or f["rows"] is None or int(m.group(1)) >= len(f["rows"]):
            raise KeyError(key)
        f["rows"][int(m.group(1))][2 if m.group(2) == "name" else 3] = value
    return f


def drop(fields, *sections):
    """A copy with each named section (checks, plugins, system, output, words) dropped."""
    f = _copy(fields)
    for section in sections:
        if section not in SECTIONS:
            raise ValueError("no section %s" % section)
        for key in SECTIONS[section]:
            f[key] = None
    return f


class _Reader:
    def __init__(self, lines, tools):
        self.lines, self.tools, self.i = lines, tools, 0

    def stop(self, why, at=None):
        raise NotTheForm((self.i if at is None else at) + 1, why)

    def peek(self):
        return self.lines[self.i] if self.i < len(self.lines) else None

    def take(self, why="the form ends early"):
        if self.i >= len(self.lines):
            self.stop(why)
        self.i += 1
        return self.lines[self.i - 1]

    def blank(self):
        if self.peek() != "":
            self.stop("a blank line is wanted")
        self.i += 1

    def tool(self, name):
        if name not in self.tools:
            self.stop("a tool the draft may not name")
        return name

    def labelled(self, label, cell=False):
        line = self.peek()
        if line is None or not line.startswith(label):
            self.stop("the label is not the form's")
        try:
            value, end = _take_span(line, len(label), cell)
        except ValueError:
            self.stop("a value outside its code span")
        return value, end, line


def _read(lines, tools):
    r = _Reader(lines, tools)
    f = dict.fromkeys(KEYS)
    m = re.fullmatch(r"(%s) (.+)" % _NAME, r.peek() or "")
    if not m:
        r.stop("the title line is not the form's")
    f["tool"], f["title"] = r.tool(m.group(1)), m.group(2)
    if len(r.peek().encode("utf-8", "surrogatepass")) > TITLE_BYTES or f["title"] != f["title"].strip():
        r.stop("the title line is not the form's")
    r.i += 1
    r.blank()
    if (r.peek() or "").startswith(RAN):
        f["ran"], end, line = r.labelled(RAN)
        code = re.fullmatch(re.escape(EXIT) + r"([0-9]{1,3}|%s)" % UNKNOWN, line[end:])
        if not code:
            r.stop("a value outside its code span")
        f["exit"] = None if code.group(1) == UNKNOWN else int(code.group(1))
        if f["exit"] is not None and f["exit"] > 255:
            r.stop("an exit the form cannot hold")
        r.i += 1
    f["happened"], end, line = r.labelled(HAPPENED)
    if line[end:]:
        r.stop("a value outside its code span")
    r.i += 1
    if (r.peek() or "").startswith(EXPECTED):
        f["expected"], end, line = r.labelled(EXPECTED)
        if line[end:]:
            r.stop("a value outside its code span")
        r.i += 1
    line = r.take()
    if not line.startswith(VERSIONS):
        r.stop("the label is not the form's", r.i - 1)
    versions, system = [], []
    for item in line[len(VERSIONS):].split(", "):
        m = VERSION_ITEM.fullmatch(item)
        if m and not system:
            if m.group(1) not in tools:
                r.stop("a tool the draft may not name", r.i - 1)
            versions.append(item)
        elif SYSTEM_ITEM.fullmatch(item):
            if not versions:
                r.stop("a system item before any version item", r.i - 1)
            system.append(item)
        else:
            r.stop("a version or system item is not the form's", r.i - 1)
    f["versions"], f["system"] = versions, system or None
    r.blank()
    if (r.peek() or "").startswith(FOLD):
        _read_fold(r, f)
    line = r.take()
    m = re.fullmatch(r"%s (%s) (%s) ([0-9a-f]{12})" % (re.escape(SCHEMA), _NAME, _VERU), line)
    if not m or m.group(1) != f["tool"]:
        r.stop("the marker line is not the form's", r.i - 1)
    f["version"], f["fingerprint"] = m.group(2), m.group(3)
    if r.i < len(lines):
        r.stop("text after the marker line")
    return f


def _read_fold(r, f):
    line = r.take()
    counts = re.fullmatch(re.escape(FOLD) + r"Diagnosis: ([0-9]+) failed, ([0-9]+) warned, ([0-9]+) passed"
                          + re.escape(FOLD_END), line)
    if counts:
        f["counts"] = [int(n) for n in counts.groups()]
    elif line != FOLD + DIAGNOSIS + FOLD_END:
        r.stop("the fold's summary is not the form's", r.i - 1)
    r.blank()
    if f["counts"] is not None:
        if r.take() != HEAD or r.take() != RULE:
            r.stop("the table's head is not the form's", r.i - 1)
        f["rows"] = []
        while r.peek() != "":
            row = r.take()
            m = re.match(r"\| (%s) \| (fail|warn) \| " % _NAME, row)
            if not m:
                r.stop("a row is not the form's", r.i - 1)
            try:
                name, end = _take_span(row, m.end(), True)
                if not row.startswith(" | ", end):
                    raise ValueError("no cell")
                detail, end = _take_span(row, end + 3, True)
                if row[end:] != " |":
                    raise ValueError("no cell")
            except ValueError:
                r.stop("a value outside its code span", r.i - 1)
            r.i -= 1
            f["rows"].append([r.tool(m.group(1)), m.group(2), name, detail])
            r.i += 1
        r.blank()
    if (r.peek() or "").startswith(PLUGINS):
        parts = r.take()[len(PLUGINS):].split(", ")
        others = re.fullmatch(OTHERS.replace("%d", "([0-9]+)"), parts.pop())
        if not others or not all(PLUGIN_ITEM.fullmatch(p) for p in parts):
            r.stop("the plugins line is not the form's", r.i - 1)
        r.i -= 1
        f["plugins"] = [p for p in parts if r.tool(PLUGIN_ITEM.fullmatch(p).group(1))]
        f["others"] = int(others.group(1))
        r.i += 1
        r.blank()
    if r.peek() == LAST:
        r.i += 1
        fence = r.take()
        if not re.fullmatch("`{3,}", fence):
            r.stop("the fence is not the form's", r.i - 1)
        start = r.i
        while r.take("the fence is never closed") != fence:
            pass
        f["lines"] = r.lines[start:r.i - 1]
        if not f["lines"]:
            r.stop("the fence is empty", r.i - 1)
        r.blank()
    if f["rows"] is None and f["plugins"] is None and f["lines"] is None:
        r.stop("an empty fold")
    if r.take() != CLOSE:
        r.stop("the fold is not closed by the form", r.i - 1)
    r.blank()


def parse(data, tools):
    """The fields of the form's bytes, `tools` the names a draft may hold. Strict: it raises
    NotTheForm, with the line it stopped at, unless the fields write again to the same bytes."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as err:
        raise NotTheForm(data[:err.start].count(b"\n") + 1, "the bytes are not UTF-8")
    lines = text.split("\n")
    if lines[-1] != "":
        raise NotTheForm(len(lines), "no line break at the end")
    lines.pop()
    fields = _read(lines, set(tools))
    try:
        again = _render(fields)[0]
    except ValueError:
        odd = [i for i, line in enumerate(lines) if BREAKS.search(line)]
        raise NotTheForm((odd or [0])[0] + 1, "a value the form cannot hold")
    if again != lines:
        diff = [i for i, (a, b) in enumerate(zip(again, lines)) if a != b] + [min(len(again), len(lines))]
        raise NotTheForm(diff[0] + 1, "the fields do not write again to the same bytes")
    return fields


def subject(tool, ran, exit, rows, launchers):
    """What the fingerprint hashes, holding no free word. A command opened by `agentik <tool>` or
    by the tool's own launcher (`launchers`, a map of tool to its launcher's name) gives
    `ran:<tool>:<verb>:<exit>`; any other command `ran:other:<exit>`; no command, the tool's first
    failing row, else its first row, `check:<tool>:<name>:<eight words of its detail>`."""
    code = "" if exit is None else str(exit)
    words = (ran or "").split()
    if words:
        first = words[0].rsplit("/", 1)[-1]
        own = (launchers or {}).get(tool)
        if first == "agentik" and words[1:2] == [tool]:
            rest = words[2:]
        elif own and first == own:
            rest = words[1:]
        else:
            return "ran:other:%s" % code
        verb = rest[0] if rest and re.fullmatch("[a-z]{1,20}", rest[0]) else ""
        return "ran:%s:%s:%s" % (tool, verb, code)
    mine = [row for row in rows or [] if row[0] == tool]
    mine = [row for row in mine if row[1] == "fail"] or mine
    if not mine:
        return "check:%s::" % tool
    name = re.sub(r"\d", "", mine[0][2])
    detail = [w.lower() for w in re.findall(r"[^\W\d_]+", mine[0][3])][:8]
    return "check:%s:%s:%s" % (tool, name, " ".join(detail))


def fingerprint(tool, subject):
    """The first 12 hex of the SHA-256 of `agentik-issue/1 <tool> <subject>`."""
    return hashlib.sha256(("%s %s %s" % (SCHEMA, tool, subject)).encode("utf-8")).hexdigest()[:12]


def _one_line(text):
    return re.sub(r" ?(?:%s)+ ?" % BREAKS.pattern, " ", text)


def title(verb, line):
    """`<verb>: <line>`, or the line alone when it opens with the verb or no verb is given."""
    line = _one_line(line or "").strip()
    if not verb or re.match(re.escape(verb) + r"(?![\w-])", line):
        return line or (verb or "")
    return "%s: %s" % (verb, line) if line else verb


def _cut(tool, text):
    line = ("%s %s" % (tool, _one_line(text).strip())).encode("utf-8")
    if len(line) > TITLE_BYTES:
        line = line[:TITLE_BYTES]
    cut = line.decode("utf-8", "ignore")[len(tool) + 1:].strip()
    return cut or EMPTY


def draft(facts, tool, title, happened, fingerprint):
    """The fields of an `agentik.issue-facts/1` object already scrubbed and bounded, its line
    breaks folded to spaces; a title whose line passes 72 bytes is cut on a character's edge."""
    out = facts.get("output") or {}
    words = facts.get("words") or {}
    checks = facts.get("checks") or {}
    named = facts.get("plugins")
    system = facts.get("system")
    ran = out.get("ran")
    versions, version = [], "unreadable"
    for v in facts.get("versions") or []:
        shown = v.get("plugin") or v.get("launcher")
        if not shown:
            continue
        item = "%s %s" % (v["name"], shown)
        if v.get("plugin") and v.get("commit"):
            item += " (%s)" % v["commit"]
        if v.get("plugin") and v.get("launcher") and v["launcher"] != v["plugin"]:
            item += " launcher %s" % v["launcher"]
        versions.append(item)
        if v["name"] == tool:
            version = shown
    f = {"tool": tool, "title": _cut(tool, title), "ran": None if ran is None else _one_line(ran),
         "exit": out.get("exit") if ran is not None else None, "happened": _one_line(happened or ""),
         "expected": None if words.get("expected") is None else _one_line(words["expected"]),
         "versions": versions, "system": None, "counts": None, "rows": None, "plugins": None,
         "others": None, "lines": [_one_line(x) for x in out.get("lines") or []] or None,
         "version": version, "fingerprint": fingerprint}
    if system:
        f["system"] = ["Claude Code %s" % system["claude"],
                       "%s %s %s" % (system["os"], system["release"] or "unreadable", system["arch"]),
                       "Python %s" % system["python"], system["where"]]
    if checks.get("read"):
        f["rows"] = [[r["tool"], r["status"], _one_line(r["name"]), _one_line(r["detail"])]
                     for r in checks.get("rows") or []]
        f["counts"] = [checks["failed"], checks["warned"], checks["passed"]]
    if named is not None:
        f["plugins"] = ["%s %s" % (p["name"], p["version"]) for p in named.get("named") or []]
        f["others"] = named.get("others") or 0
    return f


def fit(fields, ceiling=CEILING):
    """(fields, went): over the ceiling the plugins go first, then the `warn` rows, then the
    oldest lines, one at a time; `went` names each with its count, in that order, and ends with
    `("over", <bytes>)` when the form is still over the ceiling after the three, to be cut by hand."""
    f, went = _copy(fields), []

    def over():
        return len(build(f)) > ceiling

    if over() and f["plugins"] is not None:
        went.append(("plugins", len(f["plugins"])))
        f["plugins"] = f["others"] = None
    if over() and f["rows"]:
        kept = [row for row in f["rows"] if row[1] != "warn"]
        if len(kept) < len(f["rows"]):
            went.append(("warn", len(f["rows"]) - len(kept)))
            f["rows"] = kept
    if over() and f["lines"]:
        n = 0
        while f["lines"] and over():
            f["lines"] = f["lines"][1:] or None
            n += 1
        went.append(("lines", n))
    if over():
        went.append(("over", len(build(f))))
    return f, went


_EDGES = "\"'`()[]{},;:!?*|\\“”‘’"


def _words(text):
    out = []
    for raw in text.split():
        word = raw.strip(_EDGES).rstrip(".").strip(_EDGES)
        if word:
            out.append(word)
    return out


def _marked(word):
    """A word that could carry a name: a digit, `/ . @ _ ~`, an inner capital or hyphen, or a
    letter outside ASCII."""
    return (any(c.isdigit() or c in "/.@_~" or (c.isalpha() and ord(c) > 127) for c in word)
            or any(c.isupper() for c in word[1:]) or "-" in word[1:-1])


def _said(render):
    return "%s\n%s" % (render.get("happened") or "", render.get("expected") or "")


def nothing_new(render, fields):
    """[(kind, text)], empty when the render may stand: a `word` marked or capitalised that the
    draft's form does not hold (a capitalised word alone is compared in any case), a
    `placeholder` of the draft's two values that the render lacks, and `happened` when the
    draft's text does not stand whole in the render's."""
    known = _words(build(fields).decode("utf-8"))
    exact, lower = set(known), {w.lower() for w in known}
    said, misses = _said(render), []
    for word in _words(said):
        if _marked(word):
            miss = word not in exact
        else:
            miss = word[0].isupper() and word.lower() not in lower
        if miss and ("word", word) not in misses:
            misses.append(("word", word))
    for p in PLACEHOLDER.findall(_said(fields)):
        if p not in said and ("placeholder", p) not in misses:
            misses.append(("placeholder", p))
    if fields["happened"] not in (render.get("happened") or ""):
        misses.append(("happened", fields["happened"]))
    return misses


def added(render, fields):
    """Every other word of the render that the draft does not hold, once, in the render's order."""
    lower = {w.lower() for w in _words(build(fields).decode("utf-8"))}
    out = []
    for word in _words(_said(render)):
        if not _marked(word) and not word[0].isupper() and word.lower() not in lower and word not in out:
            out.append(word)
    return out
