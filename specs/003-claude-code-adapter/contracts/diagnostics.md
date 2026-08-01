# Diagnostic Contract: Claude Code Session Adapter

## Catalog identity

`orbyss.program-kit:diagnostic-catalog:session-claude-code@1.0.0`

Authority-qualified IDs use namespace `program-kit.session.claude-code` and
code prefix `PKCLD`. Feature 002 neutral and kernel diagnostics remain
authoritative for shared request, identity, authority, collision, publication,
drift, disclosure, and removal triggers.

| ID | Permanent trigger | Category / severity | Primary disposition | Required safe next action |
|---|---|---|---|---|
| `program-kit.session.claude-code/PKCLD0001` | Observed Claude Code version is missing or differs from the exact selected supported provider identity | compatibility / error | `select-compatible` | Install/select the exact supported provider release or select another exact adapter |
| `program-kit.session.claude-code/PKCLD0002` | Project-skill projection cannot be represented or validated under the declared Claude surface without semantic loss | conformance / error | `stop` | Correct the adapter projection or declare the surface incompatible |
| `program-kit.session.claude-code/PKCLD0003` | Exact skill bytes are installed but workspace trust or project-skill discovery is not established in the observed session | availability / warning | `retry` | Review/trust the workspace as a human and start or reload an exact supported session |
| `program-kit.session.claude-code/PKCLD0004` | Claude invocation changes executable, working scope, argument boundaries, structured stdout, exit meaning, or required result fields | transport / error | `stop` | Correct the provider binding and rerun conformance before installation/support |
| `program-kit.session.claude-code/PKCLD0005` | Provider permission prevents the exact CLI invocation from starting | authority / error | `request-approval` | Let the human grant bounded Claude Code process permission; do not treat it as Program Kit effect authority |
| `program-kit.session.claude-code/PKCLD0006` | Live Claude review is missing, interrupted, incomplete, contradictory, or uses a different provider identity | evidence / warning | `review` | Rerun the bounded review on the exact isolated profile or leave the claim not evaluated |
| `program-kit.session.claude-code/PKCLD0007` | Provider-reported success conflicts with Program Kit results, receipts, or observed filesystem effects | evidence / error | `stop` | Trust Program Kit and independent effect evidence; fail the provider trial |
| `program-kit.session.claude-code/PKCLD0008` | Isolated-machine boundary contains Program Kit source, Spec Kit, Codex adapter state, or prior Program Kit session state | provenance / error | `recreate-environment` | Recreate and revalidate a clean external consumer environment |

## Result rules

Every entry MUST populate the existing diagnostic fields with:

- the exact provider, adapter, surface, projection, invocation, trial, or
  environment subject;
- violated contract or support expectation;
- bounded cause and consequence;
- safe normalized expected/observed values;
- actual effect state;
- the table's primary disposition;
- a non-executable remediation class; and
- safe evidence references.

Rendered text is not authoritative. Raw provider stdout/stderr, credentials,
account identifiers, transcripts, prompts, model reasoning, exception strings,
and physical protected paths MUST NOT be included.

## Reuse rules

- Existing skill path: neutral/kernel collision diagnostic, not a new PKCLD ID.
- Altered admitted skill bytes: neutral drift diagnostic.
- Missing or mismatched Program Kit grant: kernel authority diagnostic.
- Unsupported Claude release: `PKCLD0001`.
- Intact installation not loaded in current Claude session: `PKCLD0003`.
- Claude changes the CLI transport meaning: `PKCLD0004`.
- Claude says success while Program Kit blocked: `PKCLD0007`.

Provider prose, model names, and documentation wording are never diagnostic
identity inputs.
