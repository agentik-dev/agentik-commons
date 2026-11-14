---
name: issue
description: Draft a report of a problem with an agentik tool, scrubbed of private names, for the user to read and send from their own terminal.
---

# Report an issue with an agentik tool

You draft; the user sends. A draft never leaves this machine until the user reads it on a terminal of their own and types the word there.

1. Draft it through Bash, with what the user said failed. Give the command they ran, its exit code, a file holding its last lines if there is one, and what they expected:

   ```
   agentik issue new TOOL --ran 'COMMAND' --exit CODE --output FILE --expected 'WHAT THEY EXPECTED'
   ```

   Leave out what you do not know. Show the user the printed draft, the counts of what was replaced and the warning, whole.

2. Ask the respeak plugin's narrator agent to render the draft's two lines of prose. Hand it the path of the draft's `issue.md` (from `agentik issue --json`) and this contract: technical, at most two sentences a line, error text verbatim, nothing added that the draft does not hold. Write its answer to a file of two lines, `Happened: ...` and `Expected: ...`, and give it to the draft:

   ```
   agentik issue reword FILE
   ```

   When reword keeps the template, the draft stands with the user's own words; that is fine.

3. Ask the user to read every line. Make the removals they ask for through Bash: `agentik issue strike WORD...` replaces a word wherever it stands, `agentik issue drop SECTION...` removes `checks`, `plugins`, `system`, `output` or `words`, and `agentik issue show` prints the draft again.

4. End by handing the user this one line to type in a terminal of their own, outside this session: `agentik issue send`. You never run that line yourself, in any form; it refuses inside Claude Code, and filing is the user's act alone.
