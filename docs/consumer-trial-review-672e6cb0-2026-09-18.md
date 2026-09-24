# Human consumer trial review: 672e6cb0

## Verdict

The bootstrap is validly completed. Its evidence integrity is sound, its architecture
is a usable baseline, and the recent routing/newline fixes worked. Efficiency regressed:
bounded reading eliminated observed output truncation but substantially increased
interaction and context-processing cost. This is not another failed consumer workflow;
it is evidence that the reading/context design needs refinement.

Candidate: `8acb05d961e36bd8f83d060fb134dd4033874e6c`, clean at setup.
Evidence: `artifacts/intake-sessions/e87abe7c9e1d4fd9bc3a06055c2d4e49`.
Consumer: `C:/Users/Joeyb/AppData/Local/Temp/program-kit-intake-bsu287vg`.
Comparison: run `916d623d`. Review is read-only with respect to the consumer; no
workflow resumed, coding agent launched, compatibility probe rerun or approval changed.

## Integrity

- Installed `workflow_lifecycle.py validate-completion --run-id 672e6cb0` independently
  returned `completed`, `engine_verified: true`.
- Native log contains 62 starts, 62 completed steps and one successful workflow finish;
  no failed native step, restart or recovery is recorded.
- All seven assessment approval hashes and all 25 bootstrap approval hashes match.
  Both approvals record interactive mode. The archived consumer ZIP hash also matches
  the session manifest.
- Three compatibility receipts contain 13 passing JUnit cases: Foundation activation
  and boundary/restart checks (5), real Keycloak/BFF login and permission/logout checks
  (3), real PostgreSQL concurrency/rollback/restart checks (5). No failed, errored or
  skipped case. JUnit and preserved diagnostic stream hashes were checked independently.
- Identity execution used the exact required SDK/Node/npm versions and managed provider
  fixtures. The helper, default resolver, intake builder and proof executor installed
  in this consumer are byte-identical to the reviewed source candidate.

`downstream-review-required` is the launcher's expected warning that the original
intake map hash no longer describes the map evolved by architecture. The native run
admitted the intake and current-stage completion validates. This does not mean the
completed bootstrap failed intake or needs to be rerun.

## Findings

### P2: the reading fix protects completeness but is too expensive

There are zero observed truncated tool outputs, versus seven previously. Parsing the
bounded reader's returned source-hash/page metadata finds 124 successful page responses.
Every observed sequence is complete; there are no repeated identical pages within a
stage for the same source hash and JSON pointer. Thus this is not primarily a duplicate
page bug. There are 131 tool-call records mentioning the reader, including failed or
auxiliary invocations.

Constitution reads seven intake pages plus the assessment, decision register and core/
hook instructions. Architecture reads the map, schemas and selection contracts. Closure
has 39 successful page responses across 24 source/hash/pointer groups, including existing
ADRs, baseline documents, lifecycle guidance, profile references, evidence and recipes.
Small separate responses protect against truncation but require many model/tool turns,
and retained source material increases subsequent input. Repeated references across
independent stages remain another source of processing.

Recommendation: reduce the necessary content first. Supply each stage with exact typed
facts, read dependencies and source hashes; project decisive fields rather than asking
it to navigate full schemas/maps. Keep genuinely mandatory reference content complete.
Permit a byte-budgeted bundle of small reads where the aggregate is bounded, rather
than forcing every page into a separate response. Retain pagination as a fallback.
Measure stage tokens and calls, not only absence of truncation. One uncontrolled trial
cannot attribute every added token to paging, but the interaction pattern and measured
regression make the current design unsuitable to call an efficiency improvement.

### P2: avoidable discovery and interpretation still occur inside stages

Observed detours include:

- Architecture constructed an incorrect reader path through `../` segments, then
  corrected it to the installed command.
- Tooling guessed JSON pointer `/assurance_levels`; the key was absent.
- Closure used `/` as a root JSON pointer; that requests an empty property, not the
  complete document. The reader returned the unhelpful `Bounded read failed: ''`.
- Roadmap tried to read its not-yet-created output.
- Closure initially declared ADR bindings stale after comparing ordinary hashes,
  then correctly recognized that canonical status-normalized hashes matched.

No stale-source rewrite or invalid approval was observed. Recommendation: supply exact
read commands/JSON pointers and input-existence information, add bounded key discovery
and useful pointer errors, and expose the existing canonical source-binding comparison
as the supplied check. These are machine-owned facts, not work the agent should infer.

### P3: authoring retries remain, despite better diagnostics

The intake builder rejected three constraints missing `decision_refs` in one diagnostic
batch. Architecture validation rejected a repository-props target outside its composition
application scope (PKB303); the agent corrected the binding before validation passed.
Roadmap terminal validation rejected 6,497 authored bytes above the 6,144-byte limit;
the agent trimmed it, then closure produced a final 5,688-byte roadmap.

These are local corrections, not native workflow failures. The previous invalid enum,
duplicate-ID and missing blocking-field failures did not recur, but this is not proof
that all draft mistakes are eliminated. Empty mechanical metadata can be derived where
its meaning is unambiguous; composition initialization should supply valid typed scope
relationships. Keep substantive scope validation. Improve first-draft targeting instead
of introducing larger universal limits or more retry instructions.

### P3: execution-context evidence needs clearer reconciliation

