"""send: the last check of a draft's exact bytes, the account, the search, the screen that is the
bytes, the typed word on the terminal device, and the one door to a writing `gh` call (packet
rp5-send; hq design/22 section 3 items 7, 8, 9, 11, 12 and 16).

A model drafts, and a person sends. `approve` is the only function that makes what `_file` takes,
and `_file` is the only function of the package that starts `gh` with a writing verb. `approve`
writes the bytes to the terminal device, page by page when they are taller than it, reads one
line from that device and never from stdin, and passes only the word `send`. Nothing stands in
for that word: no flag, no environment variable, no config key and no test hook.

`send` is the stated exception to three of the command's own rules: it takes no `-y`, it prompts
on the terminal device whatever stdin is, and it starts `gh`. `gh` and `ps` come from the PATH of
the `env` each function is given. Every line it adds to the screen is a catalogue message.
"""
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import unicodedata

from . import term

HOST = "github.com"
CEILING = 4096  # bytes of a draft
LINK = 6000  # bytes of a prefilled new-issue link
READ_WALL = 20  # seconds for a reading gh call or ps
FILE_WALL = 60  # seconds for the one writing call
WORD = b"send\n"
FALLBACK = (80, 24)
MARKER = re.compile(r"^agentik-issue/1 (\S+) (\S+) ([0-9a-f]{12})$")
# What a terminal does not draw as itself (hq design/22 section 3 item 4(e)): the one list of the
# package. Each character of these categories but the plain space is refused anywhere in the bytes.
UNSEEN = {"Cc": "control", "Cf": "format", "Cs": "surrogate", "Co": "private", "Cn": "unassigned",
          "Zl": "separator", "Zp": "separator", "Zs": "space"}
# The blank letters: the variation selectors, the Mongolian ones, the combining grapheme joiner,
# the Hangul and Khmer fillers and the braille blank.
BLANK = frozenset(chr(c) for c in [0x034F, 0x115F, 0x1160, 0x17B4, 0x17B5, 0x180B, 0x180C, 0x180D,
                                   0x180F, 0x2800, 0x3164, 0xFFA0]
                  + list(range(0xFE00, 0xFE10)) + list(range(0xE0100, 0xE01F0)))
KIND = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
SAFE = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")


class Refusal(Exception):
    """Nothing is sent: `code` is the exit, `mid` the catalogue message, `values` its slots."""

    def __init__(self, code, mid, **values):
        Exception.__init__(self, mid)
        self.code, self.mid, self.values = code, mid, values


class Approved:
    """What `approve` returns when the word was typed: the bytes shown, their SHA-256 and the
    repo shown. `_file` takes this alone and checks it again."""
    __slots__ = ("data", "sha256", "repo")

    def __init__(self, data, repo):
        self.data, self.sha256, self.repo = data, hashlib.sha256(data).hexdigest(), repo


def _run(argv, env, data=None, wall=READ_WALL):
    """(exit, stdout, stderr, state) of argv from env's PATH, its own group, under a wall.
    State is `ran`, `unstarted` or `timed out`; past the wall its group is killed."""
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL if data is None else subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(env),
                                start_new_session=True)
    except (OSError, ValueError):
        return None, b"", b"", "unstarted"
    try:
        out, err = proc.communicate(data, timeout=wall)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
        proc.wait()  # never read on to an end of file: a child that left the group may hold it
        return None, b"", b"", "timed out"
    return proc.returncode, out, err, "ran"


# The last check (R2)

def marker(data):
    """(tool, version, fingerprint, line) of the draft's last marker line, or None."""
    lines = data.decode("utf-8", "replace").split("\n")
    for n in range(len(lines), 0, -1):
        m = MARKER.match(lines[n - 1])
        if m:
            return m.group(1), m.group(2), m.group(3), n
    return None


def repo_of(data, public):
    """OWNER/REPO for the marker's tool, from the public table alone; None when it names none."""
    mark = marker(data)
    tools = public.get("tools") or {}
    return tools.get(mark[0]) if mark and isinstance(tools, dict) else None


