# Public CLI Contract

This document fixes the new orchestrator-neutral Program Kit command boundary.
Every public command emits the single current `program-kit.operation-result/v2`
contract; there is no parallel live v1 result surface.

## Common invocation

```text
program-kit <command> --workspace <path> --request <path> --format json
```

- `workspace` is an explicit existing directory.
- `request` is a regular non-reparse file inside the workspace.
- JSON mode writes exactly one schema-valid document to stdout.
- Recoverable running failures return a structured result and documented exit
  code; stderr is never part of the machine contract.
- No command uses interactive prompts or environment-derived semantic defaults.

## Commands

| Command | Request schema | Result schema | Maximum effect |
|---|---|---|---|
| `init` | `program-kit.workspace-init-request/v1` | `program-kit.operation-result/v2` + initialization payload | Create absent bootstrap files only |
| `catalog list` | `program-kit.catalog-request/v1` | `program-kit.operation-result/v2` + distribution catalog | None |
| `restore` | `program-kit.workspace-restore-request/v1` | `program-kit.operation-result/v2` + workspace lock | Generated lock/state only |
| `prepare` | `program-kit.preparation-request/v1` | `program-kit.operation-result/v2` + preparation proposal | None |
| `authority record` | `program-kit.authority-record-request/v1` | `program-kit.operation-result/v2` + authority record | Exact repository authority records only |

## `init`

### Preconditions

- Invoked CLI matches the exact distribution binding in the request.
- Workspace path and requested output paths are safe and non-colliding.
- `program-kit.yaml` and initial state are absent, or all existing initialization
  outputs are byte-exact results of the same request.

### Success

- Creates an absent neutral `program-kit.yaml` with zero selections.
- Creates only required Program Kit bootstrap ownership/evidence state.
- Records the explicit invocation declaration and bounded bootstrap effect.
- Repeating the same request returns `unchanged` without rewriting bytes.

### Refusal

Conflict, drift, collision, unsafe path, global shadow, mismatched release, or an
attempted profile/restore/network/factory effect returns `blocked` or
`needs-input`, effect `none`, and no partial trusted file.

## `catalog list`

The request has `scope: distribution`. The command returns the exact immutable
catalog of the invoked distribution. It performs no network, install, selection,
restore, activation, authority, or write. Zero/one/many results remain merely
available.

## `restore`

The request names the consumer manifest and target lock path.

- `mode: base` accepts zero selections and locks distribution/contracts/catalogs.
- `mode: factory` requires one exact supported selection for this V1 journey.
- Ranges, implicit defaults, duplicates, unavailable evidence, or ambiguous
  relationships refuse the lock.
- The lock is staged, schema/canonicalization validated, and atomically
  published as generated-owned.
- An unchanged exact lock is reused; unrelated repository edits do not stale it.

## `prepare`

The request supplies the exact bundle, workspace, mode, desired effect,
selection, evaluation context, and current workspace lock.

Success returns an effect-free `PreparationProposal` with request binding,
closure/live-state digests, explanation, authority requirements, and complete
ungranted construct projection. It creates no candidate, live product, grant,
or authority record.

## `authority record`

The request supplies an exact current preparation proposal and separate human
decision record. The repository authority provider:

- validates proposal/decision/request/subject/operation/effect/condition/
  provenance/validity/revocation bindings;
- refuses denial, widening, stale state, ambiguity, invalid validity, or changed
  live preconditions;
- creates the exact grant and revocation records as one atomic set; and
- never invents reviewer identity, defaults, subjects, operations, or effects.

The adapter and Spec Kit hooks never invoke this command automatically.

## Result and exit codes

| Outcome | Exit code |
|---|---:|
| `succeeded` | 0 |
| `faulted` | 1 |
| `needs-input` | 2 |
| `blocked` | 3 |
| `cancelled` | 130 |

`program-kit.operation-result/v2` retains the established outcome, effect,
disposition, diagnostic, evidence, continuation, and disclosure semantics. It
adds the new command/phase enums and one discriminated typed `payload`. The
existing `OperationResult` implementation and every command advance together;
v1 remains historical evidence rather than a separately supported runtime path.

## CLI grammar negatives

- Unknown commands/subcommands/options never echo opaque raw tokens.
- Duplicate options, missing values, positional arguments, and request paths
  outside the workspace are refused before effects.
- `--format` is exactly `text` or `json`.
- Utility commands keep their existing option rules.
- New workspace/preparation/authority commands require both `--workspace` and
  `--request`.
