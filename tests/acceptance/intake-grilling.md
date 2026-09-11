# Interactive intake acceptance

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
| Answer only part of a round. | Answered questions stay settled, unanswered ones stay open, and dependent questions wait. |
| Say "accept all recommendations" with one explicit exception. | Only presented recommendations are adopted, the exception wins, future choices remain open, and intake stays unconfirmed. |
| Resolve the audience as internal employees for the first release. | Applicable technical defaults are recorded for final review; speculative customer/tenant details are excluded or deferred with a named trigger. |
| Later change the first-release audience to include external partner companies. | Affected trust, ownership, and data-isolation assumptions are reopened; unrelated answers are retained with stable evidence IDs. |
| Supply a project document contradicting an earlier answer. | The conflict is surfaced for resolution and neither source silently overrides the other. |
| Require an existing non-Orbyss NuGet dependency, with its actual package ID and purpose. | Consumer ownership is preserved; available compatibility facts are investigated and unknowns assigned without inventing managed coverage. |
| Leave exact form fields and review-screen layout undecided. | Details that can close in a feature specification are deferred there; any boundary-changing uncertainty is still investigated. |
| Pause and resume intake. | The compact record preserves answers, provenance, pending questions, corrections, and dependencies. Confirmed artifacts are not silently overwritten. |
| Review the draft and revise one default. | One synthesis includes defaults and consequences, domain boundaries, founding candidates, and deferrals. The change updates affected evidence before confirmation. |
| Confirm the final synthesis. | Draft validation passed first; the four artifacts validate after confirmation; architecture remains provisional; only the normal-shell handoff command is emitted. |

Run the installed `bootstrap_intake.py validate-draft --json` before confirmation and
`bootstrap_intake.py validate --json` afterward. Record diagnostics and repairs. Check that every
named journey survives, each decision's provenance is accurate, and no unresolved bootstrap blocker
was hidden behind a deferral. Report observed failures, not merely whether prescribed phrases
appeared. A successful conversation can become a reviewed fixture for later regression work.
