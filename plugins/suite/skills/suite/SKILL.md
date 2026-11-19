---
name: suite
description: Find a setting and the line that changes it, check the install, or see what runs, across the agentik tools. Use when asked where something is set, what is installed or why a tool fails.
---

# The agentik command: settings, the install and what runs

You read; the user writes. The `agentik` command answers for every agentik tool at once, and each answer names the line that changes it.

1. Read through Bash, as often as you need. Add `--json` to any of these when you parse the answer, and read the plain form to the user:

   ```
   agentik doctor
   agentik config
   agentik config TOOL
   agentik config TOOL.KEY
   agentik config --changed
   agentik status
   agentik help
   ```

   `doctor` checks this machine and each tool, and gives each check that fails the line that mends it. `config` walks from every tool to one tool's keys to one key: its value, the file and line that set it, and how to change it. `status` shows what runs now. `help` with a tool's name after it prints that tool's own help.

2. The command writes no setting, and neither do you on its behalf. When the user wants a key changed, show them the `change` line of that key's card, whole, and let them make the change.

3. Setup, update and remove are the user's to run. Run each with `--dry-run` and show the plan:

   ```
   agentik setup --dry-run
   agentik update --dry-run
   ```

   and `remove` the same way, with the plugin's name. Then hand the user the line without `--dry-run` to type themselves. Never pass `--yes`: it answers for the user the one question these verbs ask. The command's own `next:` lines follow the same rule.

4. When a tool fails in a way none of this explains, the user may report it: the `issue` skill drafts the report.
