"""pick: the one reader (row sc12-picker, design/23 section 4a). Every key or line a person
types is read here, and nowhere else in the package.

`ask(t, questions, command)` puts one or more questions and returns `{id: answer}`; `confirm(t,
question, yes, no, typed, **values)` is a writer's yes or no, resting on no. On a full terminal
one frame is drawn on stderr, in place, under what the verb printed, through `term.put`; keys are
read from stdin; stdout is never touched. `layout(state, columns, rows)` is a pure function of the
state and the size, so every screen is checked with no terminal. Off a full terminal `ask` gives
the plain prompt and `confirm` its typed question; with no terminal at all, or `CI` set, both
raise `NoTerminal` having written and read nothing.

The standard library alone: `termios` is imported inside the functions that use it, so a Python
without it still imports this module and gets the plain prompt.
"""
import os
import select
import shlex
import signal
import sys
import time
import unicodedata

from . import term

UTF = {"pointer": "❯", "up": "↑", "down": "↓", "cut": "…", "ok": "✓", "left": "‹",
       "right": "›", "updown": "↑↓"}
ASC = {"pointer": ">", "up": "^", "down": "v", "cut": "...", "ok": "ok", "left": "<",
       "right": ">", "updown": "up/down"}
MIN_COLS, MIN_ROWS, WINDOW, TRIES, TAB_MAX = 40, 13, 10, 3, 12
ESC_WAIT, PASTE_WAIT, CLOSE_WAIT = 0.05, 1.0, 0.25
BOLD, DIM, FOCUS, ACTIVE, WARN = "1", "2", "1;36", "7", "33"
MARK = term.GLYPH["warn"]
EINTR, EIO = 4, 5  # the POSIX numbers, the same on macOS and Linux
HELD = ("SIGINT", "SIGTERM", "SIGHUP", "SIGQUIT")
CSI_KEYS = {(b"", b"A"): "up", (b"", b"B"): "down", (b"", b"C"): "right", (b"", b"D"): "left",
            (b"", b"Z"): "backtab", (b"", b"H"): "home", (b"", b"F"): "end",
            (b"1", b"~"): "home", (b"7", b"~"): "home", (b"4", b"~"): "end", (b"8", b"~"): "end",
            (b"5", b"~"): "pageup", (b"6", b"~"): "pagedown",
            (b"200", b"~"): "paste_on", (b"201", b"~"): "paste_off"}
SS3_KEYS = {b"A": "up", b"B": "down", b"C": "right", b"D": "left", b"H": "home", b"F": "end"}
CTRL = {0x0d: "enter", 0x0a: "enter", 0x09: "tab", 0x7f: "back", 0x08: "back", 0x04: "eof",
        0x15: "clear", 0x0e: "down", 0x10: "up", 0x0c: "redraw"}


class Other(str):
    """An answer the person typed on the question's `other` row."""


class Cancelled(Exception):
    """Esc, Ctrl-D, the end of input, three wrong lines at the plain prompt, or a terminal gone."""


class NoTerminal(Exception):
    """stdin or stderr is no terminal, or CI is set: nothing was asked, no byte written or read."""


class _Signal(Exception):
    """A held signal arrived: the loop ends, the terminal is restored, the signal is sent again."""


wid = term.columns


def cut(text, room, ell):
    """The text in `room` columns, cut at its end with `ell`."""
    if wid(text) <= room:
        return text
    out, used, room = "", 0, max(room - wid(ell), 0)
    for c in text:
        if used + wid(c) > room:
            break
        out, used = out + c, used + wid(c)
    return out.rstrip() + ell


def middle(text, room, ell):
    """A label in `room` columns, cut in its middle, since two keys differ at their ends."""
    if wid(text) <= room:
        return text
    room = max(room - wid(ell), 2)
    head, tail_ = "", ""
    chars = list(text)
    while chars and wid(head) + wid(tail_) < room:
        if wid(head) <= wid(tail_):
            nxt = chars.pop(0)
            if wid(head) + wid(nxt) + wid(tail_) > room:
                break
            head += nxt
        else:
            nxt = chars.pop()
            if wid(head) + wid(nxt) + wid(tail_) > room:
                break
            tail_ = nxt + tail_
    return head + ell + tail_


def tail(text, room, ell):
    """The end of a text being typed, when the whole does not fit."""
    if wid(text) <= room:
        return text
    out, used, room = "", 0, max(room - wid(ell), 0)
    for c in reversed(text):
        if used + wid(c) > room:
            break
        out, used = c + out, used + wid(c)
    return ell + out


def wrap(text, room, lines, ell):
    out, now = [], ""
    for word in text.split():
        if now and wid(now) + 1 + wid(word) > room:
            out.append(now)
            now = word
        else:
            now = (now + " " + word) if now else word
    out.append(now)
    if len(out) > lines:
        out = out[:lines - 1] + [cut(" ".join(out[lines - 1:]), room, ell)]
    return [cut(line, room, ell) for line in out]


def pad(text, room):
    return text + " " * max(room - wid(text), 0)


def utf8_locale(env):
    """The marks are UTF-8 only where the first set of LC_ALL, LC_CTYPE and LANG names UTF-8."""
    for name in ("LC_ALL", "LC_CTYPE", "LANG"):
        if env.get(name):
            return "utf8" in env[name].lower().replace("-", "")
    return False


def _marks(t):
    if not utf8_locale(t.err.env):
        return False
    try:
        "".join(UTF.values()).encode(t.err.encoding)
    except (LookupError, UnicodeEncodeError):
        return False
    return True


