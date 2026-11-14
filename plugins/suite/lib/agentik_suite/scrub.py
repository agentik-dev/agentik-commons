"""The reporter's layer 1 (hq design/22 §3 item 4): what leaves a free value before it is a
draft, and the detector the last scan runs over the exact bytes.

`machine` reads this machine's own names when it is called and writes them nowhere. `scrub`
replaces what is private with a placeholder of a closed set and applies a pass to its own output
until a pass changes nothing; `detect` names the kinds a pass would still replace; `strike` is the
user's own removal; `clean` takes out what a terminal does not draw as itself. Nothing here prints
or writes a file, and a private row is held behind a repr that only counts it, so its term is in
no return value and no message.

Inside a pass a placeholder is a sealed character of plane 15's private use area: `clean`
removes that category, so text never holds one, and no rule reads one. A kept span (a public
repo's URL path, a path of 4(b)'s closed list) is held between two marks of plane 16 instead: the
path and long-run steps, which would replace it, pass over it, and every other step reads it.
"""
import os
import re
import subprocess
import unicodedata

import agentik_hygiene

from . import settings

NUMBERED = ("path", "email", "address", "private", "struck", "name", "url", "site", "run")
SINGLE = ("user", "host", "repo", "project", "secret")
KINDS = NUMBERED + SINGLE
PH = re.compile(r"<(?:(%s)-([1-9][0-9]*)|(%s))>" % ("|".join(NUMBERED), "|".join(SINGLE)))
STRUCK = re.compile(r"<struck-([1-9][0-9]*)>")
BASE = 0xF0000
SENT = "\U000F0000-\U000FFFFD"
SEALED = re.compile("[%s]" % SENT)
OPEN, CLOSE = "\U0010FFFC", "\U0010FFFD"
STOP = SENT + OPEN + CLOSE
KEPT = re.compile("%s[^%s]*%s" % (OPEN, CLOSE, CLOSE))
LIMIT = 32

# The public words beside the public table's names: the suite's verbs and 4(b)'s twelve programs.
# A caller extends either through `public["verbs"]` and `public["programs"]`.
VERBS = ("help", "version", "setup", "config", "describe", "status", "install-cli", "doctor",
         "issue", "new", "show", "strike", "drop", "edit", "reword", "send", "discard")
PROGRAMS = ("claude", "git", "gh", "python3", "python", "sh", "bash", "zsh", "env", "ps", "make",
            "uname")
SECRET_VARS = ("TOKEN", "KEY", "SECRET", "PASS", "AUTH", "CREDENTIAL")
GROUPS = {"home": "path", "lan": "address", "secret": "secret", "email": "email"}
# A character each pattern of a group holds today: a text without it skips the group, since the
# scanner's `email` and `lan` patterns start at every `\b` and read a long dashed or dotted run
# once from each of its letters.
NEEDS = {"email": "@", "lan": "."}
BIN_DIRS = ("/usr/bin", "/bin", "/usr/sbin", "/sbin", "/usr/local/bin", "/opt/homebrew/bin")
SYSTEM_PREFIXES = ("/System/Volumes/Data", "/private")
REPO_FILES = (".claude/agentik/config.yaml", ".claude/settings.json", ".claude/settings.local.json")
# 4(b)'s prose pairs: a word, a slash and a word that is no path.
PAIRS = frozenset(("and/or", "either/or", "read/write", "input/output", "in/out", "on/off", "yes/no",
                   "true/false", "open/close", "start/stop", "get/set", "push/pull", "up/down",
                   "before/after", "send/receive", "request/response", "key/value",
                   "client/server", "his/her", "he/she", "w/o", "n/a", "i/o"))
# 4(b)'s plain words: a word that follows a path in a tool's line ends the path's reach.
PLAIN = frozenset("""
a an the is are was were be been being not no nor does do did done has have had line lines col
column row failed fails failing error errors exists exist missing found denied refused already
cannot could would should will may might must can at in on of for to from with without by as and
or but if then than when while because which that this it its into onto via since until after
before so too also exited exit returned says said holds gives read written wrote opened open
closed ok skipped ignored unreadable empty invalid permission directory folder file repository
there here yet still now
""".split())
# 4(c)'s top-level and internal suffixes of a site; no file's extension is among them.
SUFFIXES = ("com", "net", "org", "io", "dev", "ai", "co", "uk", "de", "fr", "nl", "eu", "us", "ca",
            "au", "jp", "cn", "ru", "ch", "se", "info", "biz", "me", "tv", "cloud", "xyz", "tech",
            "site", "online", "local", "lan", "internal", "corp", "intranet", "gov")

