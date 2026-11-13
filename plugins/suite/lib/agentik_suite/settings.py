"""The suite's own settings: a reader of GUIDE §3's strict YAML subset, and the two files read.

The subset: nested mappings by indentation of spaces, scalars, flat lists (`- x` items or
`[a, b]`), `{k: v}` one level deep, comments. Anything else (a tab, an anchor, a block scalar, a
list of mappings, a key given twice) is a Fault naming its line. The reader keeps each key's line,
by its dotted path.

The user file, `${XDG_CONFIG_HOME:-~/.config}/agentik/suite/config.yaml`, written by hand: its
`checkouts`, a flat list of paths, and `watchers`, a name to `match`, `start`, and optionally
`beat` and `writer`. The repo file, `.claude/agentik/config.yaml` in the nearest folder upward
from the cwd holding `.git`: its `suite` section's `kind`, whose one value is `hq`. Each of the
three keys is read from its one file; anywhere else in the suite's reach it is an unknown key.
"""
import json
import os
import re

KEY = re.compile(r"([A-Za-z0-9_][A-Za-z0-9_-]*):(?:[ ]+(.*))?\Z")
NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
REFUSED = "&*|>!%@`"
WATCHER_FIELDS = ("match", "start", "beat", "writer")
KINDS = ("hq",)


class Fault(Exception):
    def __init__(self, line, why):
        Exception.__init__(self, why)
        self.line, self.why = line, why


def _uncomment(raw):
    """The line without its comment: a `#` at the start or after a space, outside quotes."""
    quote = None
    for i, ch in enumerate(raw):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"" and (i == 0 or raw[i - 1] in " [{,:"):
            quote = ch
        elif ch == "#" and (i == 0 or raw[i - 1] == " "):
            return raw[:i].rstrip(" ")
    return raw.rstrip(" ")


def _split(inner, n):
    parts, quote, start = [], None, 0
    for i, ch in enumerate(inner):
        if quote:
            quote = None if ch == quote else quote
        elif ch in "'\"":
            quote = ch
        elif ch in "[]{}":
            raise Fault(n, "a nested list or mapping")
        elif ch == ",":
            parts.append(inner[start:i])
            start = i + 1
    parts.append(inner[start:])
    parts = [p.strip() for p in parts]
    if parts == [""]:
        return []
    if "" in parts:
        raise Fault(n, "an empty item")
    return parts


def _scalar(text, n):
    if not text:
        return None
    if text[0] in REFUSED:
        raise Fault(n, "%s, which the subset does not take" % text[0])
    if text[0] == '"':
        try:
            value = json.loads(text)
        except ValueError:
            raise Fault(n, "a quoted value that does not close")
        if not isinstance(value, str):
            raise Fault(n, "a quoted value that does not close")
        return value
    if text[0] == "'":
        if len(text) < 2 or not text.endswith("'") or "'" in text[1:-1].replace("''", ""):
            raise Fault(n, "a quoted value that does not close")
        return text[1:-1].replace("''", "'")
    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if text in ("null", "~"):
        return None
    if NUMBER.match(text):
        return float(text) if "." in text else int(text)
    if ": " in text or text.endswith(":") or text.startswith("- ") or text in ("-", "---"):
        raise Fault(n, "a value that reads as a key or an item")
    return text


def _value(text, n):
    if text.startswith("["):
        if not text.endswith("]"):
            raise Fault(n, "a list that does not close")
        return [_scalar(p, n) for p in _split(text[1:-1], n)]
    if text.startswith("{"):
        if not text.endswith("}"):
            raise Fault(n, "a mapping that does not close")
        found = {}
        for part in _split(text[1:-1], n):
            m = KEY.match(part)
            if not m or m.group(1) in found:
                raise Fault(n, "a mapping item that is not one key and a value")
            found[m.group(1)] = _scalar(m.group(2) or "", n)
        return found
    return _scalar(text, n)


def parse(text):
    """(tree, lines): the file's mappings, and each key's line by its dotted path."""
    root, lines = {}, {}
    stack = [(0, root, "")]  # the open mappings: indent, mapping, path prefix
    open_key = None  # (indent, mapping, key, path) of a key that has no value on its line
    open_list = None  # (indent, list) of the list whose items are being read
    for n, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw:
            raise Fault(n, "a tab; the subset indents with spaces")
        body = _uncomment(raw)
        if not body.strip():
            continue
        indent = len(body) - len(body.lstrip(" "))
        content = body.strip()
        if content == "-" or content.startswith("- "):
            if open_key and indent >= open_key[0]:
                items = []
                open_key[1][open_key[2]] = items
                open_list, open_key = (indent, items), None
            elif not (open_list and indent == open_list[0]):
                raise Fault(n, "a list item out of place")
            item = content[2:].strip()
            if item[:1] in ("[", "{") or item.startswith("- ") or KEY.match(item):
                raise Fault(n, "a list item that is not a plain value")
            open_list[1].append(_scalar(item, n))
            continue
        open_list = None
        if open_key and indent > open_key[0]:
            child = {}
            open_key[1][open_key[2]] = child
            stack.append((indent, child, open_key[3] + "."))
        open_key = None
        while stack[-1][0] > indent:
            stack.pop()
        if stack[-1][0] != indent:
            raise Fault(n, "an indent that matches no key above it")
        m = KEY.match(content)
        if not m:
            raise Fault(n, "a line that is not a key and a value")
        mapping, prefix = stack[-1][1], stack[-1][2]
        key, path = m.group(1), stack[-1][2] + m.group(1)
        if key in mapping:
            raise Fault(n, "%s given twice" % path)
        lines[path] = n
        if m.group(2) is None:
            mapping[key] = None
            open_key = (indent, mapping, key, prefix + key)
        else:
            mapping[key] = _value(m.group(2).strip(), n)
    return root, lines


