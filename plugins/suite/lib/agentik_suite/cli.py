"""The suite's command: `<tool> <verb> [<noun>...] [flags]`, its name read from agentik-tool.conf.

Verbs: help (bare, -h, --help), version (--version), setup, which plans with --dry-run and
otherwise applies the plan's steps 2 to 5, a command at a time (apply.py), config, every tool's
settings drilled down to one, describe, the suite's own answer to that read, status, which in
this version only checks the declared watchers (`status --check`), install-cli, which places this
command and the agentik door under a prefix's bin (install.py), and doctor, the machine checked
in one read (doctor.py). Every verb takes --json, -q/--quiet, --no-color and -h/--help; setup and
install-cli, the verbs that write, also take --dry-run and -y/--yes; config takes --changed and
--user-files; status takes --check, and the test hooks --ps FILE and --now ISO; install-cli takes
--prefix DIR. Those three are the only flags with a value. stdout carries the answer alone;
stderr the hints and errors. Exit 0 done, 1 a check said no or a step failed, 2 usage or a failed
precondition, 3 not installed (a plugin's name with no command here). Nothing here loops; setup
asks once on a terminal before its first command. config writes only its cache under
${XDG_CACHE_HOME:-~/.cache}/agentik/; status starts ps at most; setup starts the plan's commands
and writes what they write and its journal; install-cli writes under its prefix; doctor writes
nothing itself, and starts each listed tool's own doctor.
"""
import difflib
import os
import re
import shlex
import sys

import agentik_install

from . import apply, config, doctor, install, plan, prog, status, term, tools

VERBS = ("help", "version", "setup", "config", "describe", "status", "install-cli", "doctor")
WRITES = ("setup", "install-cli")
FLAGS = (("--json", None, "json"), ("--quiet", "-q", "quiet"), ("--no-color", None, "no_color"),
         ("--help", "-h", "help"))
WRITE_FLAGS = (("--dry-run", None, "dry_run"), ("--yes", "-y", "yes"))
CONFIG_FLAGS = (("--changed", None, "changed"), ("--user-files", None, "user_files"))
STATUS_FLAGS = (("--check", None, "check"),)
VERB_FLAGS = {verb: WRITE_FLAGS for verb in WRITES}
VERB_FLAGS["config"] = CONFIG_FLAGS
VERB_FLAGS["status"] = STATUS_FLAGS
VALUE_FLAGS = {"--ps": ("ps", "status"), "--now": ("now", "status"),  # test hooks: flag, key, verb
               "--prefix": ("prefix", "install-cli")}
ALL_FLAGS = {f: key for long, short, key in FLAGS + WRITE_FLAGS + CONFIG_FLAGS + STATUS_FLAGS
             for f in (long, short) if f}
SWITCHES = ("--json", "--quiet", "-q", "--no-color")
SKIPS = ("--yes", "-y")  # a flag that answers a question for the person: never offered (sc4 review 1)
NEVER_MENDED = WRITES + ("remove",)  # a word that is no verb is never mended into one of these
NEAR = config.NEAR
NOUN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
STATUS = {"ok": "ok", "todo": "note", "blocked": "warn"}
SCHEMA = "agentik.%s/1"
SLOTS = (("prog", ()), ("setup", ("setup",)), ("doctor", ("doctor",)), ("config", ("config",)),
         ("status", ("status",)), ("help", ("help",)), ("describe", ("describe",)),
         ("install", ("install-cli",)))


class Usage(Exception):
    """A refusal: its JSON code, message id, remedy and exit (2, or 3 for a plugin not installed)."""

    def __init__(self, code, mid, remedy, exit_code=2, **values):  # `status` is a command's slot
        Exception.__init__(self, code)
        self.code, self.mid, self.remedy, self.status, self.values = code, mid, remedy, exit_code, values


