"""Packet ak9c-plug-rest: a claimed verb runs from `agentik <verb>`; two settings screens say what
they read.

`quill`, `scribe` and the word `ink` are made up. Each test runs the launcher of a temp copy of the
suite's plugin (ak9b's `Copy`) in a temp HOME holding Claude Code's plugin table (fk_homes'
`FkHome`), each tool's command a stub that logs its words, one bracketed word each, to
`$HOME/ran.log`. The terminal's PATH is `~/.local/bin:/usr/bin:/bin`. No test starts `claude`,
reads the real home or writes outside its temp folder."""
import json
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fk_homes import FkHome  # noqa: E402
from test_ak9b_plug_reader import Copy, described  # noqa: E402
from agentik_suite import tools  # noqa: E402

W = "ink"
LOG = 'l=; for a in "$@"; do l="$l[$a]"; done; echo "$l" >> "$HOME/ran.log"'  # one write a start
REFUSED = "ink is not a verb or a tool"


def claiming(tool, *words, reads=()):
    """A describe of `tool` claiming each of `words`, one verb two words deep claiming nothing."""
    d = described(tool, reads)
    d["plugin"] = tool + "@agentik"
    d["verbs"] = [{"name": w, "summary": "a made-up verb", "top": True} for w in words] \
        + [{"name": "deep", "summary": "not claimed"}]
    return d


def body(answer=None, config=None, code=7, hang=False, tool="quill"):
    """A command: `describe` prints `answer` (or sleeps), `config` prints `config`, the rest exit
    `code`; every start logged."""
    def emit(obj):
        return "cat <<'EOF'\n%s\nEOF\n" % json.dumps(obj)

    lines = ["#!/bin/sh", LOG, 'case "$1" in']
    if hang:
        lines.append("describe) sleep 30; exit 0;;")
    elif answer is not None:
        lines.append("describe) %sexit 0;;" % emit(answer))
    if config is not None:
        lines.append("config) %sexit 0;;" % emit(config))
    lines.append("esac\nexit %d\n" % code)
    return "\n".join(lines)


def place(h, tool, text, market="agentik"):
    """`tool@market` in the home's table, its command under its root holding `text` (none for None)."""
    h.tool = tool
    root = h.install("%s@%s" % (tool, market), "0.1.0")
    if text is not None:
        h.file(os.path.join(root, "bin", "agentik-" + tool), text)
    return root


def ran(h):
    return [l for l in h.ran() if not l.startswith("[describe]")]


def config_answer(tool, warnings=(), values=()):
    return {"schema": "agentik.config/1", "ok": True, "tool": tool, "layers": [],
            "settings": [{"key": "pen.width", "value": 2, "summary": "the pen's width",
                          "source": {"layer": "user"}, "change": {"kind": "fixed"},
                          "values": list(values)}],
            "warnings": list(warnings)}


class Claims(Copy):
    def blank(self):
        self.count = getattr(self, "count", 0) + 1
        path = os.path.join(self.tmp, "c%d" % self.count)
        os.mkdir(path)
        return FkHome(path, "quill")

    def last(self, text):
        return text.splitlines()[-1] if text.splitlines() else ""


