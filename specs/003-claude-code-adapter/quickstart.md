# Quickstart: Claude Code Adapter on an Isolated Consumer Machine

This is the required post-implementation validation path. It proves Feature 003
using a sealed release/review kit on a clean machine without Program Kit source,
Spec Kit, Codex adapter state, or prior Program Kit session integration state.

Commands are PowerShell 7 examples. Provider installation and authentication
are explicit external prerequisites, not Program Kit effects.

## 1. Source-machine prerequisites

- Clean Program Kit checkout at the Feature 003 implementation commit.
- Exact SDK from `global.json` (`10.0.302` for this feature).
- Completed Feature 002 implementation and tests.
- No live Claude Code credentials are required for deterministic build/export.

Run the complete deterministic suite:

```powershell
dotnet restore --locked-mode
dotnet build --no-restore
dotnet test --no-build
```

Expected result: Feature 002 plus Claude adapter contract, projection,
diagnostic, conformance, lifecycle, runtime-isolation, and source-marker tests
pass without starting Claude Code or using a network.

## 2. Export the sealed review kit

From Program Kit source:

```powershell
pwsh ./eng/Export-ClaudeCodeReviewKit.ps1 `
  -Configuration Release `
  -OutputPath C:/tmp/program-kit-claude-review
```

Expected kit contents:

```text
program-kit-claude-review/
├── manifest.json
├── feed/
│   └── Orbyss.ProgramKit.Cli.1.0.0-alpha.1.nupkg
├── fixtures/
├── schemas/
├── scripts/
│   ├── Initialize-ConsumerWorkspace.ps1
│   ├── Invoke-DeterministicConsumerProof.ps1
│   ├── Invoke-ClaudeCodeTrials.ps1
│   └── Complete-HumanReview.ps1
└── README.md
```

The manifest binds every file digest, Program Kit package identity, canonical
definition, Claude adapter, exact Claude Code `2.1.220` profile, diagnostic
catalog, conformance corpus, and expected output schema. The kit contains no
Program Kit source, Spec Kit, credentials, transcripts, or authority grant.

Copy the complete directory to the designated external machine through the
human-approved transfer mechanism. Do not regenerate or edit it there.

## 3. Prepare the isolated machine

On the target machine, verify these conditions:

- no Program Kit source checkout;
- no Spec Kit installation inside the consumer repository;
- no `.agents/skills/program-kit/` Codex projection;
- no previous `.program-kit/session-integrations/` state;
- PowerShell 7 and the exact required .NET runtime/SDK are available; and
- Claude Code installation/authentication is separately managed by the human.

Verify the sealed kit before use:

```powershell
pwsh ./program-kit-claude-review/scripts/Initialize-ConsumerWorkspace.ps1 `
  -ReviewKit ./program-kit-claude-review `
  -ConsumerRoot ./consumer
```

Expected result: a clean consumer Git repository and a structured environment
record. Any changed kit byte or failed clean-boundary condition blocks the
isolated-machine claim.

## 4. Pin and verify Claude Code

Install exact Claude Code `2.1.220` using Anthropic's reviewed exact-version
installation procedure. Program Kit does not perform this step or modify the
provider update channel.

Verify the selected provider:

```powershell
claude --version
```

Expected normalized value:

```text
2.1.220 (Claude Code)
```

The review script records only the normalized version and executable digest. It
does not record executable location, account, credentials, or authentication
material. A different version is `PKCLD0001`, not an approximate pass.

## 5. Install the exact Program Kit CLI separately

From the clean consumer repository:

```powershell
$consumerRoot = (Resolve-Path -LiteralPath '.').Path
$toolPath = Join-Path $consumerRoot '.program-kit/tools'
$feed = (Resolve-Path -LiteralPath '../program-kit-claude-review/feed').Path

dotnet tool install Orbyss.ProgramKit.Cli `
  --tool-path $toolPath `
  --version 1.0.0-alpha.1 `
  --add-source $feed `
  --no-http-cache

$programKit = Join-Path $toolPath 'program-kit.exe'
& $programKit version --format json
```

On Linux, use the corresponding `program-kit` executable without `.exe`.

Expected result: the reported version, executable digest, package digest, and
package identity match the sealed review manifest. The session adapter records
the CLI but does not own or remove it.

## 6. Explain the Claude integration

Use the exact request fixture copied into the consumer repository:

```powershell
& $programKit session explain `
  --workspace $consumerRoot `
  --request './requests/claude-code-install.json' `
  --format json
