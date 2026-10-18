# F3 implementation checkpoint — 18 October 2026

Status: F3 approved on 18 October 2026. The human accepted the checkpoint, authorized
committing it and requested a prompt for F4 in a fresh session. F1 and F2 remain approved.
The human accepted all four F3 recommendations and confirmed shared understanding
before implementation. Stop here; F4 is not started. Review material remains retained.

Worktree: `artifacts/coding-system-f1`, branch `codex/coding-system-f1`.
Starting commit: `412ff210dbd02c2f01c69b51cd631fc3dd4249a8`.
Implementation base: `fc402ef784c025caced1770cd12f64af1a0bdf45`.
The human authorized committing the F3 changes after checkpoint approval. The shared dirty maintenance checkout,
prior F1/F2 reviews, consumer histories, failures and budget disclosures are preserved.

## Investigation, decisions and delivered route

Investigation found F2's `codingUnits`, canonical resolver, context slots and
`prepare`/`reconcile`/completion path already supplied the required composition seam.
Local patterns were linked-only. Native verification already supplied current
input/toolchain/configuration/coverage evaluation; named toolkit checks supplied
actual command exits, retained streams, input fingerprints and unresolved failures.
Those owners are reused rather than introducing a second selector or execution runner.

The agreed decisions are recorded in the plan's F3 section. The versioned contract
is executable in `coding_patterns.py:validate`; [coding patterns](../coding-patterns.md)
documents authoring and actual command use.

- Shared and consumer-owned units use one composer and canonical source resolver.
  One local authored document extends source/rule/unit declarations without shadowing
  existing owners. Pattern metadata references invariants, examples, checks, review,
  recipes/context, provenance, exact compatibility and limits; it does not copy policy.
- Draft assistance accepts prose/code by reference and prepares a single editable
  contribution with missing-proof guidance. It cannot dispatch supplied code or check
  commands, register a draft automatically or promote private source upstream.
- The existing plan records exact contextual choices. Output separates precedence,
  suitability and qualification. A compatible single qualified pattern is available
  automatically; explicit replacement/alternative choices do not waive mandatory duties.
  Ambiguity, invariant weakening, unsupported fields and wrong versions diagnose owners.
- Evidence references ordinary review and current native/named-check results. Native
  qualification uses the current verification plan, not merely a completed flag.
  Pattern/rule/code/examples/review/profile and adapter changes invalidate scoped proof.
  Earlier evidence remains history; identical successful reruns can preserve intact
  earlier proof, while subsequent unresolved failures block reuse. Binding appends
  records and supplies no approval or authenticated-reviewer authority.
- F1's pending F3 producer migrations now resolve canonical phase, provider-binding,
  source-file and exact selected Foundation guidance. Native declaration/capture/API
  detection remains in its existing owner. The native source-quality observer imports
  no governance. Existing independent native and private-hosting negatives remain.
- A blocked completion response now includes its retained checkpoint while preserving
  needs-attention, blockers and task bytes. This repairs a progress-reporting omission
  exposed by the prepared task check; it supplies no source-readiness waiver.

## Review and reproduction

Run `python tests/pattern_review_fixture.py --review` and open its printed unique
`artifacts/f3-review/<run>/index.md`. The guide links actual outputs, declarations,
ordinary plan choice, shared/private/contextual selections, later-task use,
independent browser exclusion, actual independent positive/invalid checks,
stale/incompatible/retired cases, progress preservation and canonical before/after
snapshots. Commands, exits, both stream hashes, timings, source commit, full working
input digest and fixture hash are retained. Another run preserves previous output.

Start with the [final retained guided review](../../artifacts/f3-review/20261017T223242Z-3eec29/index.md).
All 33 actual command invocations matched their expected exits, including 13 deliberate
negative exits; 41.586s elapsed, unchanged working inputs and a 1,569-word ordinary
brief against the unchanged 1,600-word bound. [Results](../../artifacts/f3-review/20261017T223242Z-3eec29/results.json)
bind exact source/fixture identities and both streams. The human subsequently approved
this checkpoint on 18 October 2026; approval preserves its limits and failure disclosures.

