## Architecture and engineering

Describe the vertical outcome, semantic owner, public contracts, important failure paths and real
dependency boundaries. Link relevant ADRs/domain/C4 views when useful. Preserve existing accepted
choices and explain substantive changes. A small plan or legitimate custom stack needs no toolkit
receipt, roadmap status, fixed table format or consumer qualification ceremony.

Choose concrete tests and verification commands at the cheapest reliable level: compiler/analyzers,
architecture, behavior, security and integration where applicable. Name actual prerequisites for
the task that needs them. Run providers, databases and application startup only when selected work
needs those capabilities; planning and independent code work do not require whole-app readiness.

Use qualified examples or optional generators when suitable, or document a local/manual alternative.
Check the actual selected SDK/API/package contracts. For a chosen .NET adapter, use its architecture,
dependency and native verification helpers on their own terms; do not copy their manifests into an
unrelated technology. Keep source generation, runtime compatibility and product acceptance distinct.

Use selected framework mechanisms and supported extensions before adding equivalent infrastructure.
For a new project, runner, wrapper or lifecycle, explain its actual responsibility and any concrete
capability gap in the selected framework. Correct unjustified replacement proposals during review.
For EF persistence, plan native migrations/snapshots/history and EF-produced deployment artifacts;
separate deployment credentials and read-only startup admission do not require a custom engine.

Agree useful runnable review points and the reviewer. Record the expected walkthrough and any
explicitly permitted work while awaiting review in normal plan/tasks notes. Pause dependent work
for those reviews; engineering success does not provide human acceptance.
