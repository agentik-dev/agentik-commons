"""The suite's command: `<tool> <verb> [<noun>...] [flags]`, its name read from agentik-tool.conf.

Verbs: help (-h, --help; bare, a first screen of ten lines: row sc5), version (--version), setup, which plans with --dry-run and
otherwise applies the plan's steps 2 to 5, a command at a time (apply.py), update, which brings
every installed tool and its command current in one call, held while a run is live (update.py),
config, every tool's
settings drilled down to one, describe, the suite's own answer to that read, status, five parts
on one screen (watchers, sessions, gate, backlog, runs; status_read.py reads them at once and
status_screen.py draws each as it is read), the object alone with --json, and with --check only
the declared watchers (status.py), install-cli, which places this command and the agentik door
under a prefix's bin (install.py), doctor, the machine checked in one read (doctor.py), inbox,
what waits on the owner across the checkouts, and `inbox answer`, the owner's answer handed to the
writer verb `reply` of the tool that gives the `questions` read, run in the checkout as the
suite's own process (inbox.py), and completion, a shell's script that calls `completion words` back
at each Tab (completion.py).
Every verb takes --json, -q/--quiet, --no-color and -h/--help; setup, update and install-cli, the
verbs that write, also take --dry-run and -y/--yes; config takes --changed and --user-files; doctor takes
--all; status takes paths to cover, --check, and the test hooks --ps FILE and --now ISO;
install-cli takes --prefix DIR; issue takes --check, --web and --not-a-duplicate, and --ran, --exit,
--output, --expected, --as and --draft, each with a value; init takes --kind KIND; inbox takes paths,
numbers and --check, and `inbox answer` takes --pick LABEL or --say TEXT, each with a value under
inbox alone (setup's and config's --pick stay switches), and --dry-run and -y/--yes. Those twelve
are the only flags with a value. stdout carries the answer alone; stderr the hints and errors. Exit 0 done, 1 a check said
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
import time

import agentik_install
import agentik_records

from . import apply, completion, config, doctor, inbox, init, install, issue, plan, prog, remove, status, term, tools, update

VERBS = ("help", "version", "setup", "update", "remove", "config", "describe", "status", "install-cli", "doctor", "inbox", "issue", "init", "records",
         "completion")
KEPT = ("rows", "guard")  # words kept for one tool's claim, named in kept.json beside the package (row ak9c R2)
WRITES = ("setup", "update", "remove", "install-cli", "issue", "init")
FLAGS = (("--json", None, "json"), ("--quiet", "-q", "quiet"), ("--no-color", None, "no_color"),
         ("--help", "-h", "help"))
WRITE_FLAGS = (("--dry-run", None, "dry_run"), ("--yes", "-y", "yes"))
# config's --all, a key of its own as remove's (row sc6-config): help glosses it, doctor's stays
CONFIG_FLAGS = (("--changed", None, "changed"), ("--user-files", None, "user_files"),
                ("--all", None, "config_all"), ("--pick", None, "config_pick"))  # its key glossed as config's (sc14)
STATUS_FLAGS = (("--check", None, "check"),)
DOCTOR_FLAGS = (("--all", None, "all"),)
# remove's --all, a key of its own so doctor's keeps its gloss (row ak4-remove R1); the parse sets
# both keys, ALL_FLAGS keeps doctor's, and a verb's flags are checked by the flag's spelling
REMOVE_FLAGS = (("--all", None, "remove_all"),)
ISSUE_FLAGS = (("--check", None, "check"), ("--web", None, "web"),
               ("--not-a-duplicate", None, "not_a_duplicate"), ("--render", None, "render"))
PICK_FLAGS = (("--pick", None, "pick"),)  # setup's list of plugins (row sc15-setup-pick R5)
# `inbox answer`'s two flags with a value, read so only where the line's verb is `inbox` (row
# in5b-inbox-answer R1): setup's and config's --pick stay switches. Not in VERB_FLAGS, so no Tab word.
ANSWER_VALUES = (("--pick", None, "pick_label"), ("--say", None, "say"))
ANSWER_FLAGS = WRITE_FLAGS + ANSWER_VALUES  # what `inbox answer` takes beyond inbox's own
INSTALL_FLAGS = (("--force", None, "force"),)  # place over a newer command (row up3-forward-only R2)
VERB_FLAGS = {verb: WRITE_FLAGS for verb in WRITES}
VERB_FLAGS["setup"] = WRITE_FLAGS + PICK_FLAGS
VERB_FLAGS["install-cli"] = WRITE_FLAGS + INSTALL_FLAGS
VERB_FLAGS["config"] = CONFIG_FLAGS
VERB_FLAGS["status"] = STATUS_FLAGS
VERB_FLAGS["inbox"] = STATUS_FLAGS
VERB_FLAGS["doctor"] = DOCTOR_FLAGS
VERB_FLAGS["remove"] = WRITE_FLAGS + REMOVE_FLAGS
VERB_FLAGS["issue"] = WRITE_FLAGS + ISSUE_FLAGS
VALUE_FLAGS = {"--ps": ("ps", "status"), "--now": ("now", "status"),  # test hooks: flag, key, verb
               "--prefix": ("prefix", "install-cli"),
               "--ran": ("ran", "issue"), "--exit": ("exit", "issue"), "--output": ("output", "issue"),
               "--expected": ("expected", "issue"), "--as": ("as_login", "issue"),
               "--draft": ("draft", "issue"),
               "--kind": ("kind", "init")}
HOOKS = ("--ps", "--now")  # the test hooks of VALUE_FLAGS: never offered at a Tab (row ak12-polish R4)
ALL_FLAGS = {f: key for long, short, key in FLAGS + WRITE_FLAGS + CONFIG_FLAGS + STATUS_FLAGS + DOCTOR_FLAGS
             + ISSUE_FLAGS + INSTALL_FLAGS + PICK_FLAGS
             for f in (long, short) if f}
SWITCHES = ("--json", "--quiet", "-q", "--no-color")
SKIPS = ("--yes", "-y", "--pick", "--say")  # answers a question for the person, or waits for one: never offered (sc4 review 1, sc15)
NEVER_MENDED = WRITES  # a word that is no verb is never mended into one of these
NEAR = config.NEAR
NOUN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
SCHEMA = "agentik.%s/1"
# setup's closes on which the help says the doctor line (row hn1-help-next R1); the PATH line
# among them, as sm2 R3 ruled: a reader with only that line left has a working command
HELP_DONE = ("hint.setup.done", "hint.setup.rest", "hint.setup.path")
SLOTS = (("prog", ()), ("setup", ("setup",)), ("doctor", ("doctor",)), ("config", ("config",)),
         ("status", ("status",)), ("help", ("help",)), ("describe", ("describe",)),
         ("install", ("install-cli",)), ("issue", ("issue",)), ("update", ("update",)),
         ("remove", ("remove",)))
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
                     (("help",), " <tool>", "help.eg.help_tool")),
            "update": ((("update",), "", "help.eg.update"), (("update", "--dry-run"), "", "help.eg.update_dry")),
            "remove": ((("remove",), " <plugin>...", "help.eg.remove_names"),
                       (("remove", "--all", "--dry-run"), "", "help.eg.remove_all")),
            "inbox": ((("inbox",), "", "help.eg.inbox"), (("inbox", "1"), "", "help.eg.inbox_open"),
                      (("inbox", "answer"), " <repo> <number> --pick <label>", "help.eg.inbox_answer")),
            "completion": ((("completion", "zsh"), "", "help.eg.completion_zsh"),
                           (("completion", "bash"), "", "help.eg.completion_bash"))}
WRAPS = {"completion": 'eval "$(%s)"'}  # an example's command inside the line a person adds
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
    opts.update({key: None for _, _, key in ANSWER_VALUES})
    words, bad, rest, at, bad_at = [], None, False, [], None
    args = iter(enumerate(argv))
    for i, arg in args:
        flag, eq, value = arg.partition("=")
        if rest or not arg.startswith("-") or arg == "-":
            words.append(arg)
            at.append(i)
        elif arg == "--":
            rest = True
        elif words[:1] == ["inbox"] and flag in ("--pick", "--say"):
            # one value, after `=` or as the next word; a next word that opens with `-` is no
            # value, and a flag with none is left unset, for inbox answer's own refusal (R2)
            if not eq and i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                eq, value = True, next(args)[1]
            if eq:
                opts["pick_label" if flag == "--pick" else "say"] = value
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
    opts["remove_all"] = opts["config_all"] = opts["all"]
    opts["config_pick"] = opts["pick"]  # config's --pick, setup's key and gloss kept (row sc14-config-pick R1)
    return opts, words, bad, at, bad_at


def _flag_fault(opts, words, verb):
    """The first flag `_dispatch` refuses for `verb`, past the parse, or None."""
    if opts["version"] and (words or opts["help"]):
        return "--version"
    takes = {f[0] for f in VERB_FLAGS.get(verb, ())}
    answer = verb == "inbox" and words[1:2] == ["answer"]
    if answer:
        takes |= {f[0] for f in WRITE_FLAGS}  # --dry-run and --yes, here alone of inbox (R1)
    elif opts["pick_label"] is not None or opts["say"] is not None:
        return "--pick" if opts["pick_label"] is not None else "--say"
    for long, short, key in (WRITE_FLAGS + CONFIG_FLAGS + STATUS_FLAGS + DOCTOR_FLAGS + REMOVE_FLAGS + ISSUE_FLAGS
                             + INSTALL_FLAGS + PICK_FLAGS):
        if opts[key] and long not in takes:
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
    if verb == "records":
        return len(nouns) <= 1
    if verb == "completion":
        return completion.takes(nouns)
    if verb == "install-cli":
        return not nouns and o["prefix"] != ""
    if verb in ("setup", "update"):
        return all(NOUN.match(n) for n in nouns)
    if verb == "remove":  # names or --all, never both, never neither (row ak4-remove R1)
        return all(NOUN.match(n) for n in nouns) and bool(nouns) != bool(o["remove_all"])
    if verb == "status":
        return not (nouns and o["check"])
    if verb == "inbox" and nouns[:1] == ["answer"]:  # row in5b-inbox-answer R2
        return inbox.answer_takes(o, nouns[1:])
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
    Usage, Refusal, VERBS, KEPT = Usage, Refusal, VERBS, KEPT

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

    def by_door(self):
        """True where this run came through the door (sc17 review 1 F1): `agentik` on PATH reaches
        the suite, and the suite was started by no word, as the launcher install-cli writes hands
        none on, or by the file the door hands a verb to; never by the launcher's other path or
        the root setup."""
        if prog.form(self.env, self.tool)[0] != prog.DOOR:
            return False
        return self.typed is None or prog._names(self.typed, self.cwd, self.env,
                                                 prog._on_path(self.env, self.tool))

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
        if verb == "inbox" and words[1:2] == ["answer"] and not opts["help"]:
            writes = not opts["dry_run"]  # it drives a writer verb (row in5b-inbox-answer R10)
        door = prog.form(self.env, self.tool)[0] != "typed"
        if refused(line) or {w.partition("=")[0] for w in line} & set(SKIPS) or flags > typed or writes or \
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
            row = tools.rows(self.env, self.lib, names=[word])[word]
            runs = (row["runs"] or {}).get("path")
            if runs and at == 0 and row["kind"] not in ("absent", "undecided"):
                self._run_tool(runs, self.argv[at + 1:])  # the word runs (row ak9b R1)
            page = tools.page(self.lib, word)  # it installs its own (row fh13 R8)
            if page and runs:
                page = None  # a file runs: the pin's refusal
            more = {"page": page} if page else {}
            if word in tools.installed(self.env):
                raise Refusal("not_installed", "err.verb.page" if page else "err.verb.plugin",
                              self.say("config", word), exit_code=3, word=word, **more)
            raise Refusal("not_installed", "err.verb.page" if page else "err.verb.missing",
                          self.say("setup", word), exit_code=3, word=word, **more)
        claimed = self._claimed(word, at) if at == 0 and not asked_help else None
        names = sorted(set(found) | set(tools.plugin_names(self.env, self.lib)))
        near = difflib.get_close_matches(word, [w for w in VERBS + tuple(names) if w != word],
                                         n=1, cutoff=NEAR)
        if not near:
            raise Refusal("unknown_verb", "err.verb.none", claimed or self.say("help"), word=word)
        near = near[0]
        if near in VERBS:  # never into a verb that writes from a word that is none (review 1 F2)
            run = self.say("help") if near in NEVER_MENDED and not asked_help else self.mend(at, near)
            raise Refusal("unknown_verb", "err.verb", claimed or run, word=word)
        rest = [w for w in self.argv[at + 1:] if w not in SWITCHES]
        if near == own and rest and not asked_help:  # the suite by its name: its own line
            run = self.offer(rest)
        else:
            run = self._tool_line(near, found.get(near), rest, asked_help)
        raise Refusal("unknown_verb", "err.verb.tool", claimed or run, word=word)

    def _claimed(self, word, at):
        """Row ak9c R1 to R4, for a first word nothing above settles: the claims read from each
        listed tool's describe, the cache's or one under the describe wall (R6). One claim of
        `word` that counts: the suite replaced by the claimant's file, `word` and every later word
        unchanged. Two or more: refused, exit 2, naming each. Else the pin's refusal follows, its
        `next:` the claimant's own line where exactly one tool claims `word` without counting
        (returned), or None."""
        suite = self.tool[len("agentik-"):]
        entries = [e for e in tools.listed(suite, self._on_path(), self.env, self.lib)[1:] if e["exe"]]
        described = tools.describe_all(entries, self.env, deadline=time.monotonic() + tools.WALL)[0] \
            if entries else {}
        mine = [c for c in doctor.claims(self, entries, described) if c["verb"] == word]
        counts = [c["tool"] for c in mine if c["counts"]]
        if len(counts) == 1:
            exe = [e["exe"] for e in entries if e["name"] == counts[0]][0]
            self._run_tool(exe, [word] + self.argv[at + 1:])
            return None  # it cannot run: the pin's refusal (ak9b R2)
        if counts:
            raise Refusal("claimed_twice", "err.verb.claimed", self.say("doctor"), word=word,
                          tools=doctor.joined(counts))
        idle = sorted({c["tool"] for c in mine})
        if len(idle) != 1:
            return None
        entry = [e for e in entries if e["name"] == idle[0]][0]
        row = entry.get("source") or {}
        if (row.get("runs") or {}).get("path") and row.get("kind") not in ("absent", "undecided"):
            return self.say(idle[0], word)  # `agentik T` runs T's file
        # the finder knows T only as a file on PATH: that file's own line (review 1 F3)
        return prog.shown(entry["exe"], self.env.get("HOME"), self.opts["json"]) + " " + shlex.quote(word)

    def _bad_flag(self, flag):
        if flag == "--version":
            raise Refusal("unknown_flag", "err.flag.version", self.say("--version"))
        verb = self.verb if self.verb and self.verb != "help" else None
        known = [f for long, short, _ in FLAGS + VERB_FLAGS.get(verb, ()) for f in (long, short) if f]
        known += [f for f, (_, owner) in VALUE_FLAGS.items() if owner == verb]
        known += ["--dry-run"] if verb == "inbox" and self.words[1:2] == ["answer"] else []
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
        page = u.values.get("page")  # a tool's page goes whole under the cause (row sc17 R6)
        whole = page or u.values.get("said")  # or a child's own last line (row sc18 R5)
        if self.opts["json"]:
            message = self.t.text(u.mid, **u.values)
            if page:  # the address in the message too, as at the pin (review 1 L4)
                message += " " + page
            elif whole:  # the child's line too, as setup's JSON keeps it
                message = self.t.text("err.setup.last", message=message, last=whole)
            error = {"code": u.code, "message": message, "remedy": u.remedy}
            if type(u.values.get("exit")) is int:  # a child's code the message held (row sc18 R8)
                error["exit"] = u.values["exit"]
            self.t.json({"schema": SCHEMA % (self.verb or "usage"), "ok": False,
                         "error": dict(error, page=page) if page else error})
        else:
            self.t.error(u.mid, next_=u.remedy if u.paste else None, whole=whole, **u.values)
        return u.status

    def _no_nouns(self, nouns, one=False):
        if nouns:
            raise Refusal("extra_word", "err.extra.one" if one else "err.extra",
                          self.say("help", self.verb), verb=self.verb, word=nouns[0])

    # ---- help -----------------------------------------------------------------------------

    def _run_tool(self, exe, rest):
        """Row ak9b R1: the suite replaced by the file the finder says runs, `rest` unchanged, the
        same streams and the environment the launcher restored; it returns only where that file
        cannot run, and the pin's refusal follows (R2)."""
        if not (os.path.isfile(exe) and os.access(exe, os.X_OK)):
            return
        self.t.flush()
        try:
            os.execve(exe, [exe] + list(rest), dict(self.env))
        except OSError:
            return

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
        if not t.quiet:  # the plan read for its close, as the dry run builds it (row sm2 R3), of
            # the plugins the doctor plans, and its setup line (row ic2-needs review 1 lead 1)
            names, _, setup = doctor.planned(self)
            steps = plan.build(names or plan.default_set(self.lib), self.env, self.lib, self.tool,
                               self.version)
            # setup's own question over the same steps (row hn1-help-next R1): the setup line
            # where its close names something to run or a page, else the doctor line
            mid = self._closing(steps, setup)[0]
            t.hint("hint.help.done" if mid in HELP_DONE else "hint.help",
                   **dict(self.slots(), setup=self.say("setup", *setup)))
        return 0

    def first_screen(self):
        """R2: the title, then a row a verb a person starts with and one for the tools by name;
        no path, no mark, no process."""
        t = self.t
        t.wrapped("help.title", **self.slots(), version=self.version)
        t.blank()
        rows = [(None, [term.name(v), t.text(ROWS[v])], None) for v in FIRST + ("help",)]
        names = [x["name"] for x in self._tools(survey=False) if x["command"]]
        tool = t.text("help.row.tool", names=", ".join(names)) if names else t.text("help.row.tool.none")
        t.table(rows + [(None, [term.name(TOOL_ROW), tool], None)])
        return self._close_help()

    def full_list(self):
        """R4: the title, the usage's two lines, the verbs, the tools and the flags; no path."""
        t, slots = self.t, self.slots()
        t.wrapped("help.title", **slots, version=self.version)
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
            found.append((WRAPS.get(verb, "%s") % (self.say(*words) + tail), self.t.text(gloss)))
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
        flags = FLAGS + VERB_FLAGS.get(verb, ()) + (ANSWER_FLAGS if verb == "inbox" else ())
        if self.opts["json"]:
            self.t.json({"schema": SCHEMA % "help", "ok": True, "tool": self.tool,
                         "version": self.version, "verb": verb,
                         "summary": self.t.text("verb." + verb.replace("-", "_")),
                         "usage": self.t.text("usage." + verb.replace("-", "_"), **self.slots()),
                         "flags": [f[0] for f in flags]})
            return 0
        t = self.t
        t.line("usage." + verb.replace("-", "_"), **self.slots())
        t.wrapped("verb." + verb.replace("-", "_"))  # at the window's width (sc17 R2)
        t.blank()
        examples = self._examples(verb)
        if examples:
            self._show_examples(examples)
            t.blank()
        t.line("help.flags", style="name")
        shared = tuple(f for f in FLAGS if f[0] != "--help")
        plain = [(None, [term.name("AGENTIK_PLAIN=1"), t.text("help.plain")], None)] if verb == "setup" else []
        own = VERB_FLAGS.get(verb, ()) + (ANSWER_FLAGS if verb == "inbox" else ())
        t.table(self._flag_rows(own) + plain
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
        if not self.env.get("HOME"):  # no path to plan from (row ic2-needs R2)
            raise Refusal("no_home", "err.setup.home", None)
        known = plan.known(self.env, self.lib)
        for pass_ in (1, 2):
            for noun in nouns:  # before any plan, the dry run's too (R2); the list's answer too
                if noun not in known:
                    raise Refusal("unknown_plugin", "err.setup.unknown", self.say("setup", "--dry-run"),
                                  name=noun, names=", ".join(known))
            if pass_ == 2 or not self.opts["pick"]:
                break
            nouns = apply.pick_names(self, nouns)  # as the same names typed (row sc15-setup-pick R5)
        names = list(dict.fromkeys(nouns)) or plan.default_set(self.lib)
        if not self.opts["dry_run"]:
            return apply.run(self, names)
        steps = plan.build(names, self.env, self.lib, self.tool, self.version)
        t, slots = self.t, self.slots()  # a held row names the config line (row fk2-plan R4)
        for s in steps:
            s["detail"] = t.text(s["mid"], **dict(slots, **s["values"]))
        if self.opts["json"]:
            t.json({"schema": SCHEMA % "setup", "ok": True, "dry_run": True, "plugins": names,
                    "steps": [apply.step_json(s) for s in steps]})
            return 0
        apply.plan_screen(self, steps, names, dry=True)  # the run's plan, no question (row sc8 R1)
        mid, values = self._closing(steps, nouns)
        if mid in ("hint.setup.next", "hint.setup.done"):  # setup while a yes runs a command
            t.hint(mid, values, **self.slots())
            return 0
        # nothing a yes would run: the second run's close, its PATH rows and next: claude (row
        # sc8 R3); no screen of setup ends on next: export
        add = [s for s in steps if s["n"] == 6 and s["state"] == "todo" and s["command"]]
        if add:
            t.blank()
            apply._tail(t, apply.path_rows(self, add[0]["command"]))
        if mid == "hint.setup.page":  # a note, since its line is no command (row sc8 R8)
            apply._note(t, mid, **values)
        t.hint("hint.setup.done")
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
        if apply.page_close(steps):  # before the PATH line's close (row fh13 R7)
            return apply.page_close(steps)
        add = [s["command"] for s in early if s["command"] and s["line"] == "add"]
        if add:
            return "hint.setup.path", {"command": add[0]}
        return "hint.setup.rest", {}


    # ---- update ---------------------------------------------------------------------------

    def do_update(self, nouns):
        return update.do_update(self, nouns)

    # ---- remove ---------------------------------------------------------------------------

    def do_remove(self, nouns):
        return remove.do_remove(self, nouns)

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

    # ---- init -----------------------------------------------------------------------------

    def do_init(self, nouns):
        return init.do_init(self, nouns)

    # ---- completion -----------------------------------------------------------------------

    def do_completion(self, nouns):
        return completion.do_completion(self, nouns)

    # ---- records --------------------------------------------------------------------------

    def do_records(self, nouns):
        """Where the repo of DIR, the working folder by default, keeps its working records: the
        `agentik.records/1` object of agentik_records.resolve (packet rr2-records-resolver R8).
        Plain, one line a key; --json, the object alone. Exit 0 in every state; it writes nothing."""
        if len(nouns) > 1:
            self._no_nouns(nouns[1:], one=True)
        typed = nouns[0] if nouns else "."
        start = os.path.join(self.cwd, typed)
        if not os.path.isdir(start):
            raise Refusal("not_dir", "err.records.dir", None, dir=typed)
        try:
            found = agentik_records.resolve(start)
        except agentik_records.NoRepo:
            raise Refusal("no_repo", "err.records.repo", None, dir=typed)
        if self.opts["json"]:
            self.t.json(found)
            return 0
        for key in ("repo", "records", "holder", "prefix", "state", "why"):
            value = found[key]
            if key == "why" and value:
                value = doctor.records_why(self.t, found, start)
            elif key == "holder" and value is None and found["state"] == "out":
                value = self.t.text("records.holder.none")
            self.t.line("records.row", key=key, value=self.t.text("records.none") if value is None else value)
        return 0


def main(argv=None, env=None, out=None, err=None):
    agentik_install.restore_parent_env()
    try:
        command = Command(sys.argv[1:] if argv is None else argv, os.environ if env is None else env, out, err)
    except (OSError, ValueError):  # the catalogue: absent, unreadable or not well formed
        return term.unreadable(term.catalogue.PATH, err)
    return command.run()
