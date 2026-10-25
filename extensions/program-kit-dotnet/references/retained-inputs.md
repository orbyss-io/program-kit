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

When explicitly using this optional preservation helper, inspect the named original
before editing. A normal task can record its intended read/write ownership as:

```markdown
- [ ] T001 Read `docs/compatibility/accepted-v1.md` and write `docs/compatibility/current-proposal.md`

## Document outputs

| Task | Path | Mode |
| --- | --- | --- |
| T001 | docs/compatibility/accepted-v1.md | read |
| T001 | docs/compatibility/current-proposal.md | write |
```

Use `verify` explicitly when this protection is relevant to the selected work. It is
not a generic task-generation or implementation gate. Add a distinct active target
linked to the original instead of changing preserved evidence. Previously completed
task descriptions remain history; checkboxes do not authorize a new mutation. Normal
authored-file ownership, architecture and agreed review constraints still apply.

The optional `archives` array names `{ "record": "original-reset" }`. Its root
and exact payload set come from that original result. New resets bind the raw
inventory hash before deletion. Older results without that field bind their
original payload/preserved maps; the reader reports that narrower anchor rather
than claiming an authenticated old review narrative. Changing payload and then
rehashing its inventory cannot alter the original result's expected bytes.
Missing, extra, aliased and escaped files fail.

The optional `retiredLocks` array contains `{ "path": "src/Old/packages.lock.json",
"record": "original-reset", "owners": ["src/Old/Old.fsproj"] }`. Every original
same-directory C#/F#/VB project owner must occur in the original abandoned map,
and the lock must occur in its preserved map. Custom lock paths require the
original archived native project declaration; dynamic/imported old ownership
needs an original evaluated ownership receipt and is currently a diagnosed gap.
Reactivation, a new active same-directory owner and changed bytes fail. Project
absence alone never grants retirement, and upgrade refuses unexplained stale
orphans. Active locks continue through native restore.

Inactivity admission examines current projects, solutions, root/eng props and
targets, recursive imports, architecture and appsettings inputs. Direct archive
references, broad includes reaching retired roots and declared lock reactivation
fail. Unknown dynamic item/import paths, external imports and Exec require an
explicit evaluated input adapter; this bounded static reader does not certify
those unsupported activation mechanisms. It never executes retired code.

Synchronization creates a named `retained-inputs` toolkit check with exact input
ownership from these records. `Invoke-RepositoryVerification.ps1 -Scope Focused
-Checks retained-inputs` runs it directly. Affected selection can combine it with
native domain projects from the original Git baseline. Consumer `toolkitChecks`
in `eng/verification.json` declare a unique `id`, current Python `script`, literal
`arguments`, exact `inputs`, and `timeoutSeconds` (1..900). No shell or coding agent
is dispatched by the adapter. Keep paid/provider operations outside these checks.
Results retain separate named outcomes, input/runtime fingerprints and both
streams under `artifacts/tests/toolkit-runs`. Failures/interruption remain pending
even if a mapping is removed. These process results never count as native tests,
do not advance the Git baseline and cannot narrow Acceptance or Release.
