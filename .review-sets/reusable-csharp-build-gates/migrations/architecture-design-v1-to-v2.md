# Architecture Design v1 to v2 migration

Architecture Design `2.0.0` adds one required exact
`staticConformanceDisposition` reference. Migration is deterministic only after
the human supplies that exact reference.

The migration:

1. reads and preserves the v1 source bytes;
2. rejects a missing, `null`, defaulted, or already-present supplied field;
3. accepts an exact
   `pkid:schema:program-kit:static-conformance-disposition@1.0.0` reference
   selected by the human;
4. produces new v2 bytes with that reference; and
5. validates the new document without rewriting the v1 input.

It never infers a disposition from repository contents or defaults to
`not-justified`. If no human decision is supplied, the migration stops without
an output.

The input and output fixtures bind the approved Program Kit extension design to
its exact `reuse-existing` disposition. They model the migration boundary and
prove that the source revision remains unchanged.