# ---- the state ----------------------------------------------------------------------------

class Q:
    def __init__(self, t, spec):
        self.id = spec["id"]
        self.tab = term.clean(spec.get("tab", spec["id"]))
        if wid(self.tab) > TAB_MAX:
            raise ValueError("pick: a tab's word is at most %d columns: %s" % (TAB_MAX, self.tab))
        if spec["kind"] not in ("one", "many"):
            raise ValueError("pick: kind is one or many: %s" % spec["kind"])
        self.prompt = t.text(spec["prompt"], **spec.get("values", {}))
        self.many = spec["kind"] == "many"
        self.options = [{"value": o["value"], "label": term.clean(o["label"]),
                         "note": term.clean(o.get("note", ""))} for o in spec["options"]]
        other = spec.get("other")
        self.other = None if not other else {
            "label": term.clean(other["label"]), "note": term.clean(other.get("note", "")),
            "check": other.get("check") or (lambda text: "")}
        self.filters = bool(spec.get("filter"))
        self.noun = term.clean(spec.get("noun", ""))
        self.least = int(spec.get("least", 0)) if self.many else 1
        default = spec.get("default")
        values = [o["value"] for o in self.options]
        if self.many:
            self.chosen = [v for v in values if v in (default or [])]
        else:
            self.chosen = [default] if default in values else []
        self.text, self.typed, self.filter, self.top = "", False, "", 0
        self.focus = values.index(self.chosen[0]) if self.chosen else 0

    def rows(self):
        words = self.filter.lower().split()
        rows = [i for i, o in enumerate(self.options)
                if all(w in (o["label"] + " " + o["note"]).lower() for w in words)]
        return rows + (["other"] if self.other else [])

    def total(self):
        return len(self.options) + (1 if self.other else 0)

    def row(self):
        rows = self.rows()
        self.focus = max(0, min(self.focus, len(rows) - 1))
        return rows[self.focus] if rows else None

    def answer(self):
        if self.many:
            return [v for v in (o["value"] for o in self.options) if v in self.chosen] + \
                ([Other(self.text)] if self.text else [])
        if self.other_on():
            return Other(self.text)
        return self.chosen[0] if self.chosen else None

    def other_on(self):
        return bool(self.text) and (self.many or self.typed)

    def answered(self):
        got = self.answer()
        return len(got) >= self.least if self.many else got is not None

    def refused(self):
        """The cause when the `other` text in use fails its check, else ''."""
        if self.other and self.other_on():
            return term.clean(self.other["check"](self.text) or "")
        return ""

    def shown(self, t):
        got = self.answer()
        if self.many:
            return ", ".join(got) if got else t.text("pick.unanswered")
        return "" if got is None else str(got)


class State:
    """One or more questions, the tab in front, and the refusal shown in the keys line."""

    def __init__(self, t, questions, utf8=True):
        self.t, self.g = t, UTF if utf8 else ASC
        self.qs = [Q(t, s) for s in questions]
        if not self.qs:
            raise ValueError("pick: no question")
        self.form = len(self.qs) > 1
        self.tab, self.error = 0, ""

    def q(self):
        return self.qs[self.tab] if self.tab < len(self.qs) else None

    def answers(self):
        return {q.id: q.answer() for q in self.qs}


class Confirm:
    """The yes or no: two rows, the no row second and under the focus as it opens."""

    def __init__(self, t, question, yes, no, utf8=True):
        self.t, self.g = t, UTF if utf8 else ASC
        self.question, self.rows, self.focus = question, [yes, no], 1


# ---- the screen, a pure function of the state and the size ---------------------------------

def _keys(st, room):
    t, q, g = st.t, st.q(), st.g
    if q is None:
        items = [t.text("pick.key.review"), t.text("pick.key.cancel")]
    else:
        items = [t.text("pick.key.move", arrows=g["updown"])]
        if q.row() != "other":
            if q.many:
                items.append(t.text("pick.key.tick"))
            if q.filters:
                items.append(t.text("pick.key.filter"))
        if st.form:
            items.append(t.text("pick.key.next"))
        else:
            items.append(t.text("pick.key.done" if q.many else "pick.key.choose"))
        items.append(t.text("pick.key.cancel"))
    return _flow(items, room)


def _flow(items, room):
    lines, now = [], ""
    for item in items:
        if now and wid(now) + 2 + wid(item) > room:
            lines.append(now)
            now = item
        else:
            now = (now + "  " + item) if now else item
    return lines + [now]


def _strip(st, room):
    g = st.g
    items = [q.tab + (" " + g["ok"] if q.answered() else "") for q in st.qs]
    items.append(st.t.text("pick.submit"))
    first = last = st.tab

    def width(a, b):
        return sum(wid(x) + 2 for x in items[a:b + 1]) + (b - a) + (2 if a else 0) + \
            (2 if b < len(items) - 1 else 0)
    grew = True
    while grew:
        grew = False
        if last < len(items) - 1 and width(first, last + 1) <= room:
            last, grew = last + 1, True
        if first > 0 and width(first - 1, last) <= room:
            first, grew = first - 1, True
    segs = [(g["left"] + " ", DIM)] if first else []
    for i in range(first, last + 1):
        segs.append(("[" + items[i] + "]", ACTIVE) if i == st.tab else (" " + items[i] + " ", None))
        if i < last:
            segs.append((" ", None))
    if last < len(items) - 1:
        segs.append((" " + g["right"], DIM))
    return segs


