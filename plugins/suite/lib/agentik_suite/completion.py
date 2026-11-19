"""`completion zsh|bash`, a script that calls the command back at each Tab, and the callback,
`completion words -- WORD...` (row ak12-polish).

The script holds no word (D1): at a Tab it runs the command as the line names it with the words
up to the cursor, offers each name that comes back, and falls to the shell's own file completion
on an empty answer. The callback reads the suite's tables, the finder's listing and the describe
cache where its stamp matches; it starts no process, writes nothing and refuses no line (D2). A
name is a name by `NOUN` or a flag of the tables, and a summary one plain line cut to 80 columns,
so what a tool's describe holds is data and never shell text (D4).
"""
from . import config, doctor, init, issue, plan, term, tools

SHELLS = ("zsh", "bash")
CALLBACK = "words"
SCHEMA = "agentik.completion/1"
WIDTH = 80  # a summary's columns
VALUES = {"--kind": init.kinds}  # a value flag whose values a table holds: the lib's own list

ZSH = r"""#compdef agentik agentik-suite
# agentik's words at a Tab, for zsh: `agentik help completion` shows the line for ~/.zshrc;
# as a file named _agentik on fpath it completes too.
_agentik() {
    local -a found
    local line
    for line in "${(@f)$("${words[1]}" completion words -- "${(@)words[2,CURRENT]}" 2>/dev/null)}"; do
        [[ -n "$line" ]] && found+=("${${line%%$'\t'*}//:/\\:}:${line#*$'\t'}")
    done
    if (( ${#found} )); then
        _describe -t words word found
    else
        _files
    fi
}
if [[ "${funcstack[1]}" == _agentik ]]; then
    _agentik "$@"
else
    (( ${+functions[compdef]} )) || { autoload -Uz compinit && compinit; }
    compdef _agentik agentik agentik-suite
fi
"""

BASH = r"""# agentik's words at a Tab, for bash 3.2 and later: `agentik help completion` shows the line
# for ~/.bashrc.
_agentik() {
    local name rest
    COMPREPLY=()
    while IFS=$'\t' read -r name rest; do
        [ -n "$name" ] && COMPREPLY[${#COMPREPLY[@]}]="$name"
    done <<_AGENTIK_
$("${COMP_WORDS[0]}" completion words -- "${COMP_WORDS[@]:1:$COMP_CWORD}" 2>/dev/null)
_AGENTIK_
}
complete -o default -F _agentik agentik agentik-suite
"""

SCRIPTS = {"zsh": ZSH, "bash": BASH}


def takes(nouns):
    """True where `completion` takes these words: one shell, or the callback with any words."""
    return nouns[:1] == [CALLBACK] or len(nouns) == 1 and nouns[0] in SHELLS


def do_completion(cmd, nouns):
    """R1: the script for one shell, on stdout as it is, or in `agentik.completion/1`; R2: the
    callback."""
    if nouns[:1] == [CALLBACK]:
        return words(cmd, nouns[1:])
    remedy = cmd.say("help", "completion")
    if not nouns:
        raise cmd.Refusal("no_shell", "err.completion.none", remedy)
    if nouns[0] not in SHELLS:
        raise cmd.Refusal("bad_shell", "err.completion.shell", remedy, word=nouns[0])
    if len(nouns) > 1:
        raise cmd.Refusal("extra_word", "err.completion.extra", remedy, word=nouns[1])
    script = SCRIPTS[nouns[0]]
    if cmd.opts["json"]:
        cmd.t.json({"schema": SCHEMA, "ok": True, "shell": nouns[0], "script": script})
    else:
        cmd.t.verbatim(script.rstrip("\n"))
    return 0


def words(cmd, line):
    """R2: `name<TAB>summary` a line for the last of `line`, the earlier words its context; exit 0
    whatever the words."""
    try:
        rows = _rows(cmd, line)
    except Exception:  # a Tab is never an error (D2): a fault offers nothing, and the shell its files
        rows = []
    if cmd.opts["json"]:
        cmd.t.json({"schema": SCHEMA, "ok": True, "words": rows})
    elif rows:
        cmd.t.verbatim("\n".join("%s\t%s" % (r["name"], r["summary"]) for r in rows))
    return 0


def _rows(cmd, line):
    from . import cli  # cli imports this module at its top
    cur = line[-1] if line else ""
    flags = {f for table in (cli.FLAGS,) + tuple(cli.VERB_FLAGS.values()) for row in table
             for f in row[:2] if f} | set(cli.VALUE_FLAGS)
    rows, seen = [], set()
    for name, said in _offered(cmd, line, cli):
        if not isinstance(name, str) or name in seen or not name.startswith(cur):
            continue
        if not (cli.NOUN.match(name) or name in flags) or name in cli.HOOKS:  # R5
            continue
        seen.add(name)
        rows.append({"name": name, "summary": summary(said)})
    return rows


