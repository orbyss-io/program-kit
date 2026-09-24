# Bootstrap efficiency improvements from c0a74a71

## Evidence and scope

The successful human trial is preserved unchanged. Its review is in
`consumer-trial-review-c0a74a71-2026-09-17.md`. Bootstrap used 503,415 uncached
input-plus-output tokens, essentially unchanged from the previous 504,713.
All eight captured sessions contained truncated tool output. This work targets
observed overhead without removing baseline evidence, gates or consumer choices.

## Root causes and changes

**Trial instructions leaked across phases.** `scripts/intake_session.py` wrote
the entire intake-only instruction into permanent consumer `AGENTS.md`. Captured
assessment, research, architecture, tooling, roadmap and closure calls reread
the bootstrap intake skill alongside their actual skill and brief. Permanent
guidance now routes by the current task; the full interview instruction remains
in `INTAKE-SESSION.md`. This supplies no new execution or approval authority.

**Whole-document reads caused truncation and repeated reads.** The real architecture
and closure briefs contain substantial selected evidence, so simply dropping
fields would risk quality. `bootstrap_context.py read-brief` displays the complete
brief in bounded 8,000-character pages, with source hash, page count and continuation.
All six producer commands use this route and require every page. It does not
regenerate artifacts, validate changing authoring inputs or summarize away facts.
Stage-required source reads and evidence indexing remain unchanged. Unicode and
the final page are covered by lossless reconstruction tests.

**Size correction aimed too near the ceiling.** Research's concise drafting rule
was phrased for a single journey, although the approved first slice had supporting
journeys. It now applies to the selected first slice. An advisory `inspect-output`
command reports all current sizes, target overruns, missing outputs and remaining
headroom without asserting validation. Research checks once after drafting;
closure checks after roadmap edits. Hard-limit diagnostics recommend the existing
generation target, avoiding repeated one- or two-byte trims. Hard limits and all
terminal validators remain unchanged. The strict context schema permits the new
advisory command without invalidating older contexts.

**Capability diagnostics required implementation discovery.** The trial marked
a binding guided without naming a Program Kit capability, then read validator
source to interpret the error. The existing authoring descriptor now explains
the coverage rule; authoring preflight reports every such error with its assessment
ID and distinguishes consumer-owned semantics from catalog mechanism coverage.
It does not infer coverage, invent IDs or silently change the model.

**Preparation observations looked like current task restrictions.** Closure's
existing instruction now keeps transient Docker/network observations in a labeled
pre-execution review, while prerequisite tasks describe durable required actions.
Current execution status remains in the ledger and receipts. No accepted ADR or
historical evidence is rewritten to manufacture freshness.

## Planning obligations retained

The ten first-slice planning items cover boundaries, provider admission, concurrency,
runtime tests, membership, web tests, device coverage, product details, contracts
and operability. Their scopes are related but not interchangeable. Removing them
to save tokens would hide actual design work. Their handling must be tested in
specification/planning: evidence-based design belongs to the agent; genuine product
choices belong to the consumer. Delivery execution remains a separate later gate.

## Validation and next comparison

Targeted tests cover lossless paged reading, advisory sizing without mutation,
batched capability diagnostics, stage-scoped launcher instructions and existing
context freshness. Test logs are under `artifacts/efficiency-*`.
The 25 authoring, 21 launcher and 8 handoff-quality tests passed, as did context
freshness regression coverage. All six preserved trial briefs reconstructed
exactly through the new reader. The bounded Development suite passed with exit 0;
its final log is `artifacts/efficiency-development-final-2.log`. Earlier suite
attempts exposed and led to correction of the strict context schema and a stale
instruction-text assertion; their logs remain preserved.

The fresh human trial should compare bootstrap separately from intake: uncached
input, cached input, output, failed authoring checks, repeated reads and final
architecture quality. Token savings are a hypothesis until that trial completes;
deterministic tests do not demonstrate agent behavior. The older completed
consumer is not modified or resumed by this work.
