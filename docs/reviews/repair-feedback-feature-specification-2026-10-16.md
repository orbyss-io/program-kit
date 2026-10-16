# Consumer repair feedback: approved feature specification

Approved 16 October 2026 in the chat **Create a repair feedback skill**
(`01a14496-89a6-7740-838b-e03d8b17205f`). After a dependency-aware design interview,
the user confirmed the consolidated design and initial operating defaults.
This document records that approval; it does not claim implementation, a created
evidence repository, successful delivery, validation, or release.

The user subsequently clarified that implementation belongs to a separate
implementation agent on a separate feature branch and isolated checkout. The
existing **Implement maintenance repair plan** session
(`01a1442e-a64f-7f73-be99-e739e15918da`) does not own this feature. The feature's
implementation session owns its own execution ledger and sequencing. Track this
as a distinct feature, not another confirmed consumer defect or a silent addition
to the maintenance approval. This ownership correction supersedes the earlier
handoff to the maintenance session without changing the agreed feature behavior.

## Purpose and authority

Program Kit learns from the blockades its consumers encounter, especially when
implementation turns prose into executable behavior. It needs comparable accounts
of what consumers encountered, what they consulted, why they chose a solution,
and what the solution actually established.

The shared contract includes diagnostic instructions, ubiquitous language, and
predictable structured output. It is not merely an attachment manifest. Program
Kit owns this contract and determines its shared direction. Consumer observations
are learning inputs; neither compliance nor a plausible local workaround proves
that Program Kit is correct or that an upstream repair is required.

Repository instructions continue to govern execution, release, and paid workers.
A skill, contributor declaration, or checkout path grants no additional access.
Deterministic CI starts no coding agent. This design authorizes no paid phase,
consumer implementation, release tag, or package publication.

## RF-01: paired capabilities and distribution

- Ship a consumer reporter through the governance extension's registered command
  mechanism and native skill generation. A suggested command is
  `speckit.program-kit-governance.repair-request`; final naming must be consistent
  across the manifest, installed commands, skills, help, and tests.
- Keep the contributor evaluator under repository `.agents/skills/`, outside
  consumer/runtime release allowlists. It can evaluate one or several explicitly
  scoped consumers and submit assessments to the implementation owner.
- Core records and local delivery must work without Codex Desktop. Chat discovery
  and notifications are optional adapters with explicit recipient scope and
  applicable user messaging authority.
- Default evaluation inspects existing evidence. Asking an active consumer for
  more evidence is a separately configured interaction, not implicit permission
  to interrupt it, rerun its work, or modify its repository.

## RF-02: versioned diagnostic instructions

Publish the diagnostic questions, term definitions, and output schema together.
The reporting agent answers from available records and identifies unknowns rather
than fabricating an explanation or requiring every missing fact from the human.
The stable diagnostic core covers:

1. The consumer, selected Program Kit/profile/knowledge versions, phase, task,
   triggering command, and observed source/dirty-state limits.
2. Expected behavior and the exact requirement, guidance, task, or tool contract
   that supports the expectation. An unsupported expectation remains explicit.
3. What actually happened, its triggering conditions, observable consequences,
   and available reproduction or counterexample.
4. What knowledge, tools, and skills were available, and which were actually
   consulted according to retained evidence. Availability does not prove use.
5. The recorded decision explanation, constraints, considered alternatives when
   recorded, and why the agent reported choosing its local remedy.
6. The local change or workaround, what was preserved or bypassed, and its scope.
7. Results, failures, uncertainty, remaining blockade, and evidence supporting
   each claim. Distinguish reported tests from inspected tests and executed proof.
8. The proposed upstream lesson, if any, without presenting it as an established
   defect, accepted architecture, or universally correct consumer solution.

Use observable actions and recorded decision summaries. Missing explanations stay
unknown; later explanations are labelled retrospective. Do not request private
chain-of-thought or invent a retrospective reasoning trail.

## RF-03: language, history, and normalization

Program Kit owns canonical fields and terms while retaining the consumer's
original wording and explicitly unclassified observations. Unknown concepts must
not be forced into an inaccurate category. Existing terms are reused only where
their meanings actually match.

