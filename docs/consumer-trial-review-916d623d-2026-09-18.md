# Human consumer trial review: 916d623d

## Verdict

The bootstrap is validly completed and materially better than the preceding trial.
Independent installed `workflow_lifecycle.py validate-completion --run-id 916d623d`
returned `completed`, `engine_verified: true`. It is an initialized, reviewed baseline,
with RM-01 eligible for specification. It is not implementation or production approval.
No consumer files were edited, workflow resumed, coding agent launched or proof rerun
for this review.

Source candidate: `4b38537dbd23040c244f608e22e888b5fdb706b4`, clean at setup.
Consumer: `C:/Users/Joeyb/AppData/Local/Temp/program-kit-intake-amyob308`.
Captured evidence: `artifacts/intake-sessions/32a2fdbbd9f4404fb5446dd056d1360e`.
Comparison: prior run `76d8b67f`, reviewed separately.

## Findings, in priority order

### P2: free-form language routing still misclassifies a managed default

The confirmed intake uses `routing.languages: ["C# (.NET managed default)"]`.
The assessment context consequently claims an explicit alternate-language constraint,
omits dotnet from resolved profiles and invents `consumer-authentication-integration`.
The agent identifies and corrects this contradiction in its assessment/backlog before
review. The final approved register correctly selects dotnet and managed Foundation.

Root: `bootstrap_defaults.py:37,53-56` case-folds free text and subtracts an exact
allowlist containing `c#`, but not the annotated value. The same installed resolver,
called read-only with the actual intake and an empty register, returns browser/UI
profiles only. Replacing the language with `C#` in memory adds dotnet. This reproduces
the discrepancy without changing the consumer or relying on model interpretation.

Recommendation: give language identity and provenance a canonical representation at
intake/default-resolution boundaries, retaining explanation separately. Support
recognized legacy spellings deliberately; preserve genuine alternate stacks and
mixed-stack constraints. Validate that managed capability dependencies and language
constraints agree before creating the assessment brief. Do not rely on another agent
noticing the contradiction, or fix only this exact annotated string.

### P2: large aggregated reads still lose context

Seven tool-output truncation occurrences appear across five sessions: research (1),
constitution (2), architecture (1), roadmap (1), closure (2). The preceding run had 12
occurrences across six sessions. These are outputs actually shown truncated, not every
mention of truncation inside source code.

Examples: constitution rereads intake/assessment/decisions in combined large commands;
architecture prints the selection schema and entire map together; closure prints the
whole evidence JSON; independent required reference reads are aggregated beyond the
outer output budget. Brief paging alone does not protect these other reads.

Recommendation: extend bounded reading to the constitution path and evidence JSON;
project needed fields, page genuinely required full references, and cap aggregate
output as well as each nested command. This is an efficiency/reliability improvement,
not evidence that a specific final requirement was lost in this run.

### P3: generated-view sizing works, but roadmap newline accounting is inconsistent

The intended fix worked: final architecture has 10,205 authored + 2,039 generated =
12,244 physical bytes, and final quality-system has 5,415 authored + 3,201 generated =
8,616 bytes. Both exceed the former whole-file caps while their authored portions pass.
Complete generated quality cases and lifecycle/navigation remain present.

Ordinary prose overproduction persists. Architecture shortened quality-attributes
from 6,394 to 4,873 bytes. Roadmap started at 6,392 bytes; an intermediate terminal
check failed at 6,147, three bytes over the 6,144 maximum, before passing at 6,076.
These were local agent corrections, not failed native workflow steps.

The final roadmap is now 6,154 bytes: 78 CRLF line endings account exactly for the
78-byte increase from the validated 6,076-byte LF version. The proof executor
`bootstrap_proof_plan.py:175-194` reads and writes the roadmap unconditionally with
platform-default newline translation, even though `readyWhenProven` is empty here.
Final narrative sizing covers architecture, traceability and quality-system, not
the roadmap. Consequently completion accepts a roadmap 10 physical bytes above its
declared hard budget. Approval hashes correctly bind the resulting final bytes;
this is a size-contract inconsistency, not unapproved semantic change.

Recommendation: avoid no-op rewrites, preserve or explicitly standardize newline
serialization, and test final roadmap accounting across the proof/acceptance path.
Do not solve this by introducing another late consumer-facing failure. Generated
synchronization should preserve the authoring contract deterministically. Near-limit
prose (architecture has 35 bytes of final headroom) also remains needlessly brittle.

### P3: intake authoring still needs avoidable repair passes

The intake author encountered three rejected drafts: invalid contract kind `capability`
(the enum requires `synchronous-capability` or another listed kind), duplicate ID
`household-membership`, and an open item without its `blocks` value. They were repaired
before confirmation/admission. An assessment search also returned exit 1; it was not
a failed governance validation. Keep these distinct from product/workflow failure.

Recommendation: use the existing authoring contract to expose enum choices and ID
namespaces before synthesis and aggregate independent diagnostics where safe. Do not
add another broad instruction document or weaken semantic validation.

## Integrity and evidence

- Native log: 62 step starts, 62 completions, one successful workflow finish; no
  failed-step or recovery events.
- Assessment approval: seven bound artifact hashes match current files. Bootstrap
  approval: all 26 bound artifact hashes match. Both record interactive review.