def summary(text):
    """R5: a tool's text as one plain line with no tab, cut to WIDTH columns; else empty."""
    if not isinstance(text, str):
        return ""
    text = (tools.plain(tools.one_line(text)) or "").replace("\t", " ")
    cut, used = "", 0
    for c in text:
        used += term.columns(c)
        if used > WIDTH:
            break
        cut += c
    return cut.strip()


def _offered(cmd, line, cli):
    """[(name, summary)] for the last word of `line`, by D3; the caller filters by its prefix."""
    if not line:
        return []
    cur, before = line[-1], list(line[:-1])
    if before and before[-1] in cli.VALUE_FLAGS and "--" not in before:
        return [(v, "") for v in VALUES.get(before[-1], lambda lib: ())(cmd.lib)]
    said = cli._parse(before)[1]
    own = cmd.tool[len("agentik-"):] if cmd.tool.startswith("agentik-") else cmd.tool
    suite = said[:1] == [own]  # `suite` first: the rest is the suite's own line
    said = said[1:] if suite else said
    flag = cur.startswith("-") and "--" not in before
    if not said:
        if flag:
            return []
        return _verbs(cmd, cli) + ([] if suite else _first(cmd))
    head, nouns = said[0], said[1:]
    if head in cli.VERBS:
        return _flags(cmd, cli, head, before) if flag else _nouns(cmd, cli, head, nouns)
    if suite or nouns or flag:
        return []
    return _tool_verbs(cmd, head)


def _text(cmd, mid):
    """The message `mid`, or no summary where the catalogue has none: a flag added to a table
    before its message is still offered (R4)."""
    return cmd.t.text(mid) if mid in cmd.t.messages else ""


def _verbs(cmd, cli):
    return [(v, _text(cmd, "verb." + v.replace("-", "_"))) for v in cli.VERBS]


def _flags(cmd, cli, verb, before):
    """R4: the shared flags, the verb's own and its flags with a value, less the test hooks and
    any flag on the line, by either spelling; each with its `flag.*` message."""
    on = {w.partition("=")[0] for w in before}
    found = []
    for long, short, key in cli.FLAGS + cli.VERB_FLAGS.get(verb, ()):
        if long not in on and short not in on:
            found.append((long, _text(cmd, "flag." + key)))
    for flag, (key, owner) in cli.VALUE_FLAGS.items():
        if owner == verb and flag not in cli.HOOKS and flag not in on:
            found.append((flag, _text(cmd, "flag." + key)))
    return found


def _nouns(cmd, cli, verb, nouns):
    """D3: setup the names it plans, update and remove the installed ones, each not yet given;
    the first noun of config (the tools), completion (the shells), issue (its words) and help
    (the verbs and the tools)."""
    if verb == "setup":
        return [(n, "") for n in plan.known(cmd.env, cmd.lib) if n not in nouns]
    if verb in ("update", "remove"):
        return [(n, "") for n in tools.installed(cmd.env, cmd.lib) if n not in nouns]
    if nouns:
        return []
    if verb == "config":
        return [(e["name"], "") for e in config.Reader(cmd).entries()]
    if verb == "completion":
        return [(s, "") for s in SHELLS]
    if verb == "issue":
        return [(w, "") for w in issue.WORDS]
    if verb == "help":
        return _verbs(cmd, cli) + _first(cmd, claims=False)
    return []


def _listed(cmd):
    """Each tool of the finder's listing with a command, as `Command._tools(survey=False)` reads
    it, and its answer from the describe cache, or None (R3)."""
    r = config.Reader(cmd)
    entries = [e for e in r.entries() if e["name"] != r.suite and e["exe"]]
    return [(e, tools.cached(e["name"], e["exe"], cmd.env)) for e in entries]


def _first(cmd, claims=True):
    """D3's first word past the verbs: each tool with a command, then each word one cached
    describe claims and that counts, as `agentik <word>` would run it."""
    listed = _listed(cmd)
    found = [(e["name"], (answer or {}).get("summary")) for e, answer in listed]
    if not claims:
        return found
    described = {e["name"]: ("answers", answer) for e, answer in listed if answer is not None}
    counted = [c for c in doctor.claims(cmd, [e for e, _ in listed], described) if c["counts"]]
    for c in counted:
        if [d["verb"] for d in counted].count(c["verb"]) == 1:
            verbs = described[c["tool"]][1].get("verbs") or ()
            gloss = [v.get("summary") for v in verbs if isinstance(v, dict) and v.get("name") == c["verb"]]
            found.append((c["verb"], gloss[0] if gloss else ""))
    return found


def _tool_verbs(cmd, head):
    """D3: after a tool's name, its first-level verbs from the cache; none without an answer."""
    for e, answer in _listed(cmd):
        if e["name"] == head:
            verbs = (answer or {}).get("verbs") or ()
            return [(v.get("name"), v.get("summary")) for v in verbs if isinstance(v, dict)]
    return []
