# Program Kit self-hosted PK-W080 plan

Canonical source: `pkid:plan:program-kit:self-hosted-w080@1.0.0`

Source digest: `sha256:0b03457928ae0b7bfb917c0b6024ea56cf2451d14ba540b8cfe00f60cc64823b`

Design:
`pkid:design:program-kit:self-hosted-baseline@1.0.0#sha256:c5ed7f0d4f278181f138dd5a4dcb9300502dd85aea8be7271c7da15762439327`

## State and authority

The self-hosted plan state is `superseded`. It is a contract-shaped
representation, not a new implementation authority. The approved bootstrap
plan `0.3.0` and its exact approval record remain authoritative.

## Requirement

`PK-R013`: carry the bootstrap design and plan through implemented contracts
without rewriting history. Self-hosted artifacts validate and a structured
comparison records real differences.

## Work unit

`PK-W080` produces:

- canonical self-hosted design and separate plan instances;
- deterministic Markdown;
- dependency, forbidden-reference, and Version Map graphs;
- an approval relationship report, not a new approval;
- a normal receipt for the actual post-registration event; and
- a structured bootstrap comparison.

Allowed edits remain `program-kit/artifacts/` plus bootstrap comparison
tests/documentation.

## Stop conditions

- Stop on bootstrap approval or source digest mismatch.
- Stop on material architectural deviation or edits outside the approved paths.
- Do not backdate a receipt or claim capability authorship of bootstrap source.

## Verification

The conformance test validates both canonical instances against exact Program
Kit schemas, fixes all projection bytes, compares the project graph to current
project references, checks the registered capability digest in the receipt, and
proves the four historical bootstrap files remain intact.
