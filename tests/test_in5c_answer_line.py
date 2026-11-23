"""Row in5c-answer-line: after `inbox answer` has written the owner's answer, the suite sends that
checkout's sitting one pointer line with the sender's `line send <checkout> --text=<sentence>`.

On in5b's home (`test_in5b_inbox_answer.AnswerHome`): the made-up `agentik-ledger` is the writer and
the made-up `agentik-bench`, which gives the `charter` read, lists a verb `line` and answers `line
send` with a stub that records its call (in5b's `LINE`). Here the writer's stub also sleeps until a
file appears, kills itself, or exits 1 on a declined prompt, as the writer does. Every checkout and
PATH is a temp folder's; no test sends a real line or writes a real answer.
"""
import fcntl
import json
import os
import pty
import select
import signal
import subprocess
import termios
import time

import test_in4_inbox as in4
import test_in5b_inbox_answer as in5b

MORE = r'''    with open(os.path.join(here, "reply.pid"), "w") as fh:
        fh.write(str(os.getpid()))
    if how.get("wait"):
        while not os.path.exists(how["wait"]):
            time.sleep(0.05)
    if how.get("kill"):
        import signal
        os.kill(os.getpid(), how["kill"])
    if got == "n":
        sys.stderr.write("nothing is written\n")
        sys.exit(1)
'''
REPLY = in5b.REPLY.replace('    print("the line after")\n', MORE + '    print("the line after")\n', 1)
SENTENCE = "--text=question 2 holds text on its answer line"
UNSENT = ("warn  no line told %s's sitting, since %s. Its inbox and its next ask still show question 2 "
          "answered, not entered.\n")
OUT, ERR = "the line after\n", "the writer's note\n"


