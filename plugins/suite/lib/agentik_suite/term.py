"""term: the one writer. Every byte a person reads leaves through here, by message id.

Each stream is judged alone, by isatty: on a terminal a status is a glyph, colour may be on, and
a table's last column is cut with an ellipsis at the terminal's width; off one a status is a word
(ok, warn, FAIL, note), with no escape byte, no cut and no redraw. NO_COLOR set to a value,
TERM=dumb or --no-color turns colour off; the glyphs stay. Columns are left-aligned, two spaces
apart; a name is bold, a path or a hint dim; nothing is told by colour alone.
"""
import json
import os
import sys

from . import catalogue

GLYPH = {"ok": "✓", "warn": "!", "fail": "✗", "note": "·"}
WORD = {"ok": "ok", "warn": "warn", "fail": "FAIL", "note": "note"}
MARK_SGR = {"ok": "32", "warn": "33", "fail": "31", "note": "36"}
STYLE_SGR = {"name": "1", "path": "2", "hint": "2"}
CUT = "…"
GAP = "  "
FALLBACK_WIDTH = 80


def name(text):
    return (text, "name")


def path(text):
    return (text, "path")


def colour_off(env, no_color):
    return bool(no_color or env.get("NO_COLOR") or env.get("TERM") == "dumb")


class _Stream:
    def __init__(self, raw, no_colour):
        self.raw = raw
        try:
            self.tty = raw.isatty()
        except (AttributeError, ValueError, OSError):
            self.tty = False
        self.colour = self.tty and not no_colour
        try:
            "".join(GLYPH.values()).encode(getattr(raw, "encoding", None) or "ascii")
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
        self.raw.write(line + "\n")


class Term:
    def __init__(self, no_color=False, quiet=False, env=None, out=None, err=None, messages=None):
        env = os.environ if env is None else env
        off = colour_off(env, no_color)
        self.out = _Stream(out if out is not None else sys.stdout, off)
        self.err = _Stream(err if err is not None else sys.stderr, off)
        self.quiet = quiet
        self.messages = messages if messages is not None else catalogue.load()

    def text(self, mid, **values):
        return catalogue.fill(self.messages[mid], values)

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
        last column's start and never cut."""
        stream = self._stream(err)
        if not rows:
            return
        marked = any(r[0] for r in rows)
        grid = []
        for status, cells, after in rows:
            cells = [c if isinstance(c, tuple) else (c, None) for c in cells]
            if marked:
                shown, painted = stream.mark(status) if status else ("", "")
                cells.insert(mark_at, (shown, painted))
            grid.append((cells, after))
        ncols = max(len(cells) for cells, _ in grid)
        widths = [max((len(cells[i][0]) for cells, _ in grid if i < len(cells)), default=0)
                  for i in range(ncols)]
        for cells, after in grid:
            used, shown = indent, " " * indent
            for i, (text, style) in enumerate(cells):
                last = i == len(cells) - 1
                is_mark = marked and i == mark_at  # its style slot holds the painted mark
                if last and stream.tty and not is_mark:
                    room = stream.width() - used
                    if len(text) > room:
                        text = text[:max(room - 1, 0)] + CUT
                painted = style if is_mark else stream.paint(text, STYLE_SGR.get(style))
                pad = "" if last else " " * (widths[i] - len(text)) + GAP
                used += len(text) + len(pad)
                shown += painted + pad
            stream.write(shown.rstrip(" "))
            if after:
                start = indent + sum(w + len(GAP) for w in widths[:len(cells) - 1])
                stream.write(" " * start + stream.paint(after, STYLE_SGR["hint"]))

    def hint(self, mid, **values):
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
        self.out.write(json.dumps(obj, ensure_ascii=False, sort_keys=False))

    def flush(self):
        for stream in (self.out, self.err):
            try:
                stream.raw.flush()
            except (AttributeError, ValueError, OSError):
                pass