class RunTest(Claims):
    def test_1_an_own_claim_runs_its_file(self):
        h = self.blank()
        place(h, "quill", body(claiming("quill", W)))
        code, out, err = self.cli(h, W, "a", "--", "--help", "")
        self.assertEqual((code, out, err), (7, "", ""))
        self.assertEqual(ran(h), ["[ink][a][--][--help][]"])

    def test_1_a_flag_first_keeps_the_refusal(self):
        h = self.blank()
        place(h, "quill", body(claiming("quill", W)))
        code, out, err = self.cli(h, "--no-color", W)
        self.assertEqual(code, 2, out + err)
        self.assertEqual(ran(h), [])

    def test_2_a_claim_from_elsewhere_is_said_never_run(self):
        fork = self.blank()
        place(fork, "quill", body(claiming("quill", W)), market="acme-tools")
        fork.user_file("sources:\n  quill: quill@acme-tools\n")
        folder = self.blank()
        root = os.path.join(folder.home, "src", "quill")
        os.makedirs(os.path.join(root, ".claude-plugin"))
        with open(os.path.join(root, ".claude-plugin", "plugin.json"), "w") as fh:
            json.dump({"name": "quill", "version": "0.1.0"}, fh)
        folder.file(os.path.join(root, "bin", "agentik-quill"), body(claiming("quill", W)))
        folder.user_file("sources:\n  quill: ~/src/quill\n")
        bare = self.blank()
        bare.file(os.path.join(bare.home, ".local", "bin", "agentik-quill"), body(claiming("quill", W)))
        for h, said in ((fork, True), (folder, True), (bare, False)):
            code, out, err = self.cli(h, W, "a")
            self.assertEqual(code, 2, out + err)
            self.assertIn(REFUSED, err)
            self.assertRegex(self.last(err), r"^next: .*quill ink$")
            self.assertEqual(ran(h), [])
            code, out, err = self.cli(h, "config", "quill")
            self.assertEqual(code, 0, out + err)
            lines = [l for l in out.splitlines() if "claims ink" in l]
            self.assertEqual(len(lines), 1 if said else 0, out)  # a bare file: --json alone
            self.assertNotIn("claims", err)
            for l in lines:
                self.assertIn("quill is not agentik's", l)
            code, out, err = self.cli(h, "config", "quill", "--json")
            self.assertEqual(json.loads(out)["claims"],
                             [{"verb": W, "counts": False, "reason": "market"}])
            self.assertEqual(ran(h), [])

    def test_3_two_claims_run_neither(self):
        h = self.blank()
        place(h, "quill", body(claiming("quill", W)))
        place(h, "scribe", body(claiming("scribe", W)))
        code, out, err = self.cli(h, W)
        self.assertEqual(code, 2, out + err)
        self.assertIn("ink is claimed by quill and scribe", err)
        self.assertEqual(ran(h), [])
        code, out, err = self.cli(h, "doctor")
        self.assertEqual(code, 1, out + err)
        rows = [l for l in out.splitlines() if "ink" in l]
        self.assertEqual(len(rows), 1, out)
        self.assertTrue("quill" in rows[0] and "scribe" in rows[0] and "FAIL" in rows[0], rows)
        code, out, err = self.cli(h, "doctor", "--json")
        suite = json.loads(out)["tools"][0]["checks"]
        self.assertEqual([c["status"] for c in suite if c["name"] == "claim"], ["fail"])
        self.assertEqual([l for l in ran(h) if l.startswith("[ink]")], [])

    def test_4_the_suites_words_and_the_kept_words(self):
        h = self.blank()
        place(h, "quill", body(claiming("quill", "doctor", "completion", "rows")))
        for word in ("completion", "rows"):
            code, out, err = self.cli(h, word)
            self.assertEqual(code, 2, out + err)
            self.assertIn("%s is not a verb" % word, err)
        code, out, err = self.cli(h, "doctor", "--json")
        self.assertEqual(json.loads(out)["schema"], "agentik.doctor/1")
        self.assertFalse([l for l in ran(h) if l.startswith(("[completion]", "[rows]"))], ran(h))
        code, out, err = self.cli(h, "config", "quill")
        said = {w: [l for l in out.splitlines() if "claims %s;" % w in l] for w in ("doctor", "completion", "rows")}
        self.assertIn("the suite keeps that word", said["doctor"][0])
        self.assertIn("the suite keeps that word", said["completion"][0])
        self.assertIn("another tool has that word", said["rows"][0])
        d, keeper = self.blank(), tools.kept(None, ("rows",))["rows"]  # kept.json's tool
        self.assertTrue(keeper)
        place(d, keeper, body(claiming(keeper, "rows")))
        code, out, err = self.cli(d, "rows", "--json")
        self.assertEqual((code, out, err), (7, "", ""))
        self.assertEqual(ran(d), ["[rows][--json]"])

    def test_5_a_kept_word_on_path_is_a_shadow(self):
        h = self.blank()
        h.file(os.path.join(h.home, ".local", "bin", "agentik-rows"), "#!/bin/sh\nexit 0\n")
        code, out, err = self.cli(h, "doctor")
        self.assertIn("runs in place of the verb rows", out)
        code, out, err = self.cli(h, "doctor", "--json")
        suite = json.loads(out)["tools"][0]["checks"]
        self.assertEqual([c["status"] for c in suite if c["name"] == "shadow"], ["fail"])

    def test_6_no_claim_counts_from_a_describe_that_does_not(self):
        hang = self.blank()
        place(hang, "quill", body(hang=True))
        other = self.blank()
        place(other, "quill", body(claiming("scribe", W)))
        none = self.blank()
        place(none, "quill", None)
        for h in (hang, other, none):
            start = time.monotonic()
            code, out, err = self.cli(h, W)
            took = time.monotonic() - start
            self.assertEqual(code, 2, out + err)
            self.assertIn(REFUSED, err)
            self.assertRegex(self.last(err), r"^next: .*help$")
            self.assertEqual(ran(h), [])
            self.assertLess(took, tools.WALL + 4)


