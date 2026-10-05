# Program Kit 0.12.7

New projects use the qualified profile
`foundation-0.2.4-exporter-0.2.4-forms-0.2.1-localization-0.1.2`.
It selects Foundation runtime and analyzer 0.2.4, Exporter 0.2.4,
Foundation host v0.2.4, Forms 0.2.1, and Localization 0.1.2.
The private descriptor builder remains independently pinned at 0.1.0.

This profile uses canonical publisher metadata. Generic integration fixtures
restore and pack a real consumer feature, verify publisher descriptors against
all registered activations, and export each of the 47 activation dependency
closures with the public exporter. The check also exports representative
minimal-web, SPA/Assurance, BFF/Assurance, and combined Forms/Localization
selections. A mismatched exporter version is rejected without writing output.
Public Forms consumer restore, build, and browser checks
exercise the selected package versions. All exact NuGet, npm and host-image pins
are checked against their public registries. The qualification receipt and profile
are checksum-bound assets listed in `dependency-profile-index-0.12.7.json`.
The published host fixture exercises Foundation 0.2.4's immutable image, compiled
Core boundary checks, two-shell registration/replacement, HTTP JSON/header/OpenAPI
behavior, and restart with the unchanged application bundle.

Publisher features marked `composeForOpenApi=false` are checked as metadata;
this qualification does not claim execution of their endpoints. Runtime behavior
and component acceptance remain publisher responsibilities. Consumer architecture,
compatibility proofs, application tests and Delivery acceptance remain separate
project-specific gates. Firefox remains required in tagged CI.

Existing accepted and scaffold-captured profiles retain their exact pins and
qualification entry. Installing this Program Kit patch does not adopt the new
profile or rewrite native locks, architecture choices, or historical evidence.
The v0.12.5 historical profile and the v0.12.6 exporter-only opt-in profile remain
available with their original bytes, hashes, and scope.

Run the maintained updater with `--plan` to inspect applicable migration guidance.
Install and synchronize the reviewed Program Kit version, then verify installation
coherence and retained dependency inputs. To change an existing project's
dependencies, use the separate Draft → review → Accepted dependency transition,
run the affected native restore, contract and application checks. Historical analysis stays historical.
This default change grants no authority to perform that transition automatically.

Sources older than v0.12.5 undergo actual managed-layout inspection; the source
version alone requires no approval. Unsupported layouts and conflicting application edits
remain protected. Preserve failed attempt evidence and retry the maintained updater.


This candidate also removes routine governance receipt dependencies. Applicable knowledge is
selected before plan/tasks/implementation from one upstream registry. Plans and tasks carry the
choices; normal engineering checks and code review enforce completion. Feature phase projections,
obligation reviews, semantic declarations and proof attestations are no longer required.

Engineering scripts/configuration move into visible eng/. Safe synchronization transfers known
engineering references and customized configuration transactionally; customized implementation
conflicts are preserved and reported for a real merge. Historical governance artifacts remain
unchanged. Routine upgrades do not restart bootstrap or run an architecture-writing worker.
The latest five completed owned execution runs are retained under ignored artifacts/, with failed
and interrupted diagnostics protected. Installation and migration status do not assert application
correctness or release readiness. Consumer rollout is a separate follow-up after assessment.

Constitution authoring now composes explicit test-first and independent-engineering principles
through the native Spec Kit template resolver. Existing constitutions are unchanged by installation;
substantive amendments still require their own review. Amendment validation no longer depends on
old bootstrap assessment state and preserves prior ratification during interrupted drafting.
Specification/task overlays retain native user stories and acceptance scenarios while explicitly
requesting automated behavioral tests before implementation. Clarify runs automatically after
specify; analyze runs automatically after tasks. Earlier drafting reviews do not require builds.
