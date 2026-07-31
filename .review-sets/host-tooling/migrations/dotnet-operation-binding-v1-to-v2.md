# DotNet operation binding v1 to v2

This source-guidance migration replaces the six parallel operation fields in a
DotNet shell v1 `operationBindings` entry with one canonical
`operationContract` descriptor plus the unchanged exact `projectionRevision`.

The migration is deterministic only when the migration input explicitly
supplies:

- one disposition for every result contract;
- one stable relation identity and request contract for every related
  operation;
- expected-revision, idempotency, cancellation, and progress policies;
- any progress, effect, and authority contract revisions;
- compatibility and deprecation declarations.

The migration must reject an input when any required declaration is absent. It
must not infer a result disposition, relation meaning, authority behavior,
effect behavior, retry policy, cancellation behavior, progress behavior,
compatibility claim, or deprecation replacement.

For an accepted input, construct `operationContract` as follows:

1. Copy `operationRevision`.
2. Copy `inputSchemaRevisions` to `requestContractRevisions`.
3. Pair every `resultSchemaRevisions` entry with its explicitly supplied
   disposition and emit `resultContracts`.
4. Copy `diagnosticSchemaRevisions` to `diagnosticContractRevisions`.
5. Emit explicitly supplied progress, related-operation, effect, authority,
   policy, compatibility, and deprecation values.
6. Copy `projectionRevision` unchanged.
7. Validate the result against the exact DotNet shell v2 and Operations
   descriptor schemas before writing target bytes.

The original v1 artifact remains unchanged on any failure. Reapplying the
migration to an already valid v2 binding returns the same v2 binding.