ESCAPES = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]"
                     r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)?"
                     r"|\x1b[PX^_][^\x1b]*(?:\x1b\\)?"
                     r"|\x1b[ -/]*[0-~]"
                     r"|\x9b[0-?]*[ -/]*[@-~]")
BLANKS = frozenset([0x115F, 0x1160, 0x3164, 0xFFA0, 0x2800] + list(range(0xFE00, 0xFE10))
                   + list(range(0xE0100, 0xE01F0)))
BREAKS = frozenset("  \u0085")
DROP = frozenset(("Cc", "Cf", "Cs", "Co", "Cn"))
PERCENT = re.compile(r"%(2[0-9A-Fa-f]|[3-6][0-9A-Fa-f]|7[0-9A-Ea-e])")

BEGIN = re.compile(r"-----BEGIN [A-Z0-9 ]+-----")
END = re.compile(r"-----END [A-Z0-9 ]+-----")
B64 = re.compile(r"[ \t]*([A-Za-z0-9+/]{4,}={0,2})[ \t]*\Z")
LONG64 = re.compile(r"(?=[^0-9]*[0-9])(?=[^a-z]*[a-z])(?=[^A-Z]*[A-Z])[A-Za-z0-9+/]{32,}={0,2}\Z")
HEADER = re.compile(r"[A-Za-z-]+: \S")

URL = re.compile(r"(?<![A-Za-z0-9+.-])([A-Za-z][A-Za-z0-9+.-]{1,15})://[^\s<>\"'`%s]+" % STOP)
SCP = re.compile(r"(?<![\w.@+-])[\w.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*:(?!//)"
                 r"(?![0-9]+(?:[^\w/]|\Z))[^\s<>\"'`%s]*[\w/~-]" % STOP)
TRAIL = ".,;:!?)]}'\""
EMAIL_CORE = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"
NAMED = re.compile(r"(?:(?<![\w.'-])\"?((?:[^\W\d_][\w.'-]*[ \t]+){0,3}[^\W\d_][\w.'-]*)\"?[ \t]*)?"
                   r"<[ \t]*(" + EMAIL_CORE + r")[ \t]*>")
EMAIL = re.compile(r"(?<![\w.%+-])" + EMAIL_CORE + r"(?![\w-])")

RUN = re.compile(r"[^\s\"'`<>()\[\]{},;:|=*?\\%s]+" % STOP)
WORD = re.compile(r"[^ \t\n]+")
ANCHOR = re.compile(r"(?:~|\.\.?)?/")
HARD = re.compile(r"[:,;()\[\]{}<>\"'`%s]" % STOP)
DIGITS = re.compile(r"\d+(?:/\d+)+/?\Z")
SCHEMA = re.compile(r"agentik[.-][a-z][a-z0-9_.-]*/\d+\Z")
VERSION = re.compile(r"(?:\d+(?:\.\d+){2,}(?:[+-]\d+(?:\.\d+)*)?|[0-9a-f]{7,40})\Z")
HASH = re.compile(r"[0-9a-f]{7,64}\Z")

SECRET_NAME = (r"[A-Za-z0-9_.-]*(?:password|passphrase|secret|token|api[_-]?key|credential"
               r"|access[_-]?key|private[_-]?key)[A-Za-z0-9_.-]*")
VALUE = r"(?:\"([^\"\n%s]*)\"|'([^'\n%s]*)'|([^\s\"',;%s]+))" % (STOP, STOP, STOP)
ASSIGN = re.compile(r"(?<![A-Za-z0-9_.-])%s[\"']?[ \t]*[:=][ \t]*%s" % (SECRET_NAME, VALUE), re.I)
FLAG = re.compile(r"(?<!\S)--?%s[ \t]+%s" % (SECRET_NAME, VALUE), re.I)
NUMBER = re.compile(r"[+-]?\d+(?:\.\d+)?\Z")
BEARER = re.compile(r"\b(?:Bearer|Basic)[ \t]+([^\s\"',;%s]{8,})" % STOP)

