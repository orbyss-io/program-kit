# Household Shopping: vision-first intake and one journey delivered

Status: prepared discovery input; no intake, bootstrap or paid trial has run.

The consumer receives only `PROJECT_REQUEST.md`, a short ordinary product vision.
`fixture.json`, `OPERATOR.md` and `REVIEW.md` remain with the trial owner. No acceptance
folder, prepared map/intake, package pins, endpoint names, architecture pattern,
feature ID or complete-app first-slice boundary is supplied to the consumer.

The installed intake and bootstrap processes must discover and review the roadmap.
Only after bootstrap do we choose its first suitable Ready entry and execute that
entry's complete Spec Kit flow. Future journeys stay represented in the roadmap.
Keep the current lending trial and its evidence unchanged; this is a separate case.

## Before starting

Finish analysing the ongoing run, apply any accepted product corrections, then freeze
and record the next candidate and model/settings. Review the operator notes and
independent rubric now. Use the ordinary supported environment preflight and installed
technology-selection mechanisms; resolve any selected tool's availability before its
paid dependent phase. Do not copy old lending decisions into the new consumer.

From a normal user-owned terminal at the candidate repository root, the eventual
intake command is:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-IntakeSession.ps1 -KeepWorkspace -IdeaFile tests\live\scenarios\household-shopping\v1\PROJECT_REQUEST.md
```

Do not pass `-AcceptanceContracts` or copy this entire scenario directory. The
launcher installs normal Program Kit components, copies the vision as product-idea.md,
and conducts only the human interview. Exit after the confirmed intake handoff so it
can preserve the original evidence. Follow that handoff to start the native bootstrap
in the resulting workspace, and follow its human review gates to actual engine
completion. Do not mistake intake completion or READY alone for bootstrap completion.

The same command with `-PrepareOnly` starts no coding agent and can check installation
and input isolation. Its retained workspace is setup evidence, not a completed intake.

## Roadmap review and first feature

After bootstrap, extract a reviewer worksheet outside the consumer:

```powershell
python tests/review_discovery_roadmap.py --project <new-consumer-directory> --output artifacts/household-shopping-roadmap-review.json
```

Review the actual proposed entries and journey dispositions with the human, following
REVIEW.md. Do not prefill a successful evaluation or a selected entry before discovery.
If the roadmap is poor, preserve that first result and record the correction rather
than silently coaching it into a pass.

In the selected consumer, request the installed Spec Kit flow for the exact reviewed
Ready entry and its outcome. The normal mandatory specification-intake hook owns
grilling and exact-brief confirmation; bootstrap approval is not that confirmation.
Complete all applicable feature stages and independently verify the approved outcome.
The entry's actual ID owns its artifacts and gates. Stop after this one slice.

The older `fresh-candidate` automated sync harness and `Confirm-LiveFeatureIntake.ps1`
currently bind RM01 and the lending contracts. Do not use them for this case. This
prepared scenario uses the human-owned native flow from intake through first delivery.
It is not yet a sealed automated live-acceptance v2 fixture or receipt: that format
requires real confirmed intake and its provenance, which do not exist before interview.
Any future automated adapter needs separate review and exact phase authorization.

After first delivery, preserve the complete learning evidence and score discovery,
roadmap quality, delivered scope, tokens and work classification separately. Upgrade
testing remains a separate case and is not silently added to the one-journey budget.
