# Consumer upgrade implementation journal

Approved requirements: [plan](consumer-upgrade-workflow-plan-2026-10-08.md).

Base: `42a14c1f34527ee922a2e2cf348ff85c1dedf303`, fetched from origin/main on
2026-10-08; VERSION 0.12.9. Branch: `codex/consumer-upgrade-workflow`.
Primary checkout's untracked `.agents` and handoff documents remain untouched.
The app-managed checkout was outside writable roots and was archived unused;
implementation uses an isolated checkout inside the ignored artifacts directory.

Work packages: reviewed cumulative semantic metadata; consumer inventory and
coordination; owned installation reproduction and activation recovery; normal hook
integration, migration pickup/discovery and evidence export; disposable consumer
and archive qualification; bounded Development validation.

Implementation choices: no new external dependency; preserve updater and dependency
transition authority; snapshots contain explicit owned assets, never arbitrary
caches or relocated proof/runtime readiness. Semantic review uses normal documents.
Scans are views and cannot prove compatibility from version age or keyword matches.
Git integration and destination installation are distinct stages. External rollout
has separate authority and cannot be undone by workspace recovery.

Delivered contracts:

- Checksum-bound cumulative consumer changes join target supersession to actual
  adoption. Maintained recipes must have applicability, behavior, scope, ordering,
  verification and recovery contracts; packaging rejects unknown methods.
- `speckit.program-kit-governance.upgrade` is registered and installed as a real
  integration skill. One coordinator links generated inventories, normal authority,
  plans/tasks and actual checks. It distinguishes findings, optional adoption,
  supported retention, conditional/deferred work and executed migrations.
- Pre-directory intake and normal phase hooks scope obligations to actual owners,
  contracts and due phases. Selective reconciliation preserves existing requirements,
  task IDs and completed work. It does not dispatch bootstrap or a coding worker.
- Discovery appends local recovery without rewriting prior findings. Demonstrated
  omissions require a local regression path and an actually executed passing check.
  Owner names alone cannot bind code verification; resolve concrete paths at pickup.
- Preparation reproduces explicit owned ignored setup, with exact originals and
  resumable provenance. Concurrent source development requires combined-candidate
  review. Destination activation runs the real updater and fresh checks, with a
  closed toolkit recovery surface that preserves application edits.
- Inspection uses native preset rendering in a disposable output directory, with
  registry writes suppressed. Core manifests predate preset replacement; exact
  native preset output is recognised without concealing manual skill edits.
- Git can change archived installation text line endings. Activation restores exact
  content-addressed bytes only after the reviewed Git blob and both copies agree
  apart from line endings. Other differences remain conflicts; recovery retains
  original destination bytes. Installation history is not fabricated or rehashed.
- Local evidence export uses an allowlist, recursive sanitization, field and total
  size bounds (64 KiB), and provenance/redaction/truncation metadata. Raw local logs
  remain unchanged; export sends nothing.

Qualification used disposable consumers only. The 20 consumer workflow scenarios
cover cumulative semantics, retained defaults and exact transition guards, selective
task repair, shared/deferred/conditional due phases, customization, pre-directory
scans, current migration pickup/checks, omission recovery/regressions, report bounds,
baseline versus introduced failures, incomplete history, root overrides, coordination
conflicts, immutable originals, installation reproduction, concurrent development,
observed interruption and conflicting consumer edits. The installed extension fixture
uses the actual public ExtensionManager; convergence injection in its interruption
test qualifies recovery mechanics, not the real updater.

The separate full archive fixture uses native first-install bundle ownership,
all real primitive installations, the real sequential updater, installed assessment
and verification, Git source integration, then destination activation. It verifies
read-only native preset inspection and detection of a manual skill edit. A required
destination check intentionally fails after a real updater run; exact ignored setup
is restored and the recovery ledger sealed. A fresh retry activates and executes
checks in the actual destination, preserving the named consumer output. Results live
in `artifacts/consumer-upgrade-install.json`; raw fixture invocations and failure
diagnostics remain in `artifacts/consumer-upgrade-package-runs/048f189a3cdf406989c5d6ecad543b5c/`.
The built full archive contains 465 files, below Spec Kit's 512-entry limit.

Targeted checks passed: consumer workflow (20), real packaged consumer activation
and recovery, existing local sequential upgrade, existing packaged release install,
release guidance (including recipe integrity), knowledge application/inventory,
specification intake and Windows shell preflight. The earlier bounded Development
run `20261008T195507Z-c6af3b7f` passed all its declared checks; subsequent review added
assessment and regression safeguards. Run `20261008T203150Z-ad25e3f3` exposed a
completion-review input mutation on a rejected review; copying that input before
validation fixed the retry and targeted scenarios passed. These preserved journals
are development evidence against the working tree, not publication receipts.

The host's machine-wide Spec Kit was 1.1.1 while current test pins require 1.1.2,
and its inherited PATH selected a Windows Python alias. Validation uses a separate
1.1.2 tool environment under this worktree's ignored
`artifacts/validation-tooling/`, with UV_TOOL_DIR, UV_TOOL_BIN_DIR and PATH scoped
only to the child validation process. No machine-wide tooling was changed. JSON
Schema runtime setup used the existing maintained exact runtime; caches are explicit
fixture preparation and never transferred as current readiness by the product adapter.

Final bounded Development evidence: `20261008T204026Z-60494b79`, all 82 declared
checks passed with Chromium/WebKit via
`./scripts/Test-ProgramKit.ps1 -Suite Development -BrowserEngines 'chromium,webkit'`.
The final product code and tests were held stable during this successful run; only
this non-shipped journal was completed afterward. `git diff --check` passed. The
implementation and approved handoff documents are scoped to the local implementation
branch; the primary checkout retains its original untracked files. Nothing was pushed.

Material limits: semantic inspection and consequential decisions remain human/agent
work through existing authority; helpers cannot prove application semantics from
graphs, metadata or successful installation. The real archive qualification is a
same-version minimal consumer with a named file-output invariant, not arbitrary
application, database, cloud, delivery or production acceptance. Cumulative multi-version
comparison and retained dependency behavior have separate deterministic coverage.
Preparation requires the actual committed Git/project root; nested consumer layouts
need an explicit supported reproduction assessment rather than guessed relocation.
Abrupt host/process loss requires reviewed interrupted inputs and confirmation that
children stopped before recovery; workspace restoration cannot reverse external state.
Firefox is unavailable on this Windows host; local engines are Chromium/WebKit and
the CI Firefox matrix remains unchanged. No Release suite, release selection,
publication, paid live workers, interactive intake, real consumer rollout or messages
were performed. Review the local branch before separately authorizing publication work.
