# Feature 002 Independent Product Review

- **Decision**: Rejected — not approved
- **Reviewer identity**: `joey-orbyss`
- **Decision recorded (UTC)**: `2026-08-01T13:28:07.307Z`
- **Reviewed branch commit**: `959970beb553fb0bc5dad4b8077ea9aa04cbd093`

## Decision

> Rejected—not approved. Feature 002 must not claim product acceptance until
> the authority-closure defect and resulting session-guidance failures are
> remediated and the affected live evidence is rerun.

## Evidence considered

- `deterministic-session-review.json`, normalized aggregate SHA-256
  `sha256:c253d0b4cbf1eed212b57777244713debe7f8560412495b154da5bbcecfc0171`:
  20/20 supported-platform deterministic workspace trials passed.
- `codex-session-review.json`, normalized-LF SHA-256
  `sha256:e7d6b00c53b0473e9e2a0de98bf8a2c783a50d21447d66f96ef5f5e72ea6f91d`:
  8/10 fresh Codex sessions passed every attestation; the bounded status is
  `findings-present`.
- GitHub Actions workflow run `30701577869`: the Ubuntu and Windows vertical
  slice jobs both passed at the reviewed branch state.

## Findings

1. Trial 3 did not ask for missing input within two interaction turns.
2. Trial 9 neither completed evaluation nor asked for missing input within two
   interaction turns.
3. The construct authority grant declared consumer-owned
   `requests/revocations.json` and `requests/review.json` artifacts that were
   absent, while Program Kit still admitted construction. The current
   repository authority loader does not close those declared revocation and
   provenance references.
4. Green automation establishes execution evidence only; it does not overcome
   the failed live criteria or authorize product acceptance.

## Conditions for reconsideration

1. Remediate the authority-closure defect in the first-vertical-slice work
   without masking it in Feature 002 fixtures or provider guidance.
2. Remediate the resulting session-guidance behavior so incomplete authority is
   surfaced before effects and evaluation completes consistently.
3. Re-run the full ten-consecutive-fresh-session review because SC-003 and
   SC-005 require a complete consecutive evidence set.
4. Obtain a new independent human product-review decision over the remediated
   evidence.

This rejection decides product acceptance only. It does not approve release,
publication, merge, or any deferred factory/VSL semantics.

## Remediated candidate decision

- **Decision**: Approved for Feature 002 product acceptance and feature closure
- **Reviewer identity**: `joey-orbyss`
- **Decision recorded (UTC)**: `2026-08-02T13:08:34.541Z`
- **Reviewed implementation candidate**: `16e08c89674cd6c970e33cfca20e9161746bba7f`

### Decision

> Approved for the bounded Feature 002 product scope after ten of ten fresh
> Codex sessions completed the explain, exact-grant authorization, construct,
> and evaluate journey successfully.

This decision supersedes the earlier rejection only for the remediated exact
candidate and evidence below. The rejection and its findings remain historical
provenance and are not reinterpreted as passing evidence.

### Evidence considered

- Protected GitHub Actions run `30746970810` at exact candidate
  `16e08c89674cd6c970e33cfca20e9161746bba7f`: preflight, Ubuntu, and Windows
  jobs passed. Each platform passed 46 unit, 65 contract, and 57 acceptance
  tests and ten deterministic isolated-workspace trials.
- `codex-session-review-remediated.json`, normalized-LF SHA-256
  `sha256:6d343ac32a6cc0c5af1deef581fb261adfc47d1b0f0c32a8a776c122745a69fb`:
  10/10 uniquely identified fresh Codex sessions passed every bounded
  attestation using Codex `0.137.0` and model `gpt-5.5`; status is
  `review-ready`.
- The retained live-review consumer preflight exactly matched the evidence's
  packet, seed-contract, CLI, projection, and installation-record digests. Its
  packet digest is
  `sha256:4b552e71fe3e75462d8468386b41e5f83f3c6e12c11ee00a127581100703433e`.
- The four conditions for reconsideration in the rejected decision were met:
  authority closure and recovery were repaired and protected by CI, guidance
  named the exact request-bound grant, a new ten-consecutive-session set passed,
  and this new independent decision was explicitly provided.

### Scope and limitations

The approval covers the Feature 002 provider-neutral session-integration
contract, the Codex reference adapter, its bounded human-led factory journey,
and its exact installation, verification, diagnostics, disclosure, and removal
claims. It does not approve release, publication, merge, a Claude adapter, a
Spec Kit adapter, general consumer authoring, arbitrary provider behavior, or a
claim that AI conversation is deterministic. Raw prompts, responses,
transcripts, provider output, credentials, conversation identifiers, and local
paths remain deliberately excluded from the bounded evidence.

### Invalidation set

This decision must be repeated if a change affects the reviewed CLI artifact or
release identity; canonical session definition or guidance; Codex provider,
adapter, projection, conformance profile, supported provider/model inputs;
factory request or authority closure; explain, construct, evaluate, diagnostic,
or result behavior; review scenario/protocol/schema; or any requirement behind
SC-003 or SC-005. Documentation-only closure records that preserve all reviewed
artifact identities do not invalidate the decision.