Every request identifies its diagnostic-contract version and the selected
knowledge the consumer had. Preserve the original account and evidence identity.
A later assessment can map it into current terminology, recording the mapping,
unknown fields, and assessment version separately. Never imply that older answers
were produced from newer questions or that a newer default profile was available.

The implementation must publish actual machine-readable field names and enums;
neither agent nor validator should infer their spelling from this prose.

## RF-04: identity and relationships

Assign a stable request identity and identifiable evidence revisions/hashes.
Distinguish request identity from repair/finding identity. Several consumers or
revisions can substantiate one underlying repair; related but distinct repairs
can form an explicitly explained group. Preserve each observation's provenance.

Ordinary corrections explicitly supersede earlier revisions. Keep consumer
observations, evaluator conclusions, implementation decisions, and closure proof
as distinguishable records. Transport retries reuse the request/revision identity
instead of generating duplicate requests, issues, comments, or PRs.

## RF-05: setup and personal records

On first unconfigured use, ask whether the person is a Program Kit contributor.
Consumer mode is the default. Contributor mode requires a user-selected Program
Kit checkout, validated before local writes or discovery of its internal skill.
It enables the local route and leaves explicit GitHub delivery available.

Create a small ignored preference file when an equivalent suitable file does not
exist, and disclose its creation and saved routing choices. Preserve choices
through upgrades and allow changing/clearing them. Prove ignore behavior; a
`.local` suffix alone is insufficient. Keep preferences out of governance input
digests, public request evidence, credentials, and acceptance authority.

Keep an ignored per-consumer submission index, alongside those preferences,
containing stable identities, account/host references where needed, issue/comment
and evidence PR links, evidence revisions/hashes, and historical publication
receipts. It is reconstructable from known references and GitHub discovery.
Do not persist current status in this index. Store no authentication tokens.

## RF-06: local delivery

Local delivery durably records the request in the selected checkout's bounded
development-session intake queue. The implementation owner incorporates it into
the shared ledger or records duplicate, rejected, deferred, or other dispositions.
Collector and reporter do not concurrently rewrite implementation status.

A queued request is not an adopted repair. Notification of a configured running
agent is an optional convenience; durable delivery must survive a busy or offline
agent. Keep local context in linked request/ledger records instead of manufacturing
individual GitHub issues. Preserve historical plans, approvals, and audits.

This route creates no public issue, comment, fork, upload, or evidence PR. It may
perform read-only GitHub correlation. If correlation is unavailable, record it as
pending without claiming it succeeded. Never silently fall back to public delivery.

## RF-07: search, correlation, and public discussion

Both reporters and evaluators search upstream reports. Explicitly target
`orbyss-io/program-kit`, not the consumer repository's default Git remote.

- Produce descriptive titles using consistent component terms, observable failure
  or diagnostic identifiers, and distinguishing triggers. Do not encode a guessed
  root cause as an established fact.
- Search open and closed issues using bounded queries. Start with distinctive
  identifiers/component terms, refine excessive results, and use deliberate
  alternative terms when an initial search is empty.
- Record queries, bounds, and incomplete searches. An empty bounded search is not
  proof that no duplicate exists; do not exhaustively open an unbounded issue set.
- Inspect the strongest candidates individually, including relevant comments,
  affected versions, triggers, and causal evidence. Similar wording is insufficient.
- On the public delivery route, a supported duplicate receives a comment with the
  additional evidence. On the local route, record that relationship in local
  request/ledger records without posting a comment. Related problems retain
  cross-links. If a public destination is uncertain, present a shortlist and
  recommendation for the user's choice before publication.
- Closed issues may describe an older fixed version, declined work, or a new
  regression. Inspect their disposition rather than deciding from state alone.

Show the exact public destination, body/comment, and evidence contents for user
approval before publication. Do not ask again when that exact publication already
has explicit approval. A reviewed workflow can include its described issue/comment,
fork, evidence push, PR, and cross-link steps. Report partial outcomes honestly.

## RF-08: public evidence route

Use a separate public evidence repository, intended as
`orbyss-io/program-kit-evidence`; verify its actual provisioning and configured
identity before claiming availability. Repair issues and implementation PRs remain
in Program Kit. Supporting evidence files and evidence-submission PRs live in the
evidence repository and cross-link the relevant issue, request, and revision.

