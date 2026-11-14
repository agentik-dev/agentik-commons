"""Row fk2b-reads: the doctor and `config` say which source stands, and a fork's name stays under
one key, `source`.

Each home is fk_homes' in a temp HOME with fk2's stub `claude` and the `agentik` marketplace's own
file; a set-up home also holds the default set, the suite's launcher and the door in
`~/.local/bin`, so the suite's own steps read ok. No test reads the real home."""
import json
import os
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fk_homes import HOMES, T, build, describing  # noqa: E402
from test_agentik_suite import LAUNCHER, LIB, PLUGIN  # noqa: E402
from test_fk2_plan import Base  # noqa: E402
from agentik_suite import plan  # noqa: E402
import agentik_install  # noqa: E402

U, F = T + "@agentik", T + "@acme-tools"
USER = "~/.config/agentik/suite/config.yaml"


class Reads(Base):
    def made(self, name, tool=T, setup=True):
        self.made_n = getattr(self, "made_n", 0) + 1
        path = os.path.join(self.tmp, "%s-%s-%d" % (name, tool, self.made_n))
        os.mkdir(path)
        h = build(name, path, tool).ready()
        if setup:
            self.set_up(h)
        return h

    def set_up(self, h):
        """The default set installed (no command), the suite's launcher and the door placed."""
        for n in plan.default_set(str(LIB)):
            if n == h.tool:
                continue
            root = os.path.join(h.plugins, "cache", "agentik", n, "1.0.0")
            os.makedirs(os.path.join(root, ".claude-plugin"), exist_ok=True)
            with open(os.path.join(root, ".claude-plugin", "plugin.json"), "w") as fh:
                json.dump({"name": n, "version": "1.0.0"}, fh)
            h.table["%s@agentik" % n] = [{"scope": "user", "version": "1.0.0", "installPath": root}]
        h.write()
        bindir = os.path.join(h.home, ".local", "bin")
        h.file(os.path.join(bindir, "agentik-suite"),
               "#!/bin/sh\nVERSION=%s\nexit 0\n" % agentik_install.version(str(LIB)))
        shutil.copy(str(PLUGIN / "bin" / "agentik"), os.path.join(bindir, "agentik"))

    def go(self, h, *args, more=(), cwd=None, **extra):
        env = self.env(h, *more, **extra)
        p = subprocess.run([str(LAUNCHER)] + list(args), capture_output=True, text=True, env=env,
                           cwd=cwd or h.cwd, timeout=60)
        return p.returncode, p.stdout.replace(h.home, "~"), p.stderr

    def json_of(self, h, *args, **kw):
        code, out, err = self.go(h, *args, "--json", **kw)
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def group(self, out, name):
        """The lines of `name`'s group: its line and the lines under it, up to the next group."""
        lines, found = out.splitlines(), []
        for i, line in enumerate(lines):
            if not line.startswith(" ") and line.split()[1:2] == [name]:
                found.append(line)
                for more in lines[i + 1:]:
                    if not more.startswith("    "):
                        break
                    found.append(more)
                return found
        self.fail("no group %s in:\n%s" % (name, out))

    def checks(self, obj, name):
        return [c for g in obj["tools"] if g["name"] == name for c in g["checks"]]