def _shape(q, cols, rows, form):
    """The parts of one question's frame that do not move while it is on screen."""
    room = cols - 1
    mark = 4 if (q.many or form) else 0
    labels = [o["label"] for o in q.options] + ([q.other["label"]] if q.other else [])
    lw = min(max(wid(x) for x in labels), room - 2 - mark)
    note_room = room - 2 - mark - lw - 2
    notes = [o["note"] for o in q.options] + ([q.other["note"]] if q.other else [])
    if note_room < 10:
        note_room = 0
    detail = 2 if any(n and wid(n) > note_room for n in notes) or \
        any(wid(x) > lw for x in labels) else 0
    keys = 2 if cols < 72 else 1
    chrome = (1 if form else 0) + 1 + (1 if q.filters else 0) + 2 + detail + keys
    height = max(min(q.total(), WINDOW, rows - 1 - chrome), 3)
    return {"mark": mark, "lw": lw, "note_room": note_room, "detail": detail, "keys": keys,
            "height": height, "scrolls": q.total() > height}


def _body(st, q, cols, rows):
    """One question's lines under the tab strip, and the cursor: (line, column, shown)."""
    t, g = st.t, st.g
    room, s = cols - 1, _shape(q, cols, rows, st.form)
    rws, lines, cursor = q.rows(), [], None
    now = q.row()
    count = len(rws) - (1 if q.other else 0)
    told = t.text("pick.count.of", count=count, total=len(q.options), noun=q.noun) if q.filter \
        else t.text("pick.count", count=len(q.options), noun=q.noun)
    lines.append([(q.prompt, BOLD)] + ([("  " + told, DIM)] if q.filters and q.noun else []))
    if q.filters:
        head = "  " + t.text("pick.filter") + "  "
        typed = tail(q.filter, room - wid(head) - 1, g["cut"])
        lines.append([(head, DIM), (typed, None)])
        if now != "other":
            cursor = (len(lines) - 1, wid(head) + wid(typed), True)
    if q.focus < q.top:
        q.top = q.focus
    if q.focus >= q.top + s["height"]:
        q.top = q.focus - s["height"] + 1
    q.top = max(0, min(q.top, max(len(rws) - s["height"], 0)))
    if s["scrolls"]:
        lines.append([("  " + t.text("pick.more", mark=g["up"], count=q.top), DIM)]
                     if q.top else [])
    window, shown = rws[q.top:q.top + s["height"]], []
    if q.filter and not any(isinstance(r, int) for r in rws):
        shown.append([("  " + t.text("pick.none", noun=q.noun, text=q.filter), DIM)])
        window = window[:s["height"] - 1]
    for r in window:
        here = r == now
        segs = [(g["pointer"] + " ", FOCUS) if here else ("  ", None)]
        if r == "other":
            label, on = q.other["label"], q.other_on()
            note = tail(q.text, room - 2 - s["mark"] - s["lw"] - 3, g["cut"]) \
                if (q.text or here) else q.other["note"]
        else:
            o = q.options[r]
            label, note = o["label"], o["note"]
            on = o["value"] in q.chosen and (q.many or not q.other_on())
        if s["mark"]:
            box = ("[x] " if on else "[ ] ") if q.many else ("(x) " if on else "( ) ")
            segs.append((box, BOLD if on else None))
        segs.append((pad(middle(label, s["lw"], g["cut"]), s["lw"]), FOCUS if here else None))
        at = len(lines) + len(shown)
        if r == "other" and (q.text or here):
            segs.append(("  " + note, None))
            if here:
                cursor = (at, 2 + s["mark"] + s["lw"] + 2 + wid(note), True)
        elif s["note_room"] and note:
            segs.append(("  " + cut(note, s["note_room"], g["cut"]), DIM))
        if here and cursor is None:
            cursor = (at, 0, False)
        shown.append(segs)
    lines += shown + [[] for _ in range(s["height"] - len(shown))]
    if s["scrolls"]:
        below = len(rws) - q.top - s["height"]
        lines.append([("  " + t.text("pick.more", mark=g["down"], count=below), DIM)]
                     if below > 0 else [])
    if s["detail"]:
        note, label = "", ""
        if isinstance(now, int):
            note, label = q.options[now]["note"], q.options[now]["label"]
        elif now == "other":
            note, label = q.other["note"], q.other["label"]
        whole = (label + " " + note).strip() if wid(label) > s["lw"] else note
        told = wrap(whole, room - 2, 2, g["cut"]) \
            if whole and (wid(note) > s["note_room"] or wid(label) > s["lw"]) else []
        lines += [[("  " + x, DIM)] for x in told] + [[] for _ in range(2 - len(told))]
    return lines, cursor


def _review(st):
    t = st.t
    lw = max(wid(q.tab) for q in st.qs)
    lines = [[(t.text("pick.review"), BOLD)]]
    for q in st.qs:
        segs = [("  " + pad(q.tab, lw) + "  ", None)]
        segs.append((q.shown(t), None) if q.answered() else
                    (MARK + " " + t.text("pick.unanswered"), WARN))
        lines.append(segs)
    return lines


