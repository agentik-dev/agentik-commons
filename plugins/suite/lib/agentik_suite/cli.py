"""The suite's command: `<tool> <verb> [<noun>...] [flags]`, its name read from agentik-tool.conf.

Verbs: help (-h, --help; bare, a first screen of ten lines: row sc5), version (--version), setup, which plans with --dry-run and
otherwise applies the plan's steps 2 to 5, a command at a time (apply.py), config, every tool's
settings drilled down to one, describe, the suite's own answer to that read, status, five parts
on one screen (watchers, sessions, gate, backlog, runs; status_read.py reads them at once and
status_screen.py draws each as it is read), the object alone with --json, and with --check only
the declared watchers (status.py), install-cli, which places this command and the agentik door
under a prefix's bin (install.py), and doctor, the machine checked in one read (doctor.py).
Every verb takes --json, -q/--quiet, --no-color and -h/--help; setup and install-cli, the verbs
that write, also take --dry-run and -y/--yes; config takes --changed and --user-files; doctor takes
--all; status takes paths to cover, --check, and the test hooks --ps FILE and --now ISO;
install-cli takes --prefix DIR; issue takes --check, --web and --not-a-duplicate, and --ran, --exit,
--output, --expected, --as and --draft, each with a value. Those nine are the only flags with a
value. stdout carries the answer alone; stderr the hints and errors. Exit 0 done, 1 a check said
no or a step failed, 2 usage or a failed precondition, 3 not installed (a plugin's name with no
command here). Nothing here loops; setup asks once on a terminal before its first command. config
writes only its cache under ${XDG_CACHE_HOME:-~/.cache}/agentik/; status writes the same cache
and starts each tool's status reads and ps, each under its wall, and --check starts ps at most;
setup starts the plan's commands and writes what they write and its journal; install-cli writes
under its prefix; doctor writes nothing itself, and starts each listed tool's own doctor; issue
drafts a report of a problem under ${XDG_STATE_HOME:-~/.local/state}/agentik-suite/issues/ and
files it only when a person types send on the terminal device (issue.py).
"""
import difflib
import os
import re
import shlex
import sys

import agentik_install

from . import apply, config, doctor, inbox, install, issue, plan, prog, status, term, tools

VERBS = ("help", "version", "setup", "config", "describe", "status", "install-cli", "doctor", "inbox", "issue")
WRITES = ("setup", "install-cli", "issue")
FLAGS = (("--json", None, "json"), ("--quiet", "-q", "quiet"), ("--no-color", None, "no_color"),
         ("--help", "-h", "help"))
WRITE_FLAGS = (("--dry-run", None, "dry_run"), ("--yes", "-y", "yes"))
CONFIG_FLAGS = (("--changed", None, "changed"), ("--user-files", None, "user_files"))
STATUS_FLAGS = (("--check", None, "check"),)
DOCTOR_FLAGS = (("--all", None, "all"),)
ISSUE_FLAGS = (("--check", None, "check"), ("--web", None, "web"),
               ("--not-a-duplicate", None, "not_a_duplicate"))
VERB_FLAGS = {verb: WRITE_FLAGS for verb in WRITES}
VERB_FLAGS["config"] = CONFIG_FLAGS
VERB_FLAGS["status"] = STATUS_FLAGS
VERB_FLAGS["inbox"] = STATUS_FLAGS
VERB_FLAGS["doctor"] = DOCTOR_FLAGS
VERB_FLAGS["issue"] = WRITE_FLAGS + ISSUE_FLAGS
VALUE_FLAGS = {"--ps": ("ps", "status"), "--now": ("now", "status"),  # test hooks: flag, key, verb
               "--prefix": ("prefix", "install-cli"),
               "--ran": ("ran", "issue"), "--exit": ("exit", "issue"), "--output": ("output", "issue"),
               "--expected": ("expected", "issue"), "--as": ("as_login", "issue"),
               "--draft": ("draft", "issue")}
ALL_FLAGS = {f: key for long, short, key in FLAGS + WRITE_FLAGS + CONFIG_FLAGS + STATUS_FLAGS + DOCTOR_FLAGS
             + ISSUE_FLAGS
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
         ("install", ("install-cli",)), ("issue", ("issue",)))
