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

A question is answered only by input that comes after it is drawn and after QUIET seconds in
which no byte came: any byte in that wait refuses, so no stream that began before a question
answers it. What this cannot tell apart: a writer that waits for each question to show and then
answers is a person to this verb, since the screen is all it can watch. Refusing a call that an
agent makes of its own accord is the guard's, another row.
"""
import hashlib
import json
import os
import re
import select
import shutil
import signal
import subprocess
import time
import unicodedata

from . import term

HOST = "github.com"
CEILING = 4096  # bytes of a draft
LINK = 6000  # bytes of a prefilled new-issue link
READ_WALL = 20  # seconds for a reading gh call or ps
FILE_WALL = 60  # seconds for the one writing call
WORD = b"send\n"
FALLBACK = (80, 24)
QUIET = 0.3  # seconds with no input, since a question was drawn, before its answer is read
TOKENS = ("GH_TOKEN", "GITHUB_TOKEN")  # each overrides the account gh stores for github.com
UNPASSED = TOKENS + ("GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN")  # never in the create's env
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
    """What `approve` returns when the word was typed: the bytes shown, their SHA-256, the repo
    and the login shown. Only `approve` makes one that `_file` takes, and `_file` takes it once:
    the bytes, hash, repo and login are recorded when it is made and compared again."""
    __slots__ = ("data", "sha256", "repo", "login")

    def __init__(self, data, repo, login=None):
        self.data, self.sha256 = data, hashlib.sha256(data).hexdigest()
        self.repo, self.login = repo, login


_ISSUED = {}  # id of each approval `approve` made and no `_file` has taken: (it, what it recorded)


def _issue(data, repo, login):
    """An approval of the bytes shown, recorded so that `_file` takes it once and only as made."""
    approved = Approved(bytes(data), repo, login)
    _ISSUED[id(approved)] = (approved, (approved.data, approved.sha256, repo, login))
    return approved


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
    for name in TOKENS:
        if name in env:
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


def _rows(text, cols):
    """The screen rows one line takes, as the terminal wraps it: a wide character counts two and
    goes to the next row when it does not fit, a combining one counts none."""
    rows, row, width = [], "", 0
    for c in text:
        w = 0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in "WF" else 1
        if row and width + w > cols:
            rows.append(row)
            row, width = "", 0
        row, width = row + c, width + w
    return rows + [row]


def _settle(fd):
    """Wait QUIET seconds from the moment the question was drawn: True when no input came in
    them, so the next line can be an answer to it. A byte that was waiting or came in the wait
    is the Refusal, exit 2, since it was typed before the question could be read. False for an
    end of input or a device gone."""
    end = time.monotonic() + QUIET
    while True:
        left = end - time.monotonic()
        if left <= 0:
            return True
        if select.select([fd], [], [], left)[0]:
            try:
                got = os.read(fd, 4096)
            except OSError:
                return False
            if not got:
                return False
            raise Refusal(2, "err.issue.send.early")


def _ask(fd, dev, mid, word=False):
    """Write the question on the device, wait QUIET seconds in which no byte may come (`_settle`)
    and read one line from it: the bytes, or None for an end of input or a device gone. For the
    word, a byte that comes on within QUIET seconds after the line is the flood's Refusal, exit
    2."""
    dev.line(mid)
    dev.flush()
    if not _settle(fd):
        return None
    try:
        answer = os.read(fd, 4096)
    except OSError:
        return None
    if answer and word and select.select([fd], [], [], QUIET)[0]:
        raise Refusal(2, "err.issue.send.flood")
    return answer or None


QUESTIONS = ("issue.screen.more", "issue.screen.within", "issue.send.ask")


def _room(fd, dev, items):
    """(cols, rows, room) of the terminal as it is now. A page holds `room` rows beside its
    question, which takes its own rows at this width (the tallest of the three is counted), and
    the cursor's row under it. A Refusal, exit 2, when not one row of the draft fits beside the
    question, or a fixed line of the screen (`items` that are not the draft's) does not fit."""
    try:
        cols, rows = os.get_terminal_size(fd)
    except OSError:
        cols, rows = FALLBACK
    cols, rows = cols or FALLBACK[0], rows or FALLBACK[1]
    room = rows - 1 - max(len(_rows(dev.text(mid), cols)) for mid in QUESTIONS)
    fixed = [len(_rows(dev.text(mid, **values), cols)) for mid, values in items
             if mid != "issue.screen.text" and mid not in QUESTIONS]
    if room < max([1] + fixed):
        raise Refusal(2, "err.issue.send.small")
    return cols, rows, room


def _screen(fd, data, lines, repo, login, notes_, env, t):
    out = open(fd, "w", encoding="utf-8", errors="strict", closefd=False)
    dev = term.Term(env=env, out=out, err=out, messages=t.messages)
    items = ([("issue.screen.head", {})] + [("issue.screen.text", {"text": line}) for line in lines]
             + [("issue.screen.end", {}), ("issue.screen.repo", {"repo": repo}),
                ("issue.screen.login", {"login": login})] + list(notes_) + [("issue.send.ask", {})])
    state = dict(zip(("cols", "rows", "room"), _room(fd, dev, items)), used=0)  # before a line

    def height(mid, values):
        return len(_rows(dev.text(mid, **values), state["cols"]))

    paged = sum(height(mid, values) for mid, values in items) + 1 > state["rows"]

    def page(mid, rest):
        """At a page's end, the question for the next; False when it gets no answer. The size is
        read again for the next page."""
        if _ask(fd, dev, mid) is None:
            return False
        state.update(zip(("cols", "rows", "room"), _room(fd, dev, rest)), used=0)
        return True

    answer = None
    try:
        n = 0
        while n < len(items):
            mid, values = items[n]
            if paged and mid == "issue.screen.text" and height(mid, values) > state["room"]:
                # a line taller than a page is paged inside itself, by its screen rows
                parts, within = _rows(dev.text(mid, **values), state["cols"]), False
                while parts:
                    if state["used"] >= state["room"]:
                        if not page("issue.screen.within" if within else "issue.screen.more",
                                    items[n:]):
                            break
                        parts = _rows("".join(parts), state["cols"])  # at the width it has now
                    take = state["room"] - state["used"]
                    dev.line(mid, text="".join(parts[:take]))
                    state["used"] += len(parts[:take])
                    parts, within = parts[take:], True
                if parts:
                    break
                n += 1
                continue
            if paged and state["used"] and state["used"] + height(mid, values) > state["room"]:
                if not page("issue.screen.more", items[n:]):
                    break
                continue  # the size may have changed: this line is weighed again on the new page
            if mid == "issue.send.ask":
                answer = _ask(fd, dev, mid, word=True)
                break
            dev.line(mid, **values)
            state["used"] += height(mid, values)
            n += 1
    except KeyboardInterrupt:
        answer = None
    if answer == WORD:
        return _issue(data, repo, login)
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
    only an approval this process's `approve` made and no call has taken, with the bytes, hash
    and repo it recorded, and files the recorded bytes. Just before the create it reads gh's
    active account again and files only as the login the screen showed, never with a token
    variable set, and the child's environment holds none."""
    made = _ISSUED.pop(id(approved), None)  # taken at once: an approval is good for one try
    if made is None or made[0] is not approved:
        raise Refusal(2, "err.issue.send.unapproved")
    data, sha256, shown, login = made[1]
    if (not isinstance(approved.data, bytes) or approved.data != data
            or hashlib.sha256(approved.data).hexdigest() != sha256 or approved.sha256 != sha256
            or approved.repo != shown or repo != shown):
        raise Refusal(2, "err.issue.send.changed")
    title, blank, body = (data.split(b"\n", 2) + [b"", b""])[:3]
    if not title or blank:
        raise Refusal(2, "err.issue.send.changed")
    for name in TOKENS:
        if name in env:
            raise Refusal(2, "err.issue.send.token", name=name)
    child = {k: v for k, v in env.items() if k not in UNPASSED}
    if not login or [name for name, on in accounts(child) if on] != [login]:
        raise Refusal(2, "err.issue.send.switched", login=login or "")
    code, out, err, state = _run(["gh"] + "issue create".split() + [
        "-R", "%s/%s" % (HOST, repo), "-t", title.decode("utf-8"), "-F", "-"],
        child, data=body, wall=FILE_WALL)
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
