# Internal modularity implementation review

Date: 2026-10-24. Implemented in `codex/bootstrap-intake-analysis`, based on
`4a3455ca2366121e8bc1cab4ad9e4f4cdbbb57f5`. This review records the implementation state; the branch and PR identify its committed source.
The unrelated main checkout remains outside this work.

The user approved the [design](modularity-design-2026-10-24.md). Its five sections
are implemented within the stated internal scope. The investigation and source
classifications remain in the [audit/grilling record](distribution-and-knowledge-review-2026-10-23.md).
The public pack ecosystem remains [feature request #57](https://github.com/orbyss-io/program-kit/issues/57).

## Owners and dispositions

| Responsibility | Producer and callers | Installed/output boundary and disposition |
| --- | --- | --- |
| Native integration | Existing extension commands/hooks, governance preset and bootstrap workflow | Keep their native IDs, registrations and phase behavior. The existing five components still form the consumer bundle. No new extension/pack manager. |
| Shared runtime mechanics | `program-kit-governance/scripts/program_kit_runtime/`; Python runtime, package execution, phase result parsing, tooling witness and archive builder use this owner | Five complete `eng/` helper copies are emitted from that owner by `scripts/sync_shared_runtime.py`. Integrity and packaging enforce parity, accepting Git's LF/CRLF checkout transformation. Consumer copies import and run without the toolkit. |
| Engineering | Existing .NET templates/generators, building-block selectors, composition and native architecture checks | Keep stack-specific behavior with its owner. Existing phase/coding adapters still depend on the co-installed .NET implementation. This change does not claim a complete generic lifecycle without that adapter. Diagnostic operations retain their actual tool/pin requirements. |
| Knowledge | Existing `phase-obligations.json`, `knowledge_sources.py`, discovery, applicability and phase context | Preserve every selected canonical clause and exact-version lookup. Repeated applicability definitions and focused-reference instructions are consolidated by the renderer; no independently maintained rule summary. |
| Distribution and retained data | `scripts/build_release.py`, release asset inventory, source witness, updater consumers | Native composition and complete tooling have separate carriers. Qualified profiles, publisher captures, consumer locks, original source baselines and recovery readers remain intact. |

`bootstrap_probe_projects.py` had no current producer/caller or command route; only
historical source-baseline hashes referred to it. Its unused current helper is
removed. Those historical records remain byte-identical. The old historical-fact
compaction producer now belongs to `tests/historical_package_fixture.py`, where it
reproduces predecessor storage for independent compatibility/corruption checks.
New releases do not perform that compaction. The historical readers remain shipped.

Optional UI and engineering examples remain point-of-use assets with installed
callers and offline consumers. They are retained in their components and complete
tooling source. `npm_metadata.py` has real lookup/trial callers and is retained;
dynamically selected schemas are retained. There is no evidence-based justification
for bulk deletion or for rewriting qualified profile history. Application package
selection already computes the adopted closure: the audit resolved Domain Events
without Forms/Localization; Forms' real Localization dependency remains. This work
adds no second capability inventory and changes no application dependency pins.

## Inspect the changed outputs

- `program-kit-0.14.3.zip`: **5 entries**, previously **507**. Only `bundle.yml`,
  `VERSION`, README and license/notice metadata. The real native bounded extractor
  and archive manifest parser accept it and preserve the composition data.
- `program-kit-tooling-0.14.3.zip`: **738 entries**, 32,384,653 uncompressed bytes
  in the inspected build; largest member 2,375,100 bytes. Contains the complete
  updater/tooling/recovery source and original source witness. It no longer needs
  the additional 18,193,482-byte historical aggregate that rejected generic
  extraction of the prior composite. That earlier rejection did not establish
  failure of normal native manifest installation.
- Both assets are mandatory in the same candidate checksum inventory. Catalogs
  retain the native composition name. README/public upgrade and actual current
  source consumers select the tooling archive. Historical fixture selection accepts
  an old composite only when it actually contains the updater; a thin composition
  cannot silently substitute for a missing complete source archive.
- Builder bounds: native carriers 512 entries; tooling 8,192; each carrier 10 MiB
  per member and 128 MiB total uncompressed. Canonical paths, case collisions and
  CRCs are checked. These finite engineering safeguards do not define a public ABI.

Use `python scripts/sync_shared_runtime.py` to check mirrors and `--write` after
editing their canonical source. That contributor command regenerates repository
templates; it never refreshes a live consumer. Existing native upgrade/sync owners
remain responsible for consumer customizations and original receipts.

## Context measurements and limits

The same installed fictional API/browser journeys were retained before and after:

| Assembled planning output, including wrappers and observed context | Before UTF-8 bytes | After | Reduction |
| --- | ---: | ---: | ---: |
| API | 137,486 | 130,425 | 5.14% |
| Frontend-only browser | 75,329 | 73,977 | 1.79% |

Inspect `artifacts/f1-review/f36e307e6c/index.md` (before) and
`artifacts/f1-review/ac3b4acb44/index.md` (after), especially their first two command
outputs. Both journeys also exercise source/version routing, scoped mutation,
missing/ambiguous-source rejection and unrelated-owner exclusion.

The existing mixed explicit-tag constraint probe decreased from 175,549 to
167,722 bytes. This excludes other assembled phase data. These are byte counts,
not token counts, agent behavior or a quality claim. Reduction is deliberately
modest: distinct conditions, prohibitions and exceptions were not discarded to
meet an arbitrary target. Repeated `scope-N` definitions apply only to labelled
rules; focused lookup still returns original detailed source.

`contextBudgets` in the existing knowledge owner bounds assembled ordinary text at
196,608 bytes and focused text at 98,304 bytes. `PKC026` reports overflow before
printing the brief; it never truncates duties. Narrow actual operation/owner scope
or inspect the concrete responsibility. The explicit JSON diagnostic view remains
complete and is not a second ordinary brief. No claim is made to bound the agent's
entire conversation or to prevent someone concatenating unrelated contexts.

## Validation and retained failures

All paths below are relative to this checkout. Local records bind their actual
working inputs and are diagnostics, not release/publication authority.

| Record | Result and what it establishes |
| --- | --- |
| `artifacts/validation-runs/20261024T011406Z-0f4c78e2/results.json` | Integrity: 7 passed in 7.329s. Source syntax, mirrors and validation definition coherent. |
| `artifacts/validation-runs/20261024T010603Z-39102cbd/results.json` | Affected: 40 passed, one compiled-evaluation fixture failed; 428.170s, no unknown coverage gaps or budget overruns. Includes clean actual native installation, bootstrap, supported predecessor upgrade/customization/retry and knowledge/coding checks. Retains manual scenario coverage decisions. |
| `artifacts/validation-runs/20261024T011447Z-f7f0d46e/results.json` | Focused first run: dependency profiles (89.735s), release guidance/checksum negatives, package execution, witnesses, installation and isolation passed. Preserves the remaining archive assertion and host-access failures. |
| `artifacts/validation-runs/20261024T011826Z-6a1c3142/results.json` | Corrected archive assertion: build, release installation and runtime LF/CRLF/isolation tests all passed in 20.336s. Native manifest graph and complete tooling presence are checked separately. |
| `artifacts/validation-runs/20261024T011844Z-9e43b4cc/results.json` | Host-access rerun: deterministic harness contracts and compiled evaluation journey both passed in 32.434s; assertions/timeouts unchanged. |
| `artifacts/validation-runs/20261024T011923Z-01b92e56/results.json` | Host DNS rerun: builder plus complete installed source/UI/OCR recording preparation, customization refusal and later-session witness recovery passed in 34.747s. No provider or model calls. |

The initial Integrity run `20261024T010515Z-62e9c22e` found the public-download
fixture's old archive name; its corrected direct test and subsequent Integrity
passed. The later release-install fixture had another old-carrier assertion;
that assertion now checks the tooling archive while the composition graph still
comes from the native bundle. Neither required weakening a product assertion.

The compiled lesson first built successfully but its 15-second execution timed
out; the exact retained check passed directly in 2.155s. The focused journey then
exposed sandbox denial of Windows service diagnostics (`dotnet --info`). A separate
socket probe observed Windows 10013 permission denial; NuGet restore reported
blocked DNS. The focused checks passed with explicit host access. Original failures
and their streams remain available; no production code, assertions or timeouts were
changed for these host restrictions.

The representative installation/upgrade, installed source journey and unchanged
engineering bodies cover the carrier/import changes. Full browser, service,
composition and all F8 scenario matrices were not rerun for changed archive names
or generated header comments. Their manual selection notes remain visible in the
Affected record. Relevant CI still owns Linux and exact pinned Spec Kit **1.2.1**
qualification; local native checks used installed **1.2.0**. No device toolchain was
installed or changed. Public release verification/publication is outside this task.

## Review path

1. Compare the bundle and tooling builders and mandatory inventory in
   `scripts/build_release.py` and `scripts/release_assets.py`.
2. Inspect the shared owner, generator and emitted template headers. Follow fresh
   subprocess and refused-drift cases in `tests/validate_internal_modularity.py`.
3. Compare the retained installed before/after contexts and canonical-text inclusion
   and overflow cases in `tests/validate_knowledge_sources.py`.
4. Inspect actual installation/upgrade and witness results above, then the original
   failures and their focused resolutions. Historical baselines and qualifications
   have not been renewed or rewritten.

The product changes are ready for human diff review and normal exact-source package
CI. The user separately authorized committing, pushing and opening a PR. Tags and
publication remain outside this work.

## Trial preparation follow-up

Before the authorized commit, `tests/live/v2/trial_candidate.py` was updated to bind
the complete tooling archive alongside the native components. An independent
receipt test rejects omission and changed tooling bytes. Focused trial-receipt and
source-integrity checks passed in 3.044s; retained record:
`artifacts/validation-runs/20261024T084259Z-210c5151/results.json`.
This changes candidate preparation only and starts no coding worker.
