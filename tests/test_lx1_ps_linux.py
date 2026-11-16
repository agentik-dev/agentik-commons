"""Row lx1-ps-linux: the process list is read where `ps -axwwE` is refused, as procps refuses it.

Stand-ins for `ps`, each first on a temp PATH or named to the module: PROCPS exits 1 with procps's
own line on a word that holds `E` and, for `axwwe`, prints its listing and the probe line; BROKEN
exits 1 with that line on both forms; PASS_ON refuses the first form the same way and passes the
second to /bin/ps, so a live process is read through `axwwe`. Each logs its words. Every home is
a temp HOME with a stub `claude` (test_ak4a_update's Home, test_ak4_remove's RHome); no test
starts a real `claude`, reads the live home or writes outside its temp folder."""
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_install import APPLE_PY, load_module  # noqa: E402
from test_ak4_remove import RHome  # noqa: E402
from test_ak4a_update import Base  # noqa: E402

SAID = "error: unsupported option (BSD syntax)"
REFUSE = '#!/bin/sh\necho "$*" >> %s\ncase "$*" in *E*) echo "%s" >&2; echo >&2; echo " usage" >&2; exit 1 ;; esac\n'
PROBE = 'echo "2 /bin/sh AGENTIK_PRUNE_PROBE=$AGENTIK_PRUNE_PROBE"\n'
FIRST = "-axwwE -o pid=,command="
SECOND = "axwwe -o pid=,command="


def procps(log, listing):
    """procps's refusal of `-axwwE`; for `axwwe` the listing file and the probe line."""
    return (REFUSE % (shlex.quote(log), SAID) + '[ "$1" = axwwe ] || exit 3\n'
            + "cat %s\n" % shlex.quote(listing) + PROBE)


def broken(log):
    return REFUSE % (shlex.quote(log), SAID) + 'echo "%s" >&2\nexit 1\n' % SAID


def pass_on(log):
    return REFUSE % (shlex.quote(log), SAID) + 'exec /bin/ps "$@"\n'


def write(path, body):
    with open(path, "w") as fh:
        fh.write(body)
    os.chmod(path, 0o755)
    return str(path)