def unseen(line):
    """The kind of the first character of one line that a terminal does not draw as itself, or
    `nfkc` when NFKC would change the line; None when every character is drawn as itself."""
    for c in line:
        if c in BLANK:
            return "blank"
        kind = UNSEEN.get(unicodedata.category(c))
        if kind and c != " ":
            return kind
    return "nfkc" if unicodedata.normalize("NFKC", line) != line else None


def _line_at(data, offset):
    return data[:offset].count(b"\n") + 1


def check(data, m, public, form, scrub, ceiling=CEILING):
    """[(line, kind)] for the exact bytes, empty when they may be shown. The kinds: `form` (the
    bytes do not read back, or do not write again to the same bytes), `size`, `tool`, a kind of
    `unseen` for a character anywhere in the bytes that a terminal does not draw as itself, and
    each kind `scrub.detect` gives for a free value. A refusal never holds a match."""
    found = []
    if len(data) > ceiling:
        found.append((_line_at(data, ceiling), "size"))
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        return sorted(set(found + [(_line_at(data, e.start), "form")]))
    for n, line in enumerate(text.split("\n"), 1):
        kind = unseen(line)
        if kind:
            found.append((n, kind))
    tools = public.get("tools") or {}
    try:
        fields = form.parse(data, tools)
        again = form.build(fields)
        free = list(form.free(fields))
    except Exception:  # noqa: BLE001 - what the form's reader cannot read is not the form
        return sorted(set(found + [(1, "form")]))
    if again != data:
        same = 0
        while same < min(len(data), len(again)) and data[same] == again[same]:
            same += 1
        found.append((_line_at(data, same), "form"))
    mark = marker(data)
    if mark is None:
        found.append((text.count("\n") or 1, "form"))
    elif mark[0] not in tools:
        found.append((mark[3], "tool"))
    for _key, line, value in free:
        for kind in scrub.detect(value, m):
            found.append((line, kind if KIND.match(str(kind)) else "scrub"))
    return sorted(set(found))


# The account (R3) and the search (R4)

def accounts(env):
    """[(login, active)] on github.com from `gh auth status --json hosts`, which holds no token;
    [] when gh gives none or cannot be read."""
    _code, out, _err, state = _run(["gh", "auth", "status", "--json", "hosts"], env)
    try:
        hosts = json.loads(out.decode("utf-8")).get("hosts") or {}
        entries = hosts.get(HOST) or []
        return [(e["login"], e.get("active") is True) for e in entries
                if isinstance(e, dict) and isinstance(e.get("login"), str) and e["login"]]
    except (ValueError, AttributeError, TypeError):
        return []


def account(env, as_login=None):
    """The road a send takes. {"road": "gh", "login"}; {"road": "web", "why", "values"}, the
    browser's, with the message that says why; {"road": "refuse", "why", "values"}, exit 2.
    Nothing here switches an account."""
    for name in ("GH_TOKEN", "GITHUB_TOKEN"):
        if env.get(name):
            return {"road": "web", "why": "issue.send.web.token", "values": {"name": name}}
    if not shutil.which("gh", path=env.get("PATH", "")):
        return {"road": "web", "why": "issue.send.web.nogh", "values": {}}
    found = accounts(env)
    if not found:
        return {"road": "web", "why": "issue.send.web.noaccount", "values": {}}
    active = [login for login, on in found if on]
    if len(found) == 1 and as_login in (None, found[0][0]):
        return {"road": "gh", "login": found[0][0]}
    if as_login is None:
        return {"road": "refuse", "why": "err.issue.send.as", "values": {"count": len(found)}}
    if as_login not in active:
        return {"road": "refuse", "why": "err.issue.send.inactive", "values": {"login": as_login}}
    return {"road": "gh", "login": as_login}