def _confirm(st, cols):
    t, g, room = st.t, st.g, cols - 1
    lines = [[(cut(st.question, room, g["cut"]), BOLD)]]
    for i, label in enumerate(st.rows):
        here = i == st.focus
        lines.append([(g["pointer"] + " ", FOCUS) if here else ("  ", None),
                      (cut(label, room - 2, g["cut"]), FOCUS if here else None)])
    keys = [t.text("pick.key.move", arrows=g["updown"]), t.text("pick.key.choose"),
            t.text("pick.key.cancel")]
    lines += [[(x, DIM)] for x in _flow(keys, cols - 1)]
    return lines, (1 + st.focus, 0, False)


def layout(state, columns, rows):
    """The frame: a list of lines, each a list of (text, sgr), and the cursor, (line, column,
    shown) or None. No line passes columns less one; the frame keeps one height while open."""
    t = state.t
    if columns < MIN_COLS or rows < MIN_ROWS:
        return [[(MARK + " " + t.text("pick.small", columns=MIN_COLS, rows=MIN_ROWS), WARN)]], None
    if isinstance(state, Confirm):
        return _confirm(state, columns)
    st, room, lines, cursor = state, columns - 1, [], None
    q = st.q()
    bodies = [_body(st, x, columns, rows) for x in st.qs]
    tall = max(len(b[0]) for b in bodies)
    if st.form:
        tall = max(tall, len(st.qs) + 1)
        lines.append(_strip(st, room))
    if q is None:
        body = _review(st)
    else:
        body, cursor = bodies[st.tab]
        if cursor and st.form:
            cursor = (cursor[0] + 1, cursor[1], cursor[2])
    lines += body + [[] for _ in range(tall - len(body))]
    nkeys = 2 if columns < 72 else 1
    keys = [[(MARK + " " + st.error, WARN)]] if st.error else [[(k, DIM)] for k in _keys(st, room)]
    lines += keys[:nkeys] + [[] for _ in range(nkeys - len(keys))]
    return lines, cursor


def _painted(t, segs, room, ell):
    out, used = "", 0
    for text, sgr in segs:
        if used >= room:
            break
        text = cut(text, room - used, ell)
        used += wid(text)
        out += t.err.paint(text, sgr) if text.strip() else text
    return out.rstrip() if not t.err.colour else out


# ---- keys -----------------------------------------------------------------------------------

def _more(buf, final):
    return (("none", None), len(buf)) if final else (None, 0)


def parse(buf, final, utf8):
    """(event, bytes used) for the first key in buf; (None, 0) while it may still grow. Each
    escape form of design/23 4a.4 is taken whole, so none of it types into a text."""
    b = buf[0]
    if b != 0x1b:
        if b < 0x20 or b == 0x7f:
            return (CTRL.get(b, "none"), None), 1
        size = 1
        if utf8 and b >= 0xc0:
            size = 2 if b < 0xe0 else 3 if b < 0xf0 else 4
            if len(buf) < size:
                return _more(buf, final)
        char = bytes(buf[:size]).decode("utf-8" if utf8 else "latin-1", "ignore")
        if not char or unicodedata.category(char[0])[0] == "C":
            return ("none", None), size
        return ("text", char), size
    run = 1
    while run < len(buf) and buf[run] == 0x1b:
        run += 1
    if run == len(buf):  # bare ESCs alone: one esc, however many
        if final:
            return ("esc", None), run
        return (None, 0) if run <= 2 else (("esc", None), run - 2)
    if run > 2:  # the run's head is bare; its last two may be an Alt prefix and a key
        return ("esc", None), run - 2
    if run == 2:  # ESC ESC: one prefix, so Alt with an arrow is one key; never a second
        event, used = _one(buf[1:], final, utf8)
        return (None, 0) if event is None else (("none", None), used + 1)
    return _one(buf, final, utf8)


def _one(buf, final, utf8):
    """parse's ESC and one key that is no ESC."""
    c = buf[1]
    if c == 0x5b:  # CSI
        if len(buf) < 3:
            return _more(buf, final)
        if buf[2] == 0x5b:  # the Linux console's function key: ESC [ [ and one byte
            return (("none", None), 4) if len(buf) >= 4 else _more(buf, final)
        if buf[2] == 0x4d:  # an X10 mouse report: ESC [ M and three bytes
            return (("none", None), 6) if len(buf) >= 6 else _more(buf, final)
        i = 2
        while i < len(buf) and 0x30 <= buf[i] <= 0x3f:
            i += 1
        params = bytes(buf[2:i])
        start = i
        while i < len(buf) and 0x20 <= buf[i] <= 0x2f:
            i += 1
        if i >= len(buf):
            return _more(buf, final)
        if 0x40 <= buf[i] <= 0x7e:
            key = CSI_KEYS.get((params, bytes(buf[i:i + 1]))) if i == start else None
            return (key or "none", None), i + 1
        return ("none", None), i
    if c == 0x4f:  # SS3 and one byte
        if len(buf) < 3:
            return _more(buf, final)
        return (SS3_KEYS.get(bytes(buf[2:3]), "none"), None), 3
    if c in (0x5d, 0x50, 0x5f, 0x5e):  # OSC, DCS, APC, PM: to ST or BEL
        i = 2
        while i < len(buf):
            if buf[i] == 0x07:
                return ("none", None), i + 1
            if buf[i] == 0x1b and i + 1 < len(buf) and buf[i + 1] == 0x5c:
                return ("none", None), i + 2
            i += 1
        return _more(buf, final)
    size = 1  # ESC and any other one key: Alt with that key
    if utf8 and c >= 0xc0:
        size = 2 if c < 0xe0 else 3 if c < 0xf0 else 4
        if len(buf) < 1 + size:
            return _more(buf, final)
    return ("none", None), 1 + size


