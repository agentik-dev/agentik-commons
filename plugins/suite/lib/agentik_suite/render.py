"""The render of an issue's two free lines at a terminal (hq design/22 item 10; packet rp8).

`issue new --render` hands the scrubbed draft to the narrator plugin's headless script. The
plugin, its script and the mode are data in render.json beside the package, so no tool's name
stands here. `find` reads the script's path from Claude Code's installed_plugins.json; `run`
starts it from an empty temporary folder that holds the draft's bytes and the contract, and
reads back two lines, `Happened: ...` and `Expected: ...`, or None. The script's own streams are
never shown, its process group is ended on every way out, and the folder is removed either way.
What the answer may say is not decided here: `issue` holds it to the nothing-new check.
"""
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time

from . import apply, catalogue, form, gather, plan, term, tools

FILE = "render.json"
KEYS = ("plugin", "script", "mode")
WALL = 600  # seconds, the script's own wall (design/22 §2 item 5)
SOURCE, CONTRACT, OUT = "issue.md", "contract.md", "render.md"
READ_CAP = 1 << 16  # bytes of an answer read back; two lines of a draft are far under it
LABELS = ("Happened", "Expected")
LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRACE = apply.GRACE  # seconds between the group's SIGTERM and its SIGKILL
STOPS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)  # what ends a render, then the verb


def load(lib):
    """{plugin, script, mode} from `lib`/render.json; ValueError for any other shape."""
    found = None
    try:
        with open(os.path.join(lib, FILE), "rb") as fh:
            found = json.loads(fh.read().decode("utf-8"))
    except (OSError, ValueError):
        pass
    if not isinstance(found, dict) or sorted(found) != sorted(KEYS) or \
            not all(isinstance(found[k], str) and found[k] for k in KEYS):
        raise ValueError("%s: not {plugin, script, mode}" % FILE)
    if not gather.NAME.match(found["plugin"]) or os.path.isabs(found["script"]) or \
            ".." in found["script"].split("/"):
        raise ValueError("%s: no plugin name or no relative script" % FILE)
    return found


def find(env, lib):
    """The narrator's script under the root the finder names for `<plugin>@<marketplace>`
    (row fk2-plan R7), a regular executable file that resolves inside that root; else None."""
    try:
        conf, market = load(lib), gather.load_public(lib)["marketplace"]
    except ValueError:
        return None
    root, there = apply.install_root(env, "%s@%s" % (conf["plugin"], market))
    if not there:
        return None
    path = os.path.join(root, conf["script"])
    ok = os.path.isfile(path) and os.access(path, os.X_OK) and plan._under(path, root)  # as plan._command
    return path if ok else None


def contract():
    """The contract's text, a catalogue message, so a reworded contract passes the voice gate."""
    return catalogue.load()["issue.render.contract"] + "\n"


def run(script, data, env, wall=WALL, mode=None, why=None):
    """{"happened", "expected"}, the script's answer to the draft's bytes `data`, or None.

    None for an exit that is not 0, no output file, a file that is not the two lines, or the
    wall passed; `why`, a dict when given, is filled with the reason's `code` (`start`, `exit`,
    `wall`, `nofile`, `shape`) and, for `exit`, the exit. The child's group is ended and the
    folder removed on every way out; a folder that stays is `why`'s `left`. SIGINT, SIGTERM and
    SIGHUP raise Stopped once both are done. `mode` defaults to render.json's beside the package."""
    why = {} if why is None else why
    mode = load(LIB)["mode"] if mode is None else mode
    state = {"armed": True, "got": None}
    saved = _trap(state)
    try:
        return _run(script, data, env, wall, mode, why, state)
    finally:
        for sig, handler in saved.items():
            signal.signal(sig, handler)


class Stopped(BaseException):
    """A signal of STOPS during a render, raised once the script's group is ended and its folder
    removed, so the verb exits 128 plus `signum` (review 1 F1, F5)."""

    def __init__(self, signum):
        BaseException.__init__(self, signum)
        self.signum = signum


def _trap(state):
    """The handlers of STOPS while a render runs, the ones they replace returned. The first
    signal is kept in `state`; the others are ignored from then on, so the stop ends."""
    def stop(signum, frame):
        for sig in STOPS:
            signal.signal(sig, signal.SIG_IGN)
        state["got"] = signum
        if state["armed"]:
            raise Stopped(signum)
    saved = {}
    try:
        for sig in STOPS:
            saved[sig] = signal.signal(sig, stop)
    except ValueError:  # not the main thread: the default actions stay
        pass
    return saved


