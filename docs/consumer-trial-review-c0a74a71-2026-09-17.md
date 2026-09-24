# Consumer trial review: c0a74a71

Candidate: `2d8790530f2aaa4db1aa04cc50b954ac5539beda`, clean source.
Preserved record: `artifacts/intake-sessions/f7b1c0af8cb849f3b1714baf6761f4df`.
Consumer: `C:/Users/Joeyb/AppData/Local/Temp/program-kit-intake-de8utbfo`.
Reviewed interview, eight captured rollouts, workflow events, architecture, roadmap,
prerequisites, generated quality cases and compatibility receipts. No consumer edits,
new agent sessions, installs or compatibility executions were performed in this review.

## Verified outcome

The installed read-only `workflow_lifecycle.py validate-completion` returned
`{"status":"completed","engine_verified":true}`. All 62 native steps started and
completed, with one workflow finish and no failed step or recovery run.

Four source-bound receipts have successful process outcomes and 14 JUnit cases,
with zero failures, errors or skips: Foundation activation 5, BFF/Keycloak 3,
PostgreSQL 5, browser runtime 1. These demonstrate isolated mechanisms, not an
implemented consumer, security certification or actual-device accessibility.

The baseline is INITIALIZED; RM-01 is eligible for specification. Ten owned
planning decisions remain, with executed application/device evidence assigned to
delivery. Future journeys remain Candidate. This is the intended distinction
between finishing bootstrap and finishing the application's design and delivery.

The launcher's `downstream-review-required` is not a workflow failure: the original
intake artifact hashes no longer describe all downstream architecture artifacts.
The run admitted the intake and the current completed baseline validates separately.

## Remaining findings

1. **Avoidable authoring/size retries remain.** Intake initially failed because
   `strategic_model.capability_bindings[10]` lacked the relevant Program Kit
   capability. Research failed at 9,142 and then 8,331 bytes against its 8,192-byte
   limit. Closure failed because the roadmap was 6,146 bytes against 6,144. The
   agent repaired all four within its stages, without changing installed Kit code
   or needing a user repair. Architecture and roadmap producer stages did not
   repeat the previous run's validation failures. Still, a two-byte correction
   loop is poor use of an agent: generation needs headroom and size checks before
   terminal validation, including after downstream roadmap edits.

2. **Historical environment observations remain in current task text.** The closed
   provider/identity/runtime prerequisites still say Docker access is denied in
   the authoring session. Their current closed status and proof receipts are
   correct. `compatibility/closure-review.md` is explicitly a preparation review,
   but says Proposed ADRs await review and no probe was executed. Those statements
   were true at preparation and should be clearly labeled as that stage's snapshot,
   with links to current authority. This is a clarity issue, not contradictory
   executable authority or grounds to invalidate completion.

3. **Context/read efficiency needs further measurement.** All eight captured
   rollouts contain truncated tool output (19 occurrences in total). This is a
   screening signal, not proof each read was unnecessary. Combined with higher
   cached input volume, it warrants reviewing bounded projections and oversized
   reads before increasing instruction content. Do not assume cached reads are
   free or count them as uncached tokens.

A separate Docker registry manifest request timed out. Closure obtained the same
published tag/digest binding through a successful direct registry request. This
was environmental retrieval failure, not a fourth document-size failure or a
failed native compatibility step. Authoring-session Docker restrictions did not
prevent the native executor from running all four proofs successfully.

## Previous fixes observed in the real run

- Planning has explicit decision obligations; application, runtime, web and real
  device verification are explicit delivery compatibility obligations. Planning
  does not require an already implemented application.
- All WEB-Q01 through WEB-Q13 definitions appear in the generated quality-system
  block from quality-attributes, rather than competing authored definitions.
- Roadmap dependencies link ledger IDs instead of repeating obsolete open/closed
  assertions. Current Accepted ADR states appear in the generated lifecycle view.
- The approved runtime is the published Foundation host plus shells.json,
  hostsettings.json, nuplane.settings.json and optional packages in a release
  bundle. Architecture explicitly excludes consumer image builds and host DLLs.
- Architecture names owned semantic contracts, state/conflict behavior, membership
  predicates, provider isolation, permitted project references and planned
  architecture tests. Their implementation remains future work, correctly.

## Interview and slicing

The human accepted a first useful loop of adding needs, marking/undoing bought
items and seeing remaining needs. They explicitly deferred offline and advanced
access; child requests were an example, not a commitment. Defaults for Foundation,
Keycloak and PostgreSQL were disclosed before explicit final confirmation.

RM-01 implements that accepted shared-list loop. RM-02 and RM-03 cover regular
purchases and history; RM-04 is conditional advanced-access discovery. Offline
remains an owned deferred condition rather than an invented committed feature.
There is no evidence here that the fixture forced the entire app into RM-01.

## Token and time comparison

Each metric uses the last cumulative token counter once per unique captured
session. Input includes cache; reasoning tokens are already part of output.

| Metric | Previous 0b330cb1 | Current c0a74a71 |
| --- | ---: | ---: |
| Input including cached | 6,068,243 | 7,248,506 |
| Cached input | 5,448,960 | 6,734,336 |
| Uncached input | 619,283 | 514,170 |
| Output | 77,632 | 71,220 |
| Uncached input + output | 696,915 | 585,390 |
| Total including cached input | 6,145,875 | 7,319,726 |
| Intake uncached input + output | 192,202 | 81,975 |
| Bootstrap uncached input + output | 504,713 | 503,415 |

Uncached input plus output fell 16.0%, almost entirely in intake; bootstrap itself
fell only 0.26%. Total tokens including cached input increased 19.1%. This is not
a controlled experiment or evidence of a 16% bootstrap improvement; answers,
generation choices and the additional browser proof differ.

Native workflow elapsed time was 2h05m31s, including approximately 1h28m49s in
three review steps. Excluding those review steps leaves approximately 36m42s,
which still includes orchestration/tool time and is not pure model compute.
The compatibility executor took 97.9s. Architecture took 12m37s. Launcher lifetime
including intake and human waits was 2h52m52s. Raw elapsed time should not be
treated as agent inefficiency or directly compared without accounting for waits.

## Recommendation

Accept this as a successful bootstrap trial with materially better phase and
quality-case behavior, not evidence that all feature flows are proven. The useful
next functional test is RM-01 specification and planning: ensure the ten planning
items become design work at the right moment, rather than another unnecessary
consumer questionnaire or a demand for delivery evidence. Improve authoring
headroom and historical-status labeling separately; neither requires rewriting
this consumer's accepted baseline.