def gone(pid, group=False):
    try:
        (os.killpg if group else os.kill)(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


class LineHome(in5b.AnswerHome):
    def setUp(self):
        in5b.AnswerHome.setUp(self)
        tool = in4.TOOL.replace('with open(os.path.join(here, "tools.json"))',
                                REPLY + 'with open(os.path.join(here, "tools.json"))', 1)
        with open(os.path.join(self.side, "ledger.py"), "w") as fh:
            fh.write(tool)

    def sends(self):
        try:
            with open(os.path.join(self.side, "line-calls")) as fh:
                return [json.loads(line) for line in fh]
        except FileNotFoundError:
            return []

    def set(self, key, **how):
        self.world[key] = how
        self.save()

    def sent_once(self, repo, cwd, before=0):
        """The last answer's one send: its argv, its cwd, no terminal, after the writer's call."""
        calls = self.sends()[before:]
        self.assertEqual(len(calls), 1, calls)
        c = calls[0]
        self.assertEqual(c["argv"], ["line", "send", os.path.realpath(repo), SENTENCE])
        self.assertEqual((c["cwd"], c["tty0"]), (os.path.realpath(cwd), False))
        self.assertEqual(c["replies"], len(self.replies()))
        return c

    def plain(self):
        """One plain answer at a test's end: it is written, and sent once."""
        before = len(self.sends())
        self.set("reply")
        self.set("line")
        self.assertEqual(self.answer("pear-hq", "2", "--pick", "North", "--yes"), (0, OUT, ERR))
        self.sent_once(self.pear, self.side, before)

    def on_pty(self, args, typed=b"y\n", wait=None):
        """`inbox answer ...` with the pty its controlling terminal and its three streams; `typed`
        written at the writer's prompt. (wait status, screen)."""
        master, slave = pty.openpty()

        def own_terminal():
            os.setsid()
            fcntl.ioctl(0, termios.TIOCSCTTY, 0)

        p = subprocess.Popen([self.L, "inbox", "answer"] + list(args), stdin=slave, stdout=slave, stderr=slave,
                             env=self.env(TZ="UTC"), cwd=self.side, close_fds=True, preexec_fn=own_terminal)
        os.close(slave)
        chunks, sent = [], False
        try:
            while True:
                if not sent and b"[y/N]" in b"".join(chunks):
                    time.sleep(0.2)
                    os.write(master, typed)
                    sent = True
                ready, _, _ = select.select([master], [], [], 60)
                if not ready:
                    break
                try:
                    data = os.read(master, 65536)
                except OSError:
                    break
                if not data:
                    break
                chunks.append(data)
        finally:
            os.close(master)
        return p.wait(timeout=30), b"".join(chunks).decode("utf-8", "replace")


class SendTest(LineHome):
    def test_1_the_send(self):
        self.assertEqual(self.answer("pear-hq", "2", "--pick", "North", "--yes"), (0, OUT, ERR))
        self.assertEqual([(c["argv"], c["cwd"]) for c in self.replies()],
                         [(["reply", "2", "--pick=North", "--yes"], os.path.realpath(self.pear))])
        self.assertEqual(self.sent_once(self.pear, self.side)["replies"], 1)
        n = 1
        for args in (("--say", "the west gate", "--yes"), ("--pick", "North", "-y")):
            self.assertEqual(self.answer("pear-hq", "2", *args), (0, OUT, ERR), args)
            self.sent_once(self.pear, self.side, n)
            n += 1
        link = os.path.join(self.side, "pear-link")
        os.symlink(self.pear, link)
        for repo, cwd in (("./pear-hq", self.T), (self.pear, self.side), (link, self.side)):
            self.assertEqual(self.answer(repo, "2", "--pick", "North", "--yes", cwd=cwd), (0, OUT, ERR), repo)
            self.sent_once(self.pear, cwd, n)
            n += 1
        self.assertEqual(self.answer("quince-hq", "2", "--pick", "North", "--yes"), (0, OUT, ERR))
        self.assertEqual(self.replies()[-1]["cwd"], os.path.realpath(self.quince))
        self.sent_once(self.quince, self.side, n)

    def test_2_the_terminal(self):
        code, screen = self.on_pty(["pear-hq", "2", "--pick", "North"])
        self.assertEqual(code, 0, screen)
        self.assertEqual([(c["tty0"], c["tty2"], c["got"]) for c in self.replies()], [(True, True, "y")])
        self.assertEqual(screen.replace("\r\n", "\n"), "write it? [y/N] y\n" + OUT + ERR)
        self.sent_once(self.pear, self.side)
        code, screen = self.on_pty(["pear-hq", "2", "--pick", "North"], typed=b"n\n")
        self.assertEqual(code, 1, screen)
        self.assertNotIn("warn", screen)
        self.assertEqual(len(self.sends()), 1)
        self.plain()

    def test_3_the_exit_passes_through(self):
        for k in (1, 2, 3, 7):
            self.set("reply", exit=k)
            self.assertEqual(self.answer("pear-hq", "2", "--pick", "North", "--yes"), (k, OUT, ERR), k)
        self.set("reply", kill=signal.SIGTERM)
        code, out, err = self.answer("pear-hq", "2", "--pick", "North", "--yes")
        self.assertEqual((code, err), (-signal.SIGTERM, ""))
        self.set("reply")
        code, screen = self.on_pty(["pear-hq", "2", "--pick", "North"], typed=b"\x03")
        self.assertEqual(code, -signal.SIGINT, screen)
        self.assertNotIn("warn", screen)
        self.assertEqual(self.sends(), [])
        self.plain()

    def signalled(self, signum, ignored=False):
        """The writer waits for a file; `signum` goes to the suite's pid alone, or, `ignored`, to the
        group of a suite started in its own session with SIGINT and SIGQUIT ignored, as `sh` starts
        a job with `&`. (code, out, err)."""
        mark = os.path.join(self.side, "go")
        self.set("reply", wait=mark)
        replies = os.path.join(self.side, "reply-calls")
        if os.path.exists(replies):
            os.remove(replies)

        def ignore():
            for sig in (signal.SIGINT, signal.SIGQUIT):
                signal.signal(sig, signal.SIG_IGN)

        p = subprocess.Popen([self.L, "inbox", "answer", "pear-hq", "2", "--pick", "North", "--yes"],
                             stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env=self.env(TZ="UTC"), cwd=self.side, text=True, start_new_session=ignored,
                             preexec_fn=ignore if ignored else None)
        try:
            end = time.monotonic() + 30
            while not os.path.exists(replies) and time.monotonic() < end:
                time.sleep(0.05)
            time.sleep(0.2)
            (os.killpg if ignored else os.kill)(p.pid, signum)
            time.sleep(0.5)
            with open(mark, "w"):
                pass
            out, err = p.communicate(timeout=30)
        finally:
            if os.path.exists(mark):
                os.remove(mark)
        with open(os.path.join(self.side, "reply.pid")) as fh:
            writer = int(fh.read())
        self.assertTrue(gone(writer), signum)
        return p.returncode, out, err

    def test_4_signals_to_the_suite(self):
        self.assertEqual(self.signalled(signal.SIGINT), (0, OUT, ERR))
        self.sent_once(self.pear, self.side)
        for signum in (signal.SIGTERM, signal.SIGHUP):
            self.assertEqual(self.signalled(signum), (-signum, "", ""), signum)
            self.assertEqual(len(self.sends()), 1, signum)
        self.plain()

    def test_9_a_writer_killed_by_sigkill(self):
        """Review 1 F1: a signal whose action cannot be set still ends the suite by it, no traceback."""
        self.set("reply", kill=signal.SIGKILL)
        code, out, err = self.answer("pear-hq", "2", "--pick", "North", "--yes")
        self.assertEqual((code, err), (-signal.SIGKILL, ""))
        self.assertEqual(self.sends(), [])
        self.plain()

    def test_10_a_caller_that_ignores_sigint_and_sigquit(self):
        """Review 1 F2: the caller's ignore reaches the writer, so a ^C to the group leaves it to write."""
        n = 0
        for signum in (signal.SIGINT, signal.SIGQUIT):
            self.assertEqual(self.signalled(signum, ignored=True), (0, OUT, ERR), signum)
            self.sent_once(self.pear, self.side, n)
            n += 1
        self.plain()

    def test_5_nothing_sent_where_nothing_was_written(self):
        for args in (("--pick", "North", "--yes"), ("pear-hq", "x", "--pick", "North", "--yes"),
                     ("pear-hq", "2", "--pick", "North", "--say", "no", "--yes"),
                     ("pear-hq", "2", "--pick", "North", "--check"), ("plum-hq", "2", "--pick", "North", "--yes"),
                     (os.path.join(self.pear, "README.md"), "2", "--pick", "North", "--yes"),
                     ("pear-hq", "2", "--pick", "North")):
            code, out, err = self.answer(*args)
            self.refused(code, err)
            self.assertEqual(out, "")
        code, out, err = self.answer("pear-hq", "2", "--pick", "North", "--json")
        self.assertEqual((code, err, json.loads(out)["ok"]), (2, "", False))
        other = self.checkout(os.path.join(self.T, "other", "pear-hq"))
        self.user("checkouts: [%s, %s]\n" % (self.pear, other))
        self.refused(*self.answer("pear-hq", "2", "--pick", "North", "--yes")[::2])
        self.user("checkouts: [%s, %s]\n" % (self.pear, self.quince))
        self.ledger_stub([])
        self.refused(*self.answer("pear-hq", "2", "--pick", "North", "--yes")[::2])
        os.remove(os.path.join(self.stubs, "agentik-ledger"))
        code, out, err = self.answer("pear-hq", "2", "--pick", "North", "--yes")
        self.assertEqual((code, out), (3, ""))
        self.assertNotIn("warn", err)
        self.assertEqual(self.sends(), [])
        self.assertEqual(self.replies(), [])
        self.ledger_stub(self.verbs)
        for args in (("--dry-run",), ("--dry-run", "--yes")):
            self.assertEqual(self.answer("pear-hq", "2", "--pick", "North", *args), (0, OUT, ERR), args)
        self.assertEqual(len(self.replies()), 2)
        self.assertEqual(self.sends(), [])
        self.plain()


class UnsentTest(LineHome):
    def unsent(self, why):
        code, out, err = self.answer("pear-hq", "2", "--pick", "North", "--yes")
        self.assertEqual((code, out, err), (0, OUT, ERR + UNSENT % ("pear-hq", why)))

    def test_6_no_sender(self):
        bench = os.path.join(self.stubs, "agentik-bench")
        os.rename(bench, bench + ".away")
        self.unsent("no command on PATH sends a line")
        os.rename(bench + ".away", bench)
        self.bench_stub([])
        self.unsent("no command on PATH sends a line")
        self.assertEqual(len(self.replies()), 2)
        self.assertEqual(self.sends(), [])
        self.bench_stub(self.lines)
        self.plain()

    def test_7_the_send_fails(self):
        command = "agentik-bench line send"
        for how, why in (({"exit": 2}, "%s refused it, as one older than --text does "
                                       "(run %s update)" % (command, self.L)),
                         ({"exit": 1}, "%s failed" % command), ({"exit": 3}, "%s failed" % command),
                         ({"kill": True}, "%s ended by a signal" % command)):
            self.set("line", **how)
            self.unsent(why)
        self.set("line", sleep=30)
        t0 = time.monotonic()
        self.unsent("%s gave no answer in 5 s" % command)
        self.assertLess(time.monotonic() - t0, 5 + 2 + 3)  # the wall, two seconds, and the walk's own time
        for c in self.sends():
            self.assertTrue(gone(c["pid"], group=True), c)
        self.assertEqual(len(self.sends()), 5)
        p = subprocess.run([self.L, "inbox", "answer", "pear-hq", "2", "--pick", "North", "--yes"], input="",
                           capture_output=True, text=True, env=self.env(TZ="UTC"), timeout=60, cwd=self.side)
        ended = time.time()
        self.assertEqual((p.returncode, p.stdout, p.stderr),
                         (0, OUT, ERR + UNSENT % ("pear-hq", "%s gave no answer in 5 s" % command)))
        # the wall and two seconds, from the writer's call (review 1 F6)
        self.assertLess(ended - os.path.getmtime(os.path.join(self.side, "reply-calls")), 5 + 2)
        self.assertTrue(gone(self.sends()[-1]["pid"], group=True))
        self.plain()

    def test_11_a_signal_to_the_suite_during_the_send(self):
        """Review 1 F3: SIGINT, SIGTERM and SIGQUIT to the suite while the line is sent: the send
        stopped, its group ended, R7's warn line, the writer's exit 0."""
        self.set("line", sleep=30)
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGQUIT):
            before = len(self.sends())
            p = subprocess.Popen([self.L, "inbox", "answer", "pear-hq", "2", "--pick", "North", "--yes"],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 env=self.env(TZ="UTC"), cwd=self.side, text=True)
            end = time.monotonic() + 30
            while len(self.sends()) == before and time.monotonic() < end:
                time.sleep(0.05)
            time.sleep(0.3)
            os.kill(p.pid, signum)
            out, err = p.communicate(timeout=30)
            self.assertEqual((p.returncode, out, err), (0, OUT, ERR + UNSENT % ("pear-hq", "the send was stopped")),
                             signum)
            self.assertEqual(len(self.sends()), before + 1, signum)
            self.assertTrue(gone(self.sends()[-1]["pid"], group=True), signum)
        self.plain()


class TextTest(LineHome):
    def test_8_the_texts(self):
        p = subprocess.run([self.L, "help", "inbox"], capture_output=True, text=True, env=self.env(), timeout=60,
                           cwd=self.side)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("your answer typed on its answer line, then a line sent to its sitting", p.stdout)


if __name__ == "__main__":
    import unittest
    unittest.main()
