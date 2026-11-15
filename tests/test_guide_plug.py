"""The guide's §11 held against the reader: each of its four JSON examples reads as the suite
reads that answer (packet ak9d-contract-guide R4).

The section is cut from `GUIDE.md`, from its heading to the next `## ` line or the file's end,
and its `json` fences are taken in order: the error envelope, the describe answer, the config
answer, the doctor answer. Each is handed to the function the reader itself calls on a tool's
stdout. No process is started and nothing is written outside a temp folder.
"""
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "GUIDE.md"
sys.path.insert(0, str(ROOT / "plugins" / "suite" / "lib"))
from agentik_suite import doctor, plan, tools  # noqa: E402

HEAD = "## §11 "
FENCE = re.compile(r"^```json\n(.*?)^```[ \t]*$", re.S | re.M)
PARTS = ["§11.%d" % n for n in range(1, 8)]


def section(path):
    """§11's text, from its heading to the next `## ` line or the end, or None."""
    lines = Path(path).read_text(encoding="utf-8").splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.startswith(HEAD)), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "".join(lines[start:end])


def fences(text):
    return [m.group(1) for m in FENCE.finditer(text)]


def examples(path):
    """{error, describe, config, doctor: the fence's bytes}, the four in the section's order."""
    text = section(path)
    if text is None:
        raise AssertionError("%s has no %r heading" % (path, HEAD.strip()))
    found = fences(text)
    if len(found) != 4:
        raise AssertionError("§11 holds %d json fences, not 4" % len(found))
    return dict(zip(("error", "describe", "config", "doctor"), (f.encode("utf-8") for f in found)))


def answering(out):
    """A stand-in for `tools.run_all` that answers each job with exit 0 and `out`, as a describe
    that ran, so the reader's own describe_all, cache and count run and no process starts."""
    def run_all(jobs, env, then=None, deadline=None, **_):
        results, queue = {}, list(jobs)
        while queue:
            key, _argv = queue.pop(0)
            results[key] = (0, out, "ran")
            queue.extend((then(key, results[key]) if then else None) or ())
        return results
    return run_all


def check_describe(out):
    """The describe example is an answer that counts, asked under the name `demo`."""
    answer = tools.counted_describe(0, out, "demo")
    if answer is None:
        raise AssertionError("the describe example does not count: %s" % tools.describe_reason(0, out, "demo"))
    missing = [k for k in tools.DESCRIBE_KEYS if k not in answer]
    if missing:
        raise AssertionError("the describe example lacks %s" % missing)
    return answer


class GuidePlug(unittest.TestCase):

    def test_section_stands_once_with_its_seven_parts(self):
        text = GUIDE.read_text(encoding="utf-8")
        self.assertEqual(sum(1 for line in text.splitlines() if line.startswith(HEAD)), 1)
        cut = section(GUIDE)
        for part in PARTS:
            heads = [line for line in cut.splitlines() if line.startswith("### " + part + " ")]
            self.assertEqual(len(heads), 1, part)

    def test_four_fences_each_one_object(self):
        found = examples(GUIDE)
        for name, out in found.items():
            obj = json.loads(out.decode("utf-8"))
            self.assertIsInstance(obj, dict, name)

    def test_describe_counts(self):
        answer = check_describe(examples(GUIDE)["describe"])
        kinds = [r["kind"] for r in answer["reads"]]
        self.assertEqual(kinds.count("config"), 1)
        self.assertEqual(kinds.count("doctor"), 1)
        self.assertEqual(tools.config_read(answer)["argv"], ["describe", "config", "--json"])
        self.assertEqual(doctor.doctor_read(answer)["argv"], ["doctor", "--json"])

    def test_describe_with_reads_a_string_fails(self):
        """Acceptance 2's mutation: the same test, on a temp copy whose `reads` is a string."""
        text = section(GUIDE)
        out = examples(GUIDE)["describe"].decode("utf-8")
        obj = json.loads(out)
        obj["reads"] = "describe config --json"
        with tempfile.TemporaryDirectory() as tmp:
            copy = os.path.join(tmp, "GUIDE.md")
            Path(copy).write_text(text.replace(out, json.dumps(obj) + "\n"), encoding="utf-8")
            with self.assertRaises(AssertionError):
                check_describe(examples(copy)["describe"])

    def test_reads_first_words_are_verbs(self):
        """Review 1 F8: each read's first word is a verb of the example's own `verbs`."""
        answer = check_describe(examples(GUIDE)["describe"])
        verbs = {v["name"] for v in answer["verbs"]}
        firsts = [r["argv"][0] for r in answer["reads"] if r["argv"]]
        self.assertEqual([w for w in firsts if w not in verbs], [])

    def test_example_not_in_place(self):
        """Review 1 F2: setup's launcher step (`plan.in_place`) does not take the example's tool to
        run in place, since its `verbs` list `install-cli`."""
        out = examples(GUIDE)["describe"]
        with tempfile.TemporaryDirectory() as tmp:
            exe = os.path.join(tmp, "agentik-demo")
            Path(exe).write_text("#!/bin/sh\n", encoding="utf-8")
            env = {"HOME": tmp, "XDG_CACHE_HOME": os.path.join(tmp, "cache"), "PATH": "/usr/bin:/bin"}
            with mock.patch.object(tools, "run_all", answering(out)):
                found, _ = tools.describe_all([{"name": "demo", "exe": exe}], env)
                self.assertEqual(found["demo"][0], "answers")
                os.remove(os.path.join(tools.cache_dir(env), "demo.json"))
                self.assertEqual(plan.in_place({"demo": exe}, env), set())

    def test_config_counts(self):
        cfg = tools.counted_config(0, examples(GUIDE)["config"])
        self.assertIsNotNone(cfg)
        self.assertEqual(len(cfg["settings"]), 3)
        self.assertEqual(len(cfg["warnings"]), 1)
        names = [layer["name"] for layer in cfg["layers"]]
        self.assertIn("user", names)
        for s in cfg["settings"]:
            self.assertIn(s["source"]["layer"], names, s["key"])
            for v in s["values"]:
                self.assertIn(v["layer"], names, s["key"])

    def test_error_reads_as_an_error(self):
        out = examples(GUIDE)["error"]
        error = tools.config_error(out)
        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "bad_file")
        self.assertIsNone(tools.counted_config(2, out))

    def test_doctor_answer_taken_with_one_fail(self):
        checks = doctor.read_answer(examples(GUIDE)["doctor"], "failed")
        self.assertIsNotNone(checks)
        self.assertEqual([c["status"] for c in checks].count("fail"), 1)
        self.assertIsNotNone(doctor.read_own(examples(GUIDE)["doctor"], "failed"))


if __name__ == "__main__":
    unittest.main()
