---
name: program-kit-release-readiness
description: Review exact candidate package CI, developer-reported validation and relevant optional trial gaps for Program Kit maintenance. Grants no paid-worker, tag or publication authority.
---

Read repository AGENTS.md, docs/validation.md, docs/releasing.md and release-policy.json.
Use the maintained scripts and native GitHub controls; do not invent a second approval,
receipt submission, evidence ledger or per-test disposition ceremony.

Establish the candidate commit/version and actual changes since the previous successful
public release. Review the concise PR validation summary, representative fixture scope,
measured costs and unresolved gaps. Developer execution is maintainer reported; CI
independently checks package mechanics. Product defects block release. Coverage gaps,
unsupported environments and inconclusive harness results need a concrete maintainer
disposition, never an implied passing result. Report the limits of the claim.

Dependency discovery/upgrades/profile qualification remain separate deliberate maintenance.
Do not upgrade everything simply because a release is being prepared. Preserve consumed
profile/knowledge data and existing consumer locks. Applicable security failures or missing
required dependency qualification block the affected candidate.

Use release_candidate.py find, then download/verify-promotion --run-id <id> --output
artifacts/<unique> to inspect successful exact-source package CI. Missing/expired artifacts
need an exact candidate run with qualify-candidate.yml; dispatch it only when the user's
scope includes candidate preparation. Never combine partial runs or borrow another source's
packages. Package CI is fast integrity, one archive build, Windows/Linux installed smoke
and applicable security; it does not claim complete behavioral or agent acceptance.

Recommend optional live trials only where actual changes and maintained scenario/oracle
contracts warrant them. A missing scenario is a gap, not a reason to claim acceptance.
Do not ask to run paid work during publication. If the user explicitly selects a trial,
prepare-trial verifies candidate bytes and local prerequisites in a disposable consumer;
each paid phase still requires its exact one-use interactive authorization, model,
worker sandbox and parent checkpoint. No trial run means no AI acceptance claim.

Present the concrete candidate, CI run, package hashes, security freshness and relevant
limitations. Native publication environment approval is the single publication decision,
including acceptance of developer-reported validation. Do not require a signed JSON
assessment or separate assessment workflow. Sole-maintainer self-review is allowed when
the environment is configured accordingly. Never change remote settings as an inferred
prerequisite. Tagging/publication and failed-tag correction require explicit user authority.
A dry verification does not establish public installation or successful publication.
