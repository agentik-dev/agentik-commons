"""term: the one writer. Every byte a person reads leaves through here, by message id.

Each stream is judged alone, by isatty: on a terminal a status is a glyph, colour may be on, and
a table's last cell too wide for the terminal moves whole to the dim line under its row, so a
path or a command is never cut; off one a status is a word (ok, warn, FAIL, note), with no escape
byte and no redraw. NO_COLOR set to a value,
TERM=dumb or --no-color turns colour off; the glyphs stay. Columns are left-aligned, two spaces
apart; a name is bold, a path or a hint dim; nothing is told by colour alone.

A stream that is closed, or whose reader has gone, takes nothing more and raises nothing, at a
write or at the interpreter's exit; a character a stream cannot encode is replaced; a value has
its control characters (C0, DEL, C1) removed, so no file or variable puts an escape byte out; a
tab or a line break in it is one space, and the line and direction controls (U+2028, U+2029,
U+202A to U+202E, U+2066 to U+2069) are removed.
"""
import json
import os
import re
import sys
import unicodedata

from . import catalogue

GLYPH = {"ok": "✓", "warn": "!", "fail": "✗", "note": "·"}
WORD = {"ok": "ok", "warn": "warn", "fail": "FAIL", "note": "note"}
MARK_SGR = {"ok": "32", "warn": "33", "fail": "31", "note": "36"}
STYLE_SGR = {"name": "1", "path": "2", "hint": "2"}
GAP = "  "
FALLBACK_WIDTH = 80
CONTROL = re.compile("[\x00-\x1f\x7f-\x9f]")
JSON_CONTROL = re.compile("[\x00-\x09\x0b-\x1f\x7f-\x9f]")  # a line break survives, escaped


LINE_CONTROL = re.compile("[\u2028\u2029\u202a-\u202e\u2066-\u2069]")  # line and direction controls
BREAK = re.compile("\r\n|[\t\n\x0b\x0c\r\x1c-\x1e\x85]")  # a tab or a line break


def clean(value):
    """The value as text, with its control characters removed: a tab or a line break becomes one
    space, so no value splits a row or glues two words, and the line and direction controls go,
    so no value reorders a row or starts another."""
    return LINE_CONTROL.sub("", CONTROL.sub("", BREAK.sub(" ", str(value))))


def columns(text):
    """The screen columns a text takes: a wide character two, a combining mark none."""
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in "WF" else 1
               for c in text)


def fit(text, room, mark):
    """The text cut so that it and its mark take at most `room` columns; a combining mark stays
    with the character it follows."""
    room -= columns(mark)
    kept, used = [], 0
    for c in text:
        used += columns(c)
        if used > room:
            break
        kept.append(c)
    return "".join(kept) + mark