The skill handles creating/reusing the consumer's fork, staging only the reviewed
evidence, pushing its submission branch, opening an evidence PR, and recording
the resulting links. Ordinary consumers need no upstream repository Write role.
Do not use a push-then-cleanup Action as the acceptance boundary. A public fork
push already publishes the contents, so sanitization/review must precede it.

Keep the portable report readable in the issue/comment, including stable identity,
contract version, key diagnostic information, evidence links, and omissions.
Do not depend on generic CLI issue attachments or undocumented upload endpoints.

If interrupted after a remote mutation, use known references and request/revision
markers to reconcile the actual remote result before retrying. Do not blindly
duplicate comments, forks, branches, issues, or PRs. Historical receipts record
what happened at delivery time, not the object's current status.

## RF-09: useful bounded evidence and the guardian

Prefer minimal synthetic reproductions and selected sanitized excerpts over bulk
consumer data. Support report Markdown, structured contract data, relevant logs,
patches, small source reproductions, and explicitly qualified fixture types such
as screenshots or PDFs where necessary. Treat all artifacts as untrusted data.
Full worktrees, environment dumps, and arbitrary archives are outside v1 defaults.

Publish enforceable allowed types, per-file/total/file-count budgets, manifest
requirements, and error guidance before accepting uploads. Existing packet limits
and GitHub's maximum sizes are not automatically appropriate public budgets.
Declare purpose, provenance, byte count, and hash for evidence members. Preserve
originals locally and identify redactions, truncations, omissions, and unsupported
artifacts in the public derivative. Do not silently substitute truncated proof.

The deterministic guardian validates the exact submitted inventory, paths,
manifest/schema, types/bounds, content identity, permitted changes, and supported
sensitive-content checks. Reject escapes, links/aliases, unexpected files,
tampering, and submissions that modify validator/workflow policy or accepted
evidence outside the permitted revision model. Diagnostics must not echo secrets.

Use trusted validator code and bind results to the exact submitted commit and
validator/contract version. A PR must not be able to redefine its own required
guardian through a same-name check. Do not execute supplied scripts, project
configuration, dependency setup, or reproduction commands. Add no coding-agent CI.

V1 acceptance requires passing guardian checks and maintainer review. Passing
means contract-valid evidence, not a truthful diagnosis, authenticated publisher
attestation, consumer acceptance, or a confirmed Program Kit defect. Sanitization
cannot establish that arbitrary business/personal facts are safe to publish.
Retain accepted evidence as a release reference without automatic deletion in v1;
never promise erasure from public Git history, clones, or forks.

## RF-10: evaluator learning and upstream decisions

The evaluator compares the observed path with attributable Program Kit expectations
under the consumer's actual versions and constraints. It assesses both paths:
Program Kit guidance can be wrong, incomplete, ambiguous, or hard to discover;
consumer choices can also be incorrect or appropriate domain adaptations.

Record evidence class (reported, inspected, independently reproduced), cause and
ownership assessment, missing proof, request-to-repair relationships, and the
reason for the proposed shared disposition. A single convincing counterexample
can establish a shared defect; report volume is not a correctness vote.

Identify the reusable mechanism or guidance gap, supported scope, effects on other
consumers, and what would make the expected next action clear at the point of use.
Keep domain policy local unless a shared capability is deliberately adopted.
Unknown root cause remains unknown; remedy plausibility is not qualification.

The implementation owner decides repair scope, sequencing, grouping, and explicit
defer/reject/adopt dispositions. Neither consumer nor evaluator rewrites approval
history or unilaterally turns every observation into a shared feature.

## RF-11: follow-up, identity discovery, and current status

The consumer skill supports on-demand status, additional observations, and evidence
revisions. Default history is this consumer project's requests; offer explicit
account-wide discovery. GitHub supports author, commenter, and involvement filters,
so losing the local index does not make public reports undiscoverable. Authorship
alone misses evidence added to another person's issue. Use stable request markers
and scoped provenance to distinguish projects and paginate required direct reads.

