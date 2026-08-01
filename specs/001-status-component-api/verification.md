# Verification Record

Date: 2026-08-01

## Current status

**The corrected cross-platform provenance candidate passed the complete local
T102 gate. T095 is reopened pending required Windows/Ubuntu CI and a fresh
named-human decision on the corrected exact binding.**

The corrected implementation and generated-evidence candidate is commit
`4d1c519fd5e788c36252437de03cb8c1ccb13c33`. Its checked-in
`artifacts/evidence/distribution-manifest.json` has byte digest
`sha256:25fd0146dcca3fe8b8d359a9a208e51504718eb978b95fde60570a33cd8ecebd`.
It rejects BOM, invalid UTF-8, and CR bytes before source-provenance hashing and
records the canonical LF source closure reproduced by fresh CI checkouts.

The previous T095 acceptance remains valid only for review commit
`16c6c627dfc9cd2211993580019f43d084dc718d`, implementation/evidence ancestor
`2f7151b25022d7e380d3b09e662f6debe9d787f3`, and manifest digest
`sha256:60b63f41a220c95df0fb87abcb7bbca94f17f97da8c361350d1115539110e557`.

The independent audit of prior pushed HEAD
`4d15000c7d45062d9376c3b3f2966e57fa5348ff` returned NOT READY only because
raw unknown CLI tokens could enter parse-error prose and one review sentence
retained the obsolete 89-test count. That previously accepted candidate removes those raw
tokens, adds black-box opaque-token proof for command, positional, and option
paths, corrects the count, and reruns the full gate. A subsequent independent
read-only audit returned READY against the exact accepted review commit and
manifest digest; that verdict established readiness but did not itself infer
acceptance.

The rejected baseline remains recorded in
[`reviews/task-closure-audit.md`](reviews/task-closure-audit.md). The later T096
audit identified 27 proof gaps without erasing that history. T097-T106 closed
those gaps. The human then explicitly
authorized the current `80 satisfied, 5 superseded, 0 missing` ledger treatment;
that authorization concerns evidence accounting only. Product acceptance for
the prior exact binding was recorded separately under T095 after the final
readiness verdict and is now reopened only for the corrected merge candidate.

## Passing repository gate

The repository-owned command passed against the exact implementation/evidence
candidate:

```powershell
./eng/Invoke-VerticalSliceQuickstart.ps1
```

It performed dependency-mirror bootstrap, locked restore, Release build,
deterministic distribution-evidence regeneration and stale checking, all tests,
formatting verification, and Git whitespace verification.

- build: 0 warnings, 0 errors;
- unit: 25 passed;
- contract: 35 passed;
- acceptance: 31 passed;
- total: 91 passed, 0 failed, 0 skipped;
- distribution evidence regeneration/stale check: passed;
- formatting and `git diff --check`: passed;
- implementation/evidence worktree after commit: clean and pushed.

The acceptance and contract evidence includes:

- exact request/closure/effect/freshness/review/revocation authority;
- strict public schema and three-role provider admission;
- candidate collision, receipt-last admission, and every publication-boundary
  recovery path;
- read-only drift detection and fresh-authority repair;
- typed safe values, finite waivers, safe restricted-YAML source spans, and
  canonical snapshot orientation/freshness proof;
- black-box CLI grammar, canonical explanations, executable invalid inputs, and
  result-derived stream/exit behavior;
- all 26 public diagnostic identities with schema-valid catalog projections and
  production references, including the six formerly untriggered boundaries;
- typed disposition, expected/observed values, non-empty evidence, executable
  remediation payloads, continuation grouping, adversarial disclosure/fallback,
  and opaque CLI parse-token behavior;
- nine executable SC-005 fixtures covering duplicate route, missing assembler,
  ambiguous order, unsafe disclosure, generated drift, live collision, stale
  precondition, interrupted publication, and provider failure;
- content-bound, schema-valid kernel and .NET diagnostic catalogs plus exact
  provider-manifest conformance-evidence bindings;
- dependency-mirror tamper refusal plus exact package SHA-256 and NuGet content
  hash verification;
- Unicode-path, culture, JSON/YAML, and ordering repeatability with direct
  canonical-byte comparison; and
- clean relocated locked restore/build/test/publish, assets/deps/PE allowlists,
  process startup, and `/status` without authoring state or Program Kit runtime.

The evidence generator and dependency bootstrap use isolated tool homes and do
not consult machine-local user NuGet configuration. CI regenerates the bounded
evidence set on Windows and Ubuntu and uploads only that set for 14 days.

## Previous human product decision

On 2026-08-01, `joey-orbyss`, acting as product owner and requirements author,
reviewed commit `16c6c627dfc9cd2211993580019f43d084dc718d`, bound to
distribution-manifest digest
`sha256:60b63f41a220c95df0fb87abcb7bbca94f17f97da8c361350d1115539110e557`,
and explicitly decided **ACCEPT**. The reviewer disclosed participation in
defining the requirements and accepted the limitations documented in
`reviews/first-vertical-slice.md`.

This decision accepts the bounded .NET 10 + CShells 0.0.28 `explain`,
`construct`, and `evaluate` product foundation demonstrated by Feature 001. It
does not declare Program Kit generally released, multi-provider,
migration-ready, or complete.

## Corrected merge candidate decision

**PENDING REFRESHED T095 HUMAN REVIEW.**

The local gate passed against correction commit
`4d1c519fd5e788c36252437de03cb8c1ccb13c33` and manifest digest
`sha256:25fd0146dcca3fe8b8d359a9a208e51504718eb978b95fde60570a33cd8ecebd`.
Required Windows/Ubuntu CI and a fresh named-human accept/reject decision must
complete before this corrected candidate may merge.

## Deliberately not claimed

The disabled historical Program Kit self-host integration check remains outside
this redesign gate. No further Feature 001 convergence work should be added
unless an independent readiness audit maps it to an existing unmet FR, SC, or
constitutional MUST; desirable improvements belong in a later feature.
