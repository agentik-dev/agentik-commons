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


def _lib():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _tool(lib):
    try:
        return agentik_install.names(lib)["tool_name"]
    except (OSError, ValueError):
        return os.path.basename(sys.argv[0]) or "agentik"


def parse(argv):
    opts = {key: False for key in ALL_FLAGS.values()}
    opts["version"] = False
    opts.update({key: None for key, _ in VALUE_FLAGS.values()})
    words, bad, rest = [], None, False
    args = iter(argv)
    for arg in args:
        flag, eq, value = arg.partition("=")
        if rest or not arg.startswith("-") or arg == "-":
            words.append(arg)
        elif arg == "--":
            rest = True
        elif flag in VALUE_FLAGS:
            value = value if eq else next(args, None)
            if flag == "--prefix" and (value is None or value.startswith("-")):
                value = ""  # a flag, or nothing, is no folder: install-cli refuses it (ak2b review 1)
            if value is None and bad is None:
                bad = flag
            elif value is not None:
                opts[VALUE_FLAGS[flag][0]] = value
        elif arg == "--version":
            opts["version"] = True
        elif arg in ALL_FLAGS:
            opts[ALL_FLAGS[arg]] = True
        elif bad is None:
            bad = arg
    return opts, words, bad


class Command:
    Usage, VERBS = Usage, VERBS

    def __init__(self, argv, env, out, err):
        self.opts, self.words, self.bad = parse(argv)
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
                self._not_a_verb(words[0])
        else:
            self.verb = "version" if o["version"] and not o["help"] else "help"
        nouns = words[1:]
        if self.bad is not None:
            self._bad_flag(self.bad)
        if o["version"] and (words or o["help"]):
            self._bad_flag("--version")
        for long, short, key in WRITE_FLAGS + CONFIG_FLAGS + STATUS_FLAGS:
            if o[key] and (long, short, key) not in VERB_FLAGS.get(self.verb, ()):
                self._bad_flag(long)
        for flag, (key, verb) in VALUE_FLAGS.items():
            if o[key] is not None and verb != self.verb:
                self._bad_flag(flag)
        if o["help"] and self.verb != "help":
            return self.help_verb(self.verb)
        return getattr(self, "do_" + self.verb.replace("-", "_"))(nouns)

    def _not_a_verb(self, word, asked_help=False):
        """Packet ak2 R3: a plugin's name with no agentik-<word> on PATH exits 3; any other word
        exits 2, naming the nearest of the verbs and the plugins' names."""
        names = tools.plugin_names(self.env, self.lib)
        own = self.tool[len("agentik-"):]
        if word in names and word != own and not any(
                f["name"] == "agentik-" + word for f in self._on_path()):
            raise Usage("not_installed", "err.verb.plugin", self.say("setup", "--dry-run", word),
                        exit_code=3, word=word, **self.slots())
        near = difflib.get_close_matches(word, [w for w in VERBS + tuple(names) if w != word],
                                         n=1, cutoff=0.6)
        if near:
            # a plugin's name as the remedy never succeeds here, so it gets --help (review 1 F3)
            verb = near[0] in VERBS and not asked_help
            remedy = self.say(near[0]) if verb else self.say("--help")
            raise Usage("unknown_verb", "err.verb.near", remedy,
                        word=word, near=near[0], **self.slots())
        raise Usage("unknown_verb", "err.verb", self.say("--help"), word=word, **self.slots())

    def _bad_flag(self, flag):
        known = list(ALL_FLAGS) + list(VALUE_FLAGS) + ["--version"]
        near = difflib.get_close_matches(flag, known, n=1, cutoff=0.6)
        where = self.say(self.verb) if self.verb and self.verb != "help" else self.say()
        if near and near[0] != flag:
            raise Usage("unknown_flag", "err.flag.near", "%s --help" % where,
                        flag=flag, near=near[0], where=where)
        raise Usage("unknown_flag", "err.flag", "%s --help" % where, flag=flag, where=where)

    def fail(self, u):
        if self.opts["json"]:
            self.t.json({"schema": SCHEMA % (self.verb or "usage"), "ok": False,
                         "error": {"code": u.code, "message": self.t.text(u.mid, **u.values),
                                   "remedy": u.remedy}})
        else:
            self.t.error(u.mid, **u.values)
        return u.status

    def _no_nouns(self, nouns):
        if nouns:
            where = self.say(self.verb)
            raise Usage("extra_word", "err.extra", "%s --help" % where,
                        word=nouns[0], where=where)

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
            self._no_nouns(nouns[1:])
        if nouns:
            if nouns[0] not in VERBS:
                self._not_a_verb(nouns[0], asked_help=True)
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
        if not t.quiet:  # the plan read for its close, as the dry run builds it (row sm2 R3)
            steps = plan.build(plan.default_set(self.lib), self.env, self.lib, self.tool, self.version)
            t.hint("hint.help" if any(s["n"] <= 5 and s["state"] != "ok" for s in steps)
                   else "hint.help.done", **self.slots())
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
            raise Usage("no_version", "err.version", "claude plugin install suite@agentik",
                        **self.slots(), path=path)
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
                raise Usage("bad_name", "err.setup.name", self.say("setup", "--dry-run"),
                            name=noun, **self.slots())
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


def main(argv=None, env=None, out=None, err=None):
    agentik_install.restore_parent_env()
    try:
        command = Command(sys.argv[1:] if argv is None else argv, os.environ if env is None else env, out, err)
    except (OSError, ValueError):  # the catalogue: absent, unreadable or not well formed
        return term.unreadable(term.catalogue.PATH, err)
    return command.run()
