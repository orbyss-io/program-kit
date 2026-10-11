## Application engineering principles

<!-- program-kit:story-delivery-v1 -->

### Verification selected by risk

This policy supersedes universal test-before-code examples in the core scaffold. During amendment,
replace conflicting old principles; do not append a second incompatible sequencing requirement.

New or changed application behavior MUST have automated tests traced to its user stories,
requirements and acceptance scenarios. Select sequence by changed responsibilities and uncertainty.
Materialize known scaffolds/templates coherently first, run maintained generation/configuration/
build/integration checks before dependent behavior, then add missing consumer-specific tests.
Prefer meaningful test-first checks for critical authorization, ownership, transactions, concurrency,
replay, destructive actions and recovery, and a demonstrating regression for reproducible bugs.
Straightforward wiring/presentation can be implemented and verified immediately; refactoring uses
existing behavioral regressions plus missing coverage. Labels alone never establish low risk.
Record risk, method and an alternative sequence reason briefly in plan/tasks; routine choices need
no approval or new ADR. A missing tool, compile error or unrelated environment failure is not valid red.
Reuse qualified component coverage; test the application's own policies, boundaries and integration
rather than duplicating a publisher's internal suite. Test output is ordinary execution output,
not a separate approval or proof dossier.
Run focused behavioral and affected regression checks while coding. Task batches, progress
saves and resumes are not full-suite checkpoints. Complete feature/domain closure or formal review
handoff requires complete application acceptance; publication retains its own full Release gate.

### Runnable stories and human review

Deliver small coherent actor journeys, with explicit non-goals, an independent walkthrough,
success/material failure outcomes and connected authorization, ownership, persistence and recovery.
UI stories include their UI/backend/effects; backend products use their supported interface.
Internal operations do not each require human review. Put enabling work beside its first consumer.
Estimate preparation, integration and verification to human-reviewable behavior; reconsider oversized
stories before task generation, or disclose effort and rationale for a larger coherent story.
After exercising a story and passing relevant checks, present its actual runnable entry point,
prepared account/data, walkthrough, expected results, limitations and any simulated externals.
Persist separate engineering and human dispositions in the compact tasks checkpoint.
Required story reviews pause further product work by default. Earlier checkpoints require explicit
human agreement. Only explicit acceptance or scoped deferral permits the corresponding progression;
repairs/diagnosis of the presented outcome remain allowed. All required deferred reviews remain due
before feature acceptance. Silence, time, screenshots and agent tests never grant acceptance.
Material changes reopen only affected reviews; unrelated commits/tests do not reset acceptance.
The requesting human defaults to owner/reviewer. The owner controls scope, reassignment, broader
deferrals and budgets; assigned reviewers decide their checkpoints. Delegation grants no spending
or publication authority. Optional GitHub bindings require account verification and human assignment
confirmation; explicitly supplied decisions require authenticated author and exact checkpoint scope.
Unavailable/ambiguous decisions stay pending; established decisions survive outages.

### Advisory active effort

Default drift thresholds are 60 active minutes per operation and 120 per story. Include preparation,
planning, builds, integration, tests and repairs; exclude explicit human waiting. Preserve cumulative
elapsed effort on save, interruption, resume and reassignment; never sum parallel command durations.
Warn once at crossing, reporting what works/remains, cause and smallest corrective action. Update
when diagnosis/scope materially changes. Time alone never blocks implementation. Only the owner can
explicitly revise the declared budget. Real technical/authority/review gates remain binding.

### Adoption

Existing unfinished features require archived abandonment, an amended and normally ratified
constitution and fresh specify, clarification, plan, tasks, analysis and implement. Old partial code,
tests and checkmarks grant no new progress. Preserve unchanged confirmed intent/bootstrap,
architecture, installed foundations/tooling, consumer locks and delivered features. Review an owned
reset inventory before any real reset; feature reset grants no unrelated source or live-data deletion.

### Architecture and implementation quality

Preserve accepted domain ownership and dependency directions. Apply coding guidance only when
its conditions hold; use native analyzers, architecture checks, contract/security tests and code
review to verify the resulting implementation. Keep detailed conditional examples in referenced
guidance, not repeated constitutional inventories.

### Independent engineering

Restore, build, test, contract generation, packaging and deployment MUST remain runnable by humans
from documented engineering commands without AI, toolkit extensions or governance history.
