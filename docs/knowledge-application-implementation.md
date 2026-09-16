# Integrated knowledge application and repository sync

Candidate: 0.12.0 on `codex/repository-sync-coordinator`. This document records
implementation and deterministic evidence; it is not live acceptance or a
publication decision.

Latest live disposition: **learning only; excluded from acceptance**. Run `cd738af9`
still records `failed` at `validate-architecture-output`. The standalone architecture
retry completed (5 structural and 7 final checks), but did not resume the workflow.
Three founding ADRs remained Proposed and PostgreSQL compatibility/recovery was unproved.
No full bootstrap or first-slice pass is established. The user closed the session.

The closing intake validator reported an evolved architecture-map hash against the
original confirmed intake. That is downstream artifact drift, not retrospective
proof of an invalid interview. The launcher now reports observed workflow state
separately and no longer says no workflow ran merely because it did not launch one.
Original evidence is unchanged in `artifacts/intake-sessions/23b4668918894060b003bd0c59002dc0/`;
`artifacts/bootstrap-trial-cd738af9-review/review.json` binds its hashes and disposition.
Its `usage.json` retains observed cumulative counters for five sessions: 6,200,468
input tokens (5,720,960 cached, a subset) and 72,375 output tokens. Unreported tails
remain unknown. The user-supplied CLI summary is a different accounting view and is
retained separately, never added to those totals or treated as measured monetary cost.

Lessons: the stage brief was read twice after truncated output; broad schema/map
reads and repeated structural repairs are reviewable avoidable-work candidates.
Six final artifacts exceeded advisory generation targets while meeting hard limits.
That alone is not waste: architectural evidence must be assessed against its purpose.
The most serious defect was enforcing the wrong release architecture: prior source
replaced bundle production with consumer image production, and our placement repair
reinforced it. Passing schema/structure checks did not establish product correctness.

The existing runtime reference now owns the release-bundle contract. Bootstrap context
projects that exact section with a source hash; placement binds hostsettings.json to
the published Foundation image, and feature delivery obligations require bundle/runtime
proof. Packaging includes separate Nuplane settings and projects them into hostsettings
for the existing published host. Managed consumer image files are retired with conflict
protection, runtime configuration is preserved on upgrade, and acceptance uses a
container from the published image rather than a consumer-produced host DLL.

Correction validation: `artifacts/bundle-development-complete.log` records the bounded
Development pass. The final source-configuration freshness addition is covered by
`artifacts/bundle-contract.log` (12 bundle tests), `artifacts/bundle-pins-final.log`
and the generated-schema validator. Additional targeted evidence is
`artifacts/bundle-placement.log`, `artifacts/bundle-scaffold-final.log`,
`artifacts/bundle-upgrade-final.log`, `artifacts/bundle-lifecycle-final.log` and
`artifacts/bundle-handoff.log`. The runtime default now includes validated consumer
packages instead of restricting Nuplane discovery to Orbyss.*. The maintained tests
reject the previous image-build requirement. These are deterministic contracts,
not a claim that a newly generated consumer has passed runtime acceptance.

The Docker daemon was unavailable during preparation; the new trial must pass
`docker info` before starting any model session. No Foundation runtime source or
registry image was changed, and no paid session or publication was performed.

The exact intake setup smoke test also exposed intermittent Windows loopback archive
resets, which the component-by-component packaged installer does not exercise. Archive
bytes verified against source. Intake catalogs now bind each ZIP's SHA-256, and only
a native bundle download failure explicitly reporting rollback may retry, at most
three attempts with every diagnostic retained. Other failures and model sessions never
use that retry. The guarded PrepareOnly run completed all eight installation steps;
the original failures remain in `artifacts/intake-sessions/`.

The
[placement and recovery report](lending-bootstrap-placement-recovery.md) records
the earlier diagnosis and recovery procedure. Its Dockerfile/DLL advice is superseded;
do not resume this discarded trial or apply that architectural guidance. Historical pre-trial statements below describe the
initial candidate preparation, not the later native workflow outcome.

## Accepted design and implemented behavior

Applicable knowledge reaches each producer through compact phase context and
explicit obligations with due phases. Missing output cannot disable an obligation.
Planning records design and future checks; delivery requires actual named executed
checks, source-bound evidence and attributable review. Schemas enforce contracts;
they do not prove business semantics by themselves. Weakening an accepted applicable
rule requires scoped owner approval. Routine applicability follows established rules.

