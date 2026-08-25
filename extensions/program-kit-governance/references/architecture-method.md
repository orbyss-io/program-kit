# Architecture method

## Artifact hierarchy

1. Initial design: user intent and starting assumptions.
2. Architecture baseline: current coherent model, views, constraints, quality scenarios, and risks.
3. ADRs: history and authority for significant project-specific choices.
4. Specifications: implementable behavior slices constrained by the architecture.
5. Plans and tasks: delivery design and work decomposition.
6. Implementation and verification evidence.

Later artifacts cannot silently contradict earlier accepted authority. When a valid new insight changes architecture, propose an ADR, obtain human acceptance, update the baseline and traceability, then continue the Spec Kit flow.

## Design tasks before feature slices

Architecture gaps are resolved as focused design tasks. Each task frames one decision, gathers evidence, compares credible alternatives, records consequences, updates views, and identifies which specifications it enables. Examples include isolation boundaries, queue/outbox semantics, tenancy and authorization, contract versioning, package security, reproducibility, signing/provenance, and recovery.

## Status discipline

All technologies begin `Proposed`. Only an Accepted ADR promotes them to `Accepted`. Rejected, Deprecated, and Superseded items retain links to the decision history.

## Living architecture

Architecture changes in the same change set as the decision or implementation that invalidates it. CI checks machine-verifiable structure and traceability; human review owns architectural judgment.

