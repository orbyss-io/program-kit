# Release validation audit — 0.12.0

Date: 2026-09-24. Candidate reviewed: d74dd2ef7fcda2c43bb81741a18f5789ed21c496,
plus the uncommitted public-component fixture filename correction.

## Conclusion

Keep the behavioral and integration coverage, but revise its orchestration and stale
installation assertions before another publication attempt. The suite is not merely
too strict: some assertions contradict the current product, some meaningful tests
are not scheduled, and evidence names suggest broader assurance than execution proves.
Passing these tests cannot establish that an arbitrary agent completes a consumer intake.

This is a source and failure-evidence audit, not a successful Release run. No full
Release suite, live coding agent, publication or receipt generation was started for
this audit. The existing local failure remains a failure.

## What the suite actually covers

| Layer | Current evidence | Appropriate claim |
| --- | --- | --- |
| Source contracts | 54 Development validators plus 17 Release-only validators in Test-ProgramKit.ps1; schemas, profiles, pins, instructions, hooks and migration contracts | Required declarations and selected behavioral cases agree |
| Governance behavior | Phase readiness, handoff quality, lifecycle, resumption and refusal regressions | Tested inputs preserve approvals, route obligations and reject invalid transitions |
| Real dependency execution | Public component restore/use, .NET engineering probes, real EF/Npgsql/PostgreSQL including restart | Those pinned probes execute successfully on the tested host |
| UI | Generated UI browser tests; separate packaged UI generation checks | Selected generated UI journeys and packaged generation work; not every published Forms renderer integration |
| Installation/upgrade | Source installation, archive installation, candidate upgrade from previous stable | Installation and consumer preservation work for those paths, if the stale expectations are corrected |
| Packaged bootstrap consistency | Extracted packages, prepared architecture/governance artifacts, real validation and a two-step native completion definition | Packaged governance consistency and terminal completion, not a complete production bootstrap |
| Publication | Catalog availability, artifact hashes, tagged workflow and public smoke tests | Availability and integrity of released artifacts; not agent output quality |

## Confirmed findings

1. **Packaged installation expects an obsolete workflow.**
   `tests/validate_release_install.py:29` lists 40 steps and line 561 compares the
   installed list exactly. The current workflow has 56. The missing expectations
   include answer/handoff gates, default resolution, closure context and first-feature
   handoff. An accurately installed current workflow therefore fails this assertion.
   Compare the installed definition with the version being packaged; independently
   test required ordering/authority semantics so source and expectation cannot drift
   together unnoticed. `validate_public_upgrade.py:391` already derives installation
   parity from the source workflow.

2. **Source installation requires a deliberately retired command.**
   `scripts/Test-LocalInstall.ps1:229` requires the public dotnet-sync skill, while the
   current .NET manifest exposes an internal adapter and `validate_retired_sync.py`
   explicitly verifies removal. Require governance sync and the internal adapter;
   assert the obsolete public command is absent. This is a test defect, not a reason
   to restore the retired command.

3. **Test selection has multiple authorities and incomplete parity.**
   Local PowerShell, PR CI and tagged Release maintain separate execution lists.
   The newly added parity check catches missing source-validator filenames, but
   does not cover all commands, arguments, OS responsibilities or publication order.
   Local source installation is not in CI. The read-only legacy public check is local
   only. Most CI checks run on Linux; the Windows job focuses on bootstrap and mixed
   Python. Keep deliberate platform differences, but declare them explicitly.

4. **Two real integrations are not in the suite/workflow entry points inspected.**
   `validate_bootstrap_runtime.py` exercises the published Foundation host;
   `validate_published_forms_browser.py` exercises published Forms packages/renderers.
   Neither is called by Test-ProgramKit.ps1, ci.yml or release.yml. Generated UI tests
   and NuGet component probes are not replacements. Decide and document their
   required placement and registry permissions. The host probe also passes absolute
   lock/request arguments to the relative-path executor, the same portability defect
   just corrected in the public-component test. Validate it before adding it to gates.

5. **The test named bootstrap consistency E2E is narrower than a full bootstrap.**
   `validate_bootstrap_consistency_e2e.py:340` constructs a native definition containing
   only require-readiness and complete-bootstrap after preparing artifacts. Resumption
   tests use purpose-built workflow definitions and mocked agent steps. These are
   useful regressions; they do not prove that every shell handoff in the shipped
   56-step workflow composes successfully. Add deterministic execution of the actual
   installed definition with explicit agent-output fixtures and simulated reviews.
   Exercise complete, deferred, ambiguous, blocked-feature and resume cases. Label
   simulated authoring honestly; it does not replace optional human/live quality trials.

6. **Local and CI fixture assumptions caused avoidable failures.**
   Public-component absolute paths and NuGet.Config/NuGet.config spelling differed
   across platforms. The latest filename correction passes real component probes
   locally and explicitly asserts filename case. The local initializer file has LF
   bytes despite .gitattributes requiring CRLF. Its reported failure is a missing
   batch label even though the label is present. The builder copies those bytes
   unchanged (`scripts/build_release.py:317`). Normalize distribution script endings
   and test produced bytes and executable behavior. A bounded reproduction in this
   task stopped earlier at Spec Kit command discovery, so LF is a strongly supported
   hypothesis for the reported branch failure, not yet an isolated proven cause.

