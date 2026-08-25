# Program Kit Bootstrap architecture

## Purpose

This project owns the reusable method for turning a user-provided initial design into a governed Spec Kit repository. It does not own any consuming application's architecture.

## Components

| Component | Responsibility |
|---|---|
| Workflow | Orders bootstrap activities and human approval gates. |
| Extension commands | Give agents deterministic responsibilities and output contracts. |
| Extension hooks | Make architecture validation part of the normal Spec Kit lifecycle. |
| References | Define generic policies and technology-triggered guardrails. |
| Bundle | Pins and distributes the tested component set. |
| Test harness | Validates source manifests and builds a reproducible artifact. |

## Dependency direction

The workflow depends on command IDs exposed by the extension. Commands depend on reference documents, but references do not depend on Spec Kit runtime behavior. The bundle composes components and adds no behavior.

Third-party extensions are evaluated by the workflow and recorded in the consuming project's tooling decision record. They are not dependencies of this source project unless a later ADR accepts them as universally required.

## Trust boundary

Workflow prompts and initial-design content are untrusted inputs. They never flow into a shell step. This project currently contains no workflow shell steps and no executable extension hooks; hooks invoke agent commands whose instructions require explicit approval for destructive or externally publishing actions.