| Area | Implementation and evidence |
| --- | --- |
| Native workflow | Main's v0.11 native run/resume and recovery integrated with 0.12 migrations. One-use candidate/phase/checkpoint bindings and Windows process containment retained. Workflow/resumption and live-candidate guard validators pass. |
| Knowledge application | `phase_obligations.py`, normative inventory, phase-context hooks, semantic/verification/review schemas and current delivery gates. Targeted phase, knowledge, feature and schema validators cover missing, stale, deferred and fabricated evidence. |
| Bootstrap | Compact intent projection, bounded feasibility/proof plans and supervisor-owned dependency provisioning. Actual named runtime cases are required; package availability alone cannot establish compatibility. Selection is checked read-only after native approval. |
| Domain and modularity | Explicit semantic design, policy/effect/transition/identity obligations, evaluated and compiled .NET graph checks, named runtime registration and replacement evidence. Targeted architecture and capability validators pass. Semantic review remains necessary. |
| Components | Catalog uses Foundation/Forms 0.2.0 and Localization 0.1.1. Immutable Forms production and supported rendering are separate from optional deployed management. Adoption distinguishes selection, materialization, activation and exercise. Real released .NET/npm integration probes pass. |
| Repository sync and upgrade | Shared dependency executor for applicable .NET/npm/tool targets and feature/upgrade paths. No public dotnet-sync compatibility alias. Consumer edits are preserved; managed setup coherence and application remediation are separate outcomes. Offline/local upgrade checks pass. |
| Trial infrastructure | Fictional Equipment Lending Desk, real HTTP/restart and browser oracles, released-reference admission and exact phase propagation. Real intake capture preserves confirmed bytes and original provenance; no prepared approval is substituted. |
| Learning | Per-attempt token evidence, failed/recovery attempts, separately reported cache, attributable quality/work classifications. Actual intake rollouts use latest cumulative counters per session; unreported tail usage stays unknown. No fabricated historical numerical comparison. |

## Preserved deterministic and integration evidence

Paths below are local ignored evidence, not published release receipts.

- `artifacts/public-component-use/3f1f3199/`: actual released Foundation/Forms
  public production/replay, JSON admission, WebDefaults, Json.AspNetCore and
  HostedPages behavior. Producer project references were not substituted.
- `artifacts/published-forms-browser/2e48986d/` and
  `artifacts/published-forms-browser-current2.log`: actual private npm packages,
  strict graph, shared renewal/locked restore and Chromium/WebKit renderer checks.
  The first probe exposed root-level npm target handling; that executor defect was
  repaired and verified by the real probe plus `root-npm-restore-guard.log`.
- `artifacts/native-catalog-short-path.log`: native released v0.11 catalog/bundle
  installation passed at the supported bounded fixture path. A longer diagnostic
  path hit Windows path length constraints; its original evidence is preserved.
- `artifacts/lr/83636f51/`: hand-authored reference built from pinned released v0.11
  assets with real bundle provenance, dependency renewal/locked restore, .NET/web
  builds, HTTP/restart and browser acceptance. Supplement
  `evidence/extension-cd92f1f6/supplement.json` records rebuilt consumer assemblies
  and actual Core boundary/DI resolution and adapter replacement checks.
- `artifacts/lr/83636f51/reference-review.json`: proposed reference admission,
  **not yet admitted**. Legacy governance gaps and proposed canonical identity are
  explicit. No historical live checkpoint or human governance receipt was forged.
- `artifacts/intake-handoff-check.log`: six synthetic positive/negative handoff
  tests, including real native intake validation, exact byte preservation,
  dynamic bootstrap-to-feature binding and rejection of changed inputs/evidence.
- `artifacts/intake-lending-prepare-only.log` and
  `artifacts/intake-sessions/5bb4a55674ae494eaf7f46390afb11ec/`: actual eight-step
  intake installer and archive smoke test passed. No intake or agent was started;
  confirmed architecture was absent, as required.
- `artifacts/intake-learning-check.log`: six report tests including failed work,
  preserved cumulative intake accounting, source changes and unknown missing usage.
- `artifacts/knowledge-development-final2.log`: earlier full bounded Development
  pass. It predates the final root npm and real-intake changes and is not current
  evidence for those changes. The current rerun is recorded separately below.

## Current candidate verification

Final bounded Development rerun: `artifacts/knowledge-development-intake-final.log`.
It passed, including the final root npm, intake handoff and intake accounting
changes. Final build and packaged installation also passed:
`artifacts/knowledge-intake-candidate-build.log` and
`artifacts/knowledge-intake-candidate-install.log`. Candidate freeze and a new exact
trial receipt remain prerequisites for real intake and paid phase issuance; the
receipt is generated after the freeze and preserved outside shipped content.

## Live scope and outstanding acceptance

The next requested experiment is **actual human intake → native bootstrap → first
vertical slice**, using the intake produced by the real conversation. See
`tests/live/scenarios/knowledge-application/v2/README.md` for the staged procedure.
The tracked prepared intake is a deterministic fixture only.

The human starts `Start-IntakeSession.ps1` in a foreground terminal. Capturing its
confirmed result starts no agent. Every automated paid phase, including a rerun,
then needs its own matching unexpired one-use manifest. No new paid authorization
has been issued or consumed for this candidate, and no new live run has started.

Independent final consumer verification exists, but no newly generated live
consumer has yet exercised its full positive path. All-path or 100% correctness
claims are unsupported. The real run is intended to discover remaining integration
and knowledge-application defects while measuring tokens, quality and avoidable work.

The later upgrade exercise still needs explicit reference admission, actual human
governance review where absent, the checkpoint-bound paid upgrade/continuation and
independent final acceptance. A functionally tested reference or an inconclusive
upgrade handoff is not a completed governed upgrade trial.

Firefox cannot launch on this Windows host. Local browser evidence uses Chromium
and WebKit; CI remains authoritative for Firefox. No complete Release suite or
publication was requested or performed. The earlier investigation is preserved at
`artifacts/bootstrap-sync-reassessment-2026-09-13.md`; its findings are historical
input to this implementation, not candidate acceptance results.
