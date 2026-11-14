"""A word the suite's command does not know (packet ak2 R3): a plugin's name with no command on
PATH exits 3, pointing at the setup plan; any other word exits 2 with the nearest of the verbs
and the plugins' names. Each run is the suite's launcher in ak1a's temp HOME; every plugin here
is made up."""
import json
import os
import unittest

from test_agentik_suite import LAUNCHER, Home

CMD = str(LAUNCHER)  # a printed command with no door: the launcher's path, as typed (row sc2)

LINE = "FAIL  pear is not installed\nnext: %s setup pear\n" % CMD  # row sc4 R7


class PluginWordTest(Home):
    def setUp(self):
        Home.setUp(self)
        market = os.path.join(self.home, "market")
        os.makedirs(os.path.join(market, ".claude-plugin"))
        with open(os.path.join(market, ".claude-plugin", "marketplace.json"), "w") as fh:
            json.dump({"plugins": [{"name": "pear", "description": "A made-up plugin."},
                                   {"name": "suite", "description": "The set."}]}, fh)
        self.plugins = os.path.join(self.home, ".claude", "plugins")
        os.makedirs(self.plugins)
        with open(os.path.join(self.plugins, "known_marketplaces.json"), "w") as fh:
            json.dump({"agentik": {"installLocation": market}}, fh)

    def assert_not_installed(self, *args):
        code, out, err = self.run_cli(*args)
        self.assertEqual((code, out), (3, ""), args)
        self.assertEqual(err, LINE)
        code, out, err = self.run_cli(*args, "--json")
        self.assertEqual(code, 3, args)
        answer = json.loads(out)
        self.assertEqual((answer["ok"], answer["error"]["code"]), (False, "not_installed"))
        self.assertEqual(answer["error"]["remedy"], "%s setup pear" % CMD)
        self.assertEqual(len(out.splitlines()), 1)

    def test_a4_a_plugin_with_no_command_exits_three(self):
        self.assert_not_installed("pear")
        self.assert_not_installed("pear", "status")
        self.assert_not_installed("help", "pear")

    def test_a4_any_other_word_exits_two_with_the_nearest(self):
        for args in (("paer",), ("help", "paer")):
            code, out, err = self.run_cli(*args)
            self.assertEqual((code, out), (2, ""), args)
            self.assertIn("paer is not a tool\nnext: ", err)  # a known plugin is a near tool (sc4 review 1 F6)
            self.assertTrue(err.endswith(" help pear\n"), err)
        code, out, _ = self.run_cli("paer", "--json")
        self.assertEqual((code, json.loads(out)["error"]["code"]), (2, "unknown_verb"))
        self.assertEqual(self.run_cli("nosuch")[0], 2)

    def test_f3_the_json_remedy_names_a_verb_only(self):
        # review 1 F3: `agentik-suite pear` never succeeds, so a nearest plugin's remedy is --help
        # sc4 review 1: a known plugin's help (F6); never a verb that writes (F2)
        for args, remedy in ((("paer",), CMD + " help pear"), (("stup",), CMD + " help"),
                             (("nosuch",), CMD + " help")):
            code, out, _ = self.run_cli(*args, "--json")
            self.assertEqual((code, json.loads(out)["error"]["remedy"]), (2, remedy), args)

    def test_a4_a_plugin_whose_command_is_on_path_exits_two(self):
        self.stub("agentik-pear")
        code, out, err = self.run_cli("pear")
        self.assertEqual((code, out), (2, ""))
        self.assertNotIn("nearest is pear", err)
        self.assertEqual(self.run_cli("help", "pear")[0], 2)

    def test_a4_the_names_come_from_each_of_three_places(self):
        # an installed <name>@agentik, with no marketplace entry
        with open(os.path.join(self.plugins, "installed_plugins.json"), "w") as fh:
            json.dump({"version": 2, "plugins": {"plum@agentik": [], "fig@elsewhere": []}}, fh)
        self.assertEqual(self.run_cli("plum")[0], 3)
        self.assertEqual(self.run_cli("fig")[0], 2)
        # the suite's own name is never a missing plugin
        self.assertEqual(self.run_cli("suite")[0], 2)

    def test_a4_a_row_of_the_fallback_table_counts(self):
        from test_agentik_suite import LIB
        rows = json.loads((LIB / "fallback.json").read_text())
        name = sorted(rows)[0]
        code, _, err = self.run_cli(name)
        self.assertEqual(code, 3)
        self.assertIn("setup %s" % name, err)


if __name__ == "__main__":
    unittest.main()
