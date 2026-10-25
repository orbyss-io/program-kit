# Engineering guidance and review

## Immediate phase actions

<!-- program-kit:knowledge-rule phase-action.planning -->
Describe the intended outcome, consequential design decisions and cheapest reliable tests. Planning runs no application checks.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule phase-action.after-plan -->
Review ownership, contracts, dependencies and material failure paths. Carry applicable checks and agreed review points into tasks.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule phase-action.tasks -->
Group runnable outcomes and their exact prerequisites. Choose verification sequence by risk; draft tasks without starting services or executing proofs.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule phase-action.after-tasks -->
Use native read-only analysis on the completed task plan. Check coverage, real dependencies, relevant tests and agreed human reviews.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule phase-action.implementation -->
Implement coherent outcomes with focused checks. Honor agreed human review pauses; progress saves and resumes are not full acceptance boundaries.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule phase-action.delivery -->
Run complete applicable acceptance at feature closure, review substantive findings and obtain the agreed human dispositions. Report actual execution separately from acceptance.
<!-- /program-kit:knowledge-rule -->

## Knowledge and engineering checks

Use the compact phase reference index and focused `--only <id>` lookup. Attribution names the
source; it does not certify a consumer decision or implementation. Local constitution, ADRs and
plan/tasks preserve project choices. A suitable custom stack or pattern needs its actual contracts
and tests, not qualification in Program Kit's curated catalog.

Use normal compiler, analyzer, architecture, security and behavior checks for selected work. For a
chosen .NET route, optional `eng/Invoke-RepositoryVerification.ps1 -Scope Focused` and `-Scope Affected`
retain their real scope, prerequisites and failure behavior. Document actual project/filter/commands;
a bare wrapper cannot establish coverage. The native commands remain runnable without extensions
or governance history. Do not replace supported framework, SDK or dependency contracts with prose.

Start a runtime, provider, database or browser only when the selected action needs it. Preserve
failed outputs and uncertain outcomes; an old result cannot hide changed inputs or a newer failure.
Run complete applicable acceptance at feature closure or an explicitly requested formal handoff.
A task batch, progress request or resume calls only the checks invalidated by changed work.

## Story delivery and human review

Agree useful runnable outcomes and review points in the constitution or ordinary plan/tasks. Keep
one readable progress note with remaining work, unresolved failures, actual checks and human review
dispositions. The format is the consumer's choice. No hidden checkpoint, timing ledger, review hash,
external identity binding or initialized delivery state is required.

At each agreed pause, present the real entry point, prepared account/data, walkthrough, expected
results, limitations and simulated externals. Pause dependent product work until the human accepts
or explicitly defers the named review with a bounded scope. Diagnosis and repair of the presented
outcome remain available. Earlier or additional pauses need agreement. Required deferred reviews
remain due before feature acceptance. Silence, elapsed time, checkmarks and agent tests do not grant
human acceptance. Preserve the actual disposition; substantive changed meaning reopens affected
choices while unrelated commits or representation changes do not reset it.

Engineering results, semantic review and human acceptance are distinct. Keep concrete ownership,
authorization, security, storage/migration and provider prerequisites beside the task that needs them.
The optional examples/generators retain their own input checks; unsupported automation permits an
honest manual alternative. Never use progress notes to waive real tool, API or product constraints.

## Reusable foundation proof and operation prerequisites

Existing relevant component checks can be reused only while their source, generated/configuration,
selected dependency/toolchain and environment inputs remain applicable. Application policies,
ownership, transactions and recovery still need consumer tests. Prefer real selected operation checks
over starting every service before coding. Package qualification belongs to maintainers of optional
automation; choosing a different consumer implementation is not a qualification ceremony.
