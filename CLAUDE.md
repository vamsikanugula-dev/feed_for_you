\# Working rules



@PROGRESS.md



PROGRESS.md in the project root is the single source of truth for what is done, what failed, and what to do next. Trust it over your memory of the conversation.



\## At session start and after every compaction

1\. Read PROGRESS.md.

2\. Tell me in 2-3 lines what is done and what the Next step is.

3\. Continue from the Next step. Do not restart or redo anything under Done.



\## During work

\- One subtask at a time.

\- When a subtask is finished and its test passes, update PROGRESS.md, then git commit, before starting the next subtask.

\- Before starting any step, check whether its output already exists (file, passing test, git log). If it does, mark it done and skip it.

\- Write large outputs (logs, search results) to files and keep only a short summary in the conversation.



\## Entry format

\- Done: one line each with file path and evidence.

\- Failed approaches: what was tried and why it failed. Never retry these.

\- Next step: exactly one concrete action.

\- Keep PROGRESS.md under about 80 lines. Move old finished items to PROGRESS\_ARCHIVE.md.



\## Stuck rule

If the same action fails twice, stop. Record it under Failed approaches, then try a different approach or ask me.



\## Before compacting or ending the session

Update PROGRESS.md so someone with no memory of this conversation could continue from it.



\# Compact instructions

When compacting, always preserve: the goal verbatim, the Done, Failed approaches and Next step sections of PROGRESS.md, file paths changed, commit hashes, unresolved errors with exact messages, and decisions with reasons.

