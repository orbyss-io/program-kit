# Native Windows Codex bootstrap investigation

Investigated on 2026-10-02 against consumer Program Kit 0.11.0, Spec Kit 1.0.1,
Python 3.13 and Codex reporting CLI version 0.159.0. The correction is in the
current Program Kit 0.12.2 source candidate; the installed consumer was not edited.

## Why this consumer installed 0.11.0

A live GitHub API check on 2026-10-02 reports `v0.12.1` as the latest published
release (published 2026-09-25). The live main-branch README and VERSION also name
0.12.1. This local development checkout is 0.12.2; it is not yet a published release.

The `Initialize program-kit` consumer chat downloaded the explicitly versioned
`v0.11.0/Initialize-ProgramKit-0.11.0.cmd` asset on 2026-10-02. It checked the
asset's SHA-256 against that release's API record but did not verify
`releases/latest`. The consumer's saved initializer contains
`PROGRAM_KIT_REF=v0.11.0`; bundle records show installation at
`2026-10-02T09:22:22Z`, and the saved workflow also has version 0.11.0.
This is a new installation of an older release, not a downgrade or a session
automatically selecting the current development checkout.

The chat first opened the GitHub repository through web search. The same web
retrieval during this investigation returned a cached page advertising 0.11.0,
while live GitHub API reads returned the current 0.12.1 README and latest release.
Stale retrieved installation guidance is therefore the likely source of the
selection error; the preserved chat records prove the old download and lack of
a latest-release check, but do not retain its full historical web response.
Authenticity of a versioned asset does not prove release freshness.

At the follow-up check the consumer chat was idle and run 4af9317f failed with
its lifecycle inactive. The other active consumer, dezaaglijst, recorded Program
Kit 0.12.1. No session was messaged, upgraded, resumed or modified by these checks.

## Finding and observed outcome

Spec Kit's installed Codex adapter builds `[executable, "exec", prompt]` and
appends `SPECKIT_INTEGRATION_CODEX_EXTRA_ARGS`, model and optional JSON arguments.
It does not request a writable sandbox. Codex documents a read-only default for
`exec` and recommends explicit `--sandbox workspace-write` for editing automation:
[non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).

The worker records for consumer run `4af9317f` establish the following:

| Attempt | Worker session | Effective sandbox | Assessment outcome |
| --- | --- | --- | --- |
| First assessment | `01a0fd71-8beb-7ea0-90e7-86a5eb783a91` | `read-only`, approval `never` | Final message explicitly reports inability to write; process exits 0; artifact validator fails |
| Second assessment | `01a0fd89-04b2-7d52-9043-c2dd2f575004` | `read-only`, approval `never` | Same result |
| Assessment with explicit flag | `01a0fd8f-b6cd-7323-b153-27c94839ddb5` | `workspace-write`, approval `never` | All three artifacts created; worker and workflow artifact validation pass |

The third attempt finished assessment at 19:11 Europe/Amsterdam and continued
through research and assessment validation to the human assessment review gate
at 19:15. The lifecycle execution remained active while waiting for that review.
No other consumer workflow was started or resumed by this investigation, and no
review verdict was supplied.

The consumer subsequently passed its human assessment and constitution gates and
failed at `validate-architecture-output` on a separate PKB303 placement defect.
The current lifecycle execution is inactive. See
[the placement diagnosis and version-matched recovery](bootstrap-placement-4af9317f.md).
Its architecture dispatch also exited 0; that is not architecture completion.

An OS process inspection captured the assessment command actually running:

```text
<npm @openai/codex vendor binary>/codex.exe exec "$speckit-program-kit-governance-assessment C:/Users/tech_/Code/InsurancePolicyEvaluator/docs/architecture/bootstrap-intake.json; bootstrap context: .specify/workflows/runs/4af9317f/program-kit-context/assessment.json" --sandbox workspace-write
```

The executable was below
`C:/Users/tech_/AppData/Roaming/npm/node_modules/@openai/codex/`, rather than the
Desktop app binary selected by this investigation's own agent environment. The
normal-user probe also selected the npm `codex.CMD` launcher. Keeping executable
selection tied to the installed adapter avoids confusing those installations.