class Refusal(Usage):
    """A refusal in the two-line form (row sc4 R1): the message is the cause alone and the remedy,
    the command or None, is printed under it after `next:`. A bare Usage, raised by apply.py,
    install.py and status.py until their rows turn them, keeps the pin's one sentence (R3)."""
    paste = True


Usage.paste = False


def _lib():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _tool(lib):
    try:
        return agentik_install.names(lib)["tool_name"]
    except (OSError, ValueError):
        return os.path.basename(sys.argv[0]) or "agentik"


def parse(argv):
    return _parse(argv)[:3]


def _parse(argv):
    """(opts, words, the first bad flag, each word's index in argv, the bad flag's index)."""
    opts = {key: False for key in ALL_FLAGS.values()}
    opts["version"] = False
    opts.update({key: None for key, _ in VALUE_FLAGS.values()})
    words, bad, rest, at, bad_at = [], None, False, [], None
    args = iter(enumerate(argv))
    for i, arg in args:
        flag, eq, value = arg.partition("=")
        if rest or not arg.startswith("-") or arg == "-":
            words.append(arg)
            at.append(i)
        elif arg == "--":
            rest = True
        elif flag in VALUE_FLAGS:
            value = value if eq else next(args, (None, None))[1]
            if flag == "--prefix" and (value is None or value.startswith("-")):
                value = ""  # a flag, or nothing, is no folder: install-cli refuses it (ak2b review 1)
            if value is None and bad is None:
                bad, bad_at = flag, i
            elif value is not None:
                opts[VALUE_FLAGS[flag][0]] = value
        elif arg == "--version":
            opts["version"] = True
        elif arg in ALL_FLAGS:
            opts[ALL_FLAGS[arg]] = True
        elif bad is None:
            bad, bad_at = arg, i
    return opts, words, bad, at, bad_at


def _flag_fault(opts, words, verb):
    """The first flag `_dispatch` refuses for `verb`, past the parse, or None."""
    if opts["version"] and (words or opts["help"]):
        return "--version"
    for long, short, key in WRITE_FLAGS + CONFIG_FLAGS + STATUS_FLAGS:
        if opts[key] and (long, short, key) not in VERB_FLAGS.get(verb, ()):
            return long
    for flag, (key, owner) in VALUE_FLAGS.items():
        if opts[key] is not None and owner != verb:
            return flag
    return None


def _takes(verb, o, nouns):
    """True where `verb` takes these flags and words: each verb's refusals that read no file, in
    the order the verb raises them (cli.py, config.py, install.py, status.py)."""
    if verb == "help":
        return len(nouns) <= 1 and all(n in VERBS for n in nouns)
    if verb in ("version", "doctor"):
        return not nouns
    if verb == "install-cli":
        return not nouns and o["prefix"] != ""
    if verb == "setup":
        return all(NOUN.match(n) for n in nouns)
    if verb == "status":
        return not nouns and o["check"]
    if verb == "describe":
        return o["json"] and (len(nouns) <= 2 if nouns[:1] == ["sources"] else
                              not nouns or (nouns[0] == "config" and len(nouns) <= 2))
    if verb == "config":
        name, dot, key = config.path(nouns).partition(".")
        both = o["changed"] and o["user_files"]
        return not both and not (nouns and (o["changed"] or o["user_files"])) and \
            (not nouns or bool(name) and not (dot and not key))
    return False


def _door_takes(line):
    """True where the door, bin/agentik, hands `line` on: a name first, `help` with at most one
    name after it, or `--version` alone (packet ak2 R2)."""
    if line[:1] and line[0] in ("help", "-h", "--help"):
        return len(line) == 1 or len(line) == 2 and bool(NOUN.match(line[1]))
    return line == ["--version"] or not line or bool(NOUN.match(line[0]))