def read(path):
    """(present, tree, lines); a Fault for a file outside the subset or one that cannot be read."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except FileNotFoundError:
        return False, {}, {}
    except (OSError, UnicodeDecodeError):
        raise Fault(0, "a file that cannot be read")
    tree, lines = parse(text)
    return True, tree, lines


def user_path(env):
    base = env.get("XDG_CONFIG_HOME") or os.path.join(env.get("HOME") or "", ".config")
    return os.path.join(base, "agentik", "suite", "config.yaml")


def repo_path(cwd):
    """The repo file of the nearest folder upward holding `.git`, or None outside a repo."""
    if cwd is None:
        return None
    here = os.path.abspath(cwd)
    while True:
        if os.path.exists(os.path.join(here, ".git")):
            return os.path.join(here, ".claude", "agentik", "config.yaml")
        up = os.path.dirname(here)
        if up == here:
            return None
        here = up


def _setting(key, value, default, kind, summary, layer, path, line, block, choices=None):
    return {"key": key, "value": value, "default": default, "type": kind, "choices": choices,
            "summary": summary,
            "source": {"layer": layer if line else "default", "path": path if line else None,
                       "line": line},
            "change": {"kind": "edit", "command": None, "path": path, "block": block,
                       "note": "written by hand; no verb writes it"},
            "live": True,
            "values": [{"layer": layer, "value": value}] if line else []}


def resolve(env, cwd, summaries):
    """The suite's `agentik.config/1` body: layers, settings, warnings. A Fault carries `path`."""
    user, repo = user_path(env), repo_path(cwd)
    layers, settings, warnings = [], [], []
    try:
        present, tree, lines = read(user)
    except Fault as f:
        f.path = user
        raise
    layers.append({"name": "user", "path": user, "present": present, "travels": False})
    for key in tree:
        if key not in ("checkouts", "watchers"):
            warnings.append({"path": user, "line": lines[key], "key": key, "reason": "unknown"})
    checkouts = tree.get("checkouts")
    if checkouts is not None and not isinstance(checkouts, list):
        raise _at(Fault(lines["checkouts"], "checkouts is not a flat list of paths"), user)
    settings.append(_setting("checkouts", checkouts if checkouts is not None else [], [], "list",
                             summaries["checkouts"], "user", user, lines.get("checkouts"),
                             "checkouts:\n  - <path>"))
    watchers = tree.get("watchers") or {}
    if not isinstance(watchers, dict):
        raise _at(Fault(lines["watchers"], "watchers is not a mapping of names"), user)
    for name, fields in watchers.items():
        if not isinstance(fields, dict):
            raise _at(Fault(lines["watchers." + name], "watcher %s is not a mapping" % name), user)
        for field, value in fields.items():
            path = "watchers.%s.%s" % (name, field)
            if field not in WATCHER_FIELDS:
                warnings.append({"path": user, "line": lines.get(path), "key": path, "reason": "unknown"})
                continue
            settings.append(_setting(path, value, None, "string", summaries["watcher." + field],
                                     "user", user, lines.get(path),
                                     "watchers:\n  %s:\n    %s: <value>" % (name, field)))
    kind, kind_line = None, None
    if repo:
        try:
            present, tree, lines = read(repo)
        except Fault as f:
            f.path = repo
            raise
        section = tree.get("suite") if isinstance(tree.get("suite"), dict) else {}
        for key in section:
            if key != "kind":
                warnings.append({"path": repo, "line": lines.get("suite." + key), "key": "suite." + key,
                                 "reason": "unknown"})
        kind, kind_line = section.get("kind"), lines.get("suite.kind")
        if kind is not None and kind not in KINDS:
            warnings.append({"path": repo, "line": kind_line, "key": "kind", "reason": "choice",
                             "value": kind})
    else:
        present = False
    layers.append({"name": "repo", "path": repo, "present": present, "travels": False})
    settings.append(_setting("kind", kind, None, "choice", summaries["kind"], "repo",
                             repo or ".claude/agentik/config.yaml", kind_line,
                             "suite:\n  kind: hq", choices=list(KINDS)))
    return {"layers": layers, "settings": settings, "warnings": warnings}


def _at(fault, path):
    fault.path = path
    return fault