V6 = re.compile(r"(?<![\w:.])[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7}(?![\w:])")
MAC = re.compile(r"(?<![\w:-])[0-9A-Fa-f]{2}([:-])[0-9A-Fa-f]{2}(?:\1[0-9A-Fa-f]{2}){4}(?![\w:-])")
OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
QUAD = re.compile(r"(?<![\w.])(?:%s\.){3}%s(?!\w|\.\d)" % (OCTET, OCTET))
SITE = re.compile(r"(?<![\w.-])(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+(?:%s)"
                  r"(?![\w-]|\.[A-Za-z0-9])" % "|".join(SUFFIXES), re.I)
RUNS = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/=_-]{32,}(?![A-Za-z0-9+/=_-])")
SEGMENT_RUNS = re.compile(r"(?<![A-Za-z0-9+=_-])[A-Za-z0-9+=_-]{32,}(?![A-Za-z0-9+=_-])")
LAN_REACH = re.compile(r"[A-Za-z0-9.-]")
HOME_REACH = re.compile(r"[^\s\"'`<>()\[\]{},;:|=*?\\%s]" % STOP)

DOTTED = re.compile(r"(?<![\w.-])[A-Za-z][\w-]*(?:\.[A-Za-z][\w-]*){2,}(?![\w-]|\.[A-Za-z])")
HANDLE = re.compile(r"(?<![\w.])@[A-Za-z][\w-]*")
LETTER = re.compile(r"[^\W\d_]")
L = r"[^\W\d_]"


class PrivateUnreadable(Exception):
    """The private list exists and cannot be read: the caller sends nothing (exit 2)."""


class _Hidden(list):
    """A list whose repr counts its items, so a private row's term reaches no message."""

    def __repr__(self):
        return "<%d hidden>" % len(self)

    __str__ = __repr__


def _chars(text):
    out = []
    for ch in text:
        if ch == "\n":
            out.append(ch)
        elif ch == "\t":
            out.append(" ")
        elif ch in BREAKS:
            out.append("\n")
        elif ord(ch) in BLANKS:
            continue
        else:
            cat = unicodedata.category(ch)
            if cat in DROP:
                continue
            out.append(" " if cat == "Zs" else ch)
    return "".join(out)


def clean(text):
    """4(e): each escape sequence whole; a carriage return to a line break, a tab to a space; each
    other control, format, surrogate, private and unassigned character and the blank letters out;
    a line or paragraph separator to a line break, any other space to a space; then NFKC."""
    text = ESCAPES.sub("", text).replace("\r\n", "\n").replace("\r", "\n")
    for _ in range(LIMIT):
        new = unicodedata.normalize("NFKC", _chars(text))
        if new == text:
            break
        text = new
    return text


def _decode(text):
    for _ in range(LIMIT):
        new = PERCENT.sub(lambda mt: chr(int(mt.group(1), 16)), text)
        if new == text:
            break
        text = new
    return text


def _alts(values):
    return "|".join(re.escape(v) for v in sorted(set(values), key=lambda v: (-len(v), v)))


def _homes(home):
    """The home folder's spellings, lowercased, longest first: as given and by its real path, each
    also under the two system prefixes."""
    if not home or home.rstrip("/") == "":
        return []
    bare = {home.rstrip("/"), os.path.realpath(home).rstrip("/")}
    out = set()
    for h in bare:
        out.add(h)
        out.update(prefix + h for prefix in SYSTEM_PREFIXES)
    return sorted({h.lower() for h in out}, key=lambda h: (-len(h), h))


