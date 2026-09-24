# Fresh Household Shopping trial — restart guide

Start a new terminal. The following command works in either PowerShell or CMD,
from any folder:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Code\Orbyss\_ProgramKit\artifacts\repository-sync-coordinator\scripts\Start-IntakeSession.ps1" -KeepWorkspace -IdeaFile "C:\Code\Orbyss\_ProgramKit\artifacts\repository-sync-coordinator\tests\live\scenarios\household-shopping\v1\PROJECT_REQUEST.md"
```

It creates a new isolated consumer and installs the current corrected candidate.
Do not reuse the discarded Repair Desk workspace or the PrepareOnly workspace.
The Household Shopping attempt in `program-kit-intake-nh09io7h` (run `fbf1521e`)
is also historical evidence. Restart intake using the command above after the managed-profile
routing repair; do not resume or patch that attempt's approved assessment.
No specific working folder, acceptance contract folder or preselected slice is needed.

Imagine you and your partner keeping a grocery list. Answer the interview in ordinary
language; ask for an example when a question is confusing. You do not need to design
the software. There is no Zendesk, employer, repair service or supermarket integration
in this case. The starting idea leaves the first useful journey and roadmap for the
interview to discover. Optional operator notes are at
`tests/live/scenarios/household-shopping/v1/OPERATOR.md`; do not paste them into intake.

Finish and confirm the intake, then quit with `/quit` so the launcher preserves it.
Follow the installed handoff to run bootstrap from the newly created consumer folder.
Complete its normal reviews. After engine-verified bootstrap completion, review the
roadmap, choose one useful Ready journey, confirm its feature brief, and run that
entry's full Spec Kit flow. Future journeys stay on the roadmap. The intake launcher
never starts bootstrap automatically.

## Earlier trials

The older Camera Reservation trial and interrupted Repair Desk attempt are retained
only as historical learning. Do not resume their agents, workflows or feature work.
The maintainer report records their defects, repairs and remaining design issues;
none of those older consumers is the next live acceptance target.
