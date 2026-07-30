# Agent startup notes

- Start from current human intent and repository-owned source truth.
- Remain inside this repository unless the human explicitly authorizes another
  source or destination.
- Preserve Program Kit's domain-neutral boundary; provide reusable mechanics
  without inventing consumer-domain semantics.
- Keep runtime code isolated from development-session capabilities.
- Load canonical capability guidance through an active provider skill, and
  never treat its provider-local copy as the source of truth. At the start of
  a freshly initialized task, before loading a Program Kit source capability,
  run `build/Sync-SourceContributorCapabilities.ps1 -Provider
  <active-provider-id> -RefreshIfStale`. This resolves the registered local
  root for the active provider, compares every full `SKILL.md` projection with
  its canonical definition, and refreshes only missing or stale local copies.
- Never refresh source-contributor skills after a capability has been loaded
  for the active task. Refresh again only in a new task or when the human
  explicitly requests it; capability authoring must not rewrite the rules
  governing its own in-progress session.
- Do not infer that a cloned, installed, or copied capability is active.
  Capability availability and human authority must remain explicit.
- Keep ignored provider-local projections separate from consumer
  initialization. The authoring marker must continue to reject consumer
  `capabilities` initialization, catalog, preflight, read, and removal
  operations.
- Make no capability, provider wrapper, hook, MCP binding, or tool binding
  speculatively.
- Preserve deterministic generation, stable diagnostics, pinned dependencies,
  and fail-closed validation.
- Keep changes reviewable and report assumptions, verification, and anything
  deliberately not implemented.
- Commit and push each completed task promptly with an understandable message
  that explains what changed and why.
- Treat every non-default branch as short-lived. After its tip is verified as
  reachable from `main`, delete the merged remote branch and then its clean,
  inactive local branch/worktree. Never delete `main`, a protected branch, an
  unmerged branch, a dirty branch, or a branch attached to active work.