The actual private choice selects `local-notes-query` with qualified evidence and
no blockers. The distinct contextual choice selects `local-query-alternative` with
empty `replaces`; neither choice asserts a performance improvement. The later task
selects the private lesson; the browser task selects no patterns. Changing code
returns `PKP005`, removes the selected pattern and blocks completion without fallback.
The blocked finish response retains its checkpoint and unchanged task bytes.
Retirement returns `PKP002`. The guide's final comparison changes only canonical
style prose in the disposable source; the .NET brief changes while browser output
stays byte-identical. The fixture restores the canonical source after that demonstration.

The fixture's architecture/task/review authoring is fictional, explicitly labeled.
Actual named checks run two tiny Python owner-filter implementations against a fixed
oracle; an invalid implementation fails. This establishes that bounded semantic
behavior and F3's installed-layout selection/evidence routes. It does not implement
or qualify a .NET endpoint, PostgreSQL provider, HTTP/browser runtime or performance
improvement. Shared fixture authoring is not actual upstream promotion. Emitted
instructions keep `applicationObserved: false`; agent application is not inferred.

No packaged fresh/update qualification, complete F5 seed family, full F6 learning
round, arbitrary semantic analysis, human product acceptance or feature completion
is claimed. Review source is attributable authored evidence, not authenticated human
identity. Hashes cannot establish undeclared dependencies, mutable external state or
resistance to maliciously forged local history. Native application checks and normal
semantic/human review remain due for actual consumers.

## Validation and retained failures

The broad affected selector ran against the implementation base. Its record binds
the working inputs at execution, before later evidence/progress/fixture follow-ups.
Separate recoveries do not rewrite it or combine into release qualification.

| Execution | Actual result | Local record |
| --- | --- | --- |
| Initial focused F3 check | All 11 cases passed; 31.743s, 32.922s total | [record](../../artifacts/validation-runs/20261017T222009Z-44a0fb07/results.json) |
| Canonical migration audit | Normal guidance, inventory and source checks passed; three Foundation assertions still expected retired script wording. Original group remains needs-attention; 25.558s | [record](../../artifacts/validation-runs/20261017T222140Z-ee2bd94b/results.json) |
| Broad Affected | 23 of 27 checks passed, including composition-model execution, all canonical and F2/F3 checks. Three were unsupported under the default interpreter without Spec Kit; PostgreSQL restore failed on confirmed sandbox NuGet DNS. 153.449s; no coverage gap, input drift or overrun | [record](../../artifacts/validation-runs/20261017T222253Z-70c4d66c/results.json) |
| Existing prepared Spec Kit interpreter | Phase and bootstrap mechanics passed in 3.133s/27.877s. Task-generation progress assertion exposed the missing blocked checkpoint; original group remains needs-attention, 36.513s | [record](../../artifacts/validation-runs/20261017T222516Z-e002723b/results.json) |
| PostgreSQL recovery with network/process access | Passed in 59.537s, 60.359s total; original DNS failure retained | [record](../../artifacts/validation-runs/20261017T222540Z-2fbffede/results.json) |
| Canonical/F2 and follow-up evidence audit | Normal guidance, canonical sources and all F2 cases passed in 3.688s/11.276s/32.655s. Two new fixture assertions were wrong about blocked CLI exit and corrupting earlier versus latest evidence; original group remains needs-attention, 72.946s | [record](../../artifacts/validation-runs/20261017T222754Z-afe2659e/results.json) |
| Prepared task-generation recovery | All 27 cases passed after checkpoint reporting repair, with explicit blocking assertions; 4.109s, 5.255s total | [record](../../artifacts/validation-runs/20261017T222821Z-a0d46e0e/results.json) |
| Final F3 contract and canonical-source audit | All 12 F3 cases passed, including the complete installed fixture, actual log tampering, later failure, expiry, native evidence-owner boundary and malformed private source. F3 42.392s; canonical sources 11.345s; 54.871s total, no drift/overrun | [record](../../artifacts/validation-runs/20261017T223129Z-57fa3a29/results.json) |
| Independent native/source and progression checks | Story delivery passed 14.995s; selected lifecycle 3.566s; real public analyzer four-file positive/combined-type negative 5.350s; 24.681s total, no drift/overrun | [record](../../artifacts/validation-runs/20261017T223225Z-ff9d594e/results.json) |
| Final Integrity | All 7 checks passed; 6.157s, no drift/overrun | [record](../../artifacts/validation-runs/20261017T223449Z-fc669f27/results.json) |

