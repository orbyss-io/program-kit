# ProgramKit Development Tools convergence notes

## Status and human rulings

These notes record decisions made after the validated `1.0.0` review set was
published. They do not amend the canonical design or authorize implementation.

- Development Tools is the sole active design concern.
- Corrective Reconstruction is held on the backlog until it has a concrete
  goal, first consumer, triggering scenario, and observable success condition.
- The replacement Development Tools review set must cover both Codex and Claude
  Code from the outset.
- ProgramKit will implement the provider-neutral setup and both provider
  integrations in this repository after exact human approval. Claude Code
  runtime acceptance may be executed by the human on another machine and
  returned as external evidence.
- Convergence will proceed section by section. The old canonical design and
  plan digests are baseline evidence, not current approval candidates.

## Product shape under convergence

The research supports three separately owned pieces:

1. A versioned, provider-neutral Development Tool executable contract owned by
   ProgramKit.
2. One provider-neutral MCP stdio bridge that exposes that contract without
   owning provider registration, trust, or permissions.
3. Thin provider registration integrations that translate the same reviewed
   registration into Codex project configuration or Claude Code project MCP
   configuration.

This avoids implementing a different tool protocol for every AI provider.
Provider-specific code owns only discovery/configuration, collision checks,
human trust boundaries, status, update, removal, and provider evidence.

No executable, bridge, registration integration, provider binding, capability,
permission, or runtime behavior exists yet.

## Claude Code authoritative findings

Research was limited to Anthropic's official Claude Code documentation and the
stable MCP specification:

- Claude Code supports local MCP servers over stdio and manages them explicitly
  with `claude mcp add`, `list`, `get`, and `remove`:
  <https://code.claude.com/docs/en/mcp>.
- Project-scoped servers live in `.mcp.json`. They are shareable but remain
  pending until the human trusts the workspace and approves the server. A
  cloned repository cannot approve itself:
  <https://code.claude.com/docs/en/mcp>.
- Claude Code MCP permissions use `mcp__<server>__<tool>` rules with `deny`,
  `ask`, and `allow`; restrictive policy takes precedence:
  <https://code.claude.com/docs/en/permissions>.
- Claude settings expose project-server enable/disable controls, but the
  registration integration must not grant trust or enable every project
  server:
  <https://code.claude.com/docs/en/settings>.
- Claude plugins can bundle MCP servers that start when the plugin is enabled.
  That lifecycle conflicts with the current explicit-registration and
  no-automatic-start boundary, so plugin transport is not the proposed first
  integration:
  <https://code.claude.com/docs/en/plugins-reference>.
- Stable MCP defines tool discovery/call and stdio transport independently of
  either provider:
  <https://modelcontextprotocol.io/specification/2025-11-25/server/tools> and
  <https://modelcontextprotocol.io/specification/2025-11-25/basic/transports>.

## Proposed Claude boundary for review

The current recommendation is project-scoped `.mcp.json`, because it is
reviewable, portable, provider-supported, and visible to a genuinely cold
Claude Code session. Registration would write only an owned server entry
pointing at exact locally materialized package/contract/bridge bytes. It would
not approve the server, alter Claude permission policy, start Claude Code, or
invoke a tool.

The human would explicitly trust and approve the project server in Claude Code.
Mutating Development Tool calls would remain subject to Claude's provider
permission flow. Update and removal would verify recorded ownership and exact
bytes before changing the owned entry.

The external acceptance record must include the Claude Code version, clean
machine/session preconditions, registration receipt, project trust/server
approval, cold-session discovery and semantic invocation, tool-call result,
and negative cases for collision, tampering, incompatible package versions,
permission denial, update, and removal.

## Next convergence question

Before exact identities and schemas are useful, the first Development Tool
needs a concrete outcome: what should the generated Console tool actually let
an AI session accomplish beyond proving that discovery and invocation work?
