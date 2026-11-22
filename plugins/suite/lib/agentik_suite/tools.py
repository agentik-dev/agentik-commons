"""The tools the suite lists, and their own answers about themselves.

A tool is listed when it is the suite itself, an `agentik-<name>` on PATH, or a name the suite
knows whose source the finder (`sources`, row fk1-sources) finds installed. Its executable is the
file the finder says runs, never one under the root of a plugin that does not stand (row fk2-plan).
Each executable but the suite's runs as `agentik-<name>
describe --json`, every one at once, under one wall of WALL seconds; one still running then is
killed with its process group. A counted answer is cached, one file a tool, under
`${XDG_CACHE_HOME:-~/.cache}/agentik/suite/`, while the executable's resolved path, size and
modified time hold; a config read is never cached. The suite runs no program but a listed
tool's executable, with the words a tool's read names after it.
"""
import json
import os
import re
import select
import signal
import subprocess
import tempfile
import time
import unicodedata

from . import plan, settings, sources

WALL = 2.0
# A describe or config answer is a few kilobytes; a tool with a thousand settings stays under a
# megabyte. Past CAP bytes on stdout the tool is cut, so a flood costs at most CAP a tool.
CAP = 1 << 20
POLL = 0.02
ERR_CAP = 4096  # a job's stderr kept for `errs` (packet su2-read R4)
REAP = 0.1
DESCRIBE = re.compile(r"agentik\.describe/(1)\Z")  # R3 names the one schema
CONFIG = re.compile(r"agentik\.config/([0-9]+)\Z")
DESCRIBE_KEYS = ("tool", "version", "summary", "repo", "plugin", "needs", "verbs", "reads")
READ_KINDS = ("config", "doctor", "status")
NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
LINE_CAP = 300  # a tool's message or detail, cut (row ak9b R4)


def _config_dir(env):
    return env.get("CLAUDE_CONFIG_DIR") or os.path.join(env.get("HOME") or "", ".claude")


def _cwd(cwd):
    if cwd is not None:
        return cwd
    try:
        return os.getcwd()
    except OSError:  # a removed folder: no repo's entries
        return None


def _lib(lib):
    """The folder of public.json: `lib`, else the one this package sits in."""
    return lib or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lines(env):
    """The user file's `sources` lines; none when the file is outside the subset, a fault each
    read that owns the file reports as it does today."""
    try:
        return settings.declared(env)[0]
    except settings.Fault:
        return {}


def _own(env):
    """Each name of a `<name>@agentik` in Claude Code's installed_plugins.json, in its order."""
    found = plan._read_json(os.path.join(_config_dir(env), "plugins", "installed_plugins.json"))
    table = found.get("plugins") if isinstance(found, dict) else None
    names = []
    for key in table if isinstance(table, dict) else ():
        name, at, market = key.partition("@")
        if at and market == plan.MARKETPLACE and NAME.match(name) and name not in names:
            names.append(name)
    return names


def known(env, lib=None, lines=None):
    """The names the suite knows (row fk2-plan R1): the marketplace file's, public.json's tools
    (row ak10c5 R4), each installed `<name>@agentik` and each `sources` line's, sorted."""
    lines = _lines(env) if lines is None else lines
    names = set(descriptions(env)) | set(public(lib)["tools"]) | set(_own(env)) | set(lines)
    return sorted(n for n in names if NAME.match(n))


def rows(env, lib=None, cwd=None, names=None):
    """{name: the finder's row} for each name the suite knows, or for `names`."""
    lines, cwd = _lines(env), _cwd(cwd)
    names = known(env, lib, lines) if names is None else names
    return {name: sources.find(name, env, cwd, lines) for name in names}


def listed(suite, on_path, env, lib=None, cwd=None):
    """[{name, exe, plugin, source}]: the suite first, then the rest by name. `exe` is the file
    the finder says runs, or None; `source` its row for a name the suite knows that is found or
    held, else None (R2). A name on PATH alone is listed as it is found there, unless its file
    lies under the root of a plugin that does not stand (R3)."""
    found = {suite: {"name": suite, "exe": None, "plugin": False, "source": None}}
    for entry in on_path:
        name = entry["name"][len("agentik-"):]
        if name != suite and NAME.match(name):
            found.setdefault(name, {"name": name, "exe": entry["path"], "plugin": False, "source": None})
    lines, cwd = _lines(env), _cwd(cwd)
    names = known(env, lib, lines)
    for name in sorted(set(names) | set(found)):
        row = sources.find(name, env, cwd, lines)
        if name == suite:
            if row["kind"] != "absent":
                found[suite]["plugin"] = True
            continue
        exe = (row["runs"] or {}).get("path")
        if name in names and row["kind"] != "absent":
            found[name] = {"name": name, "exe": exe, "plugin": True, "source": row}
        elif name in found and row["passed_over"] is not None:
            found[name]["exe"] = exe
    rest = sorted(n for n in found if n != suite)
    return [found[suite]] + [found[n] for n in rest]


