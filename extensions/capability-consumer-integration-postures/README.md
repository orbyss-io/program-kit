# Capability consumer integration postures

This extension implements the human-approved capability-consumer integration
design on the Program Kit `0.1.0-alpha.3` source baseline.

The original approved review set bound:

- architecture design
  `sha256:666cf457a32702cd8ecf29fbdf412a99bd7187e953c5e1696d82bd4d6fa9d1b0`;
- implementation plan
  `sha256:2d9bbfe4d45289322fad65c7971dce2618be43197f31ca3b64cf5831d334106e`;
- direct human approval: `I approve implementation`.

After current-source reconciliation, the human approved a delta-only alpha.3
amendment. Alpha.3 already owned the installed CLI's embedded exact capability
knowledge closure, preflight/read operations, and complete multi-provider
ownership lock. Those foundations were preserved rather than replaced.

The remaining implementation owns:

- the finite reviewed provider contract with Codex at `.agents/skills` and
  Claude Code at `.claude/skills`;
- exact ownership-verified migration from legacy Codex `.codex/skills`;
- durable transaction recovery for initialization and removal;
- explicit exact-byte `capabilities uninitialize`;
- `none`, `local-optional`, and `repository-managed` consumer guidance;
- exact bundle digest refresh while keeping bundle and package version
  `0.1.0-alpha.3`; and
- repository-managed adoption by the Domain Semantic Engine consumer.

The analyzer-digest task explicitly confirmed that it owns none of these
surfaces. This extension excludes compiler, analyzer, package canonicalizer,
release-selection, and release-workflow behavior. Its implementation may
change package-inventory evidence only through ordinary exact-byte propagation.

## Authority boundary

Program Kit does not choose a posture, edit `.gitignore`, stage or commit
consumer files, install an AI provider, grant trust or permissions, or start
development work. Each lifecycle command remains an explicit human-started,
project-scoped operation. Capability procedures remain development-session
content and are not runtime inputs.

## Verification

Closure requires:

- mandatory Program Kit C# gate build;
- complete unit and conformance suites;
- exact bundle manifest and package verification;
- initialization, coexistence, legacy migration, readiness, recovery, exact
  removal, tamper, and collision tests;
- documentation review for all three postures and exact alpha.3 commands;
- clean consumer repository-managed discovery; and
- review proving no analyzer/release or unrelated consumer bytes changed.
