# Completed-bootstrap maintenance after authority evolution

Program Kit 0.12.2's first completed-bootstrap maintenance fix rejected dezaaglijst
run `dae559cf` before review preparation. It compared the completion's historical
constitution/readiness digests against current files. The consumer has legitimately
amended and ratified constitution 2.0.0 and regenerated readiness, while its original
approval and engine-bound completion remain intact. Current authority must not be
rolled back to satisfy a historical receipt.

## Correction

`bootstrap_recovery.py prepare --run-id <source> --post-bootstrap` independently
validates the completed engine, unchanged approval and valid current setup/ratification.
It recovers each completion-bound historical constitution/report by exact raw SHA-256
from current files, previous content-addressed recovery archives, or local Git history
at the canonical path. Git access is read-only, with per-command safe-directory and
excludes overrides; it performs no checkout, config writes, downloads or fetches.
Caller-authored evidence JSON and hash filenames do not authorize substitute bytes.

Preparation stores historical blobs separately under `original/<sha256>` and records
their paths, hashes and provenance in `historical_completion`. It also snapshots the
current files and freezes the current ratified constitution/ratification for the
continuation. Both historical and current snapshots are verified on subsequent use.
The fresh review packet names historical bindings and current authority hashes.

The existing native proof step, latest-attempt admission, exact recipe/test/stream
bindings, fresh human review and engine-bound completion remain required. Native
readiness is rendered again after review, and new completion binds the current
constitution and report. Old approval/completion and source-run evidence remain
archived. The correction does not authorize product source implementation or close
later consumer/device/delivery obligations.

## Evidence

A read-only check against the actual dezaaglijst repository verified its completed
engine and current setup authority, including ratified constitution 2.0.0. The corrected
resolver recovered both exact historical blobs from commit
`162f97d2c39308541ba04d8abf6739dff918db21`:

- Constitution: `92c6331f4772c9e9cccc3d1df62213c39fe7c4e247f3849320f57aabbfdce6b9`.
- Readiness: `10b931c029f521c72f4d42b874c48e3d50192ae667074bd662e091d95a331056`.

The consumer's independently recorded historical-ref evidence was read as context;
the helper recovered and hashed the actual Git blobs itself. No consumer file,
ratification, approval, completion or workflow state was modified during this check.

The deterministic continuation validator now covers five cases: existing Active
admission and chained renewal; broken completion/Accepted ADR drift rejection; a real
fixture amendment/ratification plus regenerated report through fresh review and two
engine-bound completions; rejection of unratified current authority and unavailable
historical hashes; and archive reuse with actual-byte integrity verification. Dispatch
is mocked, and no coding agent is started. The bounded Development suite covers these
cases and the existing recovery, governance and installation contracts.
All 58 Development checks passed. The preserved log is
`artifacts/post-bootstrap-evolution-development.log`; the per-check journal/logs are
under `artifacts/validation-runs/20261002T203812Z-caf83da8/`. These local artifacts are
ignored files and are not part of the source commit.

## Consumer and release handoff

The consumer remains at its implementation source gate pending a maintained toolkit
update and actual reviewed continuation. After installing the correction, rerun:

```text
python .specify/extensions/program-kit-governance/scripts/bootstrap_recovery.py prepare --run-id dae559cf --post-bootstrap
```

Preparation starts no coding agent and supplies no verdict. Continue from the user's
normal terminal through `workflow_lifecycle.py resume --run-id dae559cf --post-bootstrap`;
review its concrete packet at the native human gate. Rerun source preflight after
successful continuation before continuing T002/T006 or business implementation.

VERSION remains 0.12.2 in this source correction. Publication/version selection is
separate. These are shipped helper/reference/command changes, requiring fresh Release
evidence for the final publication candidate. Follow AGENTS.md: full Windows Release
validation belongs in the user's terminal, and Firefox remains authoritative in CI.