def installed(env, lib=None, cwd=None):
    """Each name the suite knows whose kind, as the finder reads it, is not `absent` (R1)."""
    return [name for name, row in rows(env, lib, cwd).items() if row["kind"] != "absent"]


def runs(env, on_path, cwd=None):
    """{name: path} of `on_path` ({name: path}), each file the finder passes over replaced by the
    one it says runs, or left out when none does (R3)."""
    lines, cwd = _lines(env), _cwd(cwd)
    found = {}
    for name, path in on_path.items():
        row = sources.find(name, env, cwd, lines)
        if row["passed_over"] is None:
            found[name] = path
        elif row["runs"]:
            found[name] = row["runs"]["path"]
    return found


def plugin_names(env, lib):
    """Every plugin's name the suite knows (packet ak2 R3, row fk2-plan R1)."""
    return known(env, lib)


def _end(job):
    """Kill the process group and close the parent's end of the pipe, once. Never wait for EOF:
    a child that left the group may hold the pipe open."""
    if job.get("ended"):
        return
    job["ended"] = True
    try:
        os.killpg(job["proc"].pid, signal.SIGKILL)
    except OSError:
        pass
    try:
        os.close(job["fd"])
    except OSError:
        pass


def _reap(proc):
    try:
        proc.wait(timeout=REAP)
    except (subprocess.TimeoutExpired, OSError):
        pass


def _end_all(live):
    """Every live job's group killed first, then each reaped, each wait bounded by REAP."""
    for job in live.values():
        _end(job)
    for job in live.values():
        _reap(job["proc"])
        _keep_err(job, None, None)


def _drain(job):
    """Read what the pipe holds now; `eof`, `open` or `cap` (past CAP bytes)."""
    while True:
        try:
            data = os.read(job["fd"], 65536)
        except BlockingIOError:
            return "open"
        except OSError:
            return "eof"
        if not data:
            return "eof"
        job["size"] += len(data)
        if job["size"] > CAP:
            return "cap"
        job["chunks"].append(data)


def run_all(jobs, env, then=None, deadline=None, walls=None, errs=None, times=None, cwd=None):
    """{key: (exit or None, stdout bytes, state)} for jobs [(key, argv)], every one started at
    once, under one deadline (WALL seconds from now when none is given). State is `ran`, `timed
    out` (still running at the deadline, or not started by it) or `unreadable` (it could not
    start, or its stdout passed CAP). `then(key, result)` names more jobs, started at once under
    the same deadline. A job ends when its process exits; its group is then killed, so no
    process of a group outlives the run. That holds on every way out: an exception from `then`
    or an interrupt kills and reaps every live group before it leaves (packet su2-read, review 1).

    Three optional keywords (packet su2-read R4); without them the call is as it was. `walls`,
    {key: seconds}: each job runs under its own wall from its own start (WALL for a key it does
    not name), and the one deadline holds only when given. `errs`, a dict filled with each job's
    stderr up to ERR_CAP bytes. `times`, a dict filled with each job's seconds from this call's
    start to its end. `cwd`, the folder every process starts in, the caller's where None (packet
    dr2-doctor-machine R1: the doctor's reads start in the home folder)."""
    t0 = time.monotonic()
    if walls is None:
        deadline = t0 + WALL if deadline is None else deadline
    queue, live, results = list(jobs), {}, {}

    def finish(key, result):
        results[key] = result
        if times is not None:
            times[key] = time.monotonic() - t0
        queue.extend(then(key, result) if then else ())

    try:
        _run(queue, live, finish, env, deadline, walls, errs, cwd)
    except BaseException:
        _end_all(live)
        live.clear()
        raise
    for job in live.values():
        _end(job)
    for key, job in live.items():
        _reap(job["proc"])
        _keep_err(job, key, errs)
        results[key] = (None, b"", "timed out")
    for key, _ in queue:
        results[key] = (None, b"", "timed out")
    return results