def _cleaned(obj):
    """For --json: control characters removed but the line break, which json.dumps writes as
    the two characters of its escape, so a tool's block of lines keeps its shape."""
    if isinstance(obj, str):
        return JSON_CONTROL.sub("", obj)
    if isinstance(obj, dict):
        return {clean(k): _cleaned(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_cleaned(v) for v in obj]
    return obj


def name(text):
    return (text, "name")


def path(text):
    return (text, "path")


def colour_off(env, no_color):
    return bool(no_color or env.get("NO_COLOR") or env.get("TERM") == "dumb")


class _Stream:
    def __init__(self, raw, no_colour):
        self.raw = raw
        self.gone = raw is None
        try:
            self.tty = raw.isatty()
        except (AttributeError, ValueError, OSError):
            self.tty = False
        self.colour = self.tty and not no_colour
        self.encoding = getattr(raw, "encoding", None) or "ascii"
        try:  # every non-ASCII character this writer itself prints
            "".join(GLYPH.values()).encode(self.encoding)
            self.glyphs = self.tty
        except (LookupError, UnicodeEncodeError):
            self.glyphs = False

    def width(self):
        try:
            cols = os.get_terminal_size(self.raw.fileno()).columns
        except (AttributeError, ValueError, OSError):
            cols = 0
        return cols if cols > 0 else FALLBACK_WIDTH

    def paint(self, text, sgr):
        if not self.colour or not sgr or not text:
            return text
        return "\x1b[%sm%s\x1b[0m" % (sgr, text)

    def mark(self, status):
        shown = GLYPH[status] if self.glyphs else WORD[status]
        return shown, self.paint(shown, MARK_SGR[status])

    def write(self, line):
        if self.gone:
            return
        try:
            line = line.encode(self.encoding, "replace").decode(self.encoding)
        except LookupError:
            line = line.encode("ascii", "replace").decode("ascii")
        try:
            self.raw.write(line + "\n")
        except (AttributeError, ValueError, OSError):
            self.drop()

    def flush(self):
        try:
            self.gone or self.raw.flush()
        except (AttributeError, ValueError, OSError):
            self.drop()

    def drop(self):
        """Take nothing more; the stream's descriptor now points at the null device, so the
        interpreter's own flush at exit finds a place for what its buffer still holds."""
        self.gone = True
        try:
            null = os.open(os.devnull, os.O_WRONLY)
            try:
                os.dup2(null, self.raw.fileno())
            finally:
                os.close(null)
        except (AttributeError, ValueError, OSError):
            pass


def unreadable(path, err=None):  # the one line written with no catalogue to write it from
    _Stream(sys.stderr if err is None else err, True).write(
        "FAIL  cannot read %s; reinstall the plugin to mend it" % path)
    return 2


class Term:
    def __init__(self, no_color=False, quiet=False, env=None, out=None, err=None, messages=None):
        env = os.environ if env is None else env
        off = colour_off(env, no_color)
        self.out = _Stream(out if out is not None else sys.stdout, off)
        self.err = _Stream(err if err is not None else sys.stderr, off)
        self.quiet = quiet
        self.messages = messages if messages is not None else catalogue.load()

    def text(self, mid, **values):
        return catalogue.fill(self.messages[mid], {k: clean(v) for k, v in values.items()})

    def _stream(self, err):
        return self.err if err else self.out

    def line(self, mid, err=False, style=None, **values):
        stream = self._stream(err)
        stream.write(stream.paint(self.text(mid, **values), STYLE_SGR.get(style)))

    def blank(self, err=False):
        self._stream(err).write("")

    def table(self, rows, err=False, indent=2, mark_at=0):
        """rows: (status or None, [cell...], after or None); a cell is a str or (str, style).
        The status shows as a column at mark_at. `after` is a line under the row, set at the
        last column's start. Nothing is cut: on a terminal a last cell wider than the room left
        moves whole to a dim line of its own under the row, above `after`."""
        stream = self._stream(err)
        if not rows:
            return
        marked = any(r[0] for r in rows)
        grid = []
        for status, cells, after in rows:
            cells = [(clean(c[0]), c[1]) if isinstance(c, tuple) else (clean(c), None) for c in cells]
            if marked:
                shown, painted = stream.mark(status) if status else ("", "")
                cells.insert(mark_at, (shown, painted))
            grid.append((cells, clean(after) if after else after))
        ncols = max(len(cells) for cells, _ in grid)
        widths = [max((len(cells[i][0]) for cells, _ in grid if i < len(cells)), default=0)
                  for i in range(ncols)]
        for cells, after in grid:
            used, shown, under = indent, " " * indent, []
            for i, (text, style) in enumerate(cells):
                last = i == len(cells) - 1
                is_mark = marked and i == mark_at  # its style slot holds the painted mark
                if last and i and stream.tty and not is_mark and len(text) > stream.width() - used:
                    under.append(text)
                    break
                painted = style if is_mark else stream.paint(text, STYLE_SGR.get(style))
                pad = "" if last else " " * (widths[i] - len(text)) + GAP
                used += len(text) + len(pad)
                shown += painted + pad
            stream.write(shown.rstrip(" "))
            start = indent + sum(w + len(GAP) for w in widths[:len(cells) - 1])
            for line in under + ([after] if after else []):
                stream.write(" " * start + stream.paint(line, STYLE_SGR["hint"]))

    def grid(self, status, label, rows, err=False):
        """One part of a status screen (packet su2-screen R4): the mark, or its blank when the
        status is None, two spaces, the label bold and padded to 8, two spaces, then each row at
        the text's column. A row is (text or [cell...], style, whole); a row of cells pads each
        cell but the last to the widest of its column among the part's rows, two spaces apart.
        On a terminal a row past the width ends at it with an ellipsis, unless it is whole. A
        width is in screen columns (`columns`). No row ends in a space."""
        stream = self._stream(err)
        rows = rows or [("", None, False)]
        widths = {}
        for cells, _, _ in rows:
            if isinstance(cells, (list, tuple)):
                for i, cell in enumerate(cells[:-1]):
                    widths[i] = max(widths.get(i, 0), columns(clean(cell)))
        lead = 1 if stream.glyphs else 4
        label = clean(label)
        try:
            ellipsis = "…"
            ellipsis.encode(stream.encoding)
        except (LookupError, UnicodeEncodeError):
            ellipsis = "..."
        for n, (cells, style, whole) in enumerate(rows):
            if isinstance(cells, (list, tuple)):
                cells = [clean(c) for c in cells]
                line = "".join(c + " " * (widths[i] - columns(c)) + GAP for i, c in enumerate(cells[:-1]))
                line += cells[-1] if cells else ""
            else:
                line = clean(cells)
            line = line.rstrip(" ")
            plain = " " * (lead + len(GAP) + 8 + len(GAP))
            head = plain
            if n == 0:
                shown, painted = stream.mark(status) if status else ("", "")
                head = (painted + " " * (lead - len(shown)) + GAP
                        + stream.paint(label, STYLE_SGR["name"]) + " " * (8 - columns(label)) + GAP)
            room = stream.width() - len(plain)
            if stream.tty and not whole and columns(line) > room:
                line = fit(line, room, ellipsis)
            shown = head + stream.paint(line, STYLE_SGR.get(style))
            stream.write(shown if line else shown.rstrip(" "))

    def hint(self, mid, values=None, **more):
        values = dict(values or {}, **more)
        if not self.quiet:
            self.flush()  # the answer first, where both streams share one pipe
            stream = self.err
            shown, painted = stream.mark("note")
            stream.write(painted + GAP + stream.paint(self.text(mid, **values), STYLE_SGR["hint"]))

    def error(self, mid, **values):
        stream = self.err
        shown, painted = stream.mark("fail")
        stream.write(painted + GAP + self.text(mid, **values))

    def json(self, obj):
        self.out.write(json.dumps(_cleaned(obj), ensure_ascii=True, sort_keys=False))

    def flush(self):
        for stream in (self.out, self.err):
            stream.flush()


def append(path, text):
    """The one file this package appends to, setup's journal (packet ak3-setup R9)."""
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(text)