class _Ask:
    """What each key does to the questions: (True, answers) when they are done."""

    def __init__(self, st):
        self.st = st

    def __call__(self, name, value):
        st, q = self.st, self.st.q()
        st.error = ""
        field = None if q is None else "text" if q.row() == "other" else \
            "filter" if q.filters else None
        if name == "eof":
            raise Cancelled()
        if name == "esc":
            if q is not None and q.filter:
                q.filter, q.focus, q.top = "", 0, 0
                return False, None
            raise Cancelled()
        if name in ("tab", "right", "backtab", "left") and st.form:
            if q is not None and self.refuse(q):
                return False, None
            step = 1 if name in ("tab", "right") else -1
            st.tab = (st.tab + step) % (len(st.qs) + 1)
        elif q is None:
            if name == "enter":
                missing = [i for i, x in enumerate(st.qs) if not x.answered()]
                if not missing:
                    return True, st.answers()
                st.tab = missing[0]
                st.error = st.t.text("pick.needs", tab=st.qs[missing[0]].tab)
        elif name == "text" and (field or value not in "jk "):
            if field:
                self.type(q, field, value)
        elif name in ("up", "down", "pageup", "pagedown", "home", "end") or \
                name == "text" and value in "jk":
            rows = len(q.rows())
            step = {"up": -1, "down": 1, "pageup": -WINDOW, "pagedown": WINDOW, "home": -rows,
                    "end": rows, "text": 1 if value == "j" else -1}[name]
            q.focus = max(0, min(q.focus + step, rows - 1))
        elif name == "text" and value == " " or name == "enter":
            return self.choose(q, name == "enter")
        elif name == "back" and field:
            setattr(q, field, getattr(q, field)[:-1])
            if field == "filter":
                q.focus, q.top = 0, 0
        elif name == "clear" and field:
            setattr(q, field, "")
        return False, None

    def paste(self, text):
        q = self.st.q()
        if q is None:
            return
        field = "text" if q.row() == "other" else "filter" if q.filters else None
        if field:
            for c in text:
                if c != " " or field == "text" or not q.many:
                    self.type(q, field, c)

    def refuse(self, q):
        """Every `other` text passes its check before its question is left or closed."""
        wrong = q.refused()
        if wrong:
            q.filter, q.top = "", 0
            q.focus = len(q.rows()) - 1
            self.st.error = wrong
        return bool(wrong)

    def type(self, q, field, value):
        value = term.clean(value)  # what `same as:` and the plain prompt keep of it, alone
        if not value:
            return False, None
        if field == "filter" and value == " " and q.many:
            return self.choose(q, False)
        setattr(q, field, getattr(q, field) + value)
        if field == "filter":
            q.focus, q.top = 0, 0
        elif not q.many:
            q.typed = True
        return False, None

    def choose(self, q, enter):
        st, row = self.st, q.row()
        if row == "other":
            if enter and not q.text and not q.many:
                st.error = st.t.text("pick.needs", tab=q.tab)
                return False, None
            if not q.many:
                q.typed = bool(q.text)
        elif row is not None:
            value = q.options[row]["value"]
            if q.many and not enter:
                q.chosen = [o["value"] for o in q.options
                            if (o["value"] in q.chosen) != (o["value"] == value)]
            elif not q.many:
                q.chosen, q.typed = [value], False
        elif enter and not q.many:
            st.error = st.t.text("pick.none", noun=q.noun, text=q.filter)
            return False, None
        if not enter:
            return False, None
        if self.refuse(q):
            return False, None
        if st.form:
            st.tab += 1
            return False, None
        if not q.answered():
            st.error = st.t.text("pick.least") if q.many else st.t.text("pick.needs", tab=q.tab)
            return False, None
        return True, st.answers()


class _Yes:
    """What each key does to the yes or no: (True, answer) when it is taken."""

    def __init__(self, st):
        self.st = st

    def __call__(self, name, value):
        st = self.st
        if name in ("esc", "eof"):
            st.focus = 1
            return True, False
        if name == "enter":
            return True, st.focus == 0
        if name in ("up", "home", "pageup") or name == "text" and value in ("k", "y"):
            st.focus = 0
        elif name in ("down", "end", "pagedown") or name == "text" and value in ("j", "n"):
            st.focus = 1
        return False, None

    def paste(self, text):
        pass


# ---- the terminal ---------------------------------------------------------------------------