class Module(unittest.TestCase):
    """processes() and prune() of scripts/agentik_install.py against the stand-ins (R1, R5)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(os.path.realpath(tmp.name))
        self.share = self.dir / "share"
        self.share.mkdir()
        self.log = str(self.dir / "ps.log")
        self.listing = str(self.dir / "ps.txt")
        Path(self.listing).write_text("1 /sbin/init\n")
        self.mod = load_module()
        for n, name in enumerate(("a", "b", "c", "d", "new")):
            (self.share / name).mkdir()
            os.utime(self.share / name, (1000 + n, 1000 + n))

    def words(self):
        return Path(self.log).read_text().splitlines()

    def names(self):
        return sorted(os.listdir(self.share))

    def test_1_the_second_form_is_read_where_the_first_is_refused(self):
        ps = write(self.dir / "ps", procps(self.log, self.listing))
        text, why = self.mod.processes(ps)
        self.assertIsNone(why)
        self.assertIn("1 /sbin/init", text)
        self.assertEqual(self.words(), [FIRST, SECOND])

    def test_2_both_refused_carry_ps_and_its_line(self):
        ps = write(self.dir / "ps", broken(self.log))
        self.assertEqual(self.mod.processes(ps), (None, "%s exited 1: %s" % (ps, SAID)))
        self.assertEqual(self.words(), [FIRST, SECOND])

    def test_3_the_prune_prunes_through_the_second_form(self):
        Path(self.listing).write_text("7 python -I %s/b/agentik-x run\n" % self.share)
        ps = write(self.dir / "ps", procps(self.log, self.listing))
        code, lines = self.mod.prune(self.share, "new", keep=1, ps=ps)
        self.assertEqual(code, 0)
        self.assertEqual(self.names(), ["b", "new"])
        self.assertEqual(lines[-1], "prune-trees: removed 3, kept 2 (1 live, the newest 1)")

    def test_4_both_refused_keep_every_tree_and_say_why(self):
        ps = write(self.dir / "ps", broken(self.log))
        code, lines = self.mod.prune(self.share, "new", keep=1, ps=ps)
        self.assertEqual((code, lines), (0, ["prune-trees: %s exited 1: %s; keeping every tree" % (ps, SAID)]))
        self.assertEqual(len(self.names()), 5)

    def test_5_a_live_process_holds_its_tree_through_the_second_form(self):
        ps = write(self.dir / "ps", pass_on(self.log))
        tree = self.share / "b" / "agentik-x"
        live = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", str(tree)],
                                stdin=subprocess.DEVNULL)
        self.addCleanup(live.wait)
        self.addCleanup(live.kill)
        time.sleep(0.2)
        code, lines = self.mod.prune(self.share, "new", keep=1, ps=ps)
        self.assertEqual(code, 0, lines)
        self.assertEqual(self.names(), ["b", "new"], lines)
        self.assertEqual(self.words(), [FIRST, SECOND])

    def test_6_a_first_form_that_reads_is_the_only_read(self):
        ps = write(self.dir / "ps", '#!/bin/sh\necho "$*" >> %s\n' % shlex.quote(self.log) + PROBE)
        text, why = self.mod.processes(ps)
        self.assertIsNone(why)
        self.assertEqual(self.words(), [FIRST])


@unittest.skipUnless(os.access(APPLE_PY, os.X_OK), "no /usr/bin/python3 on this machine")
class Suite(Base):
    """update, remove, install-cli and the doctor in a temp HOME with a stand-in first on PATH."""

    def home(self, listed=("murmur", "paint", "x"), name="h"):
        h = RHome(os.path.join(self.tmp, name), listed)
        h.install("murmur@agentik", "1.0.0", "1.1.0")
        h.install("paint@agentik", "2.0.0", "2.1.0")
        h.root = h.real_tool()
        h.log = os.path.join(h.home, "ps.log")
        return h

    def stand_in(self, h, body):
        h.ps_path = write(os.path.join(h.bin, "ps"), body)

    def install_cli(self, h):
        p = subprocess.run([os.path.join(h.root, "bin", "agentik-x"), "install-cli"], capture_output=True,
                           text=True, env=h.env(), cwd=h.home, stdin=subprocess.DEVNULL, timeout=120)
        return p.returncode, p.stdout, p.stderr

    def test_7_procps_update_and_remove_print_their_plans(self):
        h = self.home()
        self.stand_in(h, procps(h.log, h.ps_text))
        code, out, err = h.go("update", "--dry-run")
        self.assertEqual(code, 0, out + err)
        self.assertIn("Update plan for", out)
        code, out, err = h.go("remove", "--all", "--dry-run")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("held", out + err)
        self.assertIn(SECOND, open(h.log).read().splitlines())

    def test_8_procps_install_cli_prunes(self):
        h = self.home()
        self.stand_in(h, procps(h.log, h.ps_text))
        share = os.path.join(h.home, ".local", "share", "agentik-x")
        for n in range(4):
            os.makedirs(os.path.join(share, "old%d" % n))
            os.utime(os.path.join(share, "old%d" % n), (1000 + n, 1000 + n))
        code, out, err = self.install_cli(h)
        self.assertEqual(code, 0, out + err)
        self.assertIn("prune-trees: removed 2, kept 3 (0 live, the newest 3)", out.splitlines())
        self.assertEqual(sorted(n for n in os.listdir(share) if n.startswith("old")), ["old2", "old3"])

    def test_9_both_refused_update_and_remove_say_why(self):
        h = self.home()
        self.stand_in(h, broken(h.log))
        why = "the process list cannot be read: %s exited 1: %s" % (h.ps_path, SAID)
        for args, head in ((("update", "--dry-run"), "held install: "), (("remove", "--all", "--dry-run"), "held remove: ")):
            code, out, err = h.go(*args)
            self.assertEqual(code, 2, out + err)
            lines = err.splitlines()
            self.assertTrue(lines[0].endswith(head + why), err)
            self.assertTrue(lines[1].startswith("next: "), err)
            self.assertNotIn("once it has ended", err)
            code, out, err = h.go(*(args + ("--json",)))
            self.assertEqual(code, 2, out + err)
            self.assertEqual(json.loads(out)["held"], why)

    def test_10_both_refused_install_cli_says_why(self):
        h = self.home()
        self.stand_in(h, broken(h.log))
        code, out, err = self.install_cli(h)
        self.assertEqual(code, 0, out + err)
        self.assertIn("prune-trees: ps exited 1: %s; keeping every tree" % SAID, out.splitlines())

    def test_11_the_doctor_warns_where_the_list_cannot_be_read(self):
        h = self.home()
        code, out, err = h.go("doctor", "--json")
        suite = json.loads(out)["tools"][0]
        self.assertNotIn("processes", [c["name"] for c in suite["checks"]])
        self.stand_in(h, broken(h.log))
        code, out, err = h.go("doctor", "--json")
        suite = json.loads(out)["tools"][0]
        rows = [c for c in suite["checks"] if c["name"] == "processes"]
        self.assertEqual(len(rows), 1, out)
        self.assertEqual(rows[0]["status"], "warn")
        self.assertIn("%s exited 1: %s" % (h.ps_path, SAID), rows[0]["detail"])
        self.assertIn("update and remove", rows[0]["detail"])
        code, out, err = h.go("doctor")
        self.assertIn("%s exited 1: %s" % (h.ps_path, SAID), out)


if __name__ == "__main__":
    unittest.main()
