# Bootstrap stage contracts: implementation and validation

The approved redesign is implemented on `codex/repository-sync-coordinator`, within the existing
unpublished 0.12.0 candidate. It changes executable handoffs and their existing instructions.
The earlier consumer runs remain historical evidence; they have not been resumed or rewritten.

## Behavior

| Responsibility | Implemented behavior | Source authority |
| --- | --- | --- |
| Default selection | Missing application selections resolve to .NET/Foundation; managed browser authentication closes its .NET dependency. Missing browser security selects BFF, missing local identity selects the shipped Keycloak adapter. Explicit anonymous and consumer-provider choices survive. | `bootstrap_defaults.py`, existing `default-adoption.md` and secure-web profile |
| Persistence | A declared server-relational .NET data owner with absent/auto provider resolves to EF/PostgreSQL through the same resolver used by feature setup and upgrade. Admission remains later evidence, not implied by selection. | `persistence_selection.resolve_profile` |
| Stage ownership | Brief inputs/outputs, responsibilities, later work and recovery starts share one executable stage registry. A closure brief replaces the former unbounded closure dispatch. | `bootstrap_stages.py`, `bootstrap_context.py` |
| Scope | Assessment selects source journey IDs, a useful first outcome and rationale. Later briefs separate the future portfolio. Before final acceptance, one Ready roadmap entry must cover that exact boundary without absorbing other candidate journeys. | Existing decision register and roadmap, `bootstrap_handoff.first_feature` |
| Required answers | Questions have durable identities, owners, due stages and source-bound responses. Producer-discovered questions return to a native handoff before output validation or downstream dispatch. An unanswered asynchronous question does not establish a response. | `bootstrap_handoff.py`, native run inputs/state |
| Human review | Review packets lead with the useful outcome, choices, rationale and deferral triggers. Scope/approach approval, constitution ratification and evidenced architecture acceptance retain separate authorities and descriptive prompts. Required choices are checked before provisional approval. | `governance_state.write_review`, workflow YAML |
| Proposed models | Proposed/derived records can be refined with exact before/after hashes, rationale and a Proposed/Accepted ADR. The helper derives hashes; explicit consumer choices and original evidence references remain protected. Proposal identities remain stable. | Existing canonical map plus its `refinements`, `architecture_map.py record-refinement` |
| Compatibility | Maintained .NET, browser and published-host runtime recipes use the shared package executor. Recipes consume the executable selected by sync, not a second PATH lookup. Consumer-specific risks can still use bounded custom recipes. | `managed_compatibility.py`, `bootstrap_compatibility.py` |
| Failure evidence | Failed JUnit and bounded sanitized streams survive scratch cleanup. Receipts distinguish provisioning, runtime failure, timeout and invalid results, with raw stream hashes and truncation/redaction metadata. | `compatibility_diagnostics.py`, `bootstrap_lifecycle.py` |
| Recovery | An unchanged failed recipe retries execution without paid recipe authoring. Changed execution inputs reopen affected proof evidence with archived history. Changed design/pins and already accepted scope require reopening their decision authority. | `bootstrap_proof_plan.py`, `workflow_lifecycle.py` |
| Feature handoff | The initial specification interview inherits the first entry's canonical architecture scope instead of beginning with the entire model. Existing knowledge projections, grilling and implementation/delivery gates remain the enforcement path. | `specification_intake.py`, `feature_knowledge.py` |
| Upgrade | The existing shared sync coordinator remains the authority. Bootstrap default application cannot rewrite an approved register, and upgrade does not silently apply new bootstrap defaults to existing consumer decisions. | Existing upgrade/coordinator plus shared persistence resolver |

Keycloak is the local evaluation default, not an authorization to provision production identity
hosting. The Foundation recipe runs the published image; it does not build a consumer image.
Application delivery remains a settings/Nuplane/package-feed bundle.

Native Spec Kit supports fixed-choice gates, not arbitrary answer transport. A required answer is
therefore represented by a classified recoverable shell stop in native state. The printed diagnostic
contains the exact answer-and-resume commands. Approval cannot fill an answer implicitly. Changed
answers use `workflow_lifecycle.py reopen --run-id <id> --stage research` (or their owning stage),
which preserves old evidence and invalidates the affected approval before any producer is dispatched.

## Deterministic evidence

- The bounded Development suite passed all 48 registered validators. Log:
  `artifacts/bootstrap-redesign-development-verified.log`.
- Targeted native handoff tests cover absent selections, explicit anonymous access, consumer OIDC,
  custom persistence, alternate-stack conflict, unsupported host adapter, required and deferred
  answers, late questions, changed question hashes, explicit reopening and approval invalidation,
  provisional refinement, exact first-slice scope, and sync-resolved executable use.
- Real maintained .NET and Chromium probes passed shared provisioning and execution. The complete
  compatibility validator passed seven tests. Log: `artifacts/bootstrap-redesign-managed-runtime.log`.
- Ten proof-plan tests cover success, unchanged reuse, changed recipe invalidation, preserved failed
  cases, seeded-secret redaction, missing/malformed/oversized JUnit, timeout, scope and invalid recipes.
- Targeted local upgrade validation passed planned-only and materialized consumers, preserved
  configuration and overrides, invalid states before mutation, and pending network-verification
  semantics. Log: `artifacts/bootstrap-redesign-upgrade.log`.
- Context and semantic validators passed. In the deterministic six-journey fixture, the architecture
  brief is 14,855 bytes and closure is 7,177 bytes. These are fixture byte counts, not live token savings.
- Native workflow recovery and a fresh setup-only installation are separately verified after the
  final handoff routing changes. Logs: `artifacts/bootstrap-redesign-resumption-final.log` and
  `artifacts/bootstrap-redesign-intake-verified.log`.

One Development attempt encountered a host PowerShell module-path failure; the lifecycle test passed
with the machine module path. Another correctly rejected proof evidence while its tooling source was
being edited. Neither attempt is used as passing evidence. The successful suite and subsequent
targeted routing checks are retained separately.

The host recipe's generation and diagnostic paths are tested; no real Foundation container execution
or consumer shell activation is claimed by the .NET/Chromium checks. A runtime smoke check cannot
close identity, persistence, shell activation or product behavior obligations. Those need their
own applicable inherited or executed evidence.

## Next live exercise

Use the existing household-shopping vision-only fixture. Supply no private acceptance folder or
predefined architecture. In a normal foreground PowerShell terminal at the candidate repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-IntakeSession.ps1 -KeepWorkspace -IdeaFile tests\live\scenarios\household-shopping\v1\PROJECT_REQUEST.md
```

This starts the interactive intake only. After intake confirmation, use its printed command in the
new disposable consumer to start bootstrap. After native completion, run the selected first entry's
full Spec Kit flow. The next live run measures token use, avoidable exploration/retries and useful
time alongside the quality of the roadmap and delivered journey. No live quality or efficiency
improvement is claimed before those observations exist.
