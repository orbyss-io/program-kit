# Managed browser dependency and architecture routing repair

## Observed failure

Household Shopping run `fbf1521e` in
`C:\Users\Joeyb\AppData\Local\Temp\program-kit-intake-nh09io7h` failed at
`validate-architecture-output`. Its recorded architecture blocker binds context SHA-256
`de4d1c701b4f8edce322862d52511c8e7352ade5b47fd488017cbcc91b73cc53`.
The approved assessment adopted `bff-cookie-v1` with `browser_ui: true`, but selected only
`ui-experience-v1`. It stated no language was selected. Research proposed .NET/Foundation;
architecture received only `browser_bff`, with no `api_baseline` or runtime-release projection.
The worker correctly stopped instead of reconstructing a prohibited catalog or inventing values.

The user requested a root repair and a fresh trial. This attempt remains unchanged as evidence;
its approval is not retroactively reinterpreted as acceptance of a different stack.

## Evidence and diagnosis

- `extensions/program-kit-dotnet/references/secure-web-profiles.md` already defines the managed
  profiles as Foundation implementations, with Foundation BFF/SPA-PKCE features and shell settings.
  Managed sign-in is therefore not a framework-neutral service independent of a backend.
- `extensions/program-kit-building-blocks/references/orbyss-building-blocks.json` defines the
  browser compositions with .NET and shell slots, and `dotnet-host-runtime` with `api_baseline`.
- `governance_state.py` previously validated browser security semantics only when a browser
  profile was in `selected_profiles`; `web.browser_ui: true` could evade that branch. It also
  accepted managed authentication without its .NET profile.
- `bootstrap_context.py` previously routed capability contracts and runtime release knowledge
  exclusively from intake. Profiles adopted later in assessment could not supply missing routes.
- Research-only `managed_profile_pins: null` during architecture is intentional; architecture
  already receives the adopted `toolchain` register. The missing host projection was a real gap.
  Copying all research pins into every stage would duplicate authority without repairing it.

## Repair

The existing capability descriptions and secure-web selection instructions disclose the managed
backend dependency before approval, even for a technology-neutral product vision. They preserve
explicit alternate-stack constraints for resolution instead of claiming the consumer selected .NET.

A shared profile dependency check runs in the assessment producer's terminal check, before
research context generation, and in full governance validation. A browser UI requires a browser
profile; managed authenticated profiles require .NET and its decision block. Full governance
continues to enforce the host default/opt-out, acknowledgement, exact toolchain pins and security
records before approval.

Stage context generation combines original routing with structured assessment selections without
editing confirmed intake. It replaces stale authentication suggestions with the adopted profile,
adds the selected Foundation host contract, and honors an explicit alternate host. The runtime
projection binds the installed catalog hash, exact host version/tag and source. Registry digest
and compatibility remain later empirical closure evidence; the projection makes no proof claim.
Architecture instructions point to the existing adopted toolchain authority and this host projection.

The product fixture remains an ordinary shopping vision. No .NET, host, composition, endpoint,
first-slice identifier or desired answer was added to steer the new interview.

## Verification scope

Regression tests exercise neutral intake through generated assessment, research and architecture
contexts; preserve the original intake bytes; require host slots/options and exact pin projections;
and reject the original malformed assessment before another worker dispatch. Negative/alternative
coverage includes both authenticated profiles, anonymous browser use and a reviewed alternate host.
Governance tests exercise the approval validator as well as the early producer check.

The general context suite also had a stale readiness-command assertion omitting the existing
`--json` option. The test now verifies that established command; production readiness behavior
was not changed by this repair.

The context schema also lacked the already generated `runtime_release` property. It now describes
that projection and its catalog-bound host identity. The regression validates generated assessment,
research and architecture briefs against the actual JSON Schema engine.

Completed checks:

- `python tests/validate_bootstrap_profiles.py`: four regression tests passed, including generated
  handoffs and schema validation.
- `python tests/validate_bootstrap_context.py`: generation, compactness and staleness checks passed.
- `./scripts/Test-ProgramKit.ps1 -Suite Development`: passed; log
  `artifacts/bootstrap-profile-development.log`. This includes governance rejection cases and
  native workflow resumption tests. A Desktop-local executable access failure occurred before
  validation began on the first invocation; the completed invocation used the available Python
  interpreter and installed CLI with external-process access.
- Final `Start-IntakeSession.ps1 -PrepareOnly -KeepWorkspace`: passed, record
  `artifacts/intake-sessions/f3f5e042a486475d8491e4666518319f`. No agent or bootstrap launched.
  All six changed installed script/reference files match source bytes and both generated skills
  contain the repair; `artifacts/bootstrap-profile-installed-verification.json` records hashes.
  The earlier setup-only record `0640d6d400af4e37b5e7a12f402268a3` predates final hardening;
  use the final record above for installation evidence.

This is deterministic repair evidence, not a claim that an uninterrupted paid bootstrap or first
feature trial has passed. The next fresh user-run trial measures that behavior.
