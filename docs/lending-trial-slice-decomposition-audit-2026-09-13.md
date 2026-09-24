# Lending trial slice decomposition audit

The fixture prescribed one combined slice before intake. This trial therefore
does not demonstrate independent discovery of specification boundaries.
No consumer scope, roadmap, approval or trial contract is changed by this audit.

## Verified causal chain

1. `tests/live/scenarios/knowledge-application/v1/PROJECT_REQUEST.md:3-8`
   explicitly requests "deliver one vertical slice" covering reserve, confirm and
   cancel, and assigns RM01 the entire lifecycle and public V1 contract.
2. `artifacts/intake-sessions/bccfa7c91aed47b7bfac7caccc801aed/session.json`
   identifies that exact idea file, source commit
   `274c97609002001c12e98eac79fc10fc16b0ff0c`, and consumer workspace
   `C:/Users/Joeyb/AppData/Local/Temp/program-kit-intake-3yd5a74k`.
   Source file and the consumer's `product-idea.md` both match its recorded SHA-256
   `f28dc4f753f1cb8a381dcc7998f0e0ced8f4ff8b1969a5c86b58e6f88094a81e`.
   This was actual input, not merely an unused fixture found elsewhere.
3. Consumer `docs/architecture/project-intent.md` records q1-q4 about trust,
   notification meaning/delivery, cancellation and terminal states. It records
   q5 confirmation of the complete synthesis. It does not record an explicit
   comparison of one specification versus multiple specifications. This is the
   retained question ledger, not a claim to have independently replayed the raw
   conversation transcript.
4. Consumer `docs/architecture/intake-authoring.json` retains eight journeys but
   proposes one `slice-rm01`; its outcome explicitly makes J02-J07 acceptance paths
   of that slice. Evidence includes e01, the supplied product idea.
5. The saved roadmap stage brief at
   `.specify/workflows/runs/ef606c1a/program-kit-context/roadmap.json` passes that
   same one-slice statement through `intake.candidate_slice_signals` and the
   project summary. Thus the roadmap producer received the grouping as confirmed
   upstream context. The final roadmap says J01-J07 form one confirmed slice.

## Reinforcing fixture assumptions, not proven additional causes

`tests/live/scenarios/knowledge-application/v1/acceptance.json` names RM01 as the
current entry and RM02 as future. `tests/live/v2/sync_stages.py` hard-codes RM01
intake, planning, delivery and confirmation paths. The reference identity contract
also binds one RM01 specification. These constrain later automated trial phases;
there is no evidence these harness files were read by the interactive intake agent.
The copied idea alone is sufficient direct evidence of the input constraint.

The idea also supplies implementation guidance explicitly: framework-free Core,
typed outcomes, persistence behind a capability, operation-local folders, thin
IWebShellFeature composition and named Forms/Foundation mechanisms. Acceptance
can test whether those requirements were implemented correctly, but this input
cannot establish that Program Kit independently discovered and applied all that
knowledge. This is a second limitation of using the same fixture to assess both
guided integration and autonomous knowledge selection.

The pre-authored bootstrap seed also contains one complete reservation candidate,
but this interactive session's launch evidence binds the idea and acceptance
contracts. It does not justify claiming the seed architecture caused this result.

## Program Kit enforcement gap

The shipped roadmap command already says: "Start with one roadmap entry per
normalized user-visible journey unless accepted architecture requires a split."
It does not clearly describe a reviewed exception for grouping several journeys.

`architecture_map.py` validates that each candidate slice references an existing
journey and separately preserves journey-to-dynamic-view coverage. It does not
require a disposition from every journey to a roadmap entry or an explicit merge
rationale. `governance_state.py::validate_roadmap` checks record fields, statuses,
ADR/prerequisite eligibility and delivered evidence, not decomposition coverage.
Consequently the eight-journey/one-candidate model and one-entry roadmap passed.
Passing these validators is not evidence that the chosen specification size was
independently evaluated.

## Conclusions and proposed corrections

- Proven: fixture wording prescribed the grouping; upstream intake and roadmap
  retained it. This is not evidence that Program Kit always chooses one large spec.
- Strong inference: prescribed feature identity, scope and later harness routing
  reduced the opportunity to discover alternative delivery boundaries.
- Not established: which decomposition an unconstrained intake would produce.
  That requires a revised trial; no paid rerun was started for this investigation.
- Keep the real behavioural acceptance requirements, but remove fixed spec count
  and scope grouping from a discovery fixture. Ask for the product roadmap, then
  execute only its first reviewed slice. One slice executed does not require one
  slice in the whole roadmap.
- Review reserve, confirm and cancel as possible separate user-outcome slices,
  with dependencies and durable guarantees retained. One business context can own
  several specifications; context boundaries do not fix delivery increments.
- Do not mechanically turn restart, replay and recovery checks into separate
  features. They may be acceptance obligations of each affected operation. Forms
  publication may likewise support the first usable slice rather than constitute
  an independent user-facing product feature.
- Extend the existing intake/roadmap mapping and review to distinguish deliverable
  outcomes, supporting acceptance scenarios and deferred journeys. Require an
  explicit rationale for grouping independent outcomes, and preserve coverage.
  Avoid adding a parallel instruction system.
- Adapt the live harness to the reviewed entry IDs and scoped acceptance obligations
  instead of silently routing every operation through a hard-coded RM01 spec.

These are recommendations for review. The current trial remains useful evidence
about integration, proof admission and workflow defects, with the decomposition
limitation recorded explicitly.
