"""install-cli: the suite's command on the terminal's PATH (packet ak2b R3).

`install-cli [--prefix P] [--dry-run]` runs agentik_install.install, never its install_cli, and
says what it did through term: the result on stdout in one line, the door's fate when it stays,
each line of the prune, and on stderr one hint with the PATH line when <prefix>/bin is off PATH.
An OSError, KeyError or ValueError from the install is exit 1 with one line; a --prefix
with no folder after it is exit 2.
"""
import os

import agentik_install

SCHEMA = "agentik.install-cli/1"
KEYS = ("launcher", "tree", "version", "door", "door_fate", "on_path")


def do_install_cli(cmd, nouns):
    o, t = cmd.opts, cmd.t
    cmd._no_nouns(nouns)
    again = "%s install-cli" % cmd.tool
    if o["prefix"] == "":   # none given, a flag after it, or '': never HOME's by default
        raise cmd.Usage("missing_value", "err.install.prefix", again + " --prefix <folder>", tool=cmd.tool)
    try:
        done = agentik_install.install(o["prefix"], cmd.env, dry_run=o["dry_run"])
    except (OSError, KeyError, ValueError) as e:
        raise cmd.Usage("install_failed", "err.install", again, status=1,
                        why=str(e) or type(e).__name__, tool=cmd.tool)
    if o["json"]:
        obj = {"schema": SCHEMA, "ok": True}
        obj.update((k, done[k]) for k in KEYS)
        obj["dry_run"] = bool(o["dry_run"])
        t.json(obj)
        return 0
    if o["dry_run"]:
        t.line("install.dry", launcher=done["launcher"], version=done["version"])
    else:
        t.line("install.done", launcher=done["launcher"], version=done["version"], tree=done["tree"])
    if done["door_fate"] != "write":
        t.line("install.door." + done["door_fate"], door=done["door"])
    for line in done["pruned"]:
        if not line.startswith("the door "):    # the module's own word for the fate said above
            t.line("install.pruned", line=line)
    if not done["on_path"]:
        bin_dir = os.path.dirname(done["launcher"])
        t.hint("hint.install.path", line='export PATH="%s:$PATH"' % bin_dir)
    return 0
