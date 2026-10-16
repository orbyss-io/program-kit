# Retained input and document ownership

`eng/retained_inputs.py` reads existing supported feature-reset preservation records.
It hashes original bytes and never executes historical code, restores retired projects
or turns preservation into current product acceptance. An absent index is reported as
unconfigured; it does not certify that arbitrary repository documents are mutable.

Declare the exact original record hashes already retained by the reviewed preservation
or migration input. Do not calculate a replacement expected hash to conceal a failure.
For example, `eng/retained-inputs.json` can declare:

```json
{
  "schemaVersion": 1,
  "records": [{
    "id": "original-reset",
    "path": "artifacts/reset/result.json",
    "sha256": "<exact previously retained original result SHA-256>"
  }],
  "protected": [{
    "path": "docs/compatibility/accepted-v1.md",
    "record": "original-reset"
  }],
  "activeDocuments": [{
    "path": "docs/compatibility/current-proposal.md",
    "supersedes": ["docs/compatibility/accepted-v1.md"]
  }]
}
```

The placeholder above must be the actual original digest. The named input must occur
in that executed reset result's `preserved` map. Preview results, missing/modified
records, changed protected bytes and aliased paths fail. The index selects explicit
protected inputs; it does not freeze a whole folder or every reset-preserved file.
The hash binding establishes preservation relative to the supplied original authority,
not an independent signature or proof that an operator attestation is true.

Inspect with `python eng/retained_inputs.py inspect --repository .`, or name one target
with `--path`. `verify` checks the declared current bytes against those original records.
Its result explicitly supplies no fresh application/provider acceptance.

Task preparation reports the configured ownership and binds the original frozen
entries into its existing draft. A pending task referencing protected evidence uses:

```markdown
- [ ] T001 Read `docs/compatibility/accepted-v1.md` and write `docs/compatibility/current-proposal.md`

## Document outputs

| Task | Path | Mode |
| --- | --- | --- |
| T001 | docs/compatibility/accepted-v1.md | read |
| T001 | docs/compatibility/current-proposal.md | write |
```

Saving/finalizing tasks, artifact preflight and delivery guards use the same reader.
Changing/removing the index or rehashing a replacement record cannot remove an
already bound frozen entry through `acknowledge-inputs`. Add a distinct active target
linked to the original instead. Previously completed task descriptions remain history;
their checkboxes do not authorize a new mutation. Existing artifact ownership,
architecture and review rules still apply to the new target.