def _run(script, data, env, wall, mode, why, state):
    folder = os.path.realpath(tempfile.mkdtemp(prefix="agentik-render-"))
    try:
        paths = [os.path.join(folder, n) for n in (SOURCE, CONTRACT, OUT)]
        term.keep(paths[0], data)
        term.keep(paths[1], contract().encode("utf-8"))
        argv = [script, "--mode", mode, "--source", paths[0], "--out", paths[2],
                "--contract", paths[1]]
        code = _start(argv, folder, env, wall, why, state)
        if code is None:
            return None
        if code != 0:
            why.update(code="exit", exit=code)
            return None
        answer = _read(paths[2])
        if answer is None:
            why["code"] = "nofile"
            return None
        got = _answer(answer)
        if got is None:
            why["code"] = "shape"
        return got
    finally:
        state["armed"] = False
        if not _remove(folder):
            why["left"] = folder
        if state["got"] is not None:
            raise Stopped(state["got"])


def _start(argv, folder, env, wall, why, state):
    """The script's exit, or None with `why` filled; its group ended on every way out, a
    signal of STOPS held off from then on."""
    state["armed"] = False  # a signal while the child is made is held: no script is left unseen
    try:
        proc = subprocess.Popen(argv, cwd=folder, stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                env=dict(env), start_new_session=True)
    except (OSError, ValueError):
        why["code"] = "start"
        return None
    try:
        state["armed"] = True
        if state["got"] is not None:
            raise Stopped(state["got"])
        return proc.wait(timeout=wall)
    except subprocess.TimeoutExpired:
        why["code"] = "wall"
        return None
    finally:
        state["armed"] = False
        _end(proc)


def _end(proc):
    """The script's group ended, at the wall and at the script's own exit alike (review 1 F2):
    SIGTERM, up to GRACE for the group to go, so a trap can end what the script started, then
    SIGKILL; the head reaped. A child that left the group (setsid, setpgid) is out of reach,
    unless the script's trap ends it."""
    if _signal(proc.pid, signal.SIGTERM):
        end = time.monotonic() + GRACE
        while time.monotonic() < end:
            proc.poll()  # the head reaped as it goes, so an empty group reads as gone
            if not _signal(proc.pid, 0):
                break
            time.sleep(0.02)
        _signal(proc.pid, signal.SIGKILL)
    try:
        proc.wait(timeout=tools.REAP)
    except (subprocess.TimeoutExpired, OSError):
        pass


def _signal(group, sig):
    """True when `sig` reached the process group `group`."""
    try:
        os.killpg(group, sig)
        return True
    except OSError:
        return False


def _read(path):
    """The bytes of the regular file at `path`, never through a link, or None; past READ_CAP
    the answer is no answer."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return None
    try:
        if os.fstat(fd).st_mode & 0o170000 != 0o100000:  # S_IFMT, S_IFREG: a regular file alone
            return None
        chunks, size = [], 0
        while size <= READ_CAP:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
        return b"".join(chunks) if size <= READ_CAP else b""
    except OSError:
        return None
    finally:
        os.close(fd)


def _answer(data):
    """{"happened", "expected"} when `data` is the two lines and nothing else, each opening with
    its label, one line break at the end or none; else None."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    lines = (text[:-1] if text.endswith("\n") else text).split("\n")
    if len(lines) != 2:
        return None
    got = {}
    for label, line in zip(LABELS, lines):
        head = label + ":"
        if not line.startswith(head) or form.BREAKS.search(line):
            return None
        got[label.lower()] = line[len(head):].strip()
    return got


def _remove(folder):
    """The folder and whatever the script left in it, never through a link, whatever modes the
    script left (review 1 F3): a removal that leaves it makes each folder in it 0700 and tries
    again. True when it is gone."""
    shutil.rmtree(folder, ignore_errors=True)
    if not os.path.lexists(folder):
        return True
    _open(folder)
    for top, dirs, _files in os.walk(folder):  # walk follows no link
        for name in dirs:
            _open(os.path.join(top, name))
    shutil.rmtree(folder, ignore_errors=True)
    return not os.path.lexists(folder)


def _open(path):
    """The folder at `path` made 0700, never a link or what it points at."""
    nofollow = {"follow_symlinks": False} if os.chmod in os.supports_follow_symlinks else {}
    try:
        if os.lstat(path).st_mode & 0o170000 == 0o040000:  # S_IFMT, S_IFDIR: a folder alone
            os.chmod(path, 0o700, **nofollow)
    except (OSError, NotImplementedError):
        pass
