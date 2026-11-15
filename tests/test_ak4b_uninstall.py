"""Packet ak4b-uninstall: `uninstall`, the reverse of `install-cli`, removes only what the code can
show install-cli wrote, says what it kept and why, and on any doubt removes nothing. Each test is a
real plugin and a real `install-cli` into a prefix under its own temp folder (test_agentik_install's
`Base`), and a stub `ps`; every prefix, home and state folder is asserted under that folder before
`uninstall` runs. Nothing here reads or writes the live home."""
import builtins
import os
import re
import shutil
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_agentik_install import APPLE_PY, Base, load_module  # noqa: E402

LIVE = os.path.realpath(os.path.expanduser("~"))


def snapshot(root):
    """Every path under `root`: a link's text, a file's bytes and mode, a folder's name."""
    found = {}
    for here, dirs, files in os.walk(root):
        for name in dirs + files:
            path = os.path.join(here, name)
            rel = os.path.relpath(path, root)
            if os.path.islink(path):
                found[rel] = ("link", os.readlink(path))
            elif os.path.isdir(path):
                found[rel] = ("dir",)
            else:
                with open(path, "rb") as fh:
                    found[rel] = ("file", fh.read(), os.lstat(path).st_mode)
    return found


@unittest.skipUnless(os.access(APPLE_PY, os.X_OK), "no /usr/bin/python3 on this machine")
class Uninstall(Base):
    def setUp(self):
        super().setUp()
        self.root = str(self.home)
        self.mod = load_module()
        self.stub("")

    def stub(self, body):
        """`ps` stood in for: the probe line, which says the environment shows, then `body`."""
        path = os.path.join(self.root, "ps")
        with open(path, "w") as fh:
            fh.write('#!/bin/sh\necho "1 sh AGENTIK_PRUNE_PROBE=$AGENTIK_PRUNE_PROBE"\n' + body + "\n")
        os.chmod(path, 0o755)
        self.mod.PS = path

    def under_temp(self, path):
        real = os.path.realpath(str(path))
        self.assertTrue(real == self.root or real.startswith(self.root + os.sep), real)
        self.assertNotEqual(real, LIVE)
        self.assertNotEqual(real, os.path.join(LIVE, ".local"))
        self.assertFalse(LIVE.startswith(real + os.sep) or LIVE == real, real)

    def un(self, tool="agentik-x", prefix=None, **kw):
        prefix = str(prefix or self.home / ".local")
        self.under_temp(prefix)
        return self.mod.uninstall(tool, prefix, **kw)

    def prefix(self):
        return self.home / ".local"

    def tree(self, name="agentik-x"):
        return self.share(name) / self.trees(name)[0]

    # ---- 1, 2: what install wrote goes, and dry reads alone ----

    def test_takes_back_what_install_wrote(self):
        self.install(self.plugin())
        tree = self.tree()
        rows = self.un()
        paths = [r[0] for r in rows]
        self.assertEqual(len(paths), len(set(paths)), rows)
        self.assertEqual({r[2] for r in rows}, {"removed"}, rows)
        self.assertEqual(rows[0], (str(self.bin()), "launcher", "removed"))
        self.assertIn((str(tree), "tree", "removed"), rows)
        self.assertIn((str(self.share() / ".lock"), "share", "removed"), rows)
        self.assertEqual(rows[-1], (str(self.share()), "share", "removed"))
        self.assertFalse(os.path.lexists(self.bin()))
        self.assertFalse(os.path.lexists(self.share()))
        self.assertEqual(os.listdir(self.bin().parent), ["agentik"])
        self.assertNotIn("door", [r[1] for r in rows])
        self.assertEqual(self.un(), [])

    def test_dry_reads_and_removes_nothing(self):
        self.install(self.plugin())
        os.symlink("agentik-x", str(self.bin("agentik-oldx")))
        before = snapshot(self.prefix())
        dry = self.un(dry=True)
        self.assertEqual(snapshot(self.prefix()), before)
        self.assertTrue(dry)
        self.assertEqual({r[2] for r in dry}, {"would remove"}, dry)
        rows = self.un()
        self.assertEqual(dry, [(p, w, "would remove") for p, w, _ in rows])

    # ---- 3: the links ----

    def test_links_its_own_alone(self):
        self.install(self.plugin())
        bin_dir = self.bin().parent
        os.symlink("agentik-x", str(bin_dir / "agentik-oldx"))
        os.symlink(str(self.tree() / "agentik-x"), str(bin_dir / "intree"))
        os.symlink("/bin/sh", str(bin_dir / "mysh"))
        os.symlink("agentik-y", str(bin_dir / "agentik-oldy"))
        rows = self.un()
        for name in ("agentik-oldx", "intree"):
            self.assertIn((str(bin_dir / name), "link", "removed"), rows)
            self.assertFalse(os.path.lexists(bin_dir / name))
        for name, text in (("mysh", "/bin/sh"), ("agentik-oldy", "agentik-y")):
            self.assertEqual(os.readlink(bin_dir / name), text)
            self.assertNotIn(str(bin_dir / name), [r[0] for r in rows])
        self.assertTrue(os.path.exists("/bin/sh"))

    # ---- 4: a launcher install-cli did not write keeps everything ----

    def test_a_launcher_not_install_clis_keeps_all(self):
        def no_line(path, tree):
            path.write_text("#!/bin/sh\nVERSION=1.0.0\nTREE=%s\nexec true\n" % tree)

        def tree_outside(path, tree):
            path.write_text(re.sub(r"(?m)^TREE=.*$", "TREE=%s" % (self.home / "elsewhere" / tree.name),
                                   path.read_text()))

        def a_link(path, tree):
            real = self.home / "real-launcher"
            shutil.copyfile(path, real)
            path.unlink()
            os.symlink(str(real), str(path))

        def too_big(path, tree):
            path.write_text(path.read_text() + "#" * (70 * 1024) + "\n")

        for change in (no_line, tree_outside, a_link, too_big):
            with self.subTest(change=change.__name__):
                self.setUp()
                self.install(self.plugin())
                os.symlink("agentik-x", str(self.bin("agentik-oldx")))
                tree = self.tree()
                change(self.bin(), tree)
                before = snapshot(self.prefix())
                rows = self.un()
                self.assertEqual(rows[0], (str(self.bin()), "launcher", "kept: not the launcher install-cli wrote"))
                self.assertEqual({r[2] for r in rows}, {"kept: not the launcher install-cli wrote"}, rows)
                self.assertIn(str(tree), [r[0] for r in rows])
                self.assertEqual(snapshot(self.prefix()), before)
                self.assertTrue(tree.is_dir())

    # ---- 5: the share ----

    def test_a_share_that_is_a_link_is_not_followed(self):
        self.install(self.plugin())
        elsewhere = self.home / "elsewhere"
        os.rename(self.share(), elsewhere)
        os.symlink(str(elsewhere), str(self.share()))
        before = snapshot(elsewhere)
        rows = self.un()
        self.assertEqual(snapshot(elsewhere), before)
        self.assertTrue(self.share().is_symlink())
        self.assertIn(str(self.share()), [r[0] for r in rows if r[1] == "share" and r[2].startswith("kept: ")])
        self.assertFalse([r for r in rows if r[0].startswith(str(self.share()) + "/")], rows)

    def test_a_file_of_its_own_in_the_share_stays(self):
        self.install(self.plugin())
        tree = self.tree()
        notes = self.share() / "notes.txt"
        notes.write_text("mine\n")
        rows = self.un()
        self.assertEqual(notes.read_text(), "mine\n")
        self.assertTrue(self.share().is_dir())
        self.assertFalse(os.path.lexists(tree))
        self.assertIn((str(notes), "share", "kept: not install-cli's"), rows)
        self.assertEqual(rows[-1][:2], (str(self.share()), "share"))
        self.assertTrue(rows[-1][2].startswith("kept: "), rows[-1])
        self.assertIn((str(tree), "tree", "removed"), rows)

    # ---- 6: the hold ----

    def test_a_live_tree_holds_everything(self):
        self.install(self.plugin())
        tree = self.tree()
        for line in ('echo "4242 /usr/bin/python3 -I %s/agentik-x status"' % tree,
                     'echo "4242 sh -c true HOME=/x AGENTIK_X_TREE=%s"' % tree):
            with self.subTest(line=line):
                self.stub(line)
                before = snapshot(self.prefix())
                rows = self.un()
                self.assertTrue(rows)
                self.assertTrue(all(r[2].startswith("kept: held, ") for r in rows), rows)
                self.assertIn("4242", rows[0][2])
                self.assertEqual(snapshot(self.prefix()), before)
        for body in ("exit 1", "echo no environment", "exit 0"):
            with self.subTest(body=body):
                self.mod.PS = os.path.join(self.root, "ps2")
                with open(self.mod.PS, "w") as fh:
                    fh.write("#!/bin/sh\n%s\n" % body)
                os.chmod(self.mod.PS, 0o755)
                before = snapshot(self.prefix())
                rows = self.un()
                self.assertTrue(all(r[2].startswith("kept: held, ") for r in rows), rows)
                self.assertEqual(snapshot(self.prefix()), before)
        self.stub('echo "4242 /usr/bin/python3 -I %s/agentik-x status"' % tree)
        rows = self.un(spare=(4242,))
        self.assertEqual({r[2] for r in rows}, {"removed"}, rows)
        self.assertFalse(os.path.lexists(self.share()))

    # ---- 7: the door ----

    def test_the_door_alone_goes(self):
        self.install(self.plugin())
        rows = self.un(door=True)
        self.assertEqual(rows[-1], (str(self.bin("agentik")), "door", "removed"))
        self.assertEqual(os.listdir(self.bin().parent), [])
        self.assertEqual(self.un(door=True), [])

    def test_the_door_stays_beside_another_launcher(self):
        self.install(self.plugin("agentik-x", "1.0.0"))
        self.install(self.plugin("agentik-y", "2.0.0"), "agentik-y")
        for dry in (True, False):
            rows = self.un(door=True, dry=dry)
            self.assertEqual(rows[-1][:2], (str(self.bin("agentik")), "door"))
            self.assertTrue(rows[-1][2].startswith("kept: "), rows[-1])
        self.assertTrue(self.bin("agentik").is_file())

    def test_a_door_not_the_door(self):
        def a_link(path):
            real = self.home / "real-door"
            shutil.copyfile(path, real)
            path.unlink()
            os.symlink(str(real), str(path))

        def hand_written(path):
            path.write_text("#!/bin/sh\nVERSION=9.9.9\necho mine\n")

        for change in (a_link, hand_written):
            with self.subTest(change=change.__name__):
                self.setUp()
                self.install(self.plugin())
                change(self.bin("agentik"))
                before = os.path.islink(self.bin("agentik")), self.bin("agentik").read_bytes()
                rows = self.un(door=True)
                self.assertEqual(rows[-1][:2], (str(self.bin("agentik")), "door"))
                self.assertTrue(rows[-1][2].startswith("kept: "), rows[-1])
                self.assertEqual((os.path.islink(self.bin("agentik")), self.bin("agentik").read_bytes()), before)

    # ---- 8: what is refused ----

    def test_a_bad_name_reads_no_disk(self):
        def touched(*a, **k):
            raise AssertionError("the disk was read: %r" % (a,))
        for name in ("../x", "a/b", "", "agentik-../x", "x"):
            with self.subTest(name=name):
                with mock.patch.object(os, "lstat", touched), mock.patch.object(os, "stat", touched), \
                        mock.patch.object(os, "listdir", touched), mock.patch.object(os, "scandir", touched), \
                        mock.patch.object(os, "open", touched), mock.patch.object(builtins, "open", touched):
                    with self.assertRaises(ValueError):
                        self.mod.uninstall(name, os.path.join(self.root, "p"))

    def test_a_prefix_of_root_or_the_homes_parent(self):
        with self.assertRaises(ValueError):
            self.mod.uninstall("agentik-x", "/", dry=True)
        home = self.home / "h"
        home.mkdir()
        with mock.patch.dict(os.environ, {"HOME": str(home), "XDG_STATE_HOME": str(home / "state")}):
            self.under_temp(os.environ["HOME"])
            with self.assertRaises(ValueError):
                self.mod.uninstall("agentik-x", self.root, dry=True)

    # ---- 9: a space, and another tool ----

    def test_a_space_and_another_tool_untouched(self):
        self.home = self.home / "a b"
        self.home.mkdir()
        self.env["HOME"] = str(self.home)
        self.install(self.plugin("agentik-x", "1.0.0"))
        self.install(self.plugin("agentik-y", "2.0.0"), "agentik-y")
        theirs = snapshot(self.share("agentik-y")), self.bin("agentik-y").read_bytes()
        rows = self.un("agentik-x")
        self.assertEqual({r[2] for r in rows}, {"removed"}, rows)
        self.assertFalse(os.path.lexists(self.share("agentik-x")))
        self.assertEqual((snapshot(self.share("agentik-y")), self.bin("agentik-y").read_bytes()), theirs)
        self.assertEqual(self.run_tool(self.bin("agentik-y"), "--version")[:2], (0, "2.0.0\n"))
        self.assertEqual(sorted(os.listdir(self.bin().parent)), ["agentik", "agentik-y"])

    # ---- R6: the marker, the default prefix alone ----

    def test_the_marker_at_the_default_prefix_alone(self):
        self.install(self.plugin())
        state = self.home / "state"
        marker = state / "agentik-x" / "install-needed"
        marker.parent.mkdir(parents=True)
        marker.write_text("gone\n")
        other = self.home / "other"
        with mock.patch.dict(os.environ, {"HOME": str(self.home), "XDG_STATE_HOME": str(state)}):
            for path in (os.environ["HOME"], os.environ["XDG_STATE_HOME"], other):
                self.under_temp(path)
            self.assertEqual(self.mod.uninstall("agentik-x", str(other)), [])
            self.assertTrue(marker.exists())
            rows = self.mod.uninstall("agentik-x")
        self.assertIn((str(marker), "marker", "removed"), rows)
        self.assertFalse(marker.exists())
        self.assertFalse(os.path.lexists(self.share()))


if __name__ == "__main__":
    unittest.main()
