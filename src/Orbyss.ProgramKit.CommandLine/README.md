# Orbyss.ProgramKit.CommandLine

`program-kit` is a deterministic transport over explicitly registered Program
Kit operations. It never scans the current directory, a solution, assemblies,
or package feeds.

The frozen command grammar is:

```text
program-kit validate <artifact...> | --manifest <artifact-manifest>
program-kit normalize <artifact> --output <file|->
program-kit digest <artifact>
program-kit render <artifact> --format markdown --output <file|->
program-kit graph <design> [--format text|json|dot]
program-kit versions map --manifest <component-manifest> --output <file|->
program-kit versions assess --observed <selection> --target <selection> --output <file|->
program-kit check <design|plan> | --manifest <workspace-manifest> [--profile <id>]
program-kit dotnet generate-host <api|console|worker> --shell <file> --host <id> --artifact-manifest <file> --output <dir>
program-kit dotnet generate-client --openapi <file> --tool-manifest <file> --tool-package <nupkg> --namespace-name <namespace> --class-name <class> --output <dir>
program-kit capabilities render-catalog <index> --output <file|->
program-kit capabilities verify-bundle <bundle>
program-kit capabilities initialize --provider <claude|codex> --workspace-root <dir> --program-kit-root <dir>
```

Every command also accepts `--diagnostics text|json`. Exit codes are `0` for
success, `1` for conformance failure, `2` for usage/input/I/O failure, and `3`
for an unexpected internal failure.

Operation adapters are registered from an explicit finite sequence. Duplicate
exact command keys fail before a dictionary can erase the conflict. Commands
without a selected operation adapter fail closed with `PKCLI004`.

The standalone composition backs exact-schema validation, model-less
canonical normalization/digest, and API/Console/Worker host generation.
Manifest validation awaits the W060 workspace-artifact model; package/publish
operations are backed by W065. W070 backs capability catalog rendering and
exact `.nupkg` bundle verification. Catalog rendering accepts the canonical
`.agent-capabilities/capabilities/INDEX.md` path, preserves `available`/`unavailable`
values, and includes the exact source SHA-256. Bundle verification requires the
three distributable canonical definitions and their separately listed inert
Codex and Claude Code adapter templates; it rejects the index, the authoring
capability, the repository-only local-publish capability, unlisted bytes, and
tampering.

Capability initialization requires explicit provider, workspace-root, and
Program-Kit-root arguments. It verifies the exact source manifest and bytes,
renders only `.codex/skills/<capability>/SKILL.md` (provider `codex`) or
`.claude/skills/<capability>/SKILL.md` (provider `claude`) wrappers with a
portable relative pointer to the canonical definition, and records exact
ownership in `.program-kit/capabilities.lock.json`. The lock records the most
recently initialized provider. It never copies canonical capability semantics
into the human-led workspace, never writes `.agents`, never scans for
providers, and refuses to overwrite an unowned or modified wrapper.
Host generation requires `hostDocuments[]` in the artifact manifest, binding
each selected host identity to one exact integrator-document revision. This
keeps shell and document digests independently verifiable and avoids inferred
file naming.

For `dotnet generate-host console`, the bound document revision must match the
canonical Open Console document version and bytes. Successful generation
includes the unchanged typed parser and parse-result record, the internal
consumer dispatcher contract, and deterministic dispatch lock/evidence files.
Consumer source supplies the generated `Program` partial composition method
and registers exactly one dispatcher. Parsed commands return that dispatcher's
integer as the process exit code; parse failures and information output retain
their document-declared behavior without composing the host.

Foreign-client generation accepts one explicit local JSON OpenAPI document and
one explicit `Microsoft.OpenApi.Kiota` package archive. The reviewed tool
manifest, package archive, entry assembly, version, language, and options must
all match exactly. The operation rejects external `$ref` values and publishes
only a complete generated C# tree containing `kiota-lock.json` and
`program-kit.client-generation.json`. It performs no package download, feed
lookup, login, or ambient tool/cache discovery.