def search(env, repo, fingerprint):
    """(state, found): `open`, `closed`, `none` or `failed`, with the matches as gh gave them.
    Only the fingerprint leaves this machine."""
    code, out, _err, _state = _run(
        ["gh", "issue", "list", "-R", "%s/%s" % (HOST, repo), "-S", "%s in:body" % fingerprint,
         "-s", "all", "--json", "number,title,state,url", "-L", "5"], env)
    if code != 0:
        return "failed", []
    try:
        found = [f for f in json.loads(out.decode("utf-8")) if isinstance(f, dict)]
    except (ValueError, TypeError):
        return "failed", []
    opened = [f for f in found if str(f.get("state", "")).upper() == "OPEN"]
    if opened:
        return "open", opened
    return ("closed", found) if found else ("none", [])


def notes(state, found):
    """The screen's lines for a search: one for a closed match or a failed search."""
    if state == "closed":
        return [("issue.screen.closed", {"url": found[0].get("url", "")})]
    if state == "failed":
        return [("issue.screen.failed", {})]
    return []


# The screen and the typed word (R5)

def _shown_lines(data):
    """The draft's lines as the screen writes them, or a Refusal for bytes it cannot show as
    themselves: not UTF-8, a character of `unseen` on any line, or no title over a blank line."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise Refusal(1, "err.issue.send.line", line=_line_at(data, e.start), kind="form")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for n, line in enumerate(lines, 1):
        kind = unseen(line)
        if kind:
            raise Refusal(1, "err.issue.send.line", line=n, kind=kind)
    if len(lines) < 3 or not lines[0] or lines[1]:
        raise Refusal(1, "err.issue.send.line", line=1 if not lines or not lines[0] else 2, kind="form")
    return lines


def _claude_above(env):
    """Whether a process named claude is this one or among its ancestors, by one `ps` from PATH.
    A listing that cannot be read, or that does not hold this process, refuses."""
    code, out, _err, _state = _run(["ps", "-A", "-o", "pid=", "-o", "ppid=", "-o", "comm="], env)
    parent, name = {}, {}
    for row in out.decode("utf-8", "replace").splitlines() if code == 0 else ():
        parts = row.split(None, 2)
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            parent[int(parts[0])], name[int(parts[0])] = int(parts[1]), parts[2].strip()
    pid, seen = os.getpid(), set()
    if pid not in parent:
        raise Refusal(2, "err.issue.send.ps")
    while pid in parent and pid not in seen:
        seen.add(pid)
        if os.path.basename(name[pid]) == "claude":
            return True
        pid = parent[pid]
    return False


def _height(text, cols):
    """Rows a line takes: its width over the columns, a wide character counting two."""
    width = sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in "WF"
                else 1 for c in text)
    return max(1, -(-width // cols))


def _drain(fd):
    """Drop whatever was typed before a question is shown, so only an answer to it counts."""
    os.set_blocking(fd, False)
    try:
        while os.read(fd, 4096):
            pass
    except (BlockingIOError, OSError):
        pass
    finally:
        os.set_blocking(fd, True)


def _ask(fd, dev, mid):
    """Write the question on the device and read one line from it: the bytes, or None for an
    end of input or a device gone."""
    _drain(fd)
    dev.line(mid)
    dev.flush()
    try:
        answer = os.read(fd, 4096)
    except OSError:
        return None
    return answer or None


def _screen(fd, data, lines, repo, login, notes_, env, t):
    out = open(fd, "w", encoding="utf-8", errors="strict", closefd=False)
    dev = term.Term(env=env, out=out, err=out, messages=t.messages)
    items = ([("issue.screen.head", {})] + [("issue.screen.text", {"text": line}) for line in lines]
             + [("issue.screen.end", {}), ("issue.screen.repo", {"repo": repo}),
                ("issue.screen.login", {"login": login})] + list(notes_) + [("issue.send.ask", {})])
    try:
        cols, rows = os.get_terminal_size(fd)
    except OSError:
        cols, rows = FALLBACK
    cols, rows = cols or FALLBACK[0], rows or FALLBACK[1]
    heights = [_height(dev.text(mid, **values), cols) for mid, values in items]
    room = max(rows - 2, 1)  # a page leaves a row for its question and one for the cursor
    paged = sum(heights) + 1 > rows
    used, answer = 0, None
    try:
        for (mid, values), height in zip(items, heights):
            if paged and used and used + height > room:
                if _ask(fd, dev, "issue.screen.more") is None:
                    break
                used = 0
            if mid == "issue.send.ask":
                answer = _ask(fd, dev, mid)
                break
            dev.line(mid, **values)
            used += height
    except KeyboardInterrupt:
        answer = None
    if answer == WORD:
        return Approved(data, repo)
    try:
        dev.line("issue.send.kept")
        dev.flush()
    except KeyboardInterrupt:
        pass
    return None


def approve(data, repo, login, notes, env, t):
    """Approved when a person read the exact bytes on the terminal device and typed `send`; None
    for any other answer, an end of input or an interrupt, the draft kept. A Refusal, exit 2,
    when the device does not open, CLAUDECODE is in env, or a claude process is above this one.
    `notes` are (message id, values) lines shown under the bytes."""
    try:
        fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
    except OSError:
        raise Refusal(2, "err.issue.send.tty")
    try:
        if "CLAUDECODE" in env:
            raise Refusal(2, "err.issue.send.inside")
        if _claude_above(env):
            raise Refusal(2, "err.issue.send.parent")
        lines = _shown_lines(data)
        return _screen(fd, data, lines, repo, login, notes, env, t)
    finally:
        os.close(fd)


# The one door (R5)

def _file(approved, repo, env):
    """The URL gh prints for the new issue: the approved bytes' first line as the title and the
    bytes after the second line on stdin, to github.com/OWNER/REPO, under a 60 s wall. It takes
    only what approve returned and checks its hash and repo again."""
    if (not isinstance(approved, Approved) or not isinstance(approved.data, bytes)
            or hashlib.sha256(approved.data).hexdigest() != approved.sha256
            or approved.repo != repo):
        raise Refusal(2, "err.issue.send.changed")
    title, blank, body = (approved.data.split(b"\n", 2) + [b"", b""])[:3]
    if not title or blank:
        raise Refusal(2, "err.issue.send.changed")
    argv = ["gh"] + "issue create".split() + ["-R", "%s/%s" % (HOST, repo),
                                               "-t", title.decode("utf-8"), "-F", "-"]
    code, out, err, state = _run(argv, env, data=body, wall=FILE_WALL)
    if state == "unstarted":
        raise Refusal(2, "err.issue.send.nogh")
    if state == "timed out":
        raise Refusal(1, "err.issue.send.timeout", secs=FILE_WALL)
    if code != 0:
        last = (err.decode("utf-8", "replace").strip().splitlines() or [""])[-1]
        raise Refusal(1, "err.issue.send.failed", code=code, last=last[:200])
    lines = [line.strip() for line in out.decode("utf-8", "replace").splitlines() if line.strip()]
    urls = [line for line in lines if line.startswith("https://")]
    return (urls or lines or [""])[-1]


# The browser's road (R7)

def _quote(text):
    """Percent-encoding of the UTF-8 bytes; only the unreserved characters stand as they are."""
    return "".join(chr(b) if b in SAFE else "%%%02X" % b for b in text.encode("utf-8"))


def web(data, repo, fingerprint):
    """(search link, new-issue link) for the approved bytes; the new-issue link holds the title
    and body when it stays under 6,000 bytes, and is bare otherwise. It opens nothing."""
    base = "https://%s/%s/issues" % (HOST, repo)
    found = "%s?q=%s" % (base, _quote("%s in:body" % fingerprint))
    title, _blank, body = (data.decode("utf-8").split("\n", 2) + ["", ""])[:3]
    new = "%s/new?title=%s&body=%s" % (base, _quote(title), _quote(body))
    return found, new if len(new.encode("utf-8")) < LINK else base + "/new"