- Three source-bound compatibility receipts close managed-runtime, managed-identity
  and managed-persistence. JUnit files and preserved stdout/stderr hashes were checked
  independently; 13 test cases, zero failures, errors or skips.
- Foundation: five cases cover compiled boundaries, exact-image activation,
  registration/replacement, HTTP/header/OpenAPI behavior and bundle restart.
- Identity: three cases cover pinned discovery, published BFF activation, and real
  code-flow/permission negatives/logout. The approved provider is again `Keycloak`;
  the exact Keycloak 26.7.3 digest reaches the recipe this time. Thus the spelling fix
  is exercised by real evidence, not only its unit test.
- PostgreSQL: five cases cover exact server, write/read, expected-revision conflict,
  rollback and retained-state restart.
- Identity evidence records matching managed .NET/Node/npm versions and locked NuGet
  and npm restoration. Mechanism fixtures do not certify future consumer code.

The launcher says `downstream-review-required`, with an original intake artifact hash
check failing for architecture-map.json. The admitted native run independently
validated intake before architecture legitimately evolved that map. Current-stage
completion validates. This launcher message is not a new failed bootstrap or grounds
to reconfirm an obsolete intake snapshot.

## Product and architecture quality

The interview explicitly covered responsive/online access, equal-parent permissions,
basket pickup rather than payment, undo, concurrent physical pickup limitations, an
ongoing list and retained purchase records. The user accepted those recommendations,
then separately confirmed the synthesized intake. Defaults were disclosed. Offline
and child roles were explicitly deferred; regular shortcuts and history browsing
remain future work. Fields, duplicate handling and timing were deliberately left for
the first feature. No new product answers were supplied during this review.

RM-01 combines access/add/shop/remaining/clear as the useful ongoing-list outcome the
user accepted. RM-02 through RM-05 separately cover regular-item reuse, history,
offline access and child requests. It is broader than one isolated operation, but
does not implement the entire envisioned application. This grouping is defensible
from the interview; one spec per operation would not automatically be better slicing.

One bounded context owns shopping lifecycle and household access, with a private
PostgreSQL implementation and API/composition adapter. Consumer ports do not expose
DbContext/IQueryable. Planned architecture tests cover project/package/assembly and
runtime edges. Semantic lifecycle, atomic changes, undo/history correction, request
identity, membership checks and conditional integration-event/outbox obligations are
explicit. Exact conflict/locking/retry policy remains owned feature work, not a
claimed implementation. Core is a role of the semantic project, not a mandatory suffix.

The release contract is correct: published Foundation image plus settings/Nuplane/
optional-package bundle; no consumer host DLL, Dockerfile or derived image. Public
metadata, browser tokens, provider permissions and household resource authorization
have distinct owners. Actual consumer authorization, device/accessibility, bundle,
data and recovery tests remain delivery/production obligations.

Research still uses combined 'architecture/closure must prove' wording for future
mark/undo/clear behavior. Founding ADRs explicitly refine it into mechanism proofs
now and consumer tests later, preserving the approved source rather than editing it.
That is valid authority handling, but phase-specific research wording would avoid
this recurring explanatory work.

Fifteen prerequisite entries remain: five closed, ten open. RM-01 is specification
eligible; feature-policy and verification-plan must resolve for dependent planning/
implementation. Delivery, redistribution and production gates remain. Four future
slices still need their own journey discovery. This matches initialization with owned
unknowns rather than failing bootstrap until the application is fully designed.

## Efficiency comparison

Metrics sum the final token counter per captured session; reasoning output is already
part of output and is not added again. These are usage measures, not a monetary bill.

| Measure | Previous 76d8b67f | Current 916d623d | Change |
| --- | ---: | ---: | ---: |
| Uncached input + output, whole trial | 558,762 | 517,701 | -7.35% |
| Uncached input + output, bootstrap | 466,821 | 430,286 | -7.83% |
| Intake, same measure | 91,941 | 87,415 | -4.92% |
| All input including cache + output | 7,382,442 | 6,187,845 | -16.18% |
| Output tokens | 88,012 | 63,746 | -27.57% |
| Native bootstrap elapsed | 49m06s | 36m53s | about -25% |
| Native elapsed excluding review steps | 43m48s | 31m58s | about -27% |
| Truncated tool outputs | 12 | 7 | fewer, not eliminated |

Current input: 6,124,099, including 5,670,144 cached (453,955 uncached). Architecture
took 9m51s, assessment 4m46s, closure authoring 4m23s, roadmap 3m05s and actual proof
execution 1m32s. Review steps account for about 4m55s. Human waiting and variable
agent behavior prevent treating elapsed time as pure compute or attributing all
improvement to the two fixes. The prior run had 11 cases including a standalone
browser-runtime case but no real identity proof; current coverage differs, so raw
case counts alone are not a controlled quality comparison.

## Recommended next step

Preserve this valid consumer and use it for the first specification/plan/implementation
journey when authorized. That is the missing test of actual knowledge application.
Repair the language identity boundary and newline/size inconsistency with targeted
regressions; improve bounded reads using these observed commands. Another complete
human bootstrap is not needed merely to establish that the current baseline is valid.
The remaining small repairs and a future fresh regression trial can proceed separately
from this consumer's product work. No repository implementation changes are made by
this review.
