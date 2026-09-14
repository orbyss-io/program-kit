---
description: Run an explicitly requested, non-authorizing proxy intake rehearsal with simulated consumer answers; stop before bootstrap. Use for proxy rehearsals, not ordinary intake or paid live acceptance.
---

## Scope

This optional tool requires an explicit request such as "do a non-authorizing proxy intake" or
"answer as the fictional consumer and stop before bootstrap". That request authorizes the rehearsal
and its draft artifacts within the stated scope; no further permission round is needed for those
actions. Use the current session as interviewer and disclosed fictional consumer proxy. Do not
start another coding-agent session or paid live harness, confirm intake, ratify, implement or release.
An independent automated worker remains a separate live-acceptance request.

Default to one question round for a quick scan. Use full intake when explicitly requested, stopping
at a validated draft awaiting real-user review. Say which mode is being exercised. This can test
installation, authoring tools, validation and visible reasoning. It cannot prove independent agent
behavior, complete bootstrap success or live token savings.

## Disposable setup

Use the supplied fictional idea, not a previous consumer's architecture or expected answers. From a
Program Kit source checkout, run `scripts/Start-IntakeSession.ps1 -PrepareOnly -KeepWorkspace
-IdeaFile <actual-scenario-path>` with the actual scenario path substituted. Read its returned
session record for the disposable workspace. PrepareOnly starts no coding agent. An already
prepared disposable consumer may be used only before intake authoring. If this setup capability
is unavailable, report that limitation; do not replace a real consumer.

Before authoring, run from the disposable consumer root:

`python .specify/extensions/program-kit-governance/scripts/proxy_intake.py begin --scope one-round`

For requested full intake use `--scope full-intake`. This binds the scenario and records that
simulated answers have no authority. Never remove the marker or promote proxy output to confirmed
status. A real human intake must occur separately.

## Rehearse and report

Follow the installed bootstrap front-door skill and its shipped grilling/default/authoring
references. This mode replaces human answers with visibly simulated ones and stops before the
front door's confirmation and bootstrap handoff. Do not replace its schemas or questioning method.
Keep proxy assumptions separate from supplied facts and actual user instructions. In structured
choices, use derived-choice provenance with evidence explicitly naming the simulated source;
never record a proxy assumption as actual human acceptance.

Write `docs/architecture/proxy-intake-transcript.md` with this exact notice:

`PROXY_REHEARSAL: simulated answers; no user confirmation or authorization.`

Record every round's question, recommendation, rationale, simulated answer and disposition.
Preserve corrections and validation failures. Use applicable defaults without inventing constraints,
providers, production permission or budgets. If a necessary fact cannot reasonably be simulated,
report the limitation rather than manufacture authority. Do not copy expected answers from private
acceptance fixtures or claim the proxy is an independent evaluator.

For one round, stop after the transcript. For full intake, author the normal project-intent record,
authoring source, map, DSL and draft intake with `intake_authoring.py build-draft`, from the consumer
root with a repository-relative source path. Include the proxy notice in the intent record too.
Use the descriptor for unfamiliar nested shapes, including boundary challenges. Perform the
semantic coverage review, including write operations and authentication-before-access ordering;
schema validity is not enough. Do not create a specification roadmap or implement features here.

Run `python .specify/extensions/program-kit-governance/scripts/proxy_intake.py verify`. Report its
result, questions/answers, draft synthesis, failures/repairs and limits in plain language. Report only
measured token usage if available; never estimate it from file bytes or cached volume.
Stop. Do not provide a bootstrap launch command for this unconfirmed proxy draft.

If the user subsequently requests a same-session bootstrap rehearsal, use the separate installed
`speckit.program-kit-governance.proxy-bootstrap` command. That explicit scope extension preserves
the draft and provenance marker; it does not enable ordinary bootstrap or a paid live worker.