class _Screen:
    """The terminal's modes, the signals held, and the key loop; every path out passes leave()."""

    def __init__(self, t, state, keys, closing):
        import termios
        self.tm, self.t, self.st, self.keys, self.closing = termios, t, state, keys, closing
        self.fd, self.out_fd = sys.stdin.fileno(), t.err.raw.fileno()
        self.utf8 = utf8_locale(t.err.env)
        self.saved = self.raw = None
        self.up, self.left, self.dirty, self.clear, self.prefix = 0, b"", True, False, ""
        self.caught, self.leaving, self.ours, self.cont, self.resized = None, False, False, False, False
        self.small = False  # the last frame drawn was the size line: no key but Esc acts
        self.paste, self.paste_at, self.handlers, self.wake, self.old_wake = None, 0.0, {}, None, -1
        self.held = [getattr(signal, n) for n in HELD if hasattr(signal, n)]

    # -- the signals --
    def hold(self):
        r, w = os.pipe()
        os.set_blocking(r, False)
        os.set_blocking(w, False)
        self.wake = (r, w)
        self.old_wake = signal.set_wakeup_fd(w, warn_on_full_buffer=False)
        for sig in self.held:
            self.handlers[sig] = signal.signal(sig, self._held)
        for sig, fn in ((signal.SIGTSTP, self._stop), (signal.SIGCONT, self._cont),
                        (signal.SIGWINCH, self._winch)):
            self.handlers[sig] = signal.signal(sig, fn)

    def release(self):
        for sig, fn in self.handlers.items():
            signal.signal(sig, fn if fn is not None else signal.SIG_DFL)
        self.handlers = {}
        if self.wake:
            signal.set_wakeup_fd(self.old_wake)
            for fd in self.wake:
                os.close(fd)
            self.wake = None

    def _held(self, signum, frame):
        if self.caught is None:
            self.caught = signum
            if not self.leaving:
                raise _Signal()

    def _stop(self, signum, frame):
        if self.leaving or self.saved is None:
            return
        self._restore()
        self._close("")
        self.ours = True
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGTSTP)  # stopped here until SIGCONT
        signal.signal(signal.SIGTSTP, self._stop)
        self.cont = True

    def _cont(self, signum, frame):
        self.cont = True

    def _winch(self, signum, frame):
        self.resized = True

    # -- the modes --
    def _set(self, attrs):
        """tcsetattr with TCSANOW, tried again when interrupted, and, refused in the background,
        once the job is in the foreground again."""
        while True:
            try:
                self.tm.tcsetattr(self.fd, self.tm.TCSANOW, attrs)
                return
            except self.tm.error as e:
                code = e.args[0] if e.args else None
                if code == EINTR:
                    continue
                if code == EIO and os.tcgetpgrp(self.fd) != os.getpgrp():
                    time.sleep(0.05)
                    continue
                raise

    def enter(self):
        tm = self.tm
        self.saved = tm.tcgetattr(self.fd)
        raw = tm.tcgetattr(self.fd)
        raw[0] &= ~tm.IXON
        raw[3] &= ~(tm.ICANON | tm.ECHO)  # keys one at a time, unechoed; ISIG stays on
        raw[6][tm.VMIN], raw[6][tm.VTIME] = 1, 0
        self.raw = raw
        tm.tcflush(self.fd, tm.TCIFLUSH)  # a key typed ahead answers nothing
        self._take()

    def _take(self):
        self._set(self.raw)
        self.tm.tcflow(self.fd, self.tm.TCOON)  # output a Ctrl-S stopped goes on
        self.prefix += "\x1b[?2004h"  # a paste arrives bracketed

    def _restore(self):
        """The modes as they were, with signals blocked only while they are set."""
        mask = signal.pthread_sigmask(signal.SIG_BLOCK, self.held)
        try:
            self._set(self.saved)
            self.tm.tcflush(self.fd, self.tm.TCIFLUSH)
        except (self.tm.error, OSError):
            pass
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, mask)

    def _close(self, line):
        """The frame in flight, then the frame erased, paste mode off, the cursor shown, and the
        closing line: offered for at most CLOSE_WAIT; what the screen has not taken by then is
        dropped, with the output queued, so a screen stopped or unread holds nothing up."""
        tail_ = ("\x1b[%dA" % self.up if self.up else "") + "\r\x1b[J\x1b[?2004l\x1b[?25h"
        data = self.left + self.t.err.encode(tail_ + (line + "\n" if line else ""))
        end = time.monotonic() + CLOSE_WAIT
        while data and not self.t.err.gone:
            data = self.t.put(data, wait=False)
            rest = end - time.monotonic()
            if not data or rest <= 0:
                break
            try:
                select.select([], [self.out_fd], [], rest)
            except (InterruptedError, OSError, ValueError):
                break
        if data:  # what the picker queued goes too, so no exit waits on a screen nobody reads
            try:
                self.tm.tcflush(self.fd, self.tm.TCOFLUSH)
            except (self.tm.error, OSError):
                pass
        self.up, self.left, self.dirty = 0, b"", True

    def leave(self, line):
        if self.saved is None:
            return
        self.leaving = True
        self._restore()
        self.saved = None
        self._close(line)

    # -- drawing --
    def _frame(self):
        try:
            size = os.get_terminal_size(self.out_fd)
            cols, rows = size.columns, size.lines
        except OSError:
            cols, rows = 80, 24
        lines, cursor = layout(self.st, cols, rows)
        self.small = cols < MIN_COLS or rows < MIN_ROWS
        g = self.st.g
        out = [self.prefix, "\x1b[?25l"]
        self.prefix = ""
        if self.clear:
            out.append("\x1b[2J\x1b[H")
            self.up, self.clear = 0, False
        out += ["\x1b[%dA" % self.up if self.up else "", "\r"]
        for segs in lines:
            out.append("\x1b[2K" + _painted(self.t, segs, cols - 1, g["cut"]) + "\n")
        out.append("\x1b[J")
        self.up = len(lines)
        if cursor:
            back = len(lines) - cursor[0]
            out.append("\x1b[%dA\x1b[%dG" % (back, cursor[1] + 1))
            out.append("\x1b[?25h" if cursor[2] else "")
            self.up = cursor[0]
        return "".join(out)

    def _pump(self):
        """Bytes go only as the screen takes them; a frame that cannot go waits, and a newer one
        takes its place."""
        if self.left:
            self.left = self.t.put(self.left, wait=False)
        if not self.left and self.dirty:
            self.dirty = False
            self.left = self.t.put(self._frame(), wait=False)
        if self.t.err.gone:
            raise Cancelled()

    # -- the loop --
    def _flags(self):
        if self.cont:
            self.cont = False
            self._take()
            if not self.ours:
                self.clear = True  # a SIGSTOP or a shell's reset passed no handler of ours
            self.ours, self.dirty = False, True
        if self.resized:
            self.resized, self.clear, self.dirty = False, True, True

    def _event(self, event):
        name, value = event
        if self.paste is not None:
            if name == "paste_off":
                text, self.paste = "".join(self.paste), None
                if not self.small:
                    self.keys.paste(text)
                self.dirty = True
            elif name == "text":
                self.paste.append(value)
            return False, None
        if name == "paste_on":
            self.paste, self.paste_at = [], time.monotonic()
            return False, None
        if name == "redraw":
            self.clear, self.dirty = True, True
            return False, None
        if name in ("none", "paste_off"):
            return False, None
        if self.small and name not in ("esc", "eof"):
            return False, None  # the question is off the screen: nothing is answered unseen
        self.dirty = True
        return self.keys(name, value)

    def loop(self):
        buf = b""
        while True:
            self._flags()
            self._pump()
            timeout = None
            if buf:
                timeout = ESC_WAIT
            if self.paste is not None:
                rest = max(self.paste_at + PASTE_WAIT - time.monotonic(), 0)
                timeout = rest if timeout is None else min(timeout, rest)
            try:
                ready, writable, _ = select.select([self.fd, self.wake[0]],
                                                   [self.out_fd] if self.left else [], [], timeout)
            except InterruptedError:
                continue
            if self.wake[0] in ready:
                try:
                    os.read(self.wake[0], 512)
                except BlockingIOError:
                    pass
            if self.paste is not None and time.monotonic() >= self.paste_at + PASTE_WAIT:
                self.paste = None  # a paste with no end mark closes, with no key from it
            final = not ready and not writable
            if self.fd in ready:
                data = os.read(self.fd, 1024)
                if not data:
                    done, got = self._event(("eof", None))
                    if done:
                        return got
                    raise Cancelled()
                buf += data
            if buf and self.resized:  # a key read with a resize: the frame it acts on first
                self._flags()
                self._pump()
            while buf:
                event, used = parse(buf, final, self.utf8)
                if event is None:
                    break
                buf = buf[used:]
                done, got = self._event(event)
                if done:
                    return got

    def run(self):
        self.hold()
        how, got = "cancel", None
        try:
            self.enter()
            got = self.loop()
            how = "answer"
        except _Signal:
            how = "signal"
        except OSError:
            raise Cancelled()  # the terminal is gone
        finally:
            line = ""
            try:
                line = self.closing(how, got)
            finally:
                self.leave(line)
                self.release()
        sig = self.caught
        if sig is not None:
            os.kill(os.getpid(), sig)  # the handler that was there, or the default
            time.sleep(0.05)
            raise KeyboardInterrupt() if sig == signal.SIGINT else Cancelled()
        return got


