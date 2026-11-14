"""The homes of row fk1-sources (hq design/25 §2 item 10), with a made-up tool: each is a temp HOME
holding Claude Code's `installed_plugins.json` and `known_marketplaces.json`, each root at
`.claude/plugins/cache/<marketplace>/<tool>/<version>`. A command is an executable stub,
`bin/agentik-<tool>` under a root; a launcher holds `VERSION=` and `TREE=` lines. Rows fk2 and
fk2b import this one set. Nothing here writes outside the HOME it is given."""
import json
import os

T = "murmur"
SOURCE = "agentik-dev/agentik-commons"
HOMES = ("hA", "hB", "hC", "hD", "hE", "hF", "hG", "hH", "hI", "hJ", "hK", "pA", "pB", "pC")
STUB = "#!/bin/sh\nexit 0\n"


class FkHome:
    def __init__(self, home, tool=T):
        self.home, self.tool = home, tool
        self.own, self.fork = tool + "@agentik", tool + "@acme-tools"
        self.plugins = os.path.join(home, ".claude", "plugins")
        self.table = {}
        self.known = {"agentik": {"source": {"source": "github", "repo": SOURCE}}}
        self.cmd = self.link = self.launch = None
        self.cwd = home
        self.write()

    def write(self):
        os.makedirs(self.plugins, exist_ok=True)
        with open(os.path.join(self.plugins, "installed_plugins.json"), "w") as fh:
            json.dump({"version": 2, "plugins": self.table}, fh)
        with open(os.path.join(self.plugins, "known_marketplaces.json"), "w") as fh:
            json.dump(self.known, fh)

    def root(self, pid, version):
        return os.path.join(self.plugins, "cache", pid.partition("@")[2], self.tool, version)

    def folder(self, pid, version, command=False):
        """A plugin's root with its manifest, and its command when asked; no entry."""
        root = self.root(pid, version)
        os.makedirs(os.path.join(root, ".claude-plugin"), exist_ok=True)
        with open(os.path.join(root, ".claude-plugin", "plugin.json"), "w") as fh:
            json.dump({"name": self.tool, "version": version}, fh)
        if command:
            self.cmd = self.file(os.path.join(root, "bin", "agentik-" + self.tool), STUB)
        return root

    def install(self, pid, version, command=False, scope="user", project=None):
        root = self.folder(pid, version, command)
        entry = {"scope": scope, "version": version, "installPath": root}
        if project:
            entry["projectPath"] = project
        self.table.setdefault(pid, []).append(entry)
        self.write()
        return root

    def file(self, path, body):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(body)
        os.chmod(path, 0o755)
        return path

    def launcher(self, where, version, tree=True):
        body = "#!/bin/sh\nVERSION=%s\n" % version
        if tree:
            body += "TREE=%s\n" % os.path.join(self.home, ".local", "share", "agentik", self.tool, version)
        self.launch = self.file(os.path.join(self.home, where, "agentik-" + self.tool), body + "exit 0\n")
        return self.launch

    def user_file(self, text, base=None):
        path = os.path.join(base or os.path.join(self.home, ".config"), "agentik", "suite", "config.yaml")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)
        return path

    def terminal(self, *more):
        """The terminal's PATH, with `more` after ~/.local/bin."""
        parts = [os.path.join(self.home, "bin"), os.path.join(self.home, ".local", "bin")]
        return os.pathsep.join(parts + list(more) + ["/usr/bin", "/bin"])

    def bins(self):
        """Every root's bin/, in the table's order."""
        return [os.path.join(e["installPath"], "bin") for v in self.table.values() for e in v]

    def env(self, path=None, **more):
        env = {"HOME": self.home, "PATH": path or self.terminal()}
        env.update(more)
        return env


def build(name, home, tool=T):
    """The home `name` in the folder `home`."""
    h = FkHome(home, tool)
    U, F = h.own, h.fork
    if name in ("hA", "hC", "hD", "hJ", "pA"):
        h.install(F, "0.12.7" if name == "pA" else "0.12.6", command=name != "hA")
        if name == "hC":
            h.link = os.path.join(home, ".local", "bin", "agentik-" + tool)
            os.makedirs(os.path.dirname(h.link), exist_ok=True)
            os.symlink(h.cmd, h.link)
    elif name == "hE":
        h.install(F, "0.12.6-acme.1")
    elif name == "hF":
        h.install(U, "0.13.0")
    elif name == "pB":
        h.project = os.path.join(home, "work", "app")
        os.makedirs(os.path.join(h.project, "sub"))
        h.install(U, "0.11.0", scope="project", project=h.project)
        h.install(U, "0.13.0")
        h.launcher(os.path.join(".local", "bin"), "0.13.0")
    elif name == "hB":
        h.install(U, "0.13.0", command=True)
        h.own_cmd = h.cmd
        h.install(F, "0.12.6")
    elif name == "hH":
        h.install(U, "0.12.6")
        h.install(F, "0.12.7")
    elif name in ("hI", "pC"):
        h.install(U, "0.13.0", command=True)
        h.install(F, "0.12.6", command=True)
        if name == "hI":
            h.launcher(os.path.join(".local", "bin"), "0.12.6")
        else:
            h.launcher(os.path.join(".local", "bin"), "0.13.0")
            h.launcher("bin", "0.12.6")
    elif name == "hG":
        h.folder(F, "0.12.6")
    elif name == "hK":
        h.launcher("bin", "0.12.6", tree=False)
    if name == "hJ":
        h.user_file("sources:\n  %s: %s\n  paint: ~/src/paint-fork/plugin\n" % (tool, F))
        h.repo = os.path.join(home, "repo")
        os.makedirs(os.path.join(h.repo, ".git"))
        os.makedirs(os.path.join(h.repo, ".claude", "agentik"))
        with open(os.path.join(h.repo, ".claude", "agentik", "config.yaml"), "w") as fh:
            fh.write("suite:\n  sources:\n    %s: /elsewhere/plugin\n" % tool)
    return h