def _run(queue, live, finish, env, deadline, walls, errs, cwd=None):
    """run_all's loop: it starts, drains and ends jobs until none is live or the walls pass."""
    while True:
        while queue:
            key, argv = queue.pop(0)
            now = time.monotonic()
            if deadline is not None and now >= deadline:
                finish(key, (None, b"", "timed out"))
                continue
            end = deadline
            if walls is not None:
                end = now + walls.get(key, WALL)
                end = min(end, deadline) if deadline is not None else end
            fd, out = os.pipe()
            efd, eout = os.pipe() if errs is not None else (None, None)
            try:
                proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out,
                                        stderr=subprocess.DEVNULL if eout is None else eout,
                                        env=dict(env), start_new_session=True, cwd=cwd)
                live[key] = {"proc": proc, "fd": fd, "chunks": [], "size": 0, "open": True,
                             "end": end, "efd": efd, "err": b""}
            except (OSError, ValueError):
                os.close(fd)
                if efd is not None:
                    os.close(efd)
                    errs[key] = b""
                finish(key, (None, b"", "unreadable"))
                continue
            finally:
                os.close(out)
                if eout is not None:
                    os.close(eout)
            os.set_blocking(fd, False)
            if efd is not None:
                os.set_blocking(efd, False)
        now = time.monotonic()
        for key, job in list(live.items()):
            if job["end"] is not None and job["end"] <= now and walls is not None:
                _end(job)
                _reap(job["proc"])
                del live[key]
                _keep_err(job, key, errs)
                finish(key, (None, b"", "timed out"))
        if queue:
            continue
        ends = [job["end"] for job in live.values() if job["end"] is not None]
        left = (min(ends) if ends else now) - now
        if not live or left <= 0:
            break
        fds = {job["fd"]: key for key, job in live.items() if job["open"]}
        efds = {job["efd"]: key for key, job in live.items() if job["efd"] is not None}
        try:
            ready = select.select(list(fds) + list(efds), [], [], min(left, POLL))[0] \
                if fds or efds else ()
        except (OSError, ValueError):
            ready = list(fds) + list(efds)
        if not fds and not efds:
            time.sleep(min(left, POLL))
        for fd in ready:
            if fd in efds:
                _drain_err(live[efds[fd]])
                continue
            job = live[fds[fd]]
            if _drain(job) != "open":
                job["open"] = False
        for key, job in list(live.items()):
            proc = job["proc"]
            over = job["size"] > CAP
            if not over and proc.poll() is None:
                continue
            if not over and job["open"]:
                over = _drain(job) == "cap"
            _drain_err(job)
            _end(job)
            _reap(proc)
            del live[key]
            _keep_err(job, key, errs)
            finish(key, (None, b"", "unreadable") if over
                   else (proc.returncode, b"".join(job["chunks"]), "ran"))


def _drain_err(job):
    """Keep what the stderr pipe holds now, up to ERR_CAP bytes; read past it and drop it."""
    while job["efd"] is not None:
        try:
            data = os.read(job["efd"], 65536)
        except BlockingIOError:
            return
        except OSError:
            data = b""
        if not data:
            os.close(job["efd"])
            job["efd"] = None
            return
        job["err"] = (job["err"] + data)[:ERR_CAP]


def _keep_err(job, key, errs):
    if job["efd"] is not None:
        try:
            os.close(job["efd"])
        except OSError:
            pass
        job["efd"] = None
    if errs is not None:
        errs[key] = job["err"]


def _object(code, out, pattern):
    """The answer's object when it counts, else None."""
    if code != 0:
        return None
    try:
        obj = json.loads(out.decode("utf-8", "replace"))
    except (ValueError, RecursionError):
        return None
    if not isinstance(obj, dict) or obj.get("ok") is not True:
        return None
    m = pattern.match(obj.get("schema") if isinstance(obj.get("schema"), str) else "")
    if not m or int(m.group(1)) > 1:
        return None
    return obj


def counted_describe(code, out, name):
    """The answer when it counts, asked under `name`: one whose `tool` is that name (row ak9b R3)."""
    obj = _described(code, out)
    return obj if obj is not None and obj.get("tool") == name else None


def describe_reason(code, out, name):
    """None for an answer that counts; `other` for one that would count under another tool's
    name; `unread` for one that does not read, or whose `tool` is no string (R3, review 1)."""
    obj = _described(code, out)
    if obj is None or not isinstance(obj.get("tool"), str):
        return "unread"
    return None if obj.get("tool") == name else "other"