At inspection, the user configuration had `windows.sandbox = "elevated"`, no
top-level sandbox mode or selected profile, and a trusted entry for the consumer.
The temporary project config had already been removed. The second worker's
record proves that the temporary config did not establish workspace-write; it
does not prove which config layer that historical invocation loaded. Project
config is loaded only for trusted projects, and CLI flags have precedence over
configuration defaults: [configuration precedence](https://learn.chatgpt.com/docs/config-file/config-basic).
The durable correction therefore uses an explicit dispatch argument rather than
depending on a project config change.

The workers' `permission_profile.type = "managed"` describes a resolved permission
representation; it is not proof of an organization-enforced read-only override.
The normal-user Codex doctor control reported `managed filesystem source: none`.
The successful worker's resolved filesystem entries granted the consumer root
write access while retaining protected `.git`, `.agents`, `.codex` and `.aws`
subtrees as read-only. Its network policy remained restricted.

## Why exit code 0 did not mean artifacts existed

Spec Kit's `Integration.dispatch_command` streams stdout/stderr to the terminal
and returns only the subprocess return code with empty saved streams. Its
`CommandStep.execute` marks a dispatched command completed when that code is 0.
Codex completed an agent turn whose final message described the access blocker;
the process itself did not crash. Neither component converts that natural-language
message into an artifact contract failure.

Program Kit's subsequent `validate-assessment-output` correctly failed because
the required file was missing. That validator remains mandatory. The correction
adds a precise artifact-contract diagnostic without treating a refusal message,
transport completion or an exit code as successful artifact production.

## Separate ACL and MCP observations

The original inability of the normal user to read `bootstrap-intake.json` preceded
assessment. After the three ACLs were repaired, intake validation passed. Both
later workers explicitly had a read-only policy. Those later failures are
explained by dispatch mode and do not establish another ACL failure.

The fresh normal-user native controls also exposed a distinct ACL behavior:
workspace-write successfully created probe files, but the supervisor could not
read those newly sandbox-created files. The final probe performs write/readback
and deletion in the same sandbox identity, with a nonce-bound completion marker.
It proves sandbox access and cleanup, not supervisor readability of all possible
future artifacts. The actual consumer's successful artifact validators provide
supervisor-readability evidence for those three assessment artifacts. No blanket
ACL changes or owner grants are part of the fix.

The rmcp transport errors do not account for selection of a read-only sandbox.
Codex doctor reported optional MCP configuration issues, including an absent
`CODEX_WINDOWS_REGISTERED_CORE` variable for `node_repl`. No captured evidence
connects that warning to the sandbox selection. Codex documents that failure to
initialize a server marked `required = true` causes an error exit; optional server
problems can coexist with a running session. The original Spec Kit state did not
retain the raw rmcp stderr, so the specific transport failure is not claimed to
be repaired. It is concurrent with the demonstrated dispatch defect.

## Correction and upstream work

The supported human-owned lifecycle CLI now establishes an invocation scope for
both `run` and `resume`, before schema preparation or history mutation. It acquires
the execution lock before probing, preserves compatible model/profile/reasoning
and output options, selects exactly one workspace-write argument, and checks the
argv built by the installed adapter. It restores the caller's environment on
success or failure. It changes neither persistent Codex config nor project trust.

On native Windows it runs the selected Codex executable with built-in
`:workspace` permissions and `--include-managed-config`, executing only a Python
write/readback/cleanup probe. The probe covers the root, `docs/architecture`,
`.specify/memory` and `.specify/governance`, using the PATH Python that native
workflow shell steps use. The private uv supervisor interpreter is not assumed
to be executable by the sandbox identity. No coding agent is started by the probe.

Unsupported/conflicting dispatch arguments, adapter incompatibility and failed
native writes stop with `PROGRAM_KIT_CODEX_WORKSPACE_WRITE` before a worker starts.
New per-invocation evidence is stored under
`.specify/workflows/worker-preflights/`. Existing state, resumption snapshots,
approvals and human review gates are not rewritten by the policy setup.

This correction scopes the existing Spec Kit EXTRA_ARGS mechanism internally;
consumers do not need to set it manually. A raw `specify workflow resume` bypasses
Program Kit's lifecycle invocation scope. Use the documented lifecycle CLI for
bootstrap/resumption. The initial raw workflow preflight diagnoses the missing
explicit write selection before dispatch, but a raw resume past that preflight
still needs the upstream correction.

Spec Kit should add a per-dispatch required sandbox/capability contract, forward
it from command steps into the adapter, and map workspace-writing commands to
`codex exec --sandbox workspace-write`. Analysis-only commands can retain
read-only access. Explicit artifact postconditions should be validated separately
from process exit status, and redacted streams/actual argv should be preserved.
This would cover raw Spec Kit resumes and remove the need for Program Kit's
scoped environment bridge. Codex's documented read-only default need not change.

## Evidence and validation

Copies and SHA-256 hashes of the original consumer run records, resumption
snapshots and selected session permission metadata are preserved under
`artifacts/codex-bootstrap-4af9317f/20261002T172912Z/`. The originals remain intact.
Normal-user fresh-repository controls and redacted Codex doctor output are under
`artifacts/codex-worker-permissions/`; all failed probe-development attempts are
also retained. The first control failed at CLI parsing, the second at launching
the private uv interpreter, and the third demonstrated the mode difference but
failed cross-identity readback. Those earlier attempts are not reported as passing
write-preflight runs.

The final human-owned fresh-repository control passed and is preserved at
`artifacts/codex-worker-permissions/program-kit-worker-permissions-69m05cxs/report.json`.
Its read-only control returned 1 with Python `PermissionError` and created no file;
the workspace-write control returned 0 with verified sandbox readback and cleanup
in all four directories. Managed requirements remained enabled. The record
contains both the original adapter argv without a sandbox argument and the
corrected adapter argv with explicit workspace-write.

The controls capture real adapter argv, user/project config and trust observations,
managed-policy diagnostics, and native sandbox write behavior. They do not start a
new model-driven bootstrap or claim a new `codex exec` worker session; the actual
worker-mode evidence comes from the preserved consumer sessions above.

Regression coverage uses fixtures without coding agents: scoped environment
restoration, conflicts and adapter incompatibility, nonce-bound write/readback and
cleanup, failure despite exit code 0, both lifecycle CLI entry paths, and missing
artifact rejection. Targeted Codex/bootstrap/context/component/resumption validators
and all 57 checks in the bounded Development suite passed. The Development journal is at
`artifacts/validation-runs/20261002T175127Z-3a6e91c8/journal.json`; final diagnostic/proxy
adjustments passed supplementary targeted checks. Local validation uses the
non-Firefox engine selection; the known native Windows Firefox launch limitation
remains unchanged and CI retains Firefox acceptance authority.
