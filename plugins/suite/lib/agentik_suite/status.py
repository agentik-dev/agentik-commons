"""`status --check`: each watcher the user file declares that is not running, one line each.

The declaration is the user file's `watchers` alone (settings.user_path). The listing is one
`ps -axo pid,ppid,uid,etime,command` under a 1 s wall, or a saved one given by `--ps`. A watcher
runs when a process of the reader's uid has its `match` as the head of its command (the head
found past an interpreter, a shell or `env`, by basename or a link's target), and its beat file,
when it names one, is within its `fresh_s`. The check runs no tool, reads no cache, starts `ps`
at most, and says nothing when every watcher runs.
"""
import datetime
import json
import os
import re
import shutil
import signal
import time

from . import plan, settings, tools

PS = "/bin/ps"
PS_ARGS = ("-axo", "pid,ppid,uid,etime,command")
WALL = 1.0
BEAT_CAP = tools.CAP  # 1 MiB, the listing's cap: a beat file past it is no beat
WRAPPERS = ("sh", "bash", "zsh", "dash", "env")
VALUED = ("-X", "-W", "-o")  # after any wrapper, the next word is the flag's value
ENV_VALUED = ("-u",)  # after `env` alone (`env -u NAME prog`); after python or a shell, a plain flag
# A run on the way: `-c` or `-m`, attached to its value (`-mfoo`) or anywhere in a short
# cluster (`-ce`, `-lc`); a `-X` or `-W` word is its value's, never a run. A bare `-` (the
# program read from stdin) is no match either.
RUN = re.compile(r"-(?![XW-])[A-Za-z]*[cm]")
S_IFMT, S_IFREG = 0o170000, 0o100000  # a mode's type bits, and a regular file's
ASSIGN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
ISO = re.compile(r"(\d{4}-\d\d-\d\d)[T ](\d\d:\d\d(?::\d\d(?:\.\d+)?)?)(Z|[+-]\d\d:?\d\d)?\Z")
LINE = {"missing": "status.missing", "hung": "status.hung"}


def when(text):
    """Epoch seconds of an ISO 8601 time with `Z`, an offset, or neither (local); else None."""
    m = ISO.match(text or "")
    if not m:
        return None
    zone = m.group(3) or ""
    if zone == "Z":
        zone = "+00:00"
    elif zone and ":" not in zone:
        zone = zone[:3] + ":" + zone[3:]
    try:
        stamp = datetime.datetime.fromisoformat("%sT%s%s" % (m.group(1), m.group(2), zone))
        return stamp.timestamp()  # a local time near year 1 raises here
    except (ValueError, OverflowError, OSError):
        return None


def local(at):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(at))


def regular(path, cap=None):
    """The bytes of a regular file, opened without blocking (a FIFO with no writer never hangs
    the check), read whole; OSError for anything that is no regular file and, when a `cap` is
    given, for a file past it."""
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as fh:
        if os.fstat(fd).st_mode & S_IFMT != S_IFREG:
            raise OSError("%s is not a regular file" % path)
        if cap is None:
            return fh.read()
        data = fh.read(cap + 1)
        if len(data) > cap:
            raise OSError("%s is past %d bytes" % (path, cap))
        return data


def declared(env):
    """(path, [watcher], [unchecked name]); a settings.Fault, with `path`, for a file outside the
    subset or `watchers` that is no mapping of mappings."""
    path = settings.user_path(env)
    try:
        present, tree, lines = settings.read(path)
        watchers = tree.get("watchers")
        if watchers is None:
            return path, [], []
        if not isinstance(watchers, dict):
            raise settings.Fault(lines.get("watchers"), "watchers is not a mapping of names")
        found, unchecked = [], []
        for name, fields in watchers.items():
            if not isinstance(fields, dict):
                raise settings.Fault(lines.get("watchers." + name), "watcher %s is not a mapping" % name)
            w = {f: fields[f] if isinstance(fields.get(f), str) and fields[f].strip() else None
                 for f in settings.WATCHER_FIELDS}
            if w["match"] is None or w["start"] is None:
                unchecked.append(name)
                continue
            w["name"] = name
            found.append(w)
        return path, found, unchecked
    except settings.Fault as f:
        f.path = path
        raise


def ps_argv(env):
    if os.path.isfile(PS) and os.access(PS, os.X_OK):
        return [PS] + list(PS_ARGS)
    found = shutil.which("ps", path=env.get("PATH", ""))
    return [found] + list(PS_ARGS) if found else None


