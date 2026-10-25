# Preview toolkit replacement

## Re-onboarding from 0.x

1.0.0-preview.1 is the deliberate re-onboarding boundary. Use a clean checkout and follow the current
installation instructions in a normal human terminal. Keep existing application code, architecture,
ADRs, specs/tasks, selected dependencies/locks and historical evidence. Bring useful documents into
the new intake as authored inputs; do not convert old receipts or workflow completion into authority.
The preview updater refuses a 0.x installation before mutation. No consumer or shared source,
customization, live data, workflow run or failed history is deleted automatically.

## Owned preview replacement

Retain both exact tooling archives outside the consumer: the inspected new preview and the previous
preview that owns installed toolkit sources/native outputs. Extract each into its own directory.
From the consumer root, inspect the native replacement plan:

```sh
python <new-tooling>/scripts/upgrade_program_kit.py --release-root <new-tooling> --previous-release-root <old-preview-tooling> --target . --plan
```

Apply the same command without `--plan` after reviewing its result. Native ownership and source/output
customization checks remain mandatory. A refusal names the conflicting owner; preserve the edits and
resolve them explicitly. Do not replace an old witness with installed consumer bytes or suppress a
failed check. Interrupted replacement retains recovery data and restores owned setup as documented
by the updater. Keep its original failure logs.

## Consumer work and verification

A toolkit update preserves authored source/docs, native dependency locks and current product/spec
work. It creates no application migration or architectural acceptance. Review substantive changed
choices in normal ADR/plan/tasks and continue the earliest relevant native Spec Kit phase. Preserve
IDs, checked tasks, unfinished work, failures and actual human review dispositions. Missing toolkit
checkpoint formats or approval hashes do not invalidate useful work.

Run the actual project compiler/analyzers and relevant behavior/security/contract checks for changed
inputs. A toolkit installation pass supplies no application/runtime/provider acceptance. Dependency
upgrades, device software preparation, consumer data changes and external rollout have separate
owners and authority; the updater does not select or execute them implicitly. Optional native
engineering helpers enforce the inputs their selected operation needs.

## Local choices and future previews

Local technology and pattern choices remain available with appropriate contracts and tests. Curated
profiles/generators are conveniences and must state unsupported automation honestly. Do not invent a
consumer qualification ceremony to retain a suitable alternative. Later previews preserve authored
product/specification work; an incompatible change needs an explicit notice and reviewed response.