def build(public, home=None, logins=(), hosts=(), names=(), emails=(), repos=(), checkouts=(),
          secrets=(), private="none"):
    """A machine from its values: what `machine` reads, and what a test makes by hand."""
    tools = {str(t): str(w) for t, w in (public.get("tools") or {}).items()}
    market = str(public.get("marketplace") or "")
    words = set(KINDS) | {"agentik"} | set(VERBS) | set(PROGRAMS)
    words |= {str(w).lower() for w in tuple(public.get("verbs") or ()) + tuple(public.get("programs") or ())}
    if market:
        words.add(market.lower())
    for tool, where in tools.items():
        owner, _, repo = where.partition("/")
        words |= {tool.lower(), "agentik-" + tool.lower(), owner.lower(), repo.lower()}
    words.discard("")
    homes = _homes(home)
    m = {"public": public, "words": frozenset(words), "_homes": homes,
         "_pairs": frozenset(w.lower() for w in tools.values()),
         "_tools": frozenset(tools), "_market": market,
         "secrets": _Hidden(s for s in secrets if s and len(s.encode("utf-8", "replace")) >= 8),
         "private": private if private == "none" else _Hidden(private),
         "_groups": [(g, rx) for g, rx in agentik_hygiene.COMPILED if g in GROUPS]}
    m["_secrets"] = re.compile(_alts(m["secrets"]), re.I) if m["secrets"] else None
    dashed = sorted({re.sub(r"[^A-Za-z0-9]", "-", h) for h in homes if not h.startswith(SYSTEM_PREFIXES[0].lower())})
    m["_dashed"] = (re.compile(r"(?<![A-Za-z0-9])(?:%s)(?![A-Za-z0-9])[^\s\"'`%s]*" % (_alts(dashed), STOP), re.I)
                    if dashed else None)
    fixed = {"~/.local/bin", "~/.local/bin/agentik", "~/.claude/plugins/installed_plugins.json",
             "~/.config/agentik", "~/.config/agentik/hygiene-private.tsv", "~/.cache/agentik",
             "/dev/null", "/dev/tty", "/tmp"} | set(REPO_FILES)
    for d in BIN_DIRS:
        fixed.add(d)
        fixed.update(d + "/" + p for p in PROGRAMS)
    heads = []
    for tool in tools:
        fixed |= {"~/.local/bin/agentik-" + tool, "~/.config/agentik/" + tool,
                  "~/.config/agentik/%s/config.yaml" % tool, "~/.cache/agentik/" + tool,
                  "~/.local/state/agentik-" + tool}
        heads += [["~", ".config", "agentik", tool], ["~", ".cache", "agentik", tool],
                  ["~", ".local", "state", "agentik-" + tool]]
    m["_fixed"], m["_heads"] = frozenset(fixed), heads
    alts = "|".join(re.escape(w) for w in sorted(m["_pairs"]))
    m["_github"] = (re.compile(r"(https://github\.com/(?:%s)(?:\.git)?)([/#?]\S*)?\Z" % alts, re.I)
                    if alts else None)
    m["_checkouts"] = frozenset(_norm(m, c).lower().rstrip("/") for c in checkouts if c)
    repos = list(repos) + [os.path.basename(c.rstrip("/")) for c in checkouts if c]
    named = ([(v, "user") for v in logins] + [(v, "host") for v in hosts]
             + [(v, "name") for v in names] + [(v, "email") for v in emails]
             + [(v, "repo") for v in repos])
    named = [(v.strip(), k) for v, k in named if v and len(v.strip()) >= 3]
    kinds = {}
    for v, k in named:
        kinds.setdefault(v.lower(), k)
    m["_kinds"] = kinds
    inner = [v for v in kinds if v not in words]
    plain = [v for v in kinds if v in words]
    m["weak"] = sorted({kinds[v] for v in plain})
    m["_names"] = (re.compile(r"(?<!%s)(?:%s)(?!%s)" % (L, _alts(inner), L), re.I) if inner else None)
    m["_inner"] = re.compile(_alts(inner), re.I) if inner else None
    a = _alts(plain)
    m["_at"] = (re.compile(r"(?<=@)(?:%s)(?!%s)|(?<!%s)(?:%s)(?=@)" % (a, L, L, a), re.I)
                if plain else None)
    return m