FIRST = ("setup", "doctor", "config", "status")  # the first screen's rows above help's (row sc5 R2)
TOOL_ROW = "<tool>"
# help <verb>'s examples (R5): the words after the suite's name, a tail printed as it is, the gloss;
# OWN stands for the suite's own name, as config reads it
OWN = None
EXAMPLES = {"setup": ((("setup",), "", "help.eg.setup"), (("setup", "--dry-run"), "", "help.eg.setup_dry"),
                      (("setup",), " <plugin>...", "help.eg.setup_names")),
            "config": ((("config",), "", "help.eg.config"), (("config", OWN), "", "help.eg.config_tool"),
                       (("config", OWN), ".kind", "help.eg.config_key")),
            "help": ((("help",), "", "help.eg.help"), (("help", "config"), "", "help.eg.help_verb"),
                     (("help",), " <tool>", "help.eg.help_tool"))}
ROWS = {"setup": "help.row.setup", "doctor": "help.row.doctor", "config": "help.row.config",
        "status": "help.row.status", "help": "help.row.help"}


class Usage(Exception):
    """A refusal: its JSON code, message id, remedy and exit (2, or 3 for a plugin not installed)."""

    def __init__(self, code, mid, remedy, exit_code=2, **values):  # `status` is a command's slot
        Exception.__init__(self, code)
        self.code, self.mid, self.remedy, self.status, self.values = code, mid, remedy, exit_code, values


class Refusal(Usage):
    """A refusal in the two-line form (row sc4 R1): the message is the cause alone and the remedy,
    the command or None, is printed under it after `next:`. A bare Usage, raised by apply.py and
    install.py until their rows turn them, keeps the pin's one sentence (R3); status.py's are
    turned (su2-read phase 2)."""
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
    for long, short, key in WRITE_FLAGS + CONFIG_FLAGS + STATUS_FLAGS + DOCTOR_FLAGS + ISSUE_FLAGS:
        if opts[key] and (long, short, key) not in VERB_FLAGS.get(verb, ()):
            return long
    for flag, (key, owner) in VALUE_FLAGS.items():
        if opts[key] is not None and owner != verb:
            return flag
    return None


