# What `issue new --render` hands the narrator

`agentik-suite issue new --render` starts the narrator plugin's headless script from an empty temporary folder that holds the draft and the contract, and removes the folder after.
The source is the scrubbed draft on disk, so the script is given only what an issue could hold.
The script's own tools still reach the disk outside that folder: the suite stops no read or write there.
A headless run under a login loads that user's CLAUDE.md, so words from the user's own context can reach the answer.
That is why the answer is held to the nothing-new check: a word the draft did not hold drops the render, and the template stands with the words as typed.
The whole environment reaches the script too, since the narrator needs the login it finds there.