Every status request directly retrieves the known cloud issue, comments,
evidence/implementation PRs, checks, and relevant release records as applicable.
Disable API response caching for these reads. Search is discovery, not the status
authority for an already known object. Current status never comes from a persisted
snapshot or earlier response. Failed retrieval yields unavailable/partial, never
stale fallback. Show retrieval time and distinguish source update timestamps.

For local-only requests, freshly read the authoritative local development ledger
and label the source local. Fetch linked cloud objects separately. Do not publish
local progress merely to make a cloud status available. Fresh reads establish
observed state per source, not an atomic snapshot across all systems.

Keep evidence acceptance, assessment, confirmed repair, implemented change,
validation, and released availability distinct. Closed issues, merged evidence
PRs, or arbitrary comments saying "fixed" cannot establish the full lifecycle.
Unknown lifecycle facts stay unknown with supporting links to what is available.

Follow-up publication uses the same reviewed-content workflow and request identity.
Implementation/release owners control subsequent issue comments and closure under
their existing authorization. The evaluator does not silently close issues.

## RF-12: prerequisites and failure behavior

For GitHub delivery, check installed CLI availability and authentication for the
actual host/account. Distinguish an absent executable from one outside PATH.
Provide simple Bash and PowerShell check/setup helpers with supported OS-specific
installation guidance and user-run authentication steps. Never request or log
tokens, assume one package-manager command works everywhere, or install/login
silently. Local delivery must not acquire a GitHub dependency merely to queue work.

Keep a prepared local report when prerequisites, lookup, checks, or remote delivery
fail. Public submission pauses if duplicate checking failed. Local correlation can
remain pending. Report actual partial publication and reconcile before retrying.
Do not treat lookup, validation, or security failures as success.

## RF-13: repair, release, and migration traceability

The owner records the repair, its reason, related requests/issues, changed files,
actual verification, unresolved dependencies, and closure proof in the shared
development ledger. No second independently mutable implementation ledger is
introduced by the reporter.

Keep implemented, independently validated, released, and confirmed-in-consumer
outcomes separate. Unavailable consumer confirmation remains explicit. Preserve
existing confirmed-defect readiness gates; an incoming hypothesis is not itself
a confirmed defect or a new publication authorization.

Release notes state concisely what changed, why, and useful context links: local
ledger/request records, GitHub issues, implementation PRs, and accepted evidence.
Use the authoritative versioned release/migration guidance indexed by
`releases/history.json`, with `releases/consumer-changes.json` where consumer action
is required. Do not create a competing release-note authority. Update affected
procedures, point-of-use knowledge, and migration instructions when applicable.

## Existing implementation anchors

- `extensions/program-kit-governance/extension.yml` and its command/script/reference
  layout; `scripts/native_phase_ownership.py` for generated integration ownership.
- `extensions/program-kit-governance/scripts/consumer_upgrade.py` for bounded,
  allowlisted public derivative export and honest omission/redaction provenance.
- `scripts/maintenance_packet.py` for exact UTF-8 inventory/hash/path inspection.
  It is currently repository-only, not a binary exporter, comprehensive sanitizer,
  publisher authenticator, or the new diagnostic contract.
- `docs/reviews/maintenance-implementation-ledger-2026-10-16.json` and companion
  implementation record as an example of existing maintenance coordination, not
  this feature's execution ledger or a generic schema to copy unchanged.
- Existing local governance configuration affects lifecycle inputs; do not reuse
  it for personal routing without proving separation from governance digests.

## Verified platform references

- [GitHub issue search](https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests)
  and [CLI search](https://cli.github.com/manual/gh_search_issues).
- [Issue comments](https://cli.github.com/manual/gh_issue_comment) and
  [file-attachment limitations](https://docs.github.com/en/github-cli/github-cli/attaching-files-with-github-cli).
- [Fork PRs](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-a-pull-request-from-a-fork)
  and [required checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
- [Trusted workflow guidance](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target),
  [API cache control](https://cli.github.com/manual/gh_api), and
  [public data removal limits](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

Platform details must be rechecked when provisioning or implementing. The approved
semantics above remain the requirements; these links do not assert configured
repositories, branch rules, identities, or successful remote operations.