def one_line(text, cap=LINE_CAP):
    """A tool's text as one line (R4): term.clean's cleaning, a summary's, then cut at `cap`."""
    from . import term
    return term.clean(text).strip()[:cap]


def plain(text):
    """The text where it is a string that holds no control character, a newline, a tab or a
    direction control among them, and no character of Unicode category Cf (format: a direction
    mark, a zero-width character, a soft hyphen) or Cs (a lone surrogate), else None: a remedy
    that would join a second line of the tool's to a line a person pastes, or hold a mark the
    person cannot see, is no remedy (row ak9b review 1 lead 2, review 2 F2)."""
    from . import term
    if not isinstance(text, str) or term.clean(text) != text:
        return None
    return None if any(unicodedata.category(c) in ("Cf", "Cs") for c in text) else text


def config_error(out):
    """{code, message, remedy} of a config read's counted error (R4), whatever the exit, else None:
    one object of the config schema, `ok` false, an `error` whose code and message are strings and
    whose remedy is a string or null; a remedy that is not `plain` reads as null (lead 2), and one
    is never cut: past `LINE_CAP` with its outer spaces gone, it reads as null (review 2 F3)."""
    try:
        obj = json.loads(out.decode("utf-8", "replace"))
    except (ValueError, RecursionError):
        return None
    if not isinstance(obj, dict) or obj.get("ok") is not False:
        return None
    m = CONFIG.match(obj.get("schema") if isinstance(obj.get("schema"), str) else "")
    error = obj.get("error")
    if not m or int(m.group(1)) > 1 or not isinstance(error, dict):
        return None
    code, message, remedy = error.get("code"), error.get("message"), error.get("remedy")
    if not (isinstance(code, str) and isinstance(message, str) and (remedy is None or isinstance(remedy, str))):
        return None
    remedy = plain(remedy).strip() if plain(remedy) is not None else None
    return {"code": one_line(code), "message": one_line(message),
            "remedy": remedy if remedy is not None and len(remedy) <= LINE_CAP else None}


def _described(code, out):
    obj = _object(code, out, DESCRIBE)
    if obj is None or any(k not in obj for k in DESCRIBE_KEYS):
        return None
    if not all(isinstance(obj[k], list) for k in ("needs", "verbs", "reads")):
        return None
    kinds = []
    for read in obj["reads"]:
        if not (isinstance(read, dict) and read.get("kind") in READ_KINDS
                and isinstance(read.get("argv"), list)
                and all(isinstance(w, str) for w in read["argv"])):
            return None
        kinds.append(read["kind"])
    if kinds.count("config") > 1 or kinds.count("doctor") > 1:
        return None
    return obj


def counted_config(code, out):
    obj = _object(code, out, CONFIG)
    if obj is None or not isinstance(obj.get("layers"), list) or not isinstance(obj.get("settings"), list):
        return None
    layers = [l for l in obj["layers"] if isinstance(l, dict)]
    settings = []
    for s in obj["settings"]:
        if not (isinstance(s, dict) and isinstance(s.get("key"), str) and s["key"]):
            return None
        s = dict(s)
        for k in ("source", "change"):
            s[k] = s.get(k) if isinstance(s.get(k), dict) else {}
        s["values"] = [v for v in s.get("values") or [] if isinstance(v, dict)] \
            if isinstance(s.get("values"), list) else []
        if not isinstance(s.get("choices"), list):
            s["choices"] = None
        settings.append(s)
    obj = dict(obj, layers=layers, settings=settings)
    warnings = obj.get("warnings")
    obj["warnings"] = [w for w in warnings if isinstance(w, dict)] if isinstance(warnings, list) else []
    return obj


# ---- the describe cache ---------------------------------------------------------------------

def cache_dir(env):
    base = env.get("XDG_CACHE_HOME") or os.path.join(env.get("HOME") or "", ".cache")
    return os.path.join(base, "agentik", "suite")


def _stamp(exe):
    real = os.path.realpath(exe)
    st = os.stat(real)
    return {"path": real, "size": st.st_size, "mtime_ns": st.st_mtime_ns}


def _cached(folder, name, stamp):
    found = plan._read_json(os.path.join(folder, name + ".json"))
    if isinstance(found, dict) and found.get("stamp") == stamp:
        return counted_describe(0, json.dumps(found.get("answer")).encode(), name)
    return None


