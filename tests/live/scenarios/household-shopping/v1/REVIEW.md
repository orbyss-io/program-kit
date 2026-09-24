# Independent review — do not feed this rubric to the producer

This tests vision-to-roadmap discovery, then one selected journey through delivery.
It does not test whether the producer reproduces a supplied design. There is no
prewritten architecture, reference implementation, endpoint contract or fixed entry ID.
The one-slice execution budget belongs to the trial runner, not to the product vision.

## Intake and roadmap quality

Review the first proposed synthesis before reviewing any coached correction. Retain
the conversation evidence for both. Mark each conclusion pass, fail or inconclusive,
with a source location and reason; file existence or schema validity is not enough.

1. The interview establishes actors, problems, independently observable outcomes,
   boundaries and meaningful uncertainty without requiring the customer to design
   technical internals. Proposed defaults are distinguished from confirmed facts.
2. Every discovered journey has a disposition: a deliverable slice, a supporting
   acceptance scenario of another slice, an explicitly deferred outcome, or an
   excluded outcome with a reason. No future journey silently disappears.
3. The roadmap presents multiple independently useful increments, including future
   slices. A first entry covering the whole product fails this case. Do not demand
   one entry for every click, failure path, retry, screen or technical layer. Grouping
   independent outcomes needs a convincing explanation and a smaller alternative.
4. The first proposed increment has an actor, trigger, observable result, practical
   way to try it, and honest manual handoffs for later work. It does not secretly
   depend on implementing all the deferred outcomes first. Shared foundations are
   proportional to what it needs now.
5. Future entries describe their user value, scope boundaries, dependencies, sequence
   rationale, open decisions and the point at which those decisions become necessary.
   They are a credible roadmap, not fully elaborated specifications or placeholder
   headings. "Not implemented yet" alone does not make a slice Blocked.
6. Program Kit selects and applies relevant existing knowledge without the scenario
   naming engineering solutions. Use evidence from context routing, decisions,
   obligations and resulting artifacts. A declared profile alone is not enforcement.

Use `tests/review_discovery_roadmap.py` to extract actual journey/candidate/roadmap
identities into a separate reviewer worksheet. It records evidence, not a score or
approval. Complete the dispositions and choose the first entry after inspecting the
artifacts and conversation. Never rename entries to RM01 to accommodate an old harness.

## First selected journey

After valid bootstrap completion, the human chooses one actual Ready entry. Its
feature intake refines the exact brief through the installed grilling gate. Before
implementation, review and freeze its observable acceptance scenarios, scope and
relevant failure cases from that confirmed brief. Use the actual chosen identities
and interfaces; do not graft the lending HTTP/browser oracle onto this product.

The independent acceptance plan must be reviewable before code exists. The evaluator
may keep scoring criteria private, but no undisclosed business behavior may become a
surprise delivery requirement. Publish approved behavior to the normal feature brief;
keep test implementation independent from the feature implementation. Bind any later
scope/test change to an explicit reviewed amendment, not a post-hoc weaker oracle.

Run the installed full feature flow and its applicable hooks/gates: specification,
clarification when needed, plan, tasks, analysis/implementation, tests and delivery
verification. Verify the normal user path and meaningful failures through the actual
application. Check applicable architecture, security, persistence, contract and UI
obligations from the selected design, not a universal checklist of unneeded technology.
Inspect the resulting source/delivery evidence for unrequested later journeys.
Future roadmap entries must retain accurate status; they are not delivered because
the first feature created a shared component. Stop after this one accepted slice.

## Efficiency and result validity

Reuse `live.v2.learning_metrics` and the existing learning-report evidence format.
Record intake, each bootstrap stage, each feature stage, deterministic tooling,
human reviews, failures and repairs separately. Preserve model/settings, candidate
commit and installed hashes, exact input/approval hashes and complete available logs.
Never count a repaired run as a clean first-pass success.

Report total input/output tokens, cached input separately as a subset, wall time,
and evidence-backed productive work, necessary investigation, avoidable rework,
unnecessary reading, external wait and unknown time. Missing usage stays unknown.
Compare first-pass and cumulative repaired costs. Evaluate whether questions and
source reads resolved material uncertainty; short output alone is not efficiency.

The two products and delivered scopes differ. Report absolute stage costs and the
scope/complexity differences; do not advertise a percentage efficiency improvement
from their raw token totals. A valid later controlled comparison needs matched scope,
toolchain/model/settings, comparable starting state and a disclosed cache policy.
Wait for the current run's full analysis before freezing the next candidate and
criteria. If the new run is coached or repaired, retain that outcome and distinguish
it from what Program Kit achieved independently.