# ---- off a full terminal --------------------------------------------------------------------

def _where(t):
    """full: the picker. plain: the plain prompt. none: ask nothing (design/23 4a.6)."""
    env = t.err.env
    try:
        tty = sys.stdin.isatty()
    except (AttributeError, ValueError, OSError):
        tty = False
    if not (tty and t.err.tty) or env.get("CI"):
        return "none"
    if env.get("AGENTIK_PLAIN") or env.get("TERM", "dumb") in ("", "dumb"):
        return "plain"
    try:
        import termios
        termios.tcgetattr(sys.stdin.fileno())
        size = os.get_terminal_size(t.err.raw.fileno())
    except Exception:
        return "plain"
    return "full" if size.columns >= MIN_COLS and size.lines >= MIN_ROWS else "plain"


def _drop_ahead():
    try:
        import termios
        termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except Exception:
        pass


def _say(t, text=""):
    t.put(text + "\n")


def _read(t):
    t.flush()
    try:
        line = sys.stdin.readline()
    except (OSError, ValueError):
        line = ""
    if not line:
        _say(t)
        raise Cancelled()
    return line


def _numbers(line, count, many, kept):
    words = line.replace(",", " ").split()
    if not words:
        return "keep" if kept or many else None
    if many and words == ["none"]:
        return []
    picked = []
    for word in words:
        lo, _, hi = word.partition("-")
        if not lo.isdigit() or (hi and not hi.isdigit()):
            return None
        if not 1 <= int(lo) <= count or not 1 <= int(hi or lo) <= count:
            return None  # both ends in the list before a range is built
        picked += range(int(lo) - 1, int(hi or lo))
    if any(i < 0 or i >= count for i in picked) or (not many and len(picked) != 1):
        return None
    return sorted(set(picked))


def _names(line, labels):
    """A `many` line's names, each label whole: split on commas where the line holds one; with
    none, the whole line as one label first, then split on blanks."""
    if "," in line:
        return [w.strip() for w in line.split(",") if w.strip()]
    whole = " ".join(line.split())
    return [whole] if whole in labels else line.split()


