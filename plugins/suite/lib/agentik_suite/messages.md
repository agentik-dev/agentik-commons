# Messages

Each item below is one message the command prints, by its id; the writer in `term.py` prints it.

## Help

- `help.title`: `{tool}` `{version}` manages the agentik suite's default set of plugins.
- `help.usage`: usage: `{tool}` <verb> [<noun>...] [flags]
- `help.verbs`: verbs
- `help.flags`: flags
- `help.path`: agentik commands on PATH
- `help.path.none`: No agentik command is on PATH yet.
- `hint.help`: next: `{tool}` setup --dry-run shows what setup would do on this machine.
- `hint.verb`: next: `{tool}` help lists every verb and the agentik commands on PATH.
- `verb.help`: List the verbs, the flags and the agentik commands on PATH.
- `verb.version`: Print the suite's version.
- `verb.setup`: Plan the suite's setup; this version only plans, with --dry-run.
- `usage.help`: usage: `{tool}` help [<verb>] [flags]
- `usage.version`: usage: `{tool}` version [flags]
- `usage.setup`: usage: `{tool}` setup --dry-run [<plugin>...] [flags]
- `flag.json`: Print one JSON object on stdout, and nothing else there.
- `flag.quiet`: Print no hints and no progress.
- `flag.no_color`: Print no colour, on a terminal too.
- `flag.help`: Show the usage and the flags.
- `flag.dry_run`: Show the plan, and write nothing.
- `flag.yes`: Take yes for each question; this version asks none.

## Version

- `version.line`: `{tool}` `{version}`

## Errors

- `err.verb.near`: `{word}` is not a verb; the nearest is `{near}`. Run `{tool}` --help for the list.
- `err.verb`: `{word}` is not a verb. Run `{tool}` --help for the list.
- `err.flag.near`: `{flag}` is not a flag here; the nearest is `{near}`. Run `{where}` --help for the flags.
- `err.flag`: `{flag}` is not a flag here. Run `{where}` --help for the flags.
- `err.extra`: `{where}` takes no word here, and got `{word}`. Run `{where}` --help for its usage.
- `err.setup.plan_only`: Setup wrote nothing: version `{version}` only plans. Run `{tool}` setup --dry-run for the plan.
- `err.setup.name`: `{name}` is not a plugin name: a name is lowercase letters, digits and dashes. Run `{tool}` setup --dry-run for the default set.

## Setup

- `setup.title`: Setup plan for `{plugins}`: each step is a read, and nothing is written.
- `setup.title.none`: Setup plan for no plugin, since the manifest lists none. Each step is a read.
- `setup.run`: run: `{command}`
- `setup.add`: add to your shell profile: `{command}`
- `setup.cmd.found`: on PATH at `{path}`
- `setup.cmd.missing`: not on PATH; setup stops here until it is installed
- `setup.python.ok`: Python `{version}` at `{path}`, at or above the `{floor}` floor
- `setup.python.low`: Python `{version}` at `{path}` is below the `{floor}` floor; setup stops here
- `setup.market.ok`: known to Claude Code
- `setup.market.missing`: not known to Claude Code; setup would add it
- `setup.plugin.ok`: installed at version `{version}`
- `setup.plugin.missing`: not installed; setup would install it
- `setup.launcher.wait`: not placed; it waits on step 3, since the plugin is not installed
- `setup.launcher.missing`: not placed; setup would place it from the plugin
- `setup.launcher.ok`: at version `{version}`, the plugin's own
- `setup.launcher.behind`: at version `{have}`, and the plugin is at `{want}`; setup would place it again
- `setup.launcher.unread`: holds no version line; setup would place it again at `{want}`
- `setup.suite.ok`: at version `{version}`, this command's own
- `setup.suite.behind`: at version `{have}`, and this command is at `{want}`; this version places none, so run `{path}` for now
- `setup.suite.missing`: not placed; this version places none, so run `{path}` for now
- `setup.door.ok`: in place
- `setup.door.missing`: not placed; the first install-cli of step 4 places it
- `setup.path.ok`: on PATH
- `setup.path.missing`: not on PATH; add the line below to your shell profile
- `setup.doctor.todo`: setup would run its doctor last, to check the plugin
- `setup.doctor.none`: no plugin is in the plan, so no doctor runs
- `hint.setup.todo`: next: run each line above that starts with run, in order, then `{tool}` setup --dry-run again.
- `hint.setup.done`: next: every step reads ok; `{tool}` help lists what else this command does.
