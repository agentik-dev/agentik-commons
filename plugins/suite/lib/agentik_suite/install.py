"""install-cli: the suite's command on the terminal's PATH (packet ak2b R3).

`install-cli [--prefix P] [--dry-run] [--force]` runs agentik_install.install, never its
install_cli, and says what it did through term: the result on stdout in one line, or the one line
that a newer command stays where `--force` is absent (row up3-forward-only R2), the door's fate when it stays,
the prune's lines where a tree went or it failed, and on stderr one hint with the PATH line
when <prefix>/bin is off PATH. An OSError, KeyError or ValueError from the install is exit 1
with one line; a --prefix with no folder after it is exit 2.
"""
import os

import agentik_install

from . import plan

SCHEMA = "agentik.install-cli/1"
KEYS = ("launcher", "tree", "version", "door", "door_fate", "on_path")


def do_install_cli(cmd, nouns):
    o, t = cmd.opts, cmd.t
    home = cmd.env.get("HOME")
    cmd._no_nouns(nouns)
    again = cmd.say("install-cli")
    if o["prefix"] == "":   # none given, a flag after it, or '': never HOME's by default
        raise cmd.Usage("missing_value", "err.install.prefix", again + " --prefix <folder>", **cmd.slots())
    try:
        done = agentik_install.install(o["prefix"], cmd.env, dry_run=o["dry_run"], force=o["force"])
    except (OSError, KeyError, ValueError) as e:
        raise cmd.Usage("install_failed", "err.install", again, exit_code=1,
                        why=str(e) or type(e).__name__, **cmd.slots())
    if o["json"]:
        obj = {"schema": SCHEMA, "ok": True}
        obj.update((k, done[k]) for k in KEYS)
        obj["dry_run"] = bool(o["dry_run"])
        if done["kept"]:   # the newer version left in place; absent where this one was placed
            obj["kept"] = done["kept"]
        t.json(obj)
        return 0
    if done["kept"]:
        t.line("install.newer", launcher=plan.shown(done["launcher"], home), have=done["kept"],
               want=done["version"])
        return 0
    if o["dry_run"]:
        t.line("install.dry", launcher=done["launcher"], version=done["version"])
    else:
        t.line("install.done", launcher=plan.shown(done["launcher"], home), version=done["version"],
               door=plan.shown(done["door"], home))
    if done["door_fate"] != "write":
        t.line("install.door." + done["door_fate"], door=plan.shown(done["door"], home))
    for line in agentik_install.prune_news(done["pruned"]):
        if not line.startswith("the door "):    # the module's own word for the fate said above
            t.line("install.pruned", line=line)
    if not done["on_path"]:
        bin_dir = os.path.dirname(done["launcher"])
        t.hint("hint.install.path", line='export PATH="%s:$PATH"' % bin_dir)
    return 0