def listing(env):
    """The text of one ps run, or None: no ps, a non-zero exit, or past the wall."""
    argv = ps_argv(env)
    if argv is None:
        return None
    code, out, state = tools.run_all([("ps", argv)], env, deadline=time.monotonic() + WALL)["ps"]
    if state != "ran" or code != 0:
        return None
    return out.decode("utf-8", "replace")


def rows(text):
    """[(pid, uid, [word])] of each row past the head."""
    found = []
    for line in text.splitlines()[1:]:
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        try:
            pid, uid = int(parts[0]), int(parts[2])
        except ValueError:
            continue
        found.append((pid, uid, parts[4].split()))
    return found


def holds_self(procs):
    """A listing this process took holds this process: one that does not is `bad_listing`,
    read as no listing and never as an empty one (packet su2-read, review 1)."""
    return any(pid == os.getpid() for pid, uid, words in procs)


def _wrapper(word):
    base = os.path.basename(word).lower()  # macOS shows /usr/bin/python3 as .../MacOS/Python
    return base.startswith("python") or base in WRAPPERS


def head(words):
    """The index of the command's head, or None: none left, or a -c, -m or bare - on the way."""
    i = 0
    while i < len(words) and _wrapper(words[i]):
        valued = VALUED + ENV_VALUED if os.path.basename(words[i]) == "env" else VALUED
        i += 1
        while i < len(words):
            word = words[i]
            if word == "-" or RUN.match(word):
                return None
            if word in valued:
                i += 2
            elif word.startswith("-") or ASSIGN.match(word):
                i += 1
            else:
                break
    return i if i < len(words) else None


def _names(word):
    names = {os.path.basename(word)}
    if os.path.isabs(word):
        names.add(os.path.basename(os.path.realpath(word)))
    return names


def matches(match, words):
    want = match.split()
    i = head(words)
    if i is None or os.path.basename(want[0]) not in _names(words[i]):
        return False
    return words[i + 1:i + len(want)] == want[1:]


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and value == value and abs(value) != float("inf")


