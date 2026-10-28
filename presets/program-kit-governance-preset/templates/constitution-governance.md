## Application engineering principles

### Verification selected by risk

New or changed behavior needs automated tests appropriate to its user outcomes, contracts and risk.
Use test-first for critical or uncertain behavior and a demonstrating regression for reproducible
bugs. Materialize known scaffolds coherently and check them before adding dependent behavior.
Straightforward wiring can be implemented and checked immediately; refactoring uses existing
regressions and missing coverage. Record a consequential alternative briefly. A missing tool or
unrelated compilation error is not a meaningful behavioral failure.

Run compiler/analyzers, focused tests and affected regressions while coding. Reuse successful checks
only while relevant inputs/environment remain unchanged. Feature closure needs applicable complete
acceptance; progress saves and resumes need only checks invalidated by changed work.

### Runnable stories and human review

Deliver coherent actor journeys with independent walkthroughs, explicit non-goals and material
success/failure outcomes. Keep minimal enabling work with its first consumer. Agree useful human
review points and the reviewer in the plan/tasks; earlier or additional pauses need agreement.
At each agreed point, present exercised behavior, entry point, data/account, walkthrough, expected
results, limitations and simulated externals. Pause dependent work until actual acceptance or an
explicit bounded deferral. Diagnosis/repair remains available. Record the human's disposition in
readable notes. Silence, time, checked tasks and test results never supply human acceptance.
Required deferred reviews remain due before feature acceptance; substantive changes reopen affected
choices while unrelated work does not reset acceptance.

### Architecture and independent engineering

Preserve domain ownership, typed boundaries and accepted dependency directions. Apply conditional
guidance proportionally, with relevant architecture/security/behavior tests and semantic review.
Curated patterns and generators are optional; local alternatives must satisfy their actual product
and selected technology contracts. No toolkit qualification ceremony is required for that choice.

Restore, build, test, generate, package and deploy through documented native project commands that
remain usable by humans without AI, toolkit extensions or governance history. Runtime/device checks
belong to the action needing them. Never require whole-application startup before ordinary coding.
