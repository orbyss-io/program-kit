# Interactive intake acceptance

From the candidate checkout in a fresh user-owned PowerShell console:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-IntakeSession.ps1
```

The launcher creates a new temporary Git consumer outside this repository, installs all candidate
Program Kit components, asks for a product idea, and opens the installed skill in foreground Codex.
Setup uses a short-lived loopback catalog of the current source packages and the real bundle
installer, then validates installation coherence and removes the temporary catalog registrations.
Use your existing Codex login and configured model, or pass `-Model <model>` explicitly. Normal
model usage applies. No Release receipt is needed and no bootstrap workflow is run. Exit with
`/quit` to save evidence and return to PowerShell. `-KeepWorkspace` retains the live directory;
otherwise it is removed only after a verified full archive and captured conversation on normal
exit. Interrupted/failed sessions or missing history retain the workspace. Abrupt terminal closure
can prevent finalization; the printed evidence directory contains `session.json` with its location.
After confirming Codex has exited, recover/finalize such a run from the candidate checkout with
`python scripts/intake_session.py finish --record <evidence-directory> --exit-code 130`.
This preserves the interrupted workspace as well as its review artifacts.

Evidence lives under `artifacts/intake-sessions/<id>/`: `REVIEW.md`, `session.json`, the readable
conversation and exact matching Codex rollout when available, intake artifacts, validation logs,
and a full `consumer.zip`. Return to the development conversation with the printed `REVIEW.md`
path for evaluation. Local Codex history formats can change; missing history is explicitly reported,
not inferred from the agent's summary. Nothing reads unrelated conversation bodies or copies Codex
authentication/configuration files. These local ignored artifacts may contain private product
information and raw tool output: do not publish them. `-PrepareOnly` exercises installation,
archiving and cleanup without asking questions or launching Codex; it is not interview acceptance.

Run this exercise with a human in a fresh initialized consumer using the candidate Program Kit
extension. Invoke `$speckit-program-kit-governance-bootstrap`. This evaluates the conversation
before any full bootstrap workflow run; it does not launch a paid acceptance phase or simulate
human confirmation. Installation/contract tests are supporting evidence, not proof of interview
quality. Record the candidate commit, integration, transcript location, and artifact paths.

Start with a real product idea. For a repeatable example:

> I want an internal workspace where employees fill in configurable request forms and a responsible
> colleague reviews them. We use .NET and React. I have not decided whether outside customers will
> eventually use it. I want to reuse Program Kit where it fits.

Use these interventions when relevant questions arise; do not dictate the agent's question order
or desired architecture. A reviewer should assess the resulting conversation and artifacts.

| Intervention | Observable acceptance evidence |
| --- | --- |
| Give only the initial idea. | Intake uses Program Kit grilling's numbered rounds and recommendations. It clarifies consequential product ambiguity and does not ask the user to reselect obvious managed tooling. |
| Describe a solution without explaining its purpose. | It establishes the business problem and observable success before dependent solution/lifecycle recommendations. It does not repeat already supplied purpose. |
| Use a role name that could mean buyer, intermediary or supplier, with an ambiguous core operation. | It establishes input provider, result user and expected outcome before dependent policies; a relevant worked example may clarify this. Already clear roles do not trigger a canned questionnaire. |
| Accept a recommendation that depends on an unknown condition. | The conditional policy is accepted, but its premise stays unknown until supported. Language fallback, existing providers, and planning estimates do not become organizational facts merely through blanket acceptance. |
| Answer only part of a round. | Answered questions stay settled, unanswered ones stay open, and dependent questions wait. |
| Say "accept all recommendations" with one explicit exception. | Only presented recommendations are adopted, the exception wins, future choices remain open, and intake stays unconfirmed. |
| Resolve the audience as internal employees for the first release. | Applicable technical defaults are recorded for final review; speculative customer/tenant details are excluded or deferred with a named trigger. |
| Later change the first-release audience to include external partner companies. | Affected trust, ownership, and data-isolation assumptions are reopened; unrelated answers are retained with stable evidence IDs. |
| Correct a central assumption, then settle its dependent rules. | The final current summary and affected Q&A rows agree; obsolete interpretations are explicitly superseded and resolved questions no longer appear open. Evidence IDs survive consolidation. |
| Include a compound requirement such as importing/exporting workbooks. | Each operation has an actor/trigger, relevant data and observable outcome in a journey/step, or a visible disposition. A capability label alone is not treated as coverage. |
| Supply a project document contradicting an earlier answer. | The conflict is surfaced for resolution and neither source silently overrides the other. |
| Require an existing non-Orbyss NuGet dependency, with its actual package ID and purpose. | Consumer ownership is preserved; available compatibility facts are investigated and unknowns assigned without inventing managed coverage. |
| Leave exact form fields and review-screen layout undecided. | Details that can close in a feature specification are deferred there; any boundary-changing uncertainty is still investigated. |
| Pause and resume intake. | The compact record preserves answers, provenance, pending questions, corrections, and dependencies. Confirmed artifacts are not silently overwritten. |
| Review the draft and revise one default. | One synthesis includes defaults and consequences, domain boundaries, founding candidates, and deferrals. The change updates affected evidence before confirmation. |
| Confirm the final synthesis. | Draft validation passed first; the four artifacts validate after confirmation; architecture remains provisional; only the normal-shell handoff command is emitted. |
| Review an editing journey backed only by a read-only cross-context contract. | The discrepancy is surfaced and resolved or explicitly recorded as unresolved. Schema validity alone is not accepted as semantic completeness. |

Run the installed `bootstrap_intake.py validate-draft --json` before confirmation and
`bootstrap_intake.py validate --json` afterward. Record diagnostics and repairs. Check that every
named journey survives, each decision's provenance is accurate, and no unresolved bootstrap blocker
was hidden behind a deferral. Report observed failures, not merely whether prescribed phrases
appeared. A successful conversation can become a reviewed fixture for later regression work.

## Deterministic authoring regression

The authoring helper and its worked example are exercised by `tests/validate_intake_authoring.py`.
To replay a preserved interview's final draft without any coding agent or edits to the evidence:

```powershell
python tests/validate_intake_authoring.py --session-evidence artifacts/intake-sessions/<id>
```

This checks regeneration and preservation of strategic decisions and source journeys in a temporary
consumer. It does not repair the user's architectural decisions or prove better interview behavior.
Raw private conversations stay in ignored session evidence, not committed fixtures.

## Efficiency review

Preserve relevant questioning and assess discovery quality with the human; fewer questions or a
shorter conversation do not prove improvement. Separately report agent-active time (including
tools), user waiting time, last-answer-to-review synthesis time, tool calls, validation repairs and
reported token usage. Exclude terminal idle time after the final answer. Note changed scope and
corrections before comparing runs. Cached input volume is not unique input or a monetary cost.
Inspect whether targeted descriptions replace bulk/truncated schema reads, diagnostics repair
multiple authoring problems together, and ledger edits avoid repeated competing narratives.