def _takes(verb, o, nouns):
    """True where `verb` takes these flags and words: each verb's refusals that read no file, in
    the order the verb raises them (cli.py, config.py, install.py, status.py, issue.py)."""
    if verb == "help":
        return len(nouns) <= 1 and all(n in VERBS for n in nouns)
    if verb in ("version", "doctor"):
        return not nouns
    if verb == "install-cli":
        return not nouns and o["prefix"] != ""
    if verb == "setup":
        return all(NOUN.match(n) for n in nouns)
    if verb == "status":
        return not (nouns and o["check"])
    if verb == "inbox":  # a number and --check are two answers (row in4-inbox R2)
        return not (o["check"] and any(inbox.number(n) for n in nouns))
    if verb == "issue":
        return issue.takes(o, nouns)
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
        self.bare = False  # no word and no --help: the first screen (row sc5 R1)

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
        writes is offered with --dry-run alone; of `issue`, only a word that reads, since none
        but `send` keeps --dry-run and `send` is never offered: rp6 phase 2), or that the door
        it starts with refuses (sc4 review 1)."""
        opts, words = _parse(line)[:2]
        verb = words[0] if words and words[0] in VERBS else self.verb
        flags = sum(1 for w in line if w.startswith("-") and w != "-")
        typed = sum(1 for w in self.argv if w.startswith("-") and w not in SWITCHES + ("-",))
        writes = verb in WRITES and not opts["dry_run"] and not opts["help"]
        if verb == "issue" and not opts["help"]:
            writes = not issue.reads(words[1:])
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
            self.bare = not o["help"] and not o["version"]
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
        """Bare, the first screen (R2); `help`, `-h`, `--help`, the full list (R4); --json, the
        pin's object and `tools` for both (R6)."""
        if len(nouns) > 1:
            self._no_nouns(nouns[1:], one=True)
        if nouns:
            if nouns[0] not in VERBS:
                self._not_a_verb(nouns[0], self.at[1], asked_help=True)
            return self.help_verb(nouns[0])
        if self.opts["json"]:
            found = self._on_path()
            self.t.json({"schema": SCHEMA % "help", "ok": True, "tool": self.tool,
                         "version": self.version,
                         "verbs": [{"name": v, "summary": self.t.text("verb." + v.replace("-", "_")),
                                    "usage": self.t.text("usage." + v.replace("-", "_"), **self.slots())}
                                   for v in VERBS],
                         "flags": [f[0] for f in FLAGS], "on_path": found,
                         "tools": self._tools(survey=True)})
            return 0
        if self.bare:
            return self.first_screen()
        return self.full_list()

    def _tools(self, survey):
        """[{name, version, summary, command}] for each listed tool but the suite, in the list's
        order (R4, R6). With `survey`, each `describe --json` read through config.Reader.survey
        with no config read, under its cache and its wall; without, no process starts (R2)."""
        r = config.Reader(self)
        entries = [e for e in r.entries() if e["name"] != r.suite]
        answers = {}
        if survey and any(e["exe"] for e in entries):
            answers = {row["name"]: row["answer"] for row in r.survey(entries, with_config=False)}
        found = []
        for e in entries:
            answer = answers.get(e["name"]) or {}
            said = [answer.get(k) if isinstance(answer.get(k), str) and answer.get(k).strip() else None
                    for k in ("version", "summary")]
            found.append({"name": e["name"], "version": said[0], "summary": said[1],
                          "command": bool(e["exe"])})
        return found

    def _close_help(self):
        t = self.t
        if not t.quiet:  # the plan read for its close, as the dry run builds it (row sm2 R3)
            steps = plan.build(plan.default_set(self.lib), self.env, self.lib, self.tool, self.version)
            t.hint("hint.help" if any(s["n"] <= 5 and s["state"] != "ok" for s in steps)
                   else "hint.help.done", **self.slots())
        return 0

    def first_screen(self):
        """R2: the title, then a row a verb a person starts with and one for the tools by name;
        no path, no mark, no process."""
        t = self.t
        t.line("help.title", **self.slots(), version=self.version)
        t.blank()
        rows = [(None, [term.name(v), t.text(ROWS[v])], None) for v in FIRST + ("help",)]
        names = [x["name"] for x in self._tools(survey=False) if x["command"]]
        tool = t.text("help.row.tool", names=", ".join(names)) if names else t.text("help.row.tool.none")
        t.table(rows + [(None, [term.name(TOOL_ROW), tool], None)])
        return self._close_help()

    def full_list(self):
        """R4: the title, the usage's two lines, the verbs, the tools and the flags; no path."""
        t, slots = self.t, self.slots()
        t.line("help.title", **slots, version=self.version)
        t.line("help.usage", **slots)
        if prog.form(self.env, self.tool)[0] != "typed":  # the door runs a tool by its name
            run = self.say() + " " + TOOL_ROW
        else:  # the suite by its own name runs none: the tool's own command
            run = "agentik-" + TOOL_ROW
        under = " " * t.messages["help.usage"].index("{prog}")
        t.line("help.usage.tool", run=under + run)
        t.blank()
        t.line("help.verbs", style="name")
        rows = [(None, [term.name(v), t.text(ROWS[v])], None) for v in FIRST]
        rows.append((None, [term.name("help"), t.text("help.row.help.all")], None))
        more = [v for v in VERBS if v not in FIRST + ("help",)]
        rows.append((None, [term.name(t.text("help.more")), "  ".join(more)], None))
        t.table(rows)
        t.blank()
        t.line("help.tools", style="name")
        found = self._tools(survey=True)
        if found:
            t.table([(None, [term.name(x["name"]), x["version"] or "",
                             x["summary"] or ("" if x["command"] else t.text("help.tool.bare"))], None)
                     for x in found])
        else:
            t.table([(None, [t.text("help.tools.none")], None)])
        t.blank()
        t.table([(None, [term.name(t.text("help.flags")), self._flag_words(FLAGS)], None)], indent=0)
        return self._close_help()

    @staticmethod
    def _flag_words(flags):
        return "  ".join("/".join(f for f in (short, long) if f) for long, short, _ in flags)

    def _examples(self, verb):
        """R5: (the command to paste, its gloss) for each of the verb's examples."""
        own = self.tool[len("agentik-"):] if self.tool.startswith("agentik-") else self.tool
        found = []
        for words, tail, gloss in EXAMPLES.get(verb, ()):
            words = [own if w is OWN else w for w in words]
            found.append((self.say(*words) + tail, self.t.text(gloss)))
        return found

    def _show_examples(self, examples):
        """R5's example rows, a command and its words side by side. On a terminal where one row of
        the block does not fit so, its command wider than the table's column (a third of the
        width) or the row wider than the width, the whole block stacks: each command whole on
        its own line, two spaces in, and its words under it, six in, wrapped to the width (review
        1 F2). A command is never wrapped or cut; it may pass the width."""
        t, out = self.t, self.t.out
        wide = max(term.columns(term.clean(command)) for command, _ in examples)
        row = 2 + wide + len(term.GAP) + max(term.columns(term.clean(gloss)) for _, gloss in examples)
        if not out.tty or (wide <= out.width() // 3 and row <= out.width()):
            t.table([(None, [command, gloss], None) for command, gloss in examples])
            return
        for command, gloss in examples:
            t.marked("  " + term.clean(command), [])  # one line as it is: term's own writer
            t.table([(None, [gloss], None)], indent=6)

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
        examples = self._examples(verb)
        if examples:
            self._show_examples(examples)
            t.blank()
        t.line("help.flags", style="name")
        shared = tuple(f for f in FLAGS if f[0] != "--help")
        t.table(self._flag_rows(VERB_FLAGS.get(verb, ()))
                + [(None, [term.name(t.text("help.also")), self._flag_words(shared)], None)])
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
        t, slots = self.t, self.slots()  # a held row names the config line (row fk2-plan R4)
        for s in steps:
            s["detail"] = t.text(s["mid"], **dict(slots, **s["values"]))
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
            if s["id"] == "prereqs" and s["subject"] == "claude" and s["state"] == "blocked":
                after = t.text("setup.cmd.get")  # where Claude Code comes from (row sm2 R2)
            n = str(s["n"]) if s["n"] != last else ""
            last = s["n"]
            subject = term.path(s["subject"]) if s["subject"].startswith(("~", "/")) else term.name(s["subject"])
            rows.append((STATUS[s["state"]], [n, subject, s["detail"]], after))
        t.table(rows, mark_at=1)
        t.hint(*self._closing(steps, nouns), **self.slots())
        return 0

    def _closing(self, steps, nouns):
        """The closing hint by state: the setup command, with the names given, when step 1 is
        blocked or one of steps 1 to 6 names a line setup would run (row sm2 R1, R2); done when
        steps 1 to 6 read ok; the add line when it is all that is left; else what this version
        can do is done."""
        again = "hint.setup.next", {"command": self.say("setup", *dict.fromkeys(nouns))}
        if any(s["state"] == "blocked" for s in steps):
            return again
        early = [s for s in steps if s["n"] <= 6]
        if all(s["state"] == "ok" for s in early):
            return "hint.setup.done", {}
        if any(s["command"] and s["line"] == "run" for s in early):
            return again
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

    # ---- inbox ----------------------------------------------------------------------------

    def do_inbox(self, nouns):
        return inbox.do_inbox(self, nouns)

    # ---- issue ----------------------------------------------------------------------------

    def do_issue(self, nouns):
        return issue.do_issue(self, nouns)


def main(argv=None, env=None, out=None, err=None):
    agentik_install.restore_parent_env()
    try:
        command = Command(sys.argv[1:] if argv is None else argv, os.environ if env is None else env, out, err)
    except (OSError, ValueError):  # the catalogue: absent, unreadable or not well formed
        return term.unreadable(term.catalogue.PATH, err)
    return command.run()
