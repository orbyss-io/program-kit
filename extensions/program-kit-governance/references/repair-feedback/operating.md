# Repair feedback v1 operations

From the consumer root, set `RF` below to
`.specify/extensions/program-kit-governance/scripts/repair_feedback.py` and run
`python <RF> <command>`. No Desktop, coding agent, dependency installer or paid
worker is needed. The reporter does not execute supplied reproductions.

## Diagnostic and evidence preparation

`draft --project <stable-public-project-pseudonym> --title <observable-trigger>
--output <new-request.json>` creates unknown answers and a stable request ID.
For follow-ups use `--previous <original-request.json>` to retain identity and
link its hash. Preserve the original account and earlier packet; a correction is
a new revision, not an edit to published evidence. `contract.json` publishes the
questions and vocabulary; `request.schema.json` publishes the same closed shape.
The deterministic validator is `repair_contract.py` and is tested against the schema.

Write `request.json` and `report.md` in a new selection directory. Report Markdown
must remain portable: describe the expected and observed behavior, actual selected
versions, constraints, decision explanation, local remedy, result/proof class,
proposed lesson and unknowns. Include exact diagnostic/guidance identifiers when
available. Add selected files under `evidence/`; put an entry for **every** file,
including report.md, in `evidence.members`. Required entry fields: `path`, `purpose`,
`provenance`, `bytes`, `sha256`, `transformations` and `qualification`. Before sealing,
bytes may be 0 and sha256 may be 64 zeroes; all other fields must be real or unknown.
`prepare --source <selection> --output <new-sealed-packet>` fills measured hashes,
validates exact inventory and copies a derivative without changing the originals.
`validate --packet <sealed-packet>` rechecks it. Hashes identify bytes, not truth.

Limits: at most 24 files, 256 KiB each, 1 MiB total including request/report.
Allowed extensions and binary signature requirements are in contract.json.
PNG/PDF require explicit fixture qualification and human content review; validator
does not render them or establish business/personal safety. Errors name a check,
never echo evidence. Reduce/select evidence or disclose a changed derivative;
never silently truncate proof to fit. No archives, full worktrees or env dumps.

## Preferences and local delivery

`configure --mode consumer` or `configure --mode contributor --checkout <chosen-root>`
creates `.program-kit/repair-feedback-personal/preferences.json` and `submissions.json`.
It writes a repository-local Git exclude rule, proves `git check-ignore` behavior,
and refuses already tracked personal data. Disclose these choices. This directory
is excluded from governance input digests and upgrade ownership; retain its bytes
through upgrade. `clear-preferences` clears routing only, keeping history. No tokens
or current status belong in these files. Equivalent existing choices are reused
by reading this directory before asking again; never overwrite choices silently.

Contributor `local --packet <sealed> --ledger <checkout-relative-owner-ledger>`
creates `artifacts/repair-feedback/intake/<requestId>/<revision>/packet/` and immutable
`delivery.json` in the chosen checkout. The owner ledger must exist. The reporter
never edits it. Repeating the same delivery is safe; conflicting bytes fail.
`--correlation <search.json>` links read-only correlation; without it correlation
remains pending. Owner adopts/defers/rejects/groups through the existing ledger.

## GitHub prerequisites and public review

Use `scripts/Check-RepairFeedbackGitHub.ps1` in PowerShell or
`scripts/check-repair-feedback-github.sh` in Bash. These perform read-only checks.
Install GitHub CLI yourself using https://cli.github.com/ (Windows installer/winget;
macOS Homebrew or installer; Linux distribution instructions). An executable found
in a known install directory but absent from PATH has a different diagnostic from
an absent executable. Restart the shell after PATH changes. Run `gh auth login
--hostname github.com` yourself, then `prerequisites` to check the actual account.
No token is requested, saved or printed. Local queuing has no GitHub dependency.

`search --terms <distinctive-id-and-component> --alternate <deliberate-other-terms>
--refine <narrower-trigger> --output <search.json>` searches explicit
orbyss-io/program-kit, open and closed, up to 10 results each and 20 inspected
candidates, retaining query counts/incompleteness and paginated comments. Inspect
the best candidates and causal evidence; closed may mean fixed-old-version,
declined or regressed. If incomplete, refine before public delivery. Empty search
is not proof of uniqueness. Evaluators use the same correlation path.

Before preparing public delivery, inspect actual repository metadata, pinned main,
guardian deployment and enforced required-workflow rules. Intended evidence repo:
orbyss-io/program-kit-evidence. Its absence or unavailable rules pauses publication.
`plan --packet <sealed> --correlation <search.json> --destination <new-or-number>
--rationale <causal-disposition> --account <selected-login> --base-commit <exact-sha>
--validator-commit <trusted-workflow-sha> --output <review.json>` records all exact
content and destinations. Show review.json and packet contents. The PR/cross-link
URL placeholders refer only to the objects created by this described workflow.
After explicit approval of the exact review digest, run `publish --packet <sealed>
--review <review.json> --approved-digest <human-approved-digest>`.

The CLI creates/comments on the repair issue, creates/reuses the selected user's
fork, commits only the reviewed inventory via Git Data API, publishes a stable
branch, opens an evidence PR against main and cross-links it. The consumer needs
no upstream Write. `guardian-deployment.json` is not sufficient: the live ruleset
must enforce the pinned workflow identity and maintainer review. Same-name status
checks alone cannot establish trust. See repository-owned `evidence-repository/`.
All submitted code is data. Acceptance retains evidence in v1; no automatic deletion.

Interrupted operations retain the prepared report and ignored delivery journal
under `delivery/<requestId>/<revision>.json`. Known objects and markers are read
before retry; conflicts stop. A fork may take time to provision. Inspect the exact
remote outcome and retry the same digest, never invent a new request to evade
reconciliation. Partial publication stays disclosed even when the later PR fails.

## Fresh status and reconstructable history

`history --project <id>` shows project references and attempts account discovery;
`history --account-wide` explicitly expands scope. Discovery searches author,
commenter and involvement, bounded at GitHub's 1000 result search ceiling; refine
scope if incomplete. Markers and project provenance distinguish contributions to
someone else's issue. Recovered references can be added to the personal index
through `recover --project <id>`, optionally with `--known-objects <references.json>`
for lost-index recovery from already known objects. It freshly reads bodies/comments
and restores marker/revision/hash references without fabricating publication receipts.
`link --request-id <id> --objects <references.json>` adds explicitly selected
implementation PR/release references. Each object has `repository` (one of the two
explicit repositories), positive `number`, and `kind`: `issue`, `evidence-pr`,
`implementation-pr` or `release`. No guessing from comments or current-state storage.

`status --request-id <id>` freshly reads indexed local ledgers and known issue,
comments, evidence/implementation PRs, reviews, checks and release records. It uses
direct reads with no cache and no persisted status; network failures yield partial
or unavailable. Source objects retain updated_at; retrievedAt names observation
time. Local ledger data remains labelled local. Lifecycle facts remain unknown
unless an evaluator/owner supplies attributable proof; arbitrary “fixed” comments,
closed issues or merged evidence are not proof of implementation or release.

Version compatibility: v1 refuses unknown contract versions; preserve those originals
and write a separate evaluator mapping with assessment version, original hash,
canonical mappings and unknown fields. Do not replace old answers or pretend that
new questions/knowledge were available to the original consumer.
Repository evaluators can preserve an explicitly selected historical JSON account
with `scripts/repair_evaluator.py --root <chosen-checkout> --preserve-original <file>`.
It retains exact bytes and actual recorded provenance, rejects missing provenance,
and makes no current-contract or public-delivery claim for an older contract.
