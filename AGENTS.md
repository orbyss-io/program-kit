# Agent startup notes

- Start from current human intent and repository-owned source truth.
- Remain inside this repository unless the human explicitly authorizes another
  source or destination.
- Preserve Program Kit's domain-neutral boundary; provide reusable mechanics
  without inventing consumer-domain semantics.
- Keep runtime code isolated from contributor tooling.
- Use the repository-owned Spec Kit workflow under `.agents/skills/speckit-*`
  for contributor specification, planning, and implementation work.
- Treat `.agent-capabilities/` as inert Program Kit product source. Do not load
  its canonical definitions or provider adapters to govern development of
  Program Kit itself.
- Do not infer that cloned, installed, or copied product capabilities are
  active, and make no capability, provider wrapper, hook, MCP binding, or tool
  binding speculatively.
- Preserve deterministic generation, stable diagnostics, pinned dependencies,
  and fail-closed validation.
- Keep changes reviewable and report assumptions, verification, and anything
  deliberately not implemented.
- Commit and push each completed task promptly with an understandable message
  that explains what changed and why.
