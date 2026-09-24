---
description: Coordinate approved repository setup and phase readiness across ecosystems.
scripts:
  py: scripts/repository_sync.py
---

Use this coordinator for every repository setup boundary. The .NET engineering reconciler is an
internal adapter; there is no separate public .NET sync command.

Resolve the phase from the invoking lifecycle boundary: `before_plan` means `planning`,
`after_plan` means `after-plan`. A direct invocation must identify the intended phase and current
feature. Bootstrap completion records deferred setup; it does not install application dependencies.

1. Run `{SCRIPT} plan --repository <repository> --phase <phase> --feature-dir <feature-dir>`.
   Read the generated context, exact toolchain pins, ordered operations and deferred targets. Explain
   the concrete changes. Accepted bootstrap choices authorize their managed setup; preserve adapter
   conflict checks and request new decisions only when the proposed changes exceed that authority.
2. Run `{SCRIPT} apply` with the same arguments and `--plan-digest <reviewed-plan-digest>`.
   This is offline. For interruption use `recover`, then `resume --plan-digest <saved-digest>`.
   Changed authority requires a new plan. Never edit generated receipts to make a phase ready.
3. Run `{SCRIPT} check` for the same phase. Resolve each reported blocker before continuing.

Before planning, sync establishes the accepted engineering baseline and exact SDK/Node/npm context.
Use installed `scripts/npm_metadata.py` for exact npm metadata and `scripts/npm_graph.py` for the
isolated candidate manifest. Both use `.program-kit/evidence/toolchain.json`, catalog registry routes,
credential environment references and managed CA trust, including before any application exists.
Read each helper's `--help` once for its supported arguments. Obtain authorized package access before
network operations. Missing access, trust failures, unavailable packages and incompatible graphs
have distinct diagnostics; do not probe another registry or create per-feature registry helpers.
The after-plan check requires successful graph evidence bound to the current candidate and context.

At implementation start, run `implementation_preflight.py --repository <repository> --feature-dir
<feature-dir> --stage setup`. Resolve missing planned catalog target bindings before creating files.
Create only the project or
package skeletons explicitly owned by this feature's approved plan. Then run `implementation-setup`
plan/apply/check. The coordinator materializes only compositions whose physical targets exist and
leaves future feature targets deferred. Emit `request-renew`, review its exact commands and input
digest, then use installed building-block `scripts/restore_dependencies.py renew --approved --lock
.program-kit/sync/dependencies.json --request <request-file>` with authorized network access. Repeat
for `request-locked` and `locked`. Run the full `implementation_preflight.py --repository <repository>
--feature-dir <feature-dir> --stage source` before application coding and
after dependency changes. A successful offline sync is not proof of a successful package restore.

The audit and restore inventory share exact evidence classification. Current bootstrap proof inputs
and the strict feature candidate manifest remain retained evidence, not application restore targets.
Changed evidence or active project/import/npm links to those inputs fail validation. Managed engineering
tooling requires both its installed template and exact reconciler ownership hashes; folder names never
establish ownership. A changed accepted selection requires the normal authority/proof renewal path;
never edit historical receipts to keep an obsolete design current.

Upgrade uses this same coordinator's `upgrade` phase internally, preserving existing profile choices
and future targets. Offline upgrade reports pending package verification separately. Do not bootstrap
new feature projects, renew locks or access registries as part of offline upgrade.
