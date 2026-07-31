# Program Kit review sets

This directory records human-led review sets for bounded Program Kit changes.
It is development history and authority evidence, not a collection of runtime
extensions.

A review set can contain:

- design intent and architecture;
- an implementation plan and approval record;
- amendments, compatibility decisions, and migration fixtures;
- validation reports and implementation evidence;
- deterministic materialization or verification helpers.

Status varies by child directory. Read that directory's `README.md` before
using it: some sets are completed, some are approved, and some remain on the
backlog.

## Relocation and historical paths

This tree was relocated from `extensions/` to make its purpose explicit.
Existing approved and digest-bound review artifacts retain their original
literal `extensions/...` path values and bytes. Those values record the review
context in which approval or evidence was created; they are not live repository
navigation.

Live code and tests use `.review-sets/`. If work in a frozen set resumes, create
an explicit amendment or migration that rebases its paths instead of silently
rewriting an approved record.