Closure's own Docker inspection was denied access to the engine/user configuration.
It recorded local availability as unknown and handed provisioning to the native runner,
which subsequently executed all three probes successfully. This is correct separation
of execution contexts, not a Docker/Foundation product failure.

The delivery ledger retains `browser-toolchain-proof`, including Node/npm remediation,
while the identity receipt proves those exact versions in its isolated execution context.
Keeping actual-application browser acceptance open is correct: scratch fixture evidence
does not prove the eventual consumer environment. Future handoffs should distinguish
already-proven fixture tooling from remaining application/developer-environment work,
so the next agent does not unnecessarily repeat diagnosis or installation.

## Verification of the latest fixes

- Intake routing is canonical `c#`; the assessment brief resolves dotnet, Foundation
  and local Keycloak without an invented alternate-stack integration question.
- The roadmap is 5,688 physical bytes both at closure validation and after proof/
  acceptance, including its 78 CRLF endings. The no-op executor no longer adds bytes.
- Architecture is 10,152 authored + 2,082 generated = 12,234 bytes; traceability is
  4,761 + 2,082 = 6,843; quality-system is 5,857 + 3,837 = 9,694. Generated content
  remains present and authored limits pass. Architecture still has only 88 bytes of
  headroom, a sign of brittle first-draft sizing rather than missing integrity.
- Bounded-reader sequences complete without truncation. Required information was not
  shortened merely to make the output fit; its cost trade-off is recorded above.

## Product and architectural quality

The user confirmed one private online browser list for two equally permitted adults,
free-text needs with optional quantity/note, bought/remaining sections and undo, automatic
connected updates without reservations, and separate sign-ins. Offline access, children,
regular reuse and history were explicitly deferred. The final intake was separately
confirmed with disclosed managed defaults.

This interview differs from the prior run: it does not establish basket-versus-payment
semantics or retained purchase history after clearing. The artifacts correctly leave
clearing and history rules for feature discovery rather than inheriting the prior
consumer's decisions. Those distinctions must be addressed in feature specification.

The five roadmap entries are coherent: shared shopping first, then reuse, history,
child requests and offline access. RM-01 combines access/add/shop into the useful outcome
the user accepted; it is not the entire envisioned application. One Household Shopping
context contains List, Participation and Identity Bridge. The bridge has an identifiable
translation responsibility; no additional service or domain boundary is invented.

Core owns consumer contracts, lifecycle and ports; API and PostgreSQL implementations
depend on Core rather than each other's internals. Planned architecture tests, contract
snapshots and package/feature identity checks name enforcement locations. Accepted ADRs
cover membership versus authentication, expected-version transactions, honest failure/
retry behavior, polling and the conditional Integration Events/outbox gate.

The release model remains correct: published Foundation image plus settings/Nuplane/
optional-package bundle, no consumer-built host DLL or image. Managed endpoint permission
checks are distinct from consumer household/resource authorization. Quality records
retain all 13 WEB-Q cases and separate fixture proof from actual device, accessibility,
security, business behavior and release evidence.

Persistence components/edges deliberately remain Proposed outside acceptance scope while
the storage direction is selected and mechanism proof passes. Feature admission and
actual schema/contract design are still required. This is not false acceptance of a
finished provider implementation.

The ledger has 18 obligations: three closed mechanism proofs and 15 open obligations
across feature planning (5), delivery (4), production (2) and future discovery (4).
RM-01 is specification eligible. No code has been delivered, so this run cannot prove
that .NET engineering rules or architecture tests will actually govern implementation.

## Efficiency

Final token counters are summed once per captured session. Reasoning tokens are already
included in output. Cache-inclusive input is processing volume, not a monetary bill.

| Measure | Previous 916d623d | Current 672e6cb0 | Change |
| --- | ---: | ---: | ---: |
| Uncached input + output, whole trial | 517,701 | 619,567 | +19.68% |
| Uncached input + output, bootstrap | 430,286 | 529,304 | +23.01% |
| Intake, same measure | 87,415 | 90,263 | +3.26% |
| All input including cache + output | 6,187,845 | 14,049,455 | +127.05% |
| Output tokens | 63,746 | 83,086 | +30.34% |
| Native bootstrap elapsed | 36m53s | 52m14s | about +42% |
| Native elapsed excluding reviews | 31m58s | 48m14s | about +51% |
| Compatibility execution | 1m32s | 1m33s | essentially unchanged |
| Truncated tool outputs | 7 | 0 | eliminated in this run |

Input is 13,966,369 including 13,429,888 cached, leaving 536,481 uncached input.
Largest stages: architecture 11m47s, assessment 8m56s, closure authoring 7m26s,
research 6m56s, roadmap 4m53s. Review steps account for about four minutes.
The additional elapsed time is in agent preparation/authoring, not provider probes.
Product answers, model behavior and environmental timing vary; this is observational
evidence, not a controlled benchmark.

## Recommendation

Keep this valid consumer baseline. The latest changes fixed correctness issues but
the reading change did not meet the efficiency objective. Prioritize leaner stage
inputs and exact executable read/validation contracts, with token/call measurements
on preserved inputs before requesting another expensive full human trial. Avoid adding
another large layer of instructions. Preserve the current gates and complete evidence.
Separately, the first feature flow remains the necessary test of knowledge application
to real implementation. This review changes no product code or consumer artifacts.
