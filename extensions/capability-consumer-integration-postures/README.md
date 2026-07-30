# Capability consumer integration postures

This directory contains the candidate review set for making Program Kit
capability-provider integration an explicit consumer choice.

The canonical artifacts are:

1. `architecture-design.json` — Architecture Design `2.0.0`;
2. `implementation-plan.json` — Implementation Plan `3.0.0`;
3. `static-conformance-disposition.json` —
   `StaticConformanceDisposition@1.0.0`;
4. `review-manifest.json` — exact review-set identities and digests.

Supporting intent, source-baseline, provider-contract, static-conformance, and
reviewer-facing Markdown artifacts make the candidate understandable without
becoming alternate sources of architecture.

The candidate creates no runtime behavior, provider registration, adapter,
ownership lock, Git policy, hook, watcher, or autonomous action. Implementation
remains blocked until a human approves the exact canonical design and plan
digests.
