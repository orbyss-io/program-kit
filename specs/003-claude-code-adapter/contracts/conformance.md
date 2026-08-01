# Conformance Contract: Claude Code Adapter

## Profile identity

`orbyss.program-kit:conformance-profile:session-claude-code@1.0.0`

The profile evaluates the exact adapter against Feature 002's accepted
canonical session definition. It does not declare Claude Code generally
compatible.

## Release-blocking deterministic gates

| Gate | Required proof | Failure |
|---|---|---|
| Manifest closure | Exact provider, adapter, definition, catalog, surface, operations, and projection descriptors resolve once | Adapter unavailable |
| Projection bytes | Equal accepted inputs produce byte-identical `SKILL.md`; permutation does not change bytes | Determinism gate failed |
| Provider isolation | Claude-specific symbols occur only in adapter, fixtures, and provider docs/diagnostics | Neutrality gate failed |
| Skill safety | No permission grants, executable dynamic content, scripts, settings edits, global scope, secrets, or domain semantics | Disclosure/authority gate failed |
| Invocation normalization | Executable and argument array preserve exact CLI, workspace, request, operation, and JSON mode across Windows/Linux | Transport gate failed |
| Result preservation | Outcome, phase, effect, disposition, diagnostics, artifacts, evidence, receipts, and continuation remain unchanged | Semantic conformance failed |
| Authority preservation | Missing/stale/mismatched grants remain blocked even if provider process permission exists | Authority gate failed |
| Lifecycle safety | Explain/verify are read-only; install/remove use generic atomic publisher and exact ownership | Publication gate failed |
| Drift/removal | Modified or unproven skill material is diagnosed and preserved | Ownership gate failed |
| Diagnostics | Every provider trigger maps to one exact PKCLD identity and safe fields | Diagnostic gate failed |
| Runtime isolation | Generated application has no Program Kit/session/provider runtime reference | Release blocked |
| Source isolation | Program Kit authoring marker blocks the lifecycle against source | Bootstrap gate failed |

## Shared scenario corpus

At minimum, the corpus contains:

1. valid read-only explanation;
2. construction without authority;
3. construction with exact authority;
4. stale, mismatched, widened, and reused authority;
5. valid read-only evaluation;
6. drifted generated artifact evaluation;
7. malformed request and unsupported intent;
8. zero/multiple provider or adapter resolution;
9. unavailable CLI and provider versions;
10. pre-existing skill collision;
11. interrupted/partial publication;
12. exact, stale, drifted, incompatible, partial, absent, and removed
    verification states;
13. exact and drifted removal;
14. provider permission denied;
15. contaminated/truncated/invalid structured output;
16. provider success contradicting Program Kit evidence;
17. source-authoring workspace refusal; and
18. generated runtime without authoring tooling.

For every comparable case, direct CLI, neutral harness, Codex adapter fixtures,
and Claude adapter fixtures MUST preserve the same canonical operation, maximum
and actual effect, outcome, primary disposition, and diagnostic meaning. A
provider-specific prerequisite may add a provider diagnostic without changing
the underlying Program Kit result.

## Live-provider evidence profile

Live evidence is separately classified `human-review` and never replaces the
deterministic gates.

The exact target is Claude Code `2.1.220`. Each run starts a fresh session from
the isolated consumer repository. The ten required trials cover:

- explicit `/program-kit` invocation;
- natural-language skill discovery;
- explain-before-effect behavior;
- missing-authority refusal;
- exact-authority construction;
- structured diagnostic recovery;
- read-only evaluation;
- current-session versus fresh-session availability; and
- no provider-generated success contrary to actual effects.

The live harness MAY use normal `claude -p` with:

- an exact prompt/case identity;
- `--output-format json` and an exact bounded `--json-schema` for the trial
  classification;
- an exact `--allowedTools` rule limited to the workspace-local Program Kit
  executable for headless trials; and
- provider credentials supplied outside the review kit.

It MUST NOT use `--bare`, because that disables project-skill discovery. It MUST
NOT persist raw Claude output, transcripts, prompts, credentials, or model
reasoning. It MUST independently compare Program Kit results and workspace
effects before assigning a verdict.

## Verdict rules

- `passed`: every mandatory deterministic gate passes; all required live trials
  have complete independent evidence; no unauthorized effect occurred; and a
  human reviewer accepts the product behavior.
- `failed`: a required behavior or evidence invariant is violated.
- `incompatible`: the exact provider surface cannot preserve a mandatory
  canonical boundary.
- `inconclusive`: observations conflict or required evidence is incomplete.
- `not-evaluated`: provider prerequisites were unavailable or the review did
  not run.

Only `passed` supports the full provider claim. Green deterministic tests with a
missing live review support the adapter implementation but leave live-provider
fitness visibly pending.
