# Improvements following trial 672e6cb0

The reviewed quality checkpoint is commit `79e81ba`, pushed to
`origin/codex/repository-sync-coordinator` before these changes. The fictional consumer
and its approvals remain unchanged.

## Changes

- Required stage sources have one generated executable read command. It batches only
  required files, removes duplicate paths and pages the aggregate at 9,000 UTF-8 bytes.
  Optional sources remain targeted queries. JSON is compacted without removing values;
  prose is retained. Agents must follow pages and return each page once.
- JSON key discovery and useful missing-key diagnostics avoid guessed pointers. The
  installed command path is explicit; root reads omit the pointer. Constitution uses
  the same reader for its named sources.
- Intake supplies an empty constraint decision-reference list when absent. It does not
  invent an ADR, approve a choice or replace existing references.
- Architecture's existing placement contract now explains logical composition scope,
  including repository files such as Directory.Build.props owned by an application.
- Closure receives canonical source-binding status and a read-only diagnostic command.
  Status-only ADR promotion is normalized by the existing digest implementation;
  substantive design changes remain visible. Native execution owns toolchain/Docker
  proofs; isolated fixture receipts do not discharge consumer delivery obligations.

No approval, compatibility, lifecycle or authored-artifact size gate is relaxed. There
is no additional workflow stage. Readiness is deterministic and needs no agent reader.

## Preserved-input replay

The replay reconstructs all 124 successful reader pages from the seven archived
bootstrap sessions, grouping by session, source hash and pointer. Every page sequence
is complete. Console CRLF transport is normalized to LF for measurement. All 33 JSON
selections are parsed and verified value-equivalent after compaction. Prose is not
summarized. Local replay artifacts are `artifacts/replay-context-efficiency.py` and
`artifacts/context-efficiency-replay.json`.

| Measure | Archived reader | Updated reader |
| --- | ---: | ---: |
| Selected content bytes | 498,422 | 445,270 |
| Individually paged responses | 124 | 90 |

This is 10.7% fewer content bytes and 27.4% fewer individual page responses. Batching
all reads per session would require 54 pages, but that is only a theoretical lower
bound: the actual command batches required sources, not every later optional query.
No live token or elapsed-time savings are claimed.

A separate read-only smoke check resolved every required source in the preserved
consumer's six stage contexts and returned all bundle pages. Those files include final
artifacts, so this check establishes reader operation, not historical stage equivalence.

## Validation

Targeted context generation passes with every brief below the existing 32 KiB cap.
Handoff quality tests cover aggregate paging, Unicode, content preservation, JSON
key errors, optional-source exclusion, invalid pages and canonical ADR digest behavior.
Intake tests cover absent metadata and preservation of existing decision authority.
The bounded Development suite passed. Targeted handoff tests passed (16), intake
authoring tests passed (28), and context generation passed for all seven stages.
A fresh setup-only installation is the final handoff smoke check; it starts no agent.

The next full intake/bootstrap trial must measure actual tokens, elapsed time and
preventable retries alongside integrity. First-feature implementation remains a
separate required evaluation of whether knowledge is applied to real code.