def beat(w, env):
    """The beat as {at, fresh_s, writer, line}, or None."""
    path = w["beat"]
    if not path:
        return None
    if path.startswith("~/"):
        path = os.path.join(env.get("HOME") or "", path[2:])
    if not os.path.isabs(path):
        return None
    try:
        obj = json.loads(regular(path, BEAT_CAP).decode("utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(obj, dict) or not _number(obj.get("at")) or not _number(obj.get("fresh_s")):
        return None
    if any(obj.get(k) is not None and not isinstance(obj[k], str) for k in ("writer", "line")):
        return None
    try:
        local(obj["at"])
    except (OverflowError, OSError, ValueError):
        return None  # an `at` the clock refuses (outside time_t) is no time, so no beat
    return {"at": obj["at"], "fresh_s": obj["fresh_s"], "writer": obj.get("writer"),
            "line": obj.get("line")}


def check(w, procs, now, env, uid):
    """{name, state, pid, since, beat_writer, beat_line, start, writer, beat_at} for one watcher:
    `writer` the declared one, `beat_at` the beat's `at` whoever wrote it."""
    b = beat(w, env)
    own = b is not None and (w["writer"] is None or b["writer"] == w["writer"])
    fresh = b is not None and max(0, now - b["at"]) <= b["fresh_s"]
    pid = None
    if procs is not None:
        pid = next((p for p, u, words in procs if u == uid and matches(w["match"], words)), None)
    if procs is None:
        state = "unknown"
    elif pid is None:
        state = "missing"
    else:
        state = "running" if b is None or fresh else "hung"
    return {"name": w["name"], "state": state, "pid": pid, "since": b["at"] if own else None,
            "beat_writer": b["writer"] if b else None,
            "beat_line": b["line"] if own and fresh else None, "start": w["start"],
            "writer": w["writer"], "beat_at": b["at"] if b else None}


class Signalled(BaseException):
    """SIGTERM or SIGHUP while the reads run: raised so run_all ends every read on its way out."""

    def __init__(self, signum):
        BaseException.__init__(self, signum)
        self.signum = signum


def _signalled(signum, frame):
    raise Signalled(signum)


def do_status(cmd, nouns):
    """`--check` (su1), or the full read, `status [<path>...]`: the screen, each part drawn as
    soon as it and every part above it is read, or with `--json` the object (packet su2-read R2,
    J2). For the life of the reads SIGTERM and SIGHUP end every read and exit 128 plus the
    signal's number; an interrupt ends them and exits 130, a closed stdout 141 (128 plus SIGPIPE),
    each with no traceback (su2-read, review 1 and the join)."""
    saved = {}
    try:
        for sig in (signal.SIGTERM, signal.SIGHUP):
            saved[sig] = signal.signal(sig, _signalled)
    except ValueError:  # not the main thread: the default actions stay
        pass
    try:
        return _status(cmd, nouns)
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:  # stdout was closed while the screen drew: every read is ended
        return 128 + signal.SIGPIPE
    except Signalled as s:
        return 128 + s.signum
    finally:
        for sig, handler in saved.items():
            signal.signal(sig, handler)


def _full(cmd, nouns, now, text):
    """The full read: the object on `--json`, else the screen, a part at a time (J2)."""
    from . import status_read
    t = cmd.t
    if cmd.opts["json"]:
        t.json(status_read.compose(cmd, nouns, now, text))
        return 0
    from . import status_screen
    slots = cmd.slots()

    def on_part(name, obj):
        status_screen.part(t, obj, name, slots)
        t.flush()
        if t.out.gone:  # the reader closed the pipe: raised here, run_all ends every read
            raise BrokenPipeError("stdout closed")

    obj = status_read.compose(cmd, nouns, now, text, on_part)
    status_screen.foot(t, obj, slots)
    return 0


HOOKS = ("--now", "--ps")  # the test hooks, each with its value


def mended(cmd, nouns):
    """The line to paste after a refusal of status (row sc4 R1 and R4, su2-read phase 2): the line
    as typed less each path that is no folder and less the test hooks with their values, so it
    passes every check of the verb's that reads no user file."""
    swap = {cmd.at[k + 1]: [] for k, path in enumerate(nouns) if not os.path.isdir(path)}
    args = iter(enumerate(cmd.argv))
    for i, arg in args:
        if arg == "--":
            break
        flag, eq, _ = arg.partition("=")
        if flag in HOOKS:
            swap[i] = []
            if not eq:
                j = next(args, (None, None))[0]
                if j is not None:
                    swap[j] = []
    return cmd.again(swap)


def _status(cmd, nouns):
    """Each refusal is its cause and the line to paste (sc4's form): a name after --check, a path
    that is no folder, a bad --now or --ps; a user file that does not parse is its fault alone."""
    o, t, Refusal = cmd.opts, cmd.t, cmd.Refusal
    if o["check"] and nouns:
        raise Refusal("extra_word", "err.extra", cmd.say("status", "--check"),
                      verb="status --check", word=nouns[0])
    for path in nouns:
        if not os.path.isdir(path):
            raise Refusal("bad_path", "err.status.path", mended(cmd, nouns), path=path)
    now = time.time()
    if o["now"] is not None:
        now = when(o["now"])
        if now is None:
            raise Refusal("bad_time", "err.status.now", mended(cmd, nouns), value=o["now"])
    text = None
    if o["ps"] is not None:
        try:
            text = regular(o["ps"]).decode("utf-8", "replace")
        except OSError:
            raise Refusal("bad_listing", "err.status.ps", mended(cmd, nouns), path=o["ps"])
    try:
        if not o["check"]:
            return _full(cmd, nouns, now, text)
        path, watchers, unchecked = declared(cmd.env)
    except settings.Fault as f:
        home = cmd.env.get("HOME")
        fault = t.text("config.fault" if f.line else "config.fault.noline",
                       path=plan.shown(f.path, home), line=f.line, why=f.why)
        raise Refusal("bad_file", "err.status.file", None, fault=fault)
    procs, bad = None, None
    if watchers:
        if text is None:
            text = listing(cmd.env)
            if text is not None and not holds_self(rows(text)):
                text, bad = None, ps_argv(cmd.env)[0]
        procs = rows(text) if text is not None else None
    found = [check(w, procs, now, cmd.env, os.getuid()) for w in watchers]
    shown = [r for r in found if r["state"] != "running"]
    if o["json"]:
        obj = {"schema": "agentik.status/1", "ok": True, "check": True, "watchers": found}
        if bad:
            obj["fault"] = "bad_listing"  # held only when the listing was bad: su1's object as it was
        t.json(obj)
    else:
        for r in shown:
            if r["state"] == "unknown" and bad:
                t.line("status.unknown.listing", name=r["name"], path=bad)
            elif r["state"] == "unknown":
                t.line("status.unknown", name=r["name"])
            elif r["since"] is not None:
                t.line(LINE[r["state"]] + ".since", name=r["name"], start=r["start"],
                       when=local(r["since"]))
            else:
                t.line(LINE[r["state"]], name=r["name"], start=r["start"])
    for name in unchecked:
        t.hint("hint.status.unchecked", name=name, path=plan.shown(path, cmd.env.get("HOME")),
               **cmd.slots())
    return 1 if shown else 0
