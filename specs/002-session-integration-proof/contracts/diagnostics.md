# Diagnostic Contract: Session Integration Catalogs

## Catalog identities

- Neutral session catalog:
  `orbyss.program-kit.session:diagnostic-catalog:integration@1.0.0`
- Codex adapter catalog:
  `orbyss.program-kit.session.codex:diagnostic-catalog:provider@1.0.0`

Both extend the existing kernel catalog and use the same canonical ordering,
grouping, disclosure, evidence, and remediation rules. Existing kernel IDs are
reused only when their permanent trigger is unchanged:

- malformed or missing input: `PKREQ0001` / `PKREQ0002`;
- missing authority: `PKPOL0001`;
- path or ownership collision: `PKWSP0002`;
- interrupted publication: `PKWSP0003`;
- stale live precondition: `PKWSP0004`; and
- external command failure/unavailability: `PKEXT0001` / `PKEXT0002`.

## Neutral session entries

| ID | Category | Severity | Permanent trigger/invariant | Primary disposition |
|---|---|---|---|---|
| `program-kit.session/PKSES0001` | conformance | error | Selected package, executable digest, command name, reported version, or runtime profile does not match the exact CLI release identity | stop |
| `program-kit.session/PKSES0002` | resolution | error | The exact selected session provider, adapter, definition, or conformance profile is unavailable | provide-input |
| `program-kit.session/PKSES0003` | conformance | error | The selected provider surface cannot preserve a mandatory operation, authority, effect, result, disclosure, or working-scope boundary | revise |
| `program-kit.session/PKSES0004` | workspace | error | An admitted provider projection, definition binding, adapter binding, or CLI binding is stale or drifted | repair |
| `program-kit.session/PKSES0005` | workspace | error | Session integration publication or removal began but complete trusted live state cannot be proven | repair |
| `program-kit.session/PKSES0006` | policy | error | A consumer session lifecycle operation targets the Program Kit source-authoring repository | stop |
| `program-kit.session/PKSES0007` | external | error | The provider invocation channel failed before a valid Program Kit result could be obtained or preserved | retry |
| `program-kit.session/PKSES0008` | workspace | error | Verification or removal requires an exact installation record, but none is admitted | provide-input |
| `program-kit.session/PKSES0009` | conformance | warning | Provider-session availability has not been established by a fresh-session observation | retry |

`PKSES0004` never authorizes repair. It may include a bounded proposal for a
separate future request but must not generate a force-delete instruction.

## Codex adapter entries

| ID | Category | Severity | Permanent trigger/invariant | Primary disposition |
|---|---|---|---|---|
| `program-kit.session.codex/PKCDX0001` | conformance | error | The selected Codex version does not support or has not been evaluated against repository skill discovery required by the exact adapter profile | stop |
| `program-kit.session.codex/PKCDX0002` | conformance | error | The projected `SKILL.md` or optional `agents/openai.yaml` does not conform to the exact Codex adapter template and canonical definition binding | revise |
| `program-kit.session.codex/PKCDX0003` | external | warning | Installed Codex skill bytes are exact but current-session discovery is not proven and a fresh session is required | retry |

Codex path collisions use the kernel ownership collision diagnostic because the
permanent invariant is provider-independent.

## Result semantics

| Scenario | Outcome | Effect | Disposition |
|---|---|---|---|
| Exact installation, fresh-session state not observed | `succeeded` | `none` | `retry` |
| Unsupported provider surface | `blocked` | `none` | `revise` or `stop` according to compatibility evidence |
| Missing install/remove grant | `blocked` | `none` | `request-approval` |
| Skill path collision before publication | `blocked` | `none` | `repair` |
| Interrupted publication | `faulted` or `blocked` | `indeterminate` | `repair` |
| Drifted projection during verify | `blocked` | `none` | `repair` |
| Drifted projection during remove | `blocked` | `none` | `repair` |
| Source-authoring repository target | `blocked` | `none` | `stop` |
| Provider transport cannot preserve JSON result | `faulted` | safest proven state | `retry` or `stop` |

## AI-session remediation rules

- `provide-input` identifies exact missing selections or records; it never
  chooses a provider or version.
- `request-approval` states the exact request-core identity, operation, scope,
  and effect requiring a separate grant.
- `retry` names safe preconditions such as starting a fresh provider session;
  it never repeats an effect-bearing command blindly.
- `repair` identifies drift or partial state but does not include an executable
  delete or overwrite command in this feature.
- `revise` identifies the incompatible contract boundary and acceptable support
  envelope; it does not weaken mandatory behavior.
- `stop` is used for source-authoring refusal, unsafe disclosure, unproven CLI
  identity, or an unpreservable mandatory provider boundary.

All remediations are typed proposals. Session guidance consumes diagnostic IDs
and dispositions, never rendered prose as instructions.

## Disclosure additions

The following are always withheld from ordinary session integration results:

- full executable and provider installation paths when a repository-relative
  logical path is sufficient;
- provider configuration outside the owned projection directory;
- raw `codex` or shell process output;
- prompts, responses, transcripts, conversation IDs, account/workspace IDs,
  authentication state, and credentials;
- generated command strings suitable for direct execution; and
- secret values, secret-derived fingerprints, raw exceptions, and stack traces.

Safe evidence may record tested provider name/version, exact adapter and
definition identities, normalized operation sequence, typed outcomes,
dispositions, effects, and reviewer attestation.