7. **Failure discovery and evidence capture are inefficient.**
   Local Release runs all 71 source validators before packaged installation and
   catalog-wide availability. It aborts on the first failure and writes its step
   journal only at the end. Transcript -Force overwrites the version's prior log.
   CI uploads artifacts only on success. Cheap toolchain/auth/installation checks
   should precede expensive probes. Preserve per-run logs/results on failure, and
   continue independent checks while marking dependent checks blocked. Never issue
   a success receipt when any required check fails or is unavailable.

8. **The receipt is weaker evidence than its label suggests.**
   `write_release_receipt.py:84` accepts a nonempty journal; without one, it fabricates
   one generic successful CI step. It does not reconcile executed check IDs with a
   required inventory. Workflow ordering supplies some assurance, but the receipt
   itself cannot establish coverage. Bind it to an actual per-check execution journal,
   candidate identity, required platform/engine coverage and artifact hashes.

9. **Test infrastructure changes a host monitoring setting.**
   `validate_public_upgrade.py:39` removes SSLKEYLOGFILE in child environments.
   `tests/live/v2/trial_candidate.py` does likewise. These paths were not executed by
   this audit. Use a supported runtime and actionable preflight diagnostics; tests
   should preserve host monitoring configuration rather than hide an incompatibility.

10. **Post-publication failures need distinct treatment.**
    release.yml publishes at line 165, then runs public installation/upgrade at line
    185. A red final workflow can therefore mean assets are already public. External
    propagation smoke tests cannot all precede publication, but candidate installation
    must pass first and post-publication failures must explicitly disclose exposure.
    Retain the existing failed-tag/partial-publication safeguards.

## Duplicates versus useful layers

No broad duplicate-removal is justified. CI runs the initializer check on two operating
systems intentionally. Tagged Release runs candidate upgrade before publication and
public upgrade afterward for different reasons. Source installation, packaged
installation and previous-version upgrade protect different boundaries. Retain these;
make their responsibilities explicit and share fixture setup where safe.

Text/phrase assertions are appropriate for mandatory instruction contracts, but they
cannot demonstrate that an agent follows the instructions. Keep behavior assertions
for execution and avoid exact prose checks where meaning-preserving edits are valid.

## Recommended repair order

1. Correct the two obsolete installation expectations and cross-platform fixtures;
   establish the initializer cause and test packaged script encoding. Preserve failed logs.
2. Introduce one declared check inventory (ID, purpose, prerequisites, platforms,
   arguments, network/credential needs, evidence, expected failure modes). Use it in
   local, PR and tagged runners; retain existing coverage and explicit exceptions.
3. Run cheap preflight/installation checks first; retain failed per-check journals
   and redacted evidence, and aggregate independent failures without hiding blockers.
4. Add the actual installed-workflow deterministic composition test, and explicitly
   schedule host/Forms integration checks with the necessary trusted registry access.
5. Validate receipts against executed inventory; document local/CI coverage separately.
6. Run targeted checks and Development, then green candidate CI, then request one
   clean user-owned Release run. Publish only after required gates are satisfied.

Do not reduce safety gates, require every consumer decision to be resolved at bootstrap,
or add paid agents to deterministic validation as a shortcut to green results.

## Repair evidence

The repairs replace the separate execution lists with `tests/validation-inventory.json`
and a shared runner. Per-check logs, process-tree cleanup results and a failure-preserving
journal replace the end-only journal. Required prerequisites precede their consumers;
successful receipts require exact coverage and hashed logs. CI retains failed evidence.

The two obsolete installation assertions are corrected. Packaged initializer bytes are
normalized to CRLF. A controlled test now reproduces the original missing-label failure
with LF and passes with CRLF. The initializer fixture also uses an explicit bounded PATH;
the Desktop host's inherited PATH exceeded 19,000 characters and prevented CMD discovery.

The complete packaged bootstrap now has four deterministic native-engine scenarios:
ordinary completion, deferred implementation proof, discovery before specification, and
missing-producer-output failure followed by native resume and separate simulated reviews.
All shell steps are real. Only authoring and review decisions are fictional; no agent is
started and no real consumer is approved. Completion does not waive the open phase gates.

Host and published Forms integrations are now scheduled. Cold-host execution explicitly
pulls the exact host digest; browser setup is a declared prerequisite. Forms source hashes
use documented LF normalization so provenance does not depend on checkout line endings.
Further stale hook assertions and the clean-consumer schema-runtime setup were corrected.
The registry/upgrade test paths preserve host TLS-monitoring settings.

Focused local checks passed for packaged installation, initializer behavior, journal
coverage rejection, the installed workflow scenarios, terminal consistency, guarded live
harness contracts, published host activation and published Forms (Chromium/WebKit). The
bounded Development run passed. These are supplementary checks, not a local Release
receipt; the complete user-owned Release suite remains mandatory before publication.