class ScreenTest(Claims):
    def own(self, config):
        h = self.blank()
        place(h, "quill", body(claiming("quill", reads=("config",)), config=config))
        return h

    def test_7_the_warnings_words(self):
        h = self.blank()
        where = lambda name: os.path.join(h.home, ".config", "quill", name)  # noqa: E731
        warnings = [{"key": None, "reason": "unreadable", "value": None, "path": where("bad.yaml"), "line": None},
                    {"key": "pen.tip", "reason": "ignored", "value": 1, "path": where("repo.yaml"), "line": 4},
                    {"key": "pen.ink", "reason": "unknown", "value": 1, "path": where("a.yaml"), "line": 2},
                    {"key": "pen.width", "reason": "choice", "value": "wide", "path": where("a.yaml"), "line": 3}]
        place(h, "quill", body(claiming("quill", reads=("config",)), config=config_answer("quill", warnings)))
        code, out, err = self.cli(h, "config", "quill")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("None", out)
        lines = out.splitlines()
        skipped = [l for l in lines if "bad.yaml" in l]
        self.assertEqual(len(skipped), 1, out)
        self.assertIn("quill skipped this file: it could not be read", skipped[0])
        self.assertTrue(skipped[0].rstrip().endswith("~/.config/quill/bad.yaml"), skipped)
        ignored = [l for l in lines if "repo.yaml" in l]
        self.assertIn("quill does not take pen.tip from this file", ignored[0])
        self.assertIn("~/.config/quill/repo.yaml:4", ignored[0])
        self.assertIn("  warn  unknown key pen.ink  ~/.config/quill/a.yaml:2", lines)
        self.assertIn("  warn  pen.width holds wide, which is not one of its choices  ~/.config/quill/a.yaml:3",
                      lines)
        code, out, err = self.cli(h, "config", "quill", "--json")
        self.assertEqual(json.loads(out)["warnings"], warnings)

    def test_8_the_cards_files(self):
        h = self.blank()
        values = [{"layer": "repo", "value": 3, "path": os.path.join(h.home, "work", "a.yaml"), "line": 5},
                  {"layer": "user", "value": 2, "path": os.path.join(h.home, ".config", "quill", "u.yaml")},
                  {"layer": "default", "value": 1}]
        place(h, "quill", body(claiming("quill", reads=("config",)), config=config_answer("quill", values=values)))
        code, out, err = self.cli(h, "config", "quill.pen.width")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.count("~/work/a.yaml:5"), 1, out)
        self.assertEqual(out.count("~/.config/quill/u.yaml"), 1, out)
        self.assertIn("  layer       default: 1\n", out)
        self.assertNotIn(h.home, out)
        bare = self.blank()
        place(bare, "quill", body(claiming("quill", reads=("config",)),
                                  config=config_answer("quill", values=[{"layer": "user", "value": 2},
                                                                        {"layer": "default", "value": 1}])))
        code, out, err = self.cli(bare, "config", "quill.pen.width")
        self.assertEqual(out, PIN_8, out)


# the pin's bytes, from 70dcd97's suite in this home
PIN_8 = ("quill.pen.width\n  value       2\n  about       the pen's width\n  set by      user\n"
         "  layer       user: 2\n  layer       default: 1\n  fixed       no verb changes it\n"
         "  takes hold  at the next start of Claude Code\n")


class FixTest(Claims):
    """Section 7, the fix of review 1."""

    def test_11_a_word_listed_twice_is_one_claim(self):
        h = self.blank()
        place(h, "quill", body(claiming("quill", W, W)))
        code, out, err = self.cli(h, W, "a")
        self.assertEqual((code, out, err), (7, "", ""))
        self.assertEqual(ran(h), ["[ink][a]"])
        code, out, err = self.cli(h, "doctor", "--json")
        suite = json.loads(out)["tools"][0]["checks"]
        self.assertEqual([c for c in suite if c["name"] == "claim"], [])

    def test_12_a_reason_that_is_no_string_reads_as_unknown(self):
        h = self.blank()
        path = os.path.join(h.home, ".config", "quill", "a.yaml")
        reasons = (["ignored"], {"why": "ignored"}, 3, None)
        warnings = [{"key": "pen.k%d" % n, "reason": r, "value": 1, "path": path, "line": n}
                    for n, r in enumerate(reasons, 1)]
        place(h, "quill", body(claiming("quill", reads=("config",)), config=config_answer("quill", warnings)))
        code, out, err = self.cli(h, "config", "quill")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("Traceback", err)
        lines = out.splitlines()
        for n in range(1, len(reasons) + 1):
            self.assertIn("  warn  unknown key pen.k%d  ~/.config/quill/a.yaml:%d" % (n, n), lines)

    def test_13_a_bare_claimants_next_is_its_file(self):
        bare = self.blank()
        bare.file(os.path.join(bare.home, ".local", "bin", "agentik-quill"), body(claiming("quill", W)))
        code, out, err = self.cli(bare, W, "a")
        self.assertEqual(code, 2, out + err)
        self.assertEqual(self.last(err), "next: ~/.local/bin/agentik-quill ink")
        fork = self.blank()
        place(fork, "quill", body(claiming("quill", W)), market="acme-tools")
        fork.user_file("sources:\n  quill: quill@acme-tools\n")
        code, out, err = self.cli(fork, W, "a")
        self.assertEqual(code, 2, out + err)
        self.assertRegex(self.last(err), r"^next: \S+ quill ink$")
        self.assertNotIn("agentik-quill", self.last(err))
        self.assertEqual(ran(bare) + ran(fork), [])


if __name__ == "__main__":
    unittest.main()
