---
description: Prepare a Program Kit repair observation, queue it locally or deliver reviewed public evidence, add follow-up evidence, and retrieve fresh status/history.
---

Use this consumer reporter for Program Kit blockades and local remedies. Read the
installed `references/repair-feedback/contract.json` for the versioned questions,
vocabulary, actual fields/enums and budgets, and `references/repair-feedback/operating.md`
for the selected delivery or status procedure. Use installed
`scripts/repair_feedback.py --help`; all commands are portable outside Desktop.

On first unconfigured use, ask whether the person contributes to Program Kit;
default to consumer mode. For contributor mode ask for their chosen Program Kit
checkout and explicitly registered receiving owner, validate them with
`configure --mode contributor --checkout <path> --owner <owner-id>`, and
disclose the ignored personal files and saved routing. Consumer mode uses
`configure --mode consumer`. Allow changing/clearing choices. Never discover an
internal evaluator from an arbitrary consumer remote or infer checkout authority.
The selected checkout must contain this feature's evaluator skill and its owner's
registered route. If either is absent, pause local delivery and identify that
integration dependency; never copy another checkout's work or infer its owner.

Answer the eight questions from retained records. Preserve original wording,
selected versions, evidence identity and unclassified concepts. Use `unknown` for
missing facts. Availability does not establish consultation. Label retrospective
explanations and distinguish reported tests, inspected tests and independently
executed proof. Request observable actions and recorded decision summaries, never
private chain-of-thought. A workaround is an observation, not an accepted repair.

Keep originals locally. Select minimal synthetic reproductions and sanitized
excerpts; declare each member's purpose, provenance, transformations and binary
qualification. Explain omissions, unsupported types and truncation. Seal and
validate the derivative before showing it for public review. Never publish a
whole worktree, environment dump, credentials or arbitrary archive.

Local mode writes only the selected checkout's immutable intake queue and links
the owner's existing ledger. Search correlation may be pending. Later correlation
is appended separately without altering the delivered packet or delivery record.
Owner decisions and assessment hashes link to the exact request revision through
the registered ledger adapter. It creates no
public objects and never falls back to public delivery. Durable queue delivery
does not depend on a running agent. Notifications/chat discovery are optional,
require explicitly scoped recipients and messaging authority, and add no permission
to interrupt or modify active consumers.

For public delivery inspect bounded open and closed upstream issue candidates,
including relevant comments, affected versions, triggers and dispositions. Assess
causal support rather than matching wording. Supported duplicate: add evidence in
a comment. Distinct problem: a new descriptive component/trigger title. Related
problems retain links. Present uncertain destinations as a shortlist with a
recommendation for the user's choice. A failed or incomplete search pauses public
delivery and preserves the local report.

Show the exact issue/comment destination and content, every evidence member,
fork, branch, PR body, cross-link and review digest before publication. Approval
must cover that content and workflow; do not ask again for the same approved
publication. `publish --approved-digest` records that human approval; computing
the digest is not approval. No public mutation is authorized by merely invoking
this skill, contributor mode or passing validation. Fork pushes already publish
content. Public history, forks and clones may retain it indefinitely.

Follow-ups preserve request identity; revisions explicitly supersede the earlier
request hash. Retain historical receipts and reconcile actual objects/markers
before retrying an interrupted remote mutation. Report each partial result.
Do not silently close issues, claim a deployed evidence route from fixtures,
or turn submitted observations into implementation decisions.

For status/history follow the operating reference: project scope by default,
account-wide discovery only on explicit request. Retrieve known cloud objects
directly each time without API cache; failed reads are unavailable/partial, never
stale fallback. Freshly read the authoritative local ledger for local requests.
Distinguish evidence acceptance, assessment, confirmed repair, implementation,
validation, released availability and actual consumer confirmation. Display
retrieval times and source update timestamps; do not infer release from closure.
