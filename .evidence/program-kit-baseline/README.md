# Program Kit baseline evidence

This directory preserves the evidence produced while closing the original
Program Kit bootstrap baseline. It is committed review history, not current
build output.

- [`self-hosted/`](self-hosted/README.md) expresses Program Kit's own design and
  plan through Program Kit's typed contracts. Conformance tests copy and verify
  this exact evidence, including its digests and dependency projection.
- [`final-closure/`](final-closure/README.md) records the `PK-W090` closure of
  the approved bootstrap baseline: topology, migration assessment, provenance,
  verification observations, and the human review report.

"Self-hosted" means Program Kit described and validated itself using its own
contracts. "Final closure" means the original bootstrap work was closed; it
does not claim that Program Kit can never change again.

## Relocation and historical paths

These sets were relocated from `artifacts/self-hosted/` and `artifacts/final/`
because `/artifacts/` is reserved for ignored generated output. Digest-bound
JSON and evidence retain their original literal path values and bytes so the
historical approval and verification relationships remain exact.

Live repository navigation and test project includes use the current
`.evidence/program-kit-baseline/` paths. Historical path values inside frozen
evidence describe where that evidence was created; they are not current file
lookup instructions.
