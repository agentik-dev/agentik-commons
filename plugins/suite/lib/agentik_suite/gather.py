"""The facts an issue may hold: a closed list, each typed and bounded (hq design/22 §3 item 2).

`facts` reads the machine once and gives one object, `agentik.issue-facts/1`; it reads named
keys only, prints nothing and scrubs nothing. A typed value is validated: a value that is not of
its type reads `unreadable`, an absent one None. A free value (a doctor row's name and detail,
the command run, each output line, the words expected) is returned whole up to a read cap, so
the caller can scrub it before `bound` cuts it to the table below; `map_free` reaches each free
value in a fixed order. The tools an issue may name are those of `public.json`, beside the
package, made from the suite's own marketplace file: a tool or plugin outside it is counted and
never named. Never read: a transcript, a prompt, a run's id, a ledger, a CLAUDE.md, a
charter or any file of a repo, the working folder, PATH's value or any other environment value
(PATH is walked, CLAUDECODE is tested), a settings or state file's content, a key or a token.
"""
import json
import os
import re

from . import plan

SCHEMA = "agentik.issue-facts/1"
DOCTOR = "agentik.doctor/1"
PUBLIC = "public.json"
NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
REPO = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?/[A-Za-z0-9._-]+\Z")


def load_public(lib):
    """{"marketplace": NAME, "tools": {tool: "OWNER/REPO"}} from `lib`/public.json; ValueError for
    an absent file or any other shape."""
    found = plan._read_json(os.path.join(lib, PUBLIC))
    if not isinstance(found, dict) or set(found) != {"marketplace", "tools"}:
        raise ValueError("%s: not {marketplace, tools}" % PUBLIC)
    market, tools = found["marketplace"], found["tools"]
    if not isinstance(market, str) or not NAME.match(market):
        raise ValueError("%s: marketplace is no name" % PUBLIC)
    if not isinstance(tools, dict) or not tools:
        raise ValueError("%s: tools is no table" % PUBLIC)
    for tool, repo in tools.items():
        if not NAME.match(tool) or not isinstance(repo, str) or not REPO.match(repo) or \
                repo.split("/")[1] in (".", ".."):
            raise ValueError("%s: %r is no tool and OWNER/REPO" % (PUBLIC, tool))
    return {"marketplace": market, "tools": dict(tools)}
