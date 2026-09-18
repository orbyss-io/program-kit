# Follow-up repairs from human trial 916d623d

This implements the findings in `consumer-trial-review-916d623d-2026-09-18.md` for
future disposable consumers. The completed trial and its approvals remain unchanged.

## Changes

- Language identity has one conservative normalizer shared by intake authoring and
  default resolution. Known aliases and bounded legacy provenance annotations map to
  canonical identities. New intake outputs use canonical language names; attribution
  stays in the existing choices/evidence. Unknown, mixed or explicitly constrained
  stacks remain consumer-owned, rather than being silently converted to .NET.
- Proof execution does not rewrite an unchanged roadmap. Actual status transitions
  preserve its newline convention, and validation rollback restores original bytes.
  Compatibility invalidation also preserves line endings. Final bootstrap size
  validation includes the roadmap as well as generated narrative views.
- The installed bounded reader pages one repository file at a time, at most 6,000
  UTF-8 content bytes without splitting characters. An optional JSON pointer selects
  just the needed fact; page metadata identifies the source hash and continuation.
  The six stage commands and native constitution dispatch route large reads through
  it, explicitly avoiding aggregation that defeats individual command limits.
- The existing intake descriptor/authoring contract explains the shared intake ID
  namespace, exact contract kinds, conditional open-item requirements and canonical
  language fields. Independent map-schema and intake-source errors are reported in
  one batch. Projected intake IDs are checked too. Invalid drafts do not replace
  existing consumer outputs or bypass the full semantic validator.
- Existing research guidance distinguishes external mechanism proof at bootstrap
  from future application test design at planning and execution at delivery. It does
  not waive or erase consumer verification obligations.

## Verification

Targeted regressions cover known/annotated language names, unknown/mixed constraints,
input immutability, simultaneous enum/duplicate-ID/blocking-field mistakes, existing
draft preservation, no-op near-limit roadmaps, CRLF status changes, final roadmap
size enforcement, Unicode paging, JSON pointer escaping, invalid pages, repository
path boundaries and unchanged source bytes. Context generation/freshness also passes.

Read-only replay of the actual trial's `C# (.NET managed default)` intake now selects
managed .NET/Foundation/Keycloak without a spurious integration question. The actual
closure evidence can be read in five bounded pages. No original consumer is patched.

Logs are retained as `artifacts/trial-followup-*.log`, including the bounded Development
suite and subsequent setup-only installation evidence. The fresh-install check starts
no agent or bootstrap workflow. The user-owned next intake/bootstrap trial supplies
the next end-to-end observation. Tests cannot guarantee agent compliance or establish
token savings before that trial is measured.
