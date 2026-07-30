# publish-dotnet-application-locally

## Identity and trigger

`publish-dotnet-application-locally` owns one explicit repository-local
application publish operation. Use it only when a human asks to publish a
selected generated .NET host locally and supplies the shell, host identity,
artifact manifest, prepared package-root manifest, and output root.

## Purpose

Invoke the backed Program Kit `dotnet publish-local` operation with exact
parameters, verify its output manifest, and report the local application path
and evidence. This capability is part of the exact consumer CLI capability
payload.

## Non-goals

- Do not prepare or pack packages.
- Do not push to a package feed, publish externally, deploy, sign, promote, or
  create release state.
- Do not discover a shell, host, package root, manifest, or output directory
  from the current directory.
- Do not overwrite an existing publish output.
- Do not create hooks, watchers, background services, or provider bindings.

## Inputs and outputs

Required inputs:

- `shell`: exact `shell.json` path.
- `host`: exact host identity selected from the shell.
- `artifact-manifest`: exact host-document input manifest path.
- `package-manifest`: exact prepared local package-root manifest path.
- `output`: exact local publish root.

Outputs:

- One verified application output below the supplied root.
- Its canonical `local-publish-manifest.json`.
- The command exit code and diagnostics.
- A concise report of the selected host, manifest digest, and output path.

## Preconditions

- A human explicitly requested this local publish.
- All five required parameters are supplied; none is inferred.
- The local package root was already prepared by its separately backed
  operation.
- The output target does not exist and resolves inside the intended workspace
  or explicitly named writable root.
- The Program Kit CLI and W065 publish operation are built and verified.

## Allowed actions

- Read the five explicit inputs and files referenced by their manifests.
- Run the exact Program Kit CLI `dotnet publish-local` command.
- Read and verify the resulting local publish manifest and file hashes.
- Report deterministic diagnostics and evidence.

## Prohibited actions

- Do not run `packages prepare-local` or an implicit restore source discovery.
- Do not change the shell, host, artifact manifest, package manifest, package
  root, generated source, or existing output.
- Do not use network sources beyond those already explicitly represented and
  permitted by the verified package operation.
- Do not access secrets.
- Do not delete or overwrite an existing output.
- Do not push, deploy, sign, release, promote, or operate an artifact feed.

## Stop conditions

Stop before execution when any parameter is missing, ambiguous, or outside the
intended boundary; when input hashes or host selection fail; when the output
already exists; or when the package root is incomplete, extra, or tampered.
Stop on any CLI failure and preserve its diagnostics. Do not fall back to raw
`dotnet publish`.

## Source of truth and freshness

The five supplied paths and exact current bytes are the only operation inputs.
The W065 Program Kit command implementation owns publish semantics. This
capability is a human-session wrapper and must not duplicate or reinterpret
those mechanics.

## Procedure

1. Confirm the human request and all five explicit parameters.
2. Resolve each path and verify the output boundary without creating it.
3. Confirm the output does not exist.
4. Invoke:

   ```text
   program-kit dotnet publish-local --shell <shell> --host <host> --artifact-manifest <artifact-manifest> --package-manifest <package-manifest> --output <output>
   ```

5. Require exit code `0` and no error diagnostics.
6. Locate the single selected host output from the verified manifest binding,
   not by broad directory discovery.
7. Verify the canonical manifest digest and every listed file hash.
8. Report the exact host, output path, and manifest digest. Stop.

Parameter review is the human-session judgment step. The CLI owns generation,
restore, publish, collision, hashing, and manifest verification mechanics.

## Verification and failure reporting

Report the exact command with secrets excluded, exit code, diagnostic IDs,
manifest path/digest, and output path. On failure, report whether it was input,
conformance, collision, process, or integrity related. Never claim success from
the presence of files alone.

## Authority and safety boundaries

Authority is limited to one local publish under the explicit output root.
Network, secrets, destructive actions, external publication, deployment, and
release state are outside this capability. Copying this definition does not
register it elsewhere.

## Compatibility and versioning

Preserve this capability ID while it remains a thin wrapper over the same five-
parameter W065 operation. Any parameter, collision, restore-source, output, or
authority change requires explicit compatibility review. Rename, supersession,
or retirement requires human authority plus index and wrapper migration.

## Program Kit knowledge and failure resolution

Run `program-kit commands describe dotnet.publish-local --format text` before
invocation. For failures, retrieve `software-change-troubleshooting` and use
`diagnostics explain` plus `artifacts inspect` for the explicit manifests. Do
not replace the backed command with a guessed raw `dotnet publish` sequence.

If a required typed Console artifact manifest or generated host is absent or
stale, retrieve `dotnet-console-input-materialization-guide` and report the
exact materialize/generate handoff. Do not broaden local-publication authority
into consumer source authoring or silently edit Program Kit-owned inputs; route
that work to the active approved implementation or bounded maintenance flow.

## Provider wrapper mapping and drift check

Codex and Claude wrappers contain only trigger metadata plus exact
`capabilities preflight` and `capabilities read` invocations. The installed
CLI verifies their recorded bytes before returning this definition. A changed,
missing, unowned, stale, or version-mismatched wrapper is a setup blocker.
Initialization renders Codex beneath `.agents/skills/` and Claude Code beneath
`.claude/skills/`; `.codex/skills/` is exact legacy migration input only.
