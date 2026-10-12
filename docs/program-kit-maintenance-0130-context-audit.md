# Maintenance audit against published Program Kit 0.13.0

The maintenance work started incorrectly on the released 0.12.11 branch at
`834a9f2`. Its local checkpoint was rebased onto published 0.13.0 at
`60e875799e1aa7ae408ca5b660fcd278d9f6abea`, producing maintenance checkpoint
`27139eb2aa7cc0b1f7bc2189c10deea801dc401d`. No maintenance changes have been pushed
or published. After the requester challenged the baseline mistake, further
implementation was paused for this audit. A conflict-free rebase alone was not
treated as evidence of semantic compatibility.

## Complete release comparison

`artifacts/maintenance-2026-10-12/0130-context-audit.json` records the comparison
for every maintenance file and all 57 files changed between the published
baselines. `0130-upstream.patch` and `0130-maintenance.patch` preserve both full
diffs. The audit script is read-only with respect to Git and the consumer.

Closure evidence is in `0130-context-audit-closure.json` and
`0130-audit-closure-evidence.json`. The latter validates every journal command and
log hash and binds the 512-entry local archive SHA-256
`26b95ffb8c279a7881e7fa53e5e4d2c9fa8e4c42c375c3b22dc09add77e3b403`.

There are three overlapping files:

| File | 0.13.0 change | Maintenance assessment |
| --- | --- | --- |
| `extensions/program-kit-governance/references/phase-evidence.md` | Story review, fresh-feature adoption, verification by risk, clocks and progression | New runtime/isolation paragraphs are additive. All new story/review/adoption sections remain intact. |
| `tests/validate_normal_development.py` | Seed fresh fictional delivery state; exercise new progression rules | Additional binding/negation cases retain the new imports, fixture initialization and existing tests. |
| `tests/validate_dependency_audit.py` | Recognize new task-generation state in audit fixtures | Two historical-proof tests are additive; the 0.13.0 fixture adjustment remains intact. |

The other 54 files changed by 0.13.0 are unchanged by the maintenance patch at
this audit boundary. This includes version/catalog metadata, migration recipes,
release guidance/build inputs, validation inventory, commands, templates,
constitution guidance and the story state machine. No 0.13.0 change was replaced
by an archived 0.12.11 source copy.

## Repair-by-repair assessment

Every repaired production path already present at 0.12.11 has identical Git bytes
at the published 0.13.0 baseline. Consequently, the original before-failure
reproductions apply to unchanged implementations in 0.13.0. This byte comparison
does not replace behavioral checks of their newer callers; those are recorded
below.

| Maintenance scope | Changed production paths | Interaction with 0.13.0 |
| --- | --- | --- |
| Toolkit version and deferred persistence | `building_blocks.py`, `persistence_selection.py` | Toolkit manifests now supply 0.13.0 provenance; consumer VERSION remains product-owned. Structured unmaterialized intent remains deferred; installed/materialized owner guards still apply. No dependency/default selection is advanced. |
| Historical proof readers and repaired updater | `dependency_audit.py`, `scripts/upgrade_program_kit.py` | Exact archived executed bytes establish historical readability only. Current prerequisite/tooling hashes remain required. Explicit repaired-candidate continuation retains migration origin, original archives, incomplete attempts and required migration review; it does not grant fresh-feature continuation or human acceptance. |
| Feature context | `feature_context.py` | Binding lists and explicit negation preserve relevant inherited requirements. They do not remove the new story-delivery requirement or bypass `task_draft.guard`. Neighbor owners remain excluded. |
| Verification runtime and provider isolation | `Invoke-RepositoryVerification.ps1`, `repository_verification.py` | Real child-process verification stays independent from human story acceptance, as 0.13.0 requires. All maintained dispatch routes honor required consumer isolation. No consumer-specific credential vocabulary is imposed globally. |
| Identity projections and setup mapping | `identity_fixture.py`, `dotnet_sync.py`, `foundation_composition.py`, both raw web descriptors | Projection comes from exact maintained compose authority. Sync retains consumer ownership/conflict rules. Setup mappings select actual declared tests, fail without coverage and claim no application or human acceptance. |
| Lock renewal | `restore_dependencies.py` | Complete literal reverse-dependent closure is previewed/restored. Accepted pins and unrelated locks stay unchanged. Dynamic/unproved graphs fail for an evaluated adapter; no full-suite or zero-test success fallback is added. |
| Fixture preparation and pickup | `fixture_readiness.py`, `bootstrap_compatibility.py`, `bootstrap_lifecycle.py`, `managed_provider_probes.py`, `runtime_fixture.py` | Preparation happens before dependent behavior, matching 0.13.0 scaffold-first guidance. Current fixtures use accepted authority; archives retain original inputs. Materialization establishes a draft, not a proof or spending authority. Current producer hashes include the preparation helper; frozen historical shapes remain historical only. |
| Explicit installed device interpreter | `eng/device_toolchain.py`, `scripts/Test-ProgramKit.ps1` | Explicit absolute shared Python selection is validated against the same existing device policy. It grants no installer, sandbox bypass, workflow interpreter override or Release authorization. Invalid selections fail without fallback. |

The clean audit closed on 2026-10-12 with all **88 Development checks passing**
and real packaged installation/upgrade/fresh-story adoption passing. No contradiction
with the newer release rules was found within this reviewed maintenance scope.
This establishes the development checkpoint; complete Release/publication
qualification remains a later gate. Future steps 7–9 receive their own review and
validation rather than being covered by this earlier checkpoint.