def cached(name, exe, env):
    """The counted describe of `name` in the cache whose stamp matches `exe`, else None: a stat and
    a read, no process (row ak12-polish R3)."""
    try:
        stamp = _stamp(exe)
    except OSError:
        return None
    return _cached(cache_dir(env), name, stamp)


def _keep(folder, name, stamp, answer):
    """Written by a rename, so a reader sees the old file or the new one; a failure keeps none."""
    try:
        os.makedirs(folder, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=folder, prefix="." + name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump({"stamp": stamp, "answer": answer}, fh)
            os.replace(tmp, os.path.join(folder, name + ".json"))
        except (OSError, ValueError, TypeError):
            os.unlink(tmp)
    except OSError:
        pass


def describe_all(entries, env, read=False, key=None, deadline=None, reasons=None):
    """({name: (state, answer or None)}, {name: (exit, stdout, state)}) for each entry with an
    executable. With `read`, each answer's config read, `key` appended when given, starts as soon
    as the answer is known, from the cache or its describe, under the describes' own deadline.
    `reasons`, when given, gets {name: describe_reason} for each describe that ran and did not
    count (row ak9b R3)."""
    folder, found, jobs, stamps = cache_dir(env), {}, [], {}
    exes = {e["name"]: e["exe"] for e in entries}

    def config_job(name, answer):
        r = config_read(answer) if read else None
        return [(("config", name), [exes[name]] + r["argv"] + ([key] if key is not None else []))] \
            if r else []

    for e in entries:
        try:
            stamps[e["name"]] = _stamp(e["exe"])
        except OSError:
            found[e["name"]] = ("unreadable", None)
            continue
        answer = _cached(folder, e["name"], stamps[e["name"]])
        if answer is not None:
            found[e["name"]] = ("answers", answer)
            jobs.extend(config_job(e["name"], answer))
        else:
            jobs.append((("describe", e["name"]), [e["exe"], "describe", "--json"]))

    def then(job, result):
        kind, name = job
        if kind != "describe":
            return []
        code, out, state = result
        answer = counted_describe(code, out, name) if state == "ran" else None
        if answer is None and state == "ran" and reasons is not None:
            reasons[name] = describe_reason(code, out, name)
        if answer is None:
            found[name] = ("timed out" if state == "timed out" else "unreadable", None)
            return []
        _keep(folder, name, stamps[name], answer)
        found[name] = ("answers", answer)
        return config_job(name, answer)

    ran = run_all(jobs, env, then=then, deadline=deadline)
    for (kind, name), (_, _, state) in ran.items():
        if kind == "describe" and name not in found:  # still running at the deadline
            found[name] = ("timed out" if state == "timed out" else "unreadable", None)
    return found, {name: result for (kind, name), result in ran.items() if kind == "config"}


def claims(entries, described, kept_out, kept):
    """[{tool, verb, counts, reason}]: each `{"name": W, "top": true}` of each entry's counted
    describe in `described` (describe_all's first value), in the list's order (row ak9c R2). The
    claim counts (reason null) where W is not in `kept_out` (the suite's verbs and the doctor's
    reserved words), where `kept` ({word: tool or None}) keeps W for the claimant alone, and where
    the tool's standing source is the finder's kind `own` with a file that runs. Else the reason is
    `suite` (the suite keeps W, for itself or for no tool yet), `kept` (for another tool) or
    `market` (the tool is not from the agentik marketplace). An entry is listed's, never the suite's.
    A tool claims a word once however often its describe lists it (review 1 F1)."""
    found, seen = [], set()
    for e in entries:
        answer = described.get(e["name"], (None, None))[1]
        for v in (answer or {}).get("verbs") or ():
            if not (isinstance(v, dict) and v.get("top") is True and isinstance(v.get("name"), str)
                    and NAME.match(v["name"])) or (e["name"], v["name"]) in seen:
                continue
            seen.add((e["name"], v["name"]))
            word, source = v["name"], e.get("source") or {}
            if word in kept_out or (word in kept and kept[word] is None):
                reason = "suite"
            elif word in kept and kept[word] != e["name"]:
                reason = "kept"
            elif source.get("kind") != "own" or not e.get("exe"):
                reason = "market"
            else:
                reason = None
            found.append({"tool": e["name"], "verb": word, "counts": reason is None, "reason": reason})
    return found


def kept(lib, words):
    """{word: tool or None} for each of `words` (cli.KEPT): the tool `kept.json`, beside the
    package, names for it, so no tool's name stands in the package; None where it names none or
    does not read, and no claim of that word counts (row ak9c R2)."""
    found = plan._read_json(os.path.join(_lib(lib), "kept.json"))
    found = found if isinstance(found, dict) else {}
    return {w: found[w] if isinstance(found.get(w), str) and NAME.match(found[w]) else None for w in words}


def config_read(answer):
    for read in answer.get("reads") or ():
        if read.get("kind") == "config":
            return read
    return None


# ---- what the suite knows before a tool is installed (public.json) ---------------------------

PUBLIC = "public.json"
SUITE_KEY = "suite"  # public.json's own row, the suite, which is no tool it plans as one


def public(lib):
    """public.json beside the package, read leniently: {"tools": {name: OWNER/REPO}, "needs":
    {name: [word]}, "own_command": [name], "reads": {name: [status read name]}}, each part empty
    where the file lacks it or holds another shape (row ak10c5-table-gone R4, review 1 F2); the
    issue's strict read is gather.load_public."""
    found = plan._read_json(os.path.join(_lib(lib), PUBLIC))
    found = found if isinstance(found, dict) else {}
    repos = found.get("tools") if isinstance(found.get("tools"), dict) else {}
    needs = found.get("needs") if isinstance(found.get("needs"), dict) else {}
    own = found.get("own_command") if isinstance(found.get("own_command"), list) else []
    reads = found.get("reads") if isinstance(found.get("reads"), dict) else {}
    return {"tools": {k: v for k, v in repos.items() if isinstance(v, str) and k != SUITE_KEY},
            "needs": {k: [w for w in v if isinstance(w, str)] for k, v in needs.items()
                      if isinstance(v, list)},
            "own_command": [n for n in own if isinstance(n, str)],
            "reads": {k: [w for w in v if isinstance(w, str)] for k, v in reads.items()
                      if isinstance(v, list)}}


def page(lib, name):
    """The page of a tool that installs its own command (row fh13 R1, ak10c5 R4):
    `https://github.com/<repo>#install` for a name public.json's `own_command` lists, built from
    the repo it names there; else None. A repo of OWNER/REPO whose page holds no whitespace and no
    character that is not printable (a control or format one); never opened (row fh13 review 1)."""
    found = public(lib)
    repo = found["tools"].get(name) if name in found["own_command"] else None
    if not (isinstance(repo, str) and re.match(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z", repo)):
        return None
    value = "https://github.com/%s#install" % repo
    return value if value.isprintable() and not any(c.isspace() for c in value) else None


def answered(env, rows_, deadline=None, read=False):
    """({name: counted describe answer}, {name: config result}, [name that gave none]) for each
    finder row in `rows_` ({name: row}) whose file runs: the cache first, else its describe, under
    the describes' wall (row ak10c5 R5, R6). A name whose file does not run is in no part."""
    entries = [{"name": n, "exe": r["runs"]["path"]} for n, r in sorted(rows_.items())
               if isinstance(r.get("runs"), dict) and r["runs"].get("path")]
    if not entries:
        return {}, {}, []
    found, configs = describe_all(entries, env, read=read,
                                  deadline=deadline if deadline is not None else time.monotonic() + WALL)
    answers = {n: a for n, (state, a) in found.items() if state == "answers" and a is not None}
    return answers, configs, [e["name"] for e in entries if e["name"] not in answers]


def user_layer(cfg):
    """The path of the first `user` layer of a config answer, or None (GUIDE §11.4)."""
    for layer in (cfg or {}).get("layers") or ():
        if isinstance(layer, dict) and layer.get("name") == "user" and isinstance(layer.get("path"), str):
            return layer["path"]
    return None


def descriptions(env):
    """{plugin name: description} from the agentik marketplace's own file."""
    known = plan._read_json(os.path.join(_config_dir(env), "plugins", "known_marketplaces.json"))
    entry = known.get(plan.MARKETPLACE) if isinstance(known, dict) else None
    where = entry.get("installLocation") if isinstance(entry, dict) else None
    if not isinstance(where, str):
        return {}
    market = plan._read_json(os.path.join(where, ".claude-plugin", "marketplace.json"))
    plugins = market.get("plugins") if isinstance(market, dict) else None
    return {p["name"]: p["description"] for p in plugins or ()
            if isinstance(p, dict) and isinstance(p.get("name"), str)
            and isinstance(p.get("description"), str)}