def _git(env, key):
    try:
        out = subprocess.check_output(["git", "config", "--global", key], env=env,
                                      stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.decode("utf-8", "replace").strip()


def _root(cwd):
    if not cwd:
        return None
    here = os.path.abspath(cwd)
    while True:
        if os.path.exists(os.path.join(here, ".git")):
            return here
        up = os.path.dirname(here)
        if up == here:
            return None
        here = up


def _private(env, home):
    """The private list's rows, its path found from `env` by the scanner's rule; "none" when it
    does not exist. Raised outside the handler, so no exception's context holds the file."""
    base = env.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
    path = env.get(agentik_hygiene.PRIVATE_ENV) or os.path.join(base, agentik_hygiene.PRIVATE_NAME)
    if not os.path.lexists(path):
        return "none"
    rows, failed = None, False
    try:
        with open(path, encoding="utf-8") as fh:
            fh.read()
        rows = agentik_hygiene.load_private(path, False)
    except Exception:
        failed = True
    if failed:
        raise PrivateUnreadable("the private list exists and cannot be read")
    return rows


def machine(env, cwd, public, logins=()):
    """This machine's names, read now and written nowhere (4(a), 4(c), item 13)."""
    home = env.get("HOME") or os.path.expanduser("~")
    users = [env.get("USER") or "", env.get("LOGNAME") or "", os.path.basename(home.rstrip("/"))]
    if not env.get("USER") and not env.get("LOGNAME"):
        try:
            users.append(os.getlogin())
        except OSError:
            pass
    node = os.uname().nodename
    checkouts = []
    root = _root(cwd)
    if root:
        checkouts.append(root)
    try:
        _, tree, _ = settings.read(settings.user_path(env))
    except settings.Fault:
        tree = {}
    listed = tree.get("checkouts") if isinstance(tree, dict) else None
    for c in listed if isinstance(listed, list) else []:
        if isinstance(c, str) and c.strip():
            c = c.strip()
            checkouts.append(home if c == "~" else os.path.join(home, c[2:]) if c.startswith("~/") else c)
    secrets = [v for k, v in env.items() if any(w in k.upper() for w in SECRET_VARS)]
    return build(public, home=home, logins=users + list(logins), hosts=[node, node.split(".")[0]],
                 names=[_git(env, "user.name")], emails=[_git(env, "user.email")],
                 checkouts=checkouts, secrets=secrets, private=_private(env, home))


def weak(m):
    """The kinds of machine name that are public words here, for the caller's one line."""
    return list(m["weak"])


def _norm(m, run):
    """A path with its home folder, in any case and spelling, as `~`."""
    p = re.sub(r"/{2,}", "/", run)
    low = p.lower()
    for h in m["_homes"]:
        if low == h or low.startswith(h + "/"):
            return "~" + p[len(h):]
    return p


class _State:
    def __init__(self):
        self.top = dict.fromkeys(NUMBERED, 0)
        self.values = {}
        self.counts = {}


class _Pass:
    def __init__(self, m, state):
        self.m, self.st, self.seals, self.kinds = m, state, [], set()

    def seal(self, text):
        self.seals.append(text)
        return chr(BASE + len(self.seals) - 1)

    def hold(self, s):
        """Each kept span sealed for a step that must pass over it; `held` restores them."""
        held = {}

        def one(mt):
            c = self.seal(mt.group())
            held[c] = mt.group()
            return c
        return KEPT.sub(one, s), held

    @staticmethod
    def held(s, held):
        if not held:
            return s
        return re.sub("[%s]" % "".join(held), lambda mt: held[mt.group()], s)

    def note(self, kind):
        self.kinds.add(kind)
        self.st.counts[kind] = self.st.counts.get(kind, 0) + 1

    def put(self, kind, value):
        key = (kind, value.lower())
        ph = self.st.values.get(key)
        if ph is None:
            if kind in SINGLE:
                ph = "<%s>" % kind
            else:
                self.st.top[kind] += 1
                ph = "<%s-%d>" % (kind, self.st.top[kind])
            self.st.values[key] = ph
        self.note(kind)
        return self.seal(ph)

    def unseal(self, s):
        return SEALED.sub(lambda mt: self.seals[ord(mt.group()) - BASE], s)

    def _existing(self, mt):
        if mt.group(1):
            self.st.top[mt.group(1)] = max(self.st.top[mt.group(1)], int(mt.group(2)))
        return self.seal(mt.group())

    def run(self, text):
        t = clean(text)
        if t != text:
            self.kinds.add("control")
        d = _decode(t)
        if d != t:
            self.kinds.add("encoded")
        s = PH.sub(self._existing, d)
        for step in (self._named, self._keys, self._urls, self._emails, self._paths, self._assign,
                     self._names, self._groups, self._private, self._addresses, self._sites,
                     self._runs):
            s = step(s)
        return s.replace(OPEN, "").replace(CLOSE, "")

    # the steps of a pass, in R3's order

    def _named(self, s):
        rx = self.m["_secrets"]
        return rx.sub(lambda mt: self.put("secret", mt.group()), s) if rx else s

    def _keys(self, s):
        lines, out, i = s.split("\n"), [], 0
        while i < len(lines):
            line = lines[i]
            b = BEGIN.search(line)
            if b:
                j = last = i
                while j + 1 < len(lines) and (B64.match(lines[j + 1]) or HEADER.match(lines[j + 1])
                                              or not lines[j + 1].strip()):
                    j += 1
                    if lines[j].strip():
                        last = j
                tail = ""
                if last + 1 < len(lines) and END.search(lines[last + 1]):
                    last += 1
                    tail = lines[last][END.search(lines[last]).end():]
                value = "\n".join(lines[i:last + 1])
                out.append(line[:b.start()] + self.put("secret", value) + tail)
                i = last + 1
                continue
            stripped = line.strip()
            if LONG64.match(stripped):
                width, j = len(stripped), i
                while j + 1 < len(lines) and len(lines[j + 1].strip()) == width and B64.match(lines[j + 1]):
                    j += 1
                nxt = lines[j + 1].strip() if j + 1 < len(lines) else ""
                after = lines[j + 2].strip() if j + 2 < len(lines) else ""
                if (nxt and len(nxt) < width and B64.match(nxt)
                        and (nxt.endswith("=") or re.search(r"[0-9]", nxt) or END.match(after))):
                    j += 1
                if j + 1 < len(lines) and END.match(lines[j + 1].strip()):
                    j += 1
                if j - i + 1 >= 3:
                    out.append(self.put("secret", "\n".join(lines[i:j + 1])))
                    i = j + 1
                    continue
            out.append(line)
            i += 1
        return "\n".join(out)

    def _urls(self, s):
        def url(mt):
            if mt.group(1).lower() == "file":
                return mt.group()
            cut = mt.group().rstrip(TRAIL)
            rest = mt.group()[len(cut):]
            gh = self.m["_github"] and self.m["_github"].match(cut)
            if gh:
                tail = gh.group(2) or ""
                k = len(re.match(r"[^?#]*", tail).group())
                return self.seal(gh.group(1)) + (OPEN + tail[:k] + CLOSE if k else "") + tail[k:] + rest
            return self.put("url", cut) + rest
        s = URL.sub(url, s)
        return SCP.sub(lambda mt: self.put("url", mt.group()), s)

    def _emails(self, s):
        def named(mt):
            mail = self.put("email", mt.group(2))
            return self.put("name", mt.group(1)) + " " + mail if mt.group(1) else mail
        s = NAMED.sub(named, s)
        return EMAIL.sub(lambda mt: self.put("email", mt.group()), s)

    def _paths(self, s):
        s, held = self.hold(s)
        s = self._paths_outside(s)
        return self.held(s, held)

    def _paths_outside(self, s):
        rx = self.m["_dashed"]
        if rx:
            s = rx.sub(lambda mt: self.put("project", mt.group()), s)
        out, pos = [], 0
        while True:
            mt = RUN.search(s, pos)
            if not mt:
                break
            start, end = mt.span()
            run = mt.group()
            bare = run.rstrip(".")
            if len(bare) < len(run) and bare and bare[-1] != "/":
                run, end = bare, start + len(bare)
            if "/" not in run or not re.search(r"[^/.~]", run):
                out.append(s[pos:end])
                pos = end
                continue
            out.append(s[pos:start])
            low = run.lower()
            if DIGITS.match(run) or low in PAIRS or low in self.m["_pairs"] or SCHEMA.match(run):
                out.append(OPEN + run + CLOSE)
                pos = end
                continue
            p = _norm(self.m, run)
            if p in ("~", "~/"):
                if p != run:
                    self.note("path")
                out.append(OPEN + p + CLOSE)
                pos = end
                continue
            form = self._form(p)
            if form == "keep":
                if p != run:
                    self.note("path")
                out.append(OPEN + p + CLOSE)
                pos = end
                continue
            reach = self._reach(s, start, end)
            value = p + s[end:reach]
            if form:
                head = "/".join(p.split("/")[:form]) + "/"
                out.append(self.seal(head) + self.put("path", value))
            elif reach == end and p.lower().rstrip("/") in self.m["_checkouts"]:
                out.append(self.put("repo", value))
            else:
                out.append(self.put("path", value))
            pos = reach
        out.append(s[pos:])
        return "".join(out)

    def _form(self, p):
        """'keep' when the whole path is one of 4(b)'s forms, by segments; a head's length when it
        is a public tool's config, cache or state folder with another tail; else None."""
        q = p[:-1] if p.endswith("/") and len(p) > 1 else p
        segs = q.split("/")
        if "." in segs or ".." in segs:
            return None
        if q in self.m["_fixed"]:
            return "keep"
        tools, rest = self.m["_tools"], segs[1:]
        if segs[0] == "~":
            if (rest[:3] == [".claude", "plugins", "cache"] and len(rest) >= 6
                    and rest[3] == self.m["_market"] and rest[4] in tools and VERSION.match(rest[5])):
                return "keep"
            if (rest[:2] == [".local", "share"] and len(rest) >= 4 and rest[2].startswith("agentik-")
                    and rest[2][8:] in tools and HASH.match(rest[3])):
                return "keep"
            for head in self.m["_heads"]:
                if len(segs) > len(head) and segs[:len(head)] == head and all(segs[len(head):]):
                    return len(head)
        return None

    def _reach(self, s, start, end):
        """Where a replaced path ends: the rest of its quoted string; else the words after it
        through the last that holds a slash, and on to a stop (4(b))."""
        nl = s.find("\n", end)
        nl = len(s) if nl < 0 else nl
        if start and s[start - 1] in "\"'`":
            q = s.find(s[start - 1], end, nl)
            if q >= 0:
                return q
        ls = s.rfind("\n", 0, start) + 1
        for qc in "\"`":
            if s.count(qc, ls, start) % 2:
                q = s.find(qc, end, nl)
                if q >= 0:
                    return q
        if end >= nl or s[end] not in " \t":
            return end
        h = HARD.search(s, end, nl)
        words = list(WORD.finditer(s, end, h.start() if h else nl))
        last = -1
        for k, w in enumerate(words):
            t = w.group()
            if t.startswith("-") or ANCHOR.match(t):
                break
            if "/" in t:
                last = k
        k = last + 1
        while k < len(words):
            t = words[k].group()
            if t.startswith("-") or ANCHOR.match(t) or t.rstrip(".!?") in PLAIN:
                break
            k += 1
        return words[k - 1].end() if k else end

    def _assign(self, s):
        def value(mt):
            for g in (1, 2, 3):
                v = mt.group(g)
                if v is not None:
                    break
            if not v or NUMBER.match(v):
                return mt.group()
            a, b = mt.start(g) - mt.start(), mt.end(g) - mt.start()
            return mt.group()[:a] + self.put("secret", v) + mt.group()[b:]
        s = ASSIGN.sub(value, s)
        s = FLAG.sub(value, s)

        def bearer(mt):
            v = mt.group(1)
            if re.fullmatch(r"[a-z]+", v):
                return mt.group()
            return mt.group()[:mt.start(1) - mt.start()] + self.put("secret", v)
        return BEARER.sub(bearer, s)

    def _names(self, s):
        kinds = self.m["_kinds"]
        for rx in (self.m["_names"], self.m["_at"]):
            if rx:
                s = rx.sub(lambda mt: self.put(kinds.get(mt.group().lower(), "user"), mt.group()), s)
        return s

    def _groups(self, s):
        for group, rx in self.m["_groups"]:
            if NEEDS.get(group, "") not in s:
                continue
            kind, out, pos = GROUPS[group], [], 0
            for mt in rx.finditer(s):
                a, b = mt.span()
                if a < pos or a == b:
                    continue
                if group == "lan":
                    while a > pos and LAN_REACH.match(s[a - 1]):
                        a -= 1
                    while b < len(s) and LAN_REACH.match(s[b]):
                        b += 1
                elif group == "home":
                    while b < len(s) and HOME_REACH.match(s[b]):
                        b += 1
                out.append(s[pos:a])
                out.append(self.put(kind, s[a:b]))
                pos = b
            out.append(s[pos:])
            s = "".join(out)
        return s

    def _private(self, s):
        rows = self.m["private"]
        if rows == "none":
            return s
        for _, rx in rows:
            s = rx.sub(lambda mt: self.put("private", mt.group()) if mt.group() else "", s)
        return s

    def _addresses(self, s):
        def v6(mt):
            v = mt.group()
            if "::" in v:
                groups = [g for g in v.split(":") if g]
                ok = (v.count("::") == 1 and len(groups) <= 7 and sum(map(len, groups)) >= 5
                      and max(map(len, groups)) >= 3)
            else:
                groups = v.split(":")
                ok = len(groups) == 8 and all(groups)
            return self.put("address", v) if ok else v
        s = V6.sub(v6, s)
        s = MAC.sub(lambda mt: self.put("address", mt.group()), s)
        return QUAD.sub(lambda mt: self.put("address", mt.group()), s)

    def _sites(self, s):
        return SITE.sub(lambda mt: self.put("site", mt.group()), s)

    def _runs(self, s):
        def run(mt):
            v = mt.group()
            parts = [p for p in re.split(r"[_-]+", v) if p]
            if not re.search(r"[+/=]", v) and all(p.isalpha() or p.isdigit() for p in parts):
                return v
            return self.put("run", v)
        s, held = self.hold(s)
        s = RUNS.sub(run, s)
        for c, span in held.items():
            held[c] = SEGMENT_RUNS.sub(lambda mt: mt.group() if HASH.match(mt.group()) else run(mt), span)
        return self.held(s, held)

    # the spans of a settled pass

    def spans(self, s):
        """[(start, end, kind)] over the unsealed text: each placeholder, and 4(d)'s unsure spans
        (a dotted name of three labels, an `@name`, a machine name inside a longer word)."""
        marks = [mt.span() for rx in (DOTTED, HANDLE) for mt in rx.finditer(s)]
        if self.m["_inner"]:
            for mt in self.m["_inner"].finditer(s):
                a, b = mt.span()
                if (a and LETTER.match(s[a - 1])) or (b < len(s) and LETTER.match(s[b])):
                    while a and LETTER.match(s[a - 1]):
                        a -= 1
                    while b < len(s) and LETTER.match(s[b]):
                        b += 1
                    marks.append((a, b))
        offs, add = [], 0
        for i, ch in enumerate(s):
            offs.append(i + add)
            if SEALED.match(ch):
                add += len(self.seals[ord(ch) - BASE]) - 1
        offs.append(len(s) + add)
        text = self.unseal(s)
        spans = [(mt.start(), mt.end(), mt.group(1) or mt.group(3)) for mt in PH.finditer(text)]
        edge = -1
        for a, b in sorted(set(marks)):
            if a >= edge:
                spans.append((offs[a], offs[b], "unsure"))
                edge = b
        return sorted(spans)


def scrub(text, m):
    """(text, counts, spans): `clean`, then a pass applied to its own output until a pass changes
    nothing. `counts` is {kind: n} of what was replaced, and `unsure`; `spans` is over the text."""
    st = _State()
    t = clean(text)
    for _ in range(LIMIT):
        p = _Pass(m, st)
        s = p.run(t)
        new = p.unseal(s)
        if new == t:
            break
        t = new
    else:
        raise RuntimeError("the scrub did not settle")
    spans = p.spans(s)
    counts = dict(st.counts)
    unsure = sum(1 for _, _, k in spans if k == "unsure")
    if unsure:
        counts["unsure"] = unsure
    return t, counts, spans


def detect(text, m):
    """The kinds one pass would replace in `text`, and `control` for a character `clean` would
    change: empty exactly when `scrub` leaves the text as it is. Kinds, never a match."""
    p = _Pass(m, _State())
    if p.unseal(p.run(text)) == text:
        return []
    return sorted(p.kinds or {"control"})


def strike(text, words, start=0):
    """(text, places): each word, in any case and inside longer words, as `<struck-N>`, N going
    on from `start` and from the highest already in the text; a word under four letters only as a
    whole word; a placeholder never touched. `places` is the count of places struck."""
    seals = []

    def seal(value):
        seals.append(value)
        return chr(BASE + len(seals) - 1)

    s = PH.sub(lambda mt: seal(mt.group()), text)
    top = max([start] + [int(n) for n in STRUCK.findall(text)])
    found, seen = [], set()
    for w in words:
        if not w or w.lower() in seen:
            continue
        seen.add(w.lower())
        pat = re.escape(w) if len(w) >= 4 else r"(?<!\w)%s(?!\w)" % re.escape(w)
        rx = re.compile(pat, re.I)
        if rx.search(s):
            top += 1
            found.append((w, rx, "<struck-%d>" % top))
    places = 0
    for w, rx, ph in sorted(found, key=lambda f: -len(f[0])):
        c = seal(ph)
        s, n = rx.subn(lambda mt: c, s)
        places += n
    return SEALED.sub(lambda mt: seals[ord(mt.group()) - BASE], s), places