def refused(line):
    """True where the suite refuses `line`, the words after its name, before it reads a file:
    the parse, the verb, `_dispatch`'s flags and the verb's own words (sc4 review 1)."""
    opts, words, bad = _parse(line)[:3]
    if bad is not None:
        return True
    verb = words[0] if words else "version" if opts["version"] and not opts["help"] else "help"
    if verb not in VERBS or _flag_fault(opts, words, verb):
        return True
    return not opts["help"] and not _takes(verb, opts, words[1:])


class Command:
    Usage, Refusal, VERBS = Usage, Refusal, VERBS

    def __init__(self, argv, env, out, err):
        self.argv = list(argv)
        self.opts, self.words, self.bad, self.at, self.bad_at = _parse(self.argv)
        self.env = env
        self.lib = _lib()
        self.tool = _tool(self.lib)
        self.typed = env.pop(prog.ARGV0, None)  # the word typed, kept from what this spawns (R3)
        try:
            self.cwd = os.getcwd()
        except OSError:
            self.cwd = "/"
        self.version = agentik_install.version(self.lib)
        self.t = term.Term(no_color=self.opts["no_color"], quiet=self.opts["quiet"] or self.opts["json"],
                           env=env, out=out, err=err)
        self.verb = None

    # ---- the name and the command a line prints (row sc2, hq design/23 §3) -----------------

    def say(self, *words):
        """The one way a line names a command: the words that start it, then `words`; in --json
        with the full path where the screen shows `~`."""
        return prog.start(self.env, self.lib, self.tool, self.typed, self.cwd, words,
                          full=self.opts["json"])

    def again(self, swap, tail=()):
        """The line as typed, each argv index in `swap` replaced by its words, then `tail`; the
        switches of the answer's form (--json, -q, --no-color) left out, so a screen and its
        --json name one command (row sc4 R4)."""
        line = []
        for i, word in enumerate(self.argv):
            if i in swap:
                line.extend(swap[i])
            elif word not in SWITCHES:
                line.append(word)
        return self.offer(line + list(tail))

    def mend(self, at, *words):
        return self.again({at: list(words)})

    def offer(self, line):
        """The command for `line`, the words after the suite's name, where the suite would run it
        and it does no more than the typed line asked; else the help line of its verb. A line
        is not offered that the suite refuses, that holds a flag answering a question for the
        person, that holds more flags than the person typed, that would write (a verb that
        writes is offered with --dry-run alone), or that the door it starts with refuses (sc4
        review 1)."""
        opts, words = _parse(line)[:2]
        verb = words[0] if words and words[0] in VERBS else self.verb
        flags = sum(1 for w in line if w.startswith("-") and w != "-")
        typed = sum(1 for w in self.argv if w.startswith("-") and w not in SWITCHES + ("-",))
        writes = verb in WRITES and not opts["dry_run"] and not opts["help"]
        door = prog.form(self.env, self.tool)[0] != "typed"
        if refused(line) or set(line) & set(SKIPS) or flags > typed or writes or \
                door and not _door_takes(line):
            return self.say("help", verb) if verb and verb != "help" else self.say("help")
        return self.say(*line)

    def _tool_line(self, near, path, rest, asked_help):
        """The line for the tool `near` the person meant, its file at `path`: through the door
        where one reaches the suite, else that file through sc2's `prog.shown` (review 1 F5);
        the words after the typed one, or its help where none follow, since a tool run bare is a
        usage error (R4). A plugin with no command here gets the suite's help for it (F6). Words
        that hold a flag answering a question or a word of NEVER_MENDED pass the gate a suite line
        does in `offer`: the tool's help, by either form (review 2 F1)."""
        if any(w.partition("=")[0] in SKIPS or w in NEVER_MENDED for w in rest):
            rest = []
        if path is None:
            return self.say("help", near)
        if prog.form(self.env, self.tool)[0] != "typed":
            return self.say(*([near] + rest if rest and not asked_help else ["help", near]))
        shown = prog.shown(path, self.env.get("HOME"), self.opts["json"])
        words = rest if rest and not asked_help else ["--help"]
        return " ".join([shown] + [shlex.quote(w) for w in words])

    def slots(self):
        """The catalogue's slots for a command, one a verb, `{prog}` with none, and `{tool}`, the
        name a title gives."""
        found = {slot: self.say(*verb) for slot, verb in SLOTS}
        found["tool"] = prog.name(self.env, self.tool)
        return found

    # ---- the frame ------------------------------------------------------------------------

    def run(self):
        try:
            return self._dispatch()
        except Usage as u:
            return self.fail(u)
        finally:
            self.t.flush()

    def _dispatch(self):
        o, words = self.opts, self.words
        if words:
            self.verb = words[0]
            if self.verb not in VERBS:
                self.verb = None
                self._not_a_verb(words[0], self.at[0])
        else:
            self.verb = "version" if o["version"] and not o["help"] else "help"
        nouns = words[1:]
        if self.bad is not None:
            self._bad_flag(self.bad)
        fault = _flag_fault(o, words, self.verb)
        if fault:
            self._bad_flag(fault)
        if o["help"] and self.verb != "help":
            return self.help_verb(self.verb)
        return getattr(self, "do_" + self.verb.replace("-", "_"))(nouns)

    def _not_a_verb(self, word, at, asked_help=False):
        """Packet ak2 R3, row sc4 R6: a plugin's name with no agentik-<word> on PATH exits 3; a
        tool's name is a tool, not a verb; any other word exits 2, the near verb or tool mended
        into the line as typed."""
        own = self.tool[len("agentik-"):]
        found = {f["name"][len("agentik-"):]: f["path"] for f in self._on_path()}
        found[own] = os.path.abspath(prog.files(self.lib, self.tool)[0])
        if word in found:
            run = prog.shown(found[word], self.env.get("HOME"), self.opts["json"]) + " --help"
            raise Refusal("unknown_verb", "err.verb.own", run, word=word)
        if word in tools.plugin_names(self.env, self.lib):
            if word in tools.installed(self.env):
                raise Refusal("not_installed", "err.verb.plugin", self.say("config", word),
                              exit_code=3, word=word)
            raise Refusal("not_installed", "err.verb.missing", self.say("setup", word),
                          exit_code=3, word=word)
        names = sorted(set(found) | set(tools.plugin_names(self.env, self.lib)))
        near = difflib.get_close_matches(word, [w for w in VERBS + tuple(names) if w != word],
                                         n=1, cutoff=NEAR)
        if not near:
            raise Refusal("unknown_verb", "err.verb.none", self.say("help"), word=word)
        near = near[0]
        if near in VERBS:  # never into a verb that writes from a word that is none (review 1 F2)
            run = self.say("help") if near in NEVER_MENDED and not asked_help else self.mend(at, near)
            raise Refusal("unknown_verb", "err.verb", run, word=word)
        rest = [w for w in self.argv[at + 1:] if w not in SWITCHES]
        if near == own and rest and not asked_help:  # the suite by its name: its own line
            run = self.offer(rest)
        else:
            run = self._tool_line(near, found.get(near), rest, asked_help)
        raise Refusal("unknown_verb", "err.verb.tool", run, word=word)

    def _bad_flag(self, flag):
        if flag == "--version":
            raise Refusal("unknown_flag", "err.flag.version", self.say("--version"))
        verb = self.verb if self.verb and self.verb != "help" else None
        known = [f for long, short, _ in FLAGS + VERB_FLAGS.get(verb, ()) for f in (long, short) if f]
        known += [f for f, (_, owner) in VALUE_FLAGS.items() if owner == verb]
        known += [] if verb else ["--version"]
        known = [f for f in known if f != flag and f not in SKIPS]  # never --yes (review 1 F1)
        # a value flag typed rightly with no value after it is no other flag (review 1 F4)
        near = [] if flag in VALUE_FLAGS else difflib.get_close_matches(flag, known, n=1, cutoff=NEAR)
        mid = "err.flag.of" if verb else "err.flag"
        if near and flag == self.bad:
            raise Refusal("unknown_flag", mid, self.mend(self.bad_at, near[0]), flag=flag, verb=verb)
        raise Refusal("unknown_flag", mid, self.say("help", *([verb] if verb else [])),
                      flag=flag, verb=verb)

    def fail(self, u):
        if self.opts["json"]:
            self.t.json({"schema": SCHEMA % (self.verb or "usage"), "ok": False,
                         "error": {"code": u.code, "message": self.t.text(u.mid, **u.values),
                                   "remedy": u.remedy}})
        else:
            self.t.error(u.mid, next_=u.remedy if u.paste else None, **u.values)
        return u.status

    def _no_nouns(self, nouns, one=False):
        if nouns:
            raise Refusal("extra_word", "err.extra.one" if one else "err.extra",
                          self.say("help", self.verb), verb=self.verb, word=nouns[0])

    # ---- help -----------------------------------------------------------------------------

    def _on_path(self):
        seen, found = set(), []
        for entry in self.env.get("PATH", "").split(os.pathsep):
            entry = entry or "."
            try:
                names = sorted(os.listdir(entry))
            except OSError:
                continue
            for name in names:
                if not name.startswith("agentik-") or name in seen or not NOUN.match(name):
                    continue
                full = os.path.join(entry, name)
                if os.path.isfile(full) and os.access(full, os.X_OK):
                    seen.add(name)
                    found.append({"name": name, "path": full})
        return found

    def _flag_rows(self, flags):
        return [(None, [term.name(", ".join(f for f in (short, long) if f)),
                        self.t.text("flag." + key)], None) for long, short, key in flags]

    def do_help(self, nouns):
        if len(nouns) > 1:
            self._no_nouns(nouns[1:], one=True)
        if nouns:
            if nouns[0] not in VERBS:
                self._not_a_verb(nouns[0], self.at[1], asked_help=True)
            return self.help_verb(nouns[0])
        found = self._on_path()
        if self.opts["json"]:
            self.t.json({"schema": SCHEMA % "help", "ok": True, "tool": self.tool,
                         "version": self.version,
                         "verbs": [{"name": v, "summary": self.t.text("verb." + v.replace("-", "_")),
                                    "usage": self.t.text("usage." + v.replace("-", "_"), **self.slots())}
                                   for v in VERBS],
                         "flags": [f[0] for f in FLAGS], "on_path": found})
            return 0
        t = self.t
        t.line("help.title", **self.slots(), version=self.version)
        t.line("help.usage", **self.slots())
        t.blank()
        t.line("help.verbs", style="name")
        t.table([(None, [term.name(v), t.text("verb." + v.replace("-", "_"))], None) for v in VERBS])
        t.blank()
        t.line("help.flags", style="name")
        t.table(self._flag_rows(FLAGS))
        t.blank()
        t.line("help.path", style="name")
        if found:
            t.table([("ok", [term.name(f["name"]), term.path(f["path"])], None) for f in found])
        else:
            t.table([("note", [t.text("help.path.none")], None)])
        t.hint("hint.help", **self.slots())
        return 0

    def help_verb(self, verb):
        flags = FLAGS + VERB_FLAGS.get(verb, ())
        if self.opts["json"]:
            self.t.json({"schema": SCHEMA % "help", "ok": True, "tool": self.tool,
                         "version": self.version, "verb": verb,
                         "summary": self.t.text("verb." + verb.replace("-", "_")),
                         "usage": self.t.text("usage." + verb.replace("-", "_"), **self.slots()),
                         "flags": [f[0] for f in flags]})
            return 0
        t = self.t
        t.line("usage." + verb.replace("-", "_"), **self.slots())
        t.line("verb." + verb.replace("-", "_"))
        t.blank()
        t.line("help.flags", style="name")
        t.table(self._flag_rows(flags))
        t.hint("hint.verb", **self.slots())
        return 0

    # ---- version --------------------------------------------------------------------------

    def do_version(self, nouns):
        self._no_nouns(nouns)
        if self.version == "0.0.0-unknown":  # agentik_install.version's word for no manifest
            path = os.path.join(os.path.dirname(self.lib), ".claude-plugin", "plugin.json")
            raise Refusal("no_version", "err.version", "claude plugin install suite@agentik",
                          tool=self.slots()["tool"], path=path)
        if self.opts["json"]:
            self.t.json({"schema": SCHEMA % "version", "ok": True, "tool": self.tool,
                         "version": self.version})
        else:
            self.t.line("version.line", **self.slots(), version=self.version)
        return 0

    def do_install_cli(self, nouns):
        return install.do_install_cli(self, nouns)

    # ---- setup ----------------------------------------------------------------------------

    def do_setup(self, nouns):
        for noun in nouns:
            if not NOUN.match(noun):
                raise Refusal("bad_name", "err.setup.name", self.say("setup", "--dry-run"), name=noun)
        names = list(dict.fromkeys(nouns)) or plan.default_set(self.lib)
        if not self.opts["dry_run"]:
            return apply.run(self, names)
        steps = plan.build(names, self.env, self.lib, self.tool, self.version)
        t = self.t
        for s in steps:
            s["detail"] = t.text(s["mid"], **s["values"])
        if self.opts["json"]:
            t.json({"schema": SCHEMA % "setup", "ok": True, "dry_run": True, "plugins": names,
                    "steps": [{k: s[k] for k in ("n", "id", "state", "subject", "detail", "command")}
                              for s in steps]})
            return 0
        if names:
            t.line("setup.title", plugins=", ".join(names))
        else:
            t.line("setup.title.none")
        rows, last = [], None
        for s in steps:
            after = t.text("setup." + s["line"], command=s["command"]) if s["command"] else None
            n = str(s["n"]) if s["n"] != last else ""
            last = s["n"]
            subject = term.path(s["subject"]) if s["subject"].startswith(("~", "/")) else term.name(s["subject"])
            rows.append((STATUS[s["state"]], [n, subject, s["detail"]], after))
        t.table(rows, mark_at=1)
        t.hint(*self._closing(steps), **self.slots())
        return 0

    @staticmethod
    def _closing(steps):
        """The closing hint by state: what to install when step 1 is blocked; done when steps 1
        to 6 read ok; the run lines, in order, while one of steps 1 to 6 names one; the add line
        when it is all that is left; else what this version can do is done."""
        blocked = [s["subject"] for s in steps if s["state"] == "blocked"]
        if blocked:
            return "hint.setup.blocked", {"missing": ", ".join(blocked)}
        early = [s for s in steps if s["n"] <= 6]
        if all(s["state"] == "ok" for s in early):
            return "hint.setup.done", {}
        if any(s["command"] and s["line"] == "run" for s in early):
            return "hint.setup.todo", {}
        if any(s["command"] for s in early):
            return "hint.setup.path", {}
        return "hint.setup.rest", {}


    # ---- config and describe ----------------------------------------------------------------

    def do_config(self, nouns):
        return config.do_config(self, nouns)

    def do_describe(self, nouns):
        return config.do_describe(self, nouns)

    # ---- status ---------------------------------------------------------------------------

    def do_status(self, nouns):
        return status.do_status(self, nouns)

    # ---- doctor ---------------------------------------------------------------------------

    def do_doctor(self, nouns):
        return doctor.do_doctor(self, nouns)


def main(argv=None, env=None, out=None, err=None):
    agentik_install.restore_parent_env()
    try:
        command = Command(sys.argv[1:] if argv is None else argv, os.environ if env is None else env, out, err)
    except (OSError, ValueError):  # the catalogue: absent, unreadable or not well formed
        return term.unreadable(term.catalogue.PATH, err)
    return command.run()