class Fk2bTest(Reads):
    # line 1
    def test_1_no_fork_bytes_but_under_source(self):
        for tool in (T, "session"):
            for name in HOMES:
                h = self.made(name, tool, setup=False)
                for verb in ("doctor", "config"):
                    obj = self.json_of(h, verb)
                    for row in obj["tools"]:
                        self.assertIn("source", row, (name, verb))
                        row.pop("source")
                    self.assertNotIn("acme", json.dumps(obj), (tool, name, verb))
                    if name == "hE" and verb == "doctor":
                        row = [g for g in self.json_of(h, verb)["tools"] if g["name"] == tool][0]
                        self.assertEqual(row["source"]["version"], "0.12.6-acme.1")

    def test_1_a_fork_that_answers_describe(self):
        """Review 1 F1: hE's fork answers `describe --json` with its own version; `config --json`'s
        row keeps that version under `source` alone, and `summary` stays the tool's own sentence."""
        for tool in (T, "session"):
            h = self.made("hE", tool, setup=False)
            h.commands(describing(tool, h.fork, "0.12.6-acme.1"))
            for verb in ("doctor", "config"):
                obj = self.json_of(h, verb, more=h.bins())
                row = [g for g in obj["tools"] if g["name"] == tool][0]
                self.assertEqual(row["source"]["version"], "0.12.6-acme.1", (tool, verb))
                for g in obj["tools"]:
                    g.pop("source")
                self.assertNotIn("acme", json.dumps(obj), (tool, verb))
                if verb == "config":
                    self.assertEqual(row["state"], "answers", row)
                    self.assertIsNone(row["version"], row)
                    self.assertEqual(row["summary"], "A made-up tool.", row)

    def test_1_a_fork_in_the_default_set_is_named_by_its_tool(self):
        h = self.made("hA", "session", setup=False)
        names = [c["name"] for c in self.checks(self.json_of(h, "doctor"), "suite")]
        self.assertIn("plugin session", names)

    # line 2
    def test_2_the_from_line(self):
        h = self.made("hD")
        h.commands()
        for flags in ((), ("--all",)):
            code, out, err = self.go(h, "doctor", *flags)
            self.assertEqual(code, 0, err)
            self.assertIn("    from %s 0.12.6, the only plugin of that name" % F, self.group(out, T))
        h = self.made("hJ")
        h.commands()
        for flags in ((), ("--all",)):
            code, out, err = self.go(h, "doctor", *flags)
            self.assertIn("    from %s 0.12.6, declared at %s:2" % (F, USER), self.group(out, T))

    # line 3
    def test_3_undecided(self):
        h = self.made("hI")
        code, out, err = self.go(h, "doctor")
        self.assertEqual(code, 0, err)
        lines = self.group(out, T)
        self.assertTrue(lines[0].startswith("warn"), lines)
        self.assertIn("2 plugins of this name are installed, and no source is declared", lines[0])
        self.assertIn("    seen: %s 0.13.0, %s 0.12.6" % (U, F), lines)
        self.assertIn("    runs ~/.local/bin/agentik-%s 0.12.6, a placed launcher of no known source" % T,
                      lines)
        close = (out + err).strip().splitlines()[-1].strip()
        self.assertTrue(close.startswith("next: ") and close.endswith("agentik config suite.sources.%s" % T),
                        out + err)

    # line 4
    def test_4_the_gate_and_a_folder_gone(self):
        h = self.made("hJ")
        code, out, err = self.go(h, "doctor")
        self.assertEqual(code, 0, err)
        suite = self.group(out, "suite")
        self.assertTrue([l for l in suite if "sources" in l and "%s names a source and is on no gate list" % USER in l],
                        suite)
        self.assertIn("add this line to ~/.claude/edit-gates: %s" % USER, [l.strip() for l in suite])
        self.assertTrue(self.group(out, "paint")[0].startswith("warn"), out)
        with open(os.path.join(h.home, ".claude", "edit-gates"), "w") as fh:
            fh.write(os.path.join(h.home, ".config", "agentik", "suite", "config.yaml") + "\n")
        code, out, err = self.go(h, "doctor")
        self.assertNotIn("gate list", out)

    # line 5
    def test_5_the_config_reads_warnings(self):
        h = self.made("hJ")
        obj = self.json_of(h, "doctor", cwd=h.repo)
        said = [c for c in self.checks(obj, "suite") if c["name"] == "settings" and c["status"] == "warn"]
        self.assertTrue([c for c in said if "~/repo/.claude/agentik/config.yaml:2" in c["detail"]], said)
        for text, extra, at in (("sources:\n  suite: suite@agentik\n", {}, 2),
                                ("sources:\n  %s: ./fork\n" % T, {}, 2),
                                ("sources:\n  %s: %s\n" % (T, U), {"XDG_CONFIG_HOME": "rel"}, 1)):
            h = self.made("hF")
            base = os.path.join(h.home, "rel") if extra else None
            h.user_file(text, base=base)
            obj = self.json_of(h, "doctor", **extra)
            said = [c for c in self.checks(obj, "suite") if c["name"] == "settings" and c["status"] == "warn"]
            self.assertEqual(len(said), 1, (text, self.checks(obj, "suite")))
            self.assertIn("config.yaml:%d" % at, said[0]["detail"])

    def test_5_a_line_passed_over_reads_no_source_under_the_tool(self):
        """Review 1 F3: a value the config read passes over gives no `from` line and no folder
        warn under the tool; the suite group's settings warn speaks for the line."""
        for value in ("./fork", "''", "\n    x: y"):
            h = self.made("hD")
            h.user_file("sources:\n  %s: %s\n" % (T, value))
            code, out, err = self.go(h, "doctor")
            self.assertEqual(code, 0, err)
            self.assertTrue([l for l in self.group(out, "suite")
                             if "sources.%s at %s:2 is no plugin id or folder" % (T, USER) in l], out)
            lines = self.group(out, T)
            self.assertFalse([l for l in lines if l.startswith("    from")], (value, lines))
            self.assertNotIn("declared folder", out, value)
            details = [c["detail"] for c in self.checks(self.json_of(h, "doctor"), T)]
            self.assertFalse([d for d in details if "folder" in d or "plugins have" in d], (value, details))

    # the named warn (review 1 F2)
    def test_4_the_named_warn_counts_what_is_there(self):
        """Review 1 F2: `named` shows only where the declared source stands, and counts the plugins
        seen with the one that stands; a declared source not installed has its own warn alone."""
        for name, line in (("hD", T + "@other"), ("hF", F)):
            h = self.made(name)
            h.user_file("sources:\n  %s: %s\n" % (T, line))
            details = [c["detail"] for c in self.checks(self.json_of(h, "doctor"), T)]
            self.assertIn("its declared source is not installed", details, (name, line))
            self.assertFalse([d for d in details if "plugins have this name" in d], (name, details))
        h = self.made("hB")
        h.user_file("sources:\n  %s: %s\n" % (T, F))
        details = [c["detail"] for c in self.checks(self.json_of(h, "doctor"), T)]
        self.assertIn("2 plugins have this name; the declared one stands", details)
        self.assertNotIn("its declared source is not installed", details)

    # the gate list without HOME (review 1 F4)
    def test_4_no_home_reads_no_gate_list(self):
        h = self.made("hJ")
        cfg = os.path.join(h.home, ".claude")
        with open(os.path.join(cfg, "edit-gates"), "w") as fh:
            fh.write("~/.config/agentik/suite/config.yaml\n")
        env = self.env(h, CLAUDE_CONFIG_DIR=cfg, XDG_CONFIG_HOME=os.path.join(h.home, ".config"))
        del env["HOME"]
        for flags in ((), ("--json",)):
            p = subprocess.run([str(LAUNCHER), "doctor"] + list(flags), capture_output=True, text=True,
                               env=env, cwd=h.home, timeout=60)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertNotIn("Traceback", p.stderr)
            self.assertNotIn("gate list", p.stdout)
            if flags:
                json.loads(p.stdout)

    # line 6
    def test_6_passed_over(self):
        h = self.made("hB")
        h.commands()
        code, out, err = self.go(h, "doctor", more=h.bins())
        self.assertEqual(code, 0, err)
        first = h.bins()[0].replace(h.home, "~")
        lines = self.group(out, T)
        self.assertTrue([l for l in lines if "the door runs a file the suite passes over" in l], lines)
        self.assertTrue([l for l in lines if l.startswith("    passed over %s/agentik-%s" % (first, T))], lines)
        obj = self.json_of(h, "doctor", more=h.bins())
        self.assertNotIn("agentik-" + T, json.dumps(self.checks(obj, T)))

    # line 7
    def test_7_config(self):
        h = self.made("hD")
        h.commands()
        code, out, err = self.go(h, "config")
        row = [l for l in out.splitlines() if l.split()[1:2] == [T]][0]
        self.assertTrue(row.endswith("from " + F), row)
        h = self.made("hB")
        code, out, err = self.go(h, "config")
        row = [l for l in out.splitlines() if l.split()[1:2] == [T]][0]
        self.assertTrue(row.startswith("  warn"), row)
        self.assertIn("2 plugins of this name; no source is declared", row)
        for word in (T, "suite.sources." + T):
            code, out, err = self.go(h, "config", word)
            self.assertEqual(code, 0, (word, out, err))
            self.assertIn("2 plugins of this name are installed, and no source is declared", out)
            self.assertIn("%s 0.13.0, %s 0.12.6" % (U, F), out)
            self.assertIn(USER, out)
            self.assertIn("sources:", out)
            self.assertIn("  %s: %s" % (T, U), out)
            self.assertIn("now", out)
        h = self.made("hJ")
        code, out, err = self.go(h, "config", "--changed")
        self.assertIn("suite.sources." + T, out)

    def test_7_a_written_line_shows_its_own_card(self):
        h = self.made("hJ")
        code, out, err = self.go(h, "config", "suite.sources." + T)
        self.assertEqual(code, 0, err)
        self.assertIn(F, out)
        self.assertNotIn("no source is declared", out)

    # line 8
    def test_8_a_mirror(self):
        h = self.made("hF")
        h.known["agentik"]["source"] = {"source": "github", "repo": "someone/mirror"}
        h.write()
        code, out, err = self.go(h, "doctor")
        suite = self.group(out, "suite")
        notes = [l for l in suite if l.startswith("    from ")]
        self.assertEqual(len(notes), 1, suite)
        self.assertIn(T, notes[0])

    # line 9
    def test_9_a_fork_with_no_command(self):
        h = self.made("hA")
        code, out, err = self.go(h, "doctor")
        self.assertEqual(code, 0, err)
        lines = self.group(out, T)
        self.assertTrue(lines[0].startswith("note"), lines)
        self.assertIn("    from %s 0.12.6, the only plugin of that name" % F, lines)
        self.assertNotIn("not installed", out)


if __name__ == "__main__":
    unittest.main()
