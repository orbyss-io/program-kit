# Commit and push coherently

This is an inert supporting completion profile. It is not a capability,
command, trigger, approval, or independently invokable procedure.

After required verification and diff review, commit the admitted source,
affected derived artifacts, locks, and evidence as one coherent reversible
history event. Use a message that states what changed and why.

Push only when repository guidance or explicit human authority requires it.
Confirm the pushed commit identity matches the reviewed commit. Never include
unrelated concurrent work, secrets, release state, or unapproved publication.

Treat every non-default branch as short-lived and prefer the repository host's
automatic merged-head-branch deletion setting. After a merge, update the
default branch and prove the topic-branch tip is reachable from it before
deleting the merged remote branch and then its clean, inactive local
branch/worktree. Never delete the default or a protected branch, an unmerged
branch, a dirty branch, or a branch attached to active work. When cleanup lacks
authority or safety, preserve the branch and report its unique commits.
