# Agent startup notes

- Start from current human intent and repository-owned source truth.
- Remain inside this repository unless the human explicitly authorizes another
  source or destination.
- Preserve Program Kit's domain-neutral boundary; provide reusable mechanics
  without inventing consumer-domain semantics.
- Keep runtime code isolated from development-session capabilities.
- Load canonical capability guidance through an active provider wrapper, and
  never treat a wrapper as the source of truth.
- Do not infer that a cloned, installed, or copied capability is active.
  Capability availability and human authority must remain explicit.
- Make no capability, provider wrapper, hook, MCP binding, or tool binding
  speculatively.
- Preserve deterministic generation, stable diagnostics, pinned dependencies,
  and fail-closed validation.
- Keep changes reviewable and report assumptions, verification, and anything
  deliberately not implemented.
- Commit and push each completed task promptly with an understandable message
  that explains what changed and why.