```

Expected result:

- `outcome: succeeded` and `effectState: none`;
- exact CLI, definition, adapter, Claude Code `2.1.220`, workspace and catalog
  identities;
- proposed `.claude/skills/program-kit/SKILL.md` as `generated-owned`;
- no settings, `CLAUDE.md`, plugin, MCP, user-scope, or provider-install effect;
- collision and compatibility findings;
- exact expected live-state/request-core identities; and
- a bounded request for separate install authority.

Confirm no provider projection exists yet.

## 7. Prove missing authority blocks installation

Invoke installation using the request without a valid authority grant:

```powershell
& $programKit session install `
  --workspace $consumerRoot `
  --request './requests/claude-code-install-without-authority.json' `
  --format json
```

Expected result: `blocked`, `effectState: none`, the stable authority diagnostic,
and no `.claude/skills/program-kit/` directory. Claude Code process permission
or authentication cannot change this result.

## 8. Authorize and install the exact projection

After reviewing the exact explanation, the human creates the supplied
request-bound grant through the documented repository authority workflow. Then:

```powershell
& $programKit session install `
  --workspace $consumerRoot `
  --request './requests/claude-code-install-authorized.json' `
  --format json

& $programKit session verify `
  --workspace $consumerRoot `
  --request './requests/claude-code-verify.json' `
  --format json
```

Expected result: one complete admitted projection and installation record.
Verification reports installation exact while session availability is initially
`not-evaluated` or `reload-required`.

Inspect the projection:

```powershell
Get-Content -Raw -LiteralPath '.claude/skills/program-kit/SKILL.md'
```

It must match the sealed expected bytes and contain no provider tool permission,
script, settings mutation, executable remediation, domain semantics, or grant.

## 9. Run deterministic consumer proof

```powershell
pwsh ../program-kit-claude-review/scripts/Invoke-DeterministicConsumerProof.ps1 `
  -ConsumerRoot $consumerRoot `
  -ProgramKitPath $programKit
```

Expected result:

- ten of ten clean installation repetitions succeed atomically;
- direct CLI, neutral harness, Codex fixture, and Claude fixture preserve the
  shared corpus meaning;
- collision, interruption, drift, authority, disclosure, transport, removal,
  and source-marker negative cases return the expected stable results; and
- the generated reference application restores, builds, tests, and runs with
  all authoring tools unavailable.

## 10. Perform one interactive human walkthrough

Start Claude Code from the consumer repository using the exact selected
provider. Review and accept the provider's normal workspace trust prompt as a
human; Program Kit does not automate this.

Run `/program-kit` and the reference journey. Verify that the session:

1. locates the exact workspace-local CLI;
2. verifies its version;
3. invokes read-only explanation first;
4. asks for bounded missing meaning and exact current authority;
5. does not create or widen a grant;
6. preserves the Program Kit structured result and actual effect;
7. evaluates without repair; and
8. describes provider permission separately from Program Kit authority.

Record only the bounded reviewer classifications. Do not save a transcript.

## 11. Run ten fresh Claude Code trials

After external authentication is ready:

```powershell
pwsh ../program-kit-claude-review/scripts/Invoke-ClaudeCodeTrials.ps1 `
  -ConsumerRoot $consumerRoot `
  -ProgramKitPath $programKit `
  -ExpectedClaudeCodeVersion 2.1.220 `
  -Trials 10
```

The script uses ordinary `claude -p`, not `--bare`, so project-skill discovery
is exercised. Provider output is parsed transiently against a bounded schema and
discarded. Each verdict is based on independently captured Program Kit results,
receipts, and before/after workspace identities.

Expected result: all required trials pass, or every failure/incompatibility/
unavailable prerequisite remains explicitly classified. Missing provider
credentials or network leaves live review `not-evaluated`; it does not fail the
independent Program Kit source build and cannot become a fabricated pass.

## 12. Verify drift and removal safety

First alter the admitted skill fixture and request removal. Expected result:
drift is diagnosed and the altered file is preserved.

Restore through a separate authorized lifecycle request, verify exact state,
then remove using the exact admitted record and a fresh removal grant:

```powershell
& $programKit session remove `
  --workspace $consumerRoot `
  --request './requests/claude-code-remove-authorized.json' `
  --format json
```

Expected result:

- only unchanged `.claude/skills/program-kit/SKILL.md` is removed;
- parent `.claude` directories, settings, other skills, CLI, provider, consumer
  files, and lifecycle evidence are preserved; and
- verification reports this integration absent without claiming the CLI or
  Claude Code is absent.

## 13. Complete the review record

```powershell
pwsh ../program-kit-claude-review/scripts/Complete-HumanReview.ps1 `
  -ConsumerRoot $consumerRoot `
  -Decision accepted
```

`accepted` is valid only when all mandatory deterministic and live evidence is
complete, runtime/disclosure checks pass, no unauthorized effect occurred, and
the human reviewer accepts product behavior. Otherwise choose `rejected` or
leave `pending` with exact limitations.

The final `program-kit.claude-code-machine-review/v1` record contains no
credentials, transcripts, prompts, model reasoning, raw provider output,
exceptions, or protected physical paths.