The audit also reviewed the newer indirect call paths: implementation preflight,
`phase_obligations.check/finish`, operation start/review/freshness/clock transitions,
fresh-story reset/adoption, canonical migration guidance and package composition.
The current consumer already has fresh 0.13.0 specification/task policy and ratified
constitution 2.0.0; maintenance must preserve that state. It must not apply another
reset or treat abandoned partial work as current progress.

## Defects caught during the audit

1. The maintenance identity projection introduced an eager sibling-module import
   into `foundation_composition.py`. The existing setup-only file-loader path
   reproduced `ModuleNotFoundError: identity_fixture`. The import now occurs in
   materialization, consistent with the existing local identity-validation path.
   All 26 foundation-setup tests pass after repair.
2. The new positive Foundation/CShells pickup fixture initially lacked its explicit
   bootstrap/toolchain setup. Those test inputs were corrected; product checks were
   not disabled.
3. The positive pickup then exposed a pre-existing byte-format check: semantically
   current XML without the renderer's declaration was rejected as stale pins.
   Preparation now compares parsed XML semantics, including package versions and
   restore policy. Exact source hashes still bind proofs and archive original bytes.
   All 13 effective-context tests pass, including wrong/mixed authority rejection,
   Foundation/shared ABI/Semantic Kernel renewal and original-input preservation.
4. One missing-Python fixture inherited the newly supported explicit device selector;
   it now explicitly clears that selector when simulating an absent interpreter.
   Its original strict diagnostic assertion remains. A provider-recipe fixture now
   copies the new maintained readiness helper into its disposable installation.
   These are fixture preparation corrections, not weaker production gates.
5. Actual packaging rejected 513 bundle files against Spec Kit's unchanged 512-file
   limit. Readiness and explicit fixture pickup now share `fixture_readiness.py`.
   The unused separate pickup module was removed. The resulting 512-file package
   builds successfully without dropping historical captures or raising the limit.
   Real packaged installation, sequential upgrade, destination activation and
   0.13.0 fresh-story reset pass; all resets/human decisions were fictional.

Failed logs remain preserved. Later successful checks do not rewrite them.

## Behavioral evidence

- Six affected validators rerun on published 0.13.0 passed: normal development
  (28), upgrade boundaries (23), dependency audit (12), real verification-hook
  routes, scoped verification (44) and bootstrap runtime bindings (67 groups).
  Logs: `on-0130-user-temp-*.log` under the maintenance artifact directory.
- Exact public Foundation 0.3.2 Host and BFF/Keycloak disposable native runtime
  checks passed. Evidence: `artifacts/consumer-provider-runtime/480068d5/` and
  `step6-provider-runtime-current.log`. This is separate from the unpublished
  private-page candidate owned by the Foundation chat.
- The clean bounded Development suite passed all 88 checks with Chromium/WebKit.
  Journal: `artifacts/validation-runs/20261012T173945Z-2b11fdd0/journal.json`.
  Log: `0130-context-development-after.log`. The initial four-failure run remains
  preserved at `artifacts/validation-runs/20261012T172733Z-01b793a2/`.
- Targeted audit-repair logs: `0130-setup-import-repair.log`,
  `0130-effective-context-semantic-after.log`, `0130-shell-environment-after.log`,
  and `0130-provider-support-after.log`.
- Real package checks: `0130-context-package-build-after.log` and
  `0130-context-package-upgrade.log`. The local maintenance archive is distinct
  from publicly released 0.13.0 and establishes no publication qualification.

No complete Release suite, paid worker, model/OCR provider call, deployment or
publication was performed. Firefox remains in CI; its known local Windows launch
limitation does not authorize changing production behavior.

## Concurrent consumer activity and preservation

At 17:29 UTC the original 1,521-file snapshot comparison found 1,520 unchanged files
and a changed `specs/002-policy-backed-veterinary/tasks.md`. The original snapshot
and its old hash remain unchanged. The changed hash is recorded separately, not
rebaselined into a false preservation pass.

Read-only inspection of “Implement RM-01 Veterinary Asses”
(`01a12c5a-01f8-7562-9475-f3f0d5a0abc5`) establishes a concurrent user-authorized
consumer repair turn. It executed delivery resume and preflight/finish transitions
at that time, which write the compact task state. This maintenance chat did not
execute any consumer command or write there. The separate chat owns any further
consumer changes; maintenance will observe and report them without undoing them.

All compared receipts, historical archives, native locks, pins, architecture and
managed state matched the original maintenance snapshot at that boundary.
Subsequent consumer work must be disclosed in the final comparison rather than
misattributed to this maintenance patch.

The closure comparison records six changed original files and 1,515 unchanged
files. The separate consumer chat has now completed its authorized manual repair:
it changed tasks/plan/quickstart and two maintenance feedback documents, and
archived/retired `runtime/claim-evaluator/settings.json` in favor of its own new
shell JSON. The chat's exact file-change records and delivery transitions account
for those six differences. Pins, locks, receipts, archives, architecture and managed
state still match the original snapshot. This is disclosed concurrent work, not
an all-files preservation claim; no originals were restored over the user's repair.

## Requirements for remaining maintenance work

Steps 7–9 must retain the 0.13.0 human progression/closure checks, stable IDs,
advisory 60/120-minute thresholds, cumulative effort and once-per-invocation hooks.
A repaired technical prerequisite permits a fresh preflight evaluation; it grants
no human decision or clock reset. Prerequisite receipt invalidation and human
story-review freshness remain distinct authorities.

Foundation private-page guidance must use demonstrated exact captured candidate
or released artifacts. It cannot silently advance the qualified default or any
consumer pin. Public release/default qualification, dependency maintenance and
user-owned full Release validation remain future publication gates.