def _plain_one(t, q, room, height):
    rows = q.options + ([q.other] if q.other else [])
    named = len(rows) + 3 > height  # a list longer than its window reads a name
    _say(t, q.prompt)
    lw, nw = max(wid(r["label"]) for r in rows), len(str(len(rows)))
    for n, r in enumerate(rows, 1):
        box = ("[x] " if "value" in r and r["value"] in q.chosen else "[ ] ") if q.many else ""
        line = "  %s%s" % (box, pad(r["label"], lw)) if named else \
            "  %s  %s%s" % (str(n).rjust(nw), box, pad(r["label"], lw))
        left = room - wid(line) - 2
        _say(t, (line + "  " + cut(r["note"], left, "...")) if r["note"] and left >= 10
             else line.rstrip())
    kept = [o["label"] if named else str(i) for i, o in enumerate(q.options, 1)
            if o["value"] in q.chosen]
    what = t.text(("pick.plain.names" if q.many else "pick.plain.name") if named else
                  ("pick.plain.numbers" if q.many else "pick.plain.number"))
    prompt = t.text("pick.plain.ask", what=what, kept=" ".join(kept)) if kept else \
        t.text("pick.plain.bare", what=what)
    labels = [o["label"] for o in q.options]
    for _ in range(TRIES):
        t.put(prompt + " ")
        line = _read(t)
        text = None
        if named:
            words = _names(line, labels) if q.many else ([line.strip()] if line.strip() else [])
            if not words:
                picked = "keep" if kept or q.many else None
            elif q.many and words == ["none"]:
                picked = []
            else:
                picked = []
                for w in words:
                    if w in labels:
                        picked.append(labels.index(w))
                    elif q.other and text is None:
                        text = w
                    else:
                        picked = "unknown:" + w
                        break
            if isinstance(picked, str) and picked.startswith("unknown:"):
                _say(t, MARK + " " + t.text("pick.plain.unknown", text=picked[8:]))
                continue
        else:
            picked = _numbers(line, len(rows), q.many, bool(kept))
            if picked is None:
                _say(t, MARK + " " + t.text("pick.plain.wrong", count=len(rows)))
                continue
            if picked != "keep" and q.other and len(rows) - 1 in picked:
                t.put(t.text("pick.plain.bare", what=q.other["label"]) + " ")
                text = _read(t).strip()
        if picked is None:
            _say(t, MARK + " " + t.text("pick.needs", tab=q.tab))
            continue
        if picked != "keep":
            chosen = [q.options[i]["value"] for i in picked if i < len(q.options)]
            text = term.clean(text or "")
            if text or (not named and q.other and len(rows) - 1 in picked):
                wrong = term.clean(q.other["check"](text) or "") if text else \
                    t.text("pick.needs", tab=q.tab)
                if wrong:
                    _say(t, MARK + " " + wrong)
                    continue
            was = (q.chosen, q.text, q.typed)
            q.chosen, q.text, q.typed = chosen, text, bool(text)
            if not q.answered():
                q.chosen, q.text, q.typed = was  # a refused line keeps what Enter keeps
                _say(t, MARK + " " + (t.text("pick.least") if q.many else
                                      t.text("pick.needs", tab=q.tab)))
                continue
        if q.answered():
            return
        _say(t, MARK + " " + (t.text("pick.least") if q.many else t.text("pick.needs", tab=q.tab)))
    raise Cancelled()


def _plain(t, st):
    try:
        size = os.get_terminal_size(t.err.raw.fileno())
        cols, height = size.columns or 80, size.lines or 24  # a size never set reads 0 by 0
    except (AttributeError, ValueError, OSError):
        cols, height = 80, 24
    for q in st.qs:
        _plain_one(t, q, cols - 1, height)
    return st.answers()


# ---- the two doors --------------------------------------------------------------------------

def ask(t, questions, command):
    """{id: answer} for the questions, through the writer `t`. `command(answers)` is the argv
    that gives the same result with no terminal; its `same as:` line is the one record the
    picker leaves on stderr. Raises Cancelled, NoTerminal, or KeyboardInterrupt on Ctrl-C."""
    if not callable(command):
        raise TypeError("pick.ask: command is a function from the answers to an argv")
    how = _where(t)
    if how == "none":
        raise NoTerminal()
    st = State(t, questions, _marks(t) if how == "full" else False)
    t.flush()
    if how == "full":
        _drop_ahead()
        answers = _Screen(t, st, _Ask(st), lambda how_, got: "").run()
    else:
        _drop_ahead()
        answers = _plain(t, st)
    t.line("pick.same", err=True, command=shlex.join([str(a) for a in command(answers)]))
    t.flush()
    return answers


def confirm(t, question, yes, no, typed, **values):
    """A writer's yes or no, resting on no: True only when the yes row is taken. Each of the
    four is a message id filled with `values`; `typed` is the question asked where the selector
    cannot be drawn, read as one line where `y` or `yes` is yes. It takes no default."""
    how = _where(t)
    if how == "none":
        raise NoTerminal()
    t.flush()
    _drop_ahead()
    if how == "plain":
        t.line(typed, err=True, **values)
        t.flush()
        try:
            answer = sys.stdin.readline()  # the end of input reads "", a no
        except (OSError, ValueError):
            answer = ""
        return (answer or "").strip().lower() in ("y", "yes")
    st = Confirm(t, t.text(question, **values), t.text(yes, **values), t.text(no, **values),
                 _marks(t))

    def closing(how_, got):
        if how_ == "answer":
            return "%s  %s" % (st.question, st.rows[0 if got else 1])
        if how_ == "signal":
            return "%s  %s" % (st.question, t.text("pick.interrupted"))
        return ""
    return bool(_Screen(t, st, _Yes(st), closing).run())