The first retained F3 review failed when its fixture treated the normal verification
runner's mixed progress output as one JSON document. The parser was repaired; the
actual successful check output and incomplete run remain under
`artifacts/f3-review/20261017T221548Z-4c3ca5/`. The next retained 24-command review
passed in 30.181s with unchanged working inputs and a 1,569-word brief; it predates
the later hardening and is not presented as final-source proof.

The evidence follow-up initially asserted that corrupting an older check should
invalidate a newer intact pass, and expected a blocked completion CLI to exit zero.
Both expectations were corrected: a binding must verify its own retained evidence;
blocked preparation/completion exits 2. Independent failure and stale-input oracles
remain. No production budget, timeout, assertion about actual invalid behavior,
dependency pin or native release gate was weakened.

The broad selector's manual decisions for normal development, story delivery and
lifecycle have focused execution above. The wider shared-obligation, standalone,
architecture/placement and maintenance matrices and packaged fresh/update scenario
were not repeated: F3 changes pattern metadata/evidence and guidance producers,
with actual installed commands, direct completion, existing F2 reconciliation,
canonical-source and independent native-analyzer proof. It changes no physical
project roles/placement, production provider behavior, updater or managed-file
contract. Standalone native observation is also exercised by the actual contract-layout
check without governance imports. F4 owns subsequent source realization and F8
packaged adoption/update. These are explicit omissions, not borrowed F1/F2 passes.
No browser runtime contract changed; no browser acceptance claim is made.

Records bind their actual inputs at execution; checkpoint/guide report text was
finalized afterward. Narrow follow-ups cover their named changes and do not attach
later edits to the earlier broad run. All final reported checks stayed within their
existing budgets; original failed/unsupported groups remain needs-attention.

F1's packaged check remains over its original 120-second budget; F2's default-budget
overrun and all earlier environment/fixture failures remain independently disclosed.
No F3 result converts those runs into passing evidence.

## Lessons and next-session handoff

Keep separate explanations for applicability, preference and evidence. A compatible
alternative is not the same as replacement, and a later successful check should not
invalidate an intact earlier pass solely because its run identity differs. Later
unresolved failures must still prevent reuse. Show actual invalid behavior through
an oracle that does not read pattern metadata. Make blocked progress inspectable
without altering task history or granting continuation authority. Resolve normative
adapter text from its real canonical owner while keeping observed version facts and
independent native checks in code. Preserve source during input-bound validation;
report every narrow follow-up with its actual scope.

The human approved F3 and requested F4 in a fresh session. That session reads the final
retained F3 guide and this checkpoint before investigating F4. No cleanup was requested. Keep F1/F2/F3
consumers, snapshots, failures and budgets. Do not create the deferred repository
development skill before the human assesses the workflow across item reviews.

The requested fresh F4 session investigates/interviews its actual routes using
F2's context/composition and F3's selected qualified inputs. F4 owns safe
generation, managed boundaries, conflicts, regeneration and consumer source realization.
Preserve F1 preset retirement, actual Compile ownership, selected-publisher context,
independent negative checks and bounded ordinary briefs. F5 semantic qualification,
F6's complete teaching/promotion workflow and F8 packaged adoption remain later work.
No consumer restart, worker/provider operation, publication, tag or F4 work occurred.
