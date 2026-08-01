# Quickstart: Validate the First Program Kit Vertical Slice

## Objective and time budget

This walkthrough proves the public product, not only compilation:

| Activity | Budget |
|---|---:|
| Verify exact prerequisites | 5 minutes |
| Locked restore, build, and focused tests | 10 minutes |
| Explain the valid integration without live writes | 5 minutes |
| Construct and relocate the consumer outputs | 15 minutes |
| Restore, build, test, run, and observe Status | 10 minutes |
| Prove invalid input, drift, and explicit repair | 10 minutes |
| Prove path/culture repeatability | 5 minutes |

Target: a fresh contributor completes all steps in no more than one hour and
can explain what each artifact proves.

## Prerequisites

- Repository checkout on the feature branch.
- Exact .NET SDK `10.0.302`.
- Windows x64 or Linux x64 development environment covered by the selected
  execution profile.
- No Program Kit installation and no external package feed/network access are
  required after the governed local dependency mirror is available.

From the repository root:

```powershell
dotnet --version
```

Expected: exactly `10.0.302`. Any other version must fail through
`global.json`; do not change roll-forward policy to proceed.

## 1. Independent repository bootstrap

```powershell
dotnet restore ProgramKit.slnx --locked-mode
dotnet build ProgramKit.slnx --no-restore
dotnet test ProgramKit.slnx --no-restore --no-build
```

This path must not invoke Program Kit against its own repository and must not
depend on generated Program Kit governance.

Expected:

- locked restore does not rewrite any lock file;
- all unit and contract tests pass;
- no production assembly or test bootstrap contains `Reference.Status`
  semantics outside the fixture boundary.

## 2. Create an isolated reference workspace

PowerShell:

```powershell
$programKitRoot = (Resolve-Path -LiteralPath '.').Path
$referenceSource = Join-Path $programKitRoot 'tests/Fixtures/Reference.Status/Valid'
$referenceWorkspace = Join-Path ([IO.Path]::GetTempPath()) ('program-kit-status-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath $referenceSource -Destination $referenceWorkspace -Recurse
$cliProject = Join-Path $programKitRoot 'src/ProgramKit.Cli/ProgramKit.Cli.csproj'
```

Bash:

```bash
program_kit_root="$(pwd)"
reference_source="$program_kit_root/tests/Fixtures/Reference.Status/Valid"
reference_workspace="$(mktemp -d)/program-kit-status"
cp -R "$reference_source" "$reference_workspace"
cli_project="$program_kit_root/src/ProgramKit.Cli/ProgramKit.Cli.csproj"
```

The fixture contains consumer-owned Status intent/source, exact local authority
records, exact selections, and separate explain/construct/evaluate requests.
No generated output is preinstalled.

## 3. Explain integration before construction

PowerShell:

```powershell
$explainJson = dotnet run --project $cliProject --no-build -- explain `
  --workspace $referenceWorkspace `
  --request (Join-Path $referenceWorkspace 'requests/explain.yaml') `
  --format json
$explain = $explainJson | ConvertFrom-Json
$explain | Select-Object outcome, furthestPhase, effectState, primaryDisposition
```

Bash:

```bash
dotnet run --project "$cli_project" --no-build -- explain \
  --workspace "$reference_workspace" \
  --request "$reference_workspace/requests/explain.yaml" \
  --format json
```

Expected result:

```text
outcome: succeeded
furthestPhase: explanation
effectState: none
primaryDisposition: complete
```

Inspect the returned Integration Resolution Explanation. Verify that it names:

- consumer ownership of Status meaning and custom behavior;
- the exact Status contract and component identity;
- the exact `.NET 10 + CShells 0.0.28` provider profile;
- direct component-package/API integration;
- one exact endpoint contribution seam and owning assembler;
- planned artifact ownership and canonical-claim class;
- required evidence, gates, waivers, and blockers; and
- trace references for every governed claim.

Verify that no live `products/`, `feeds/`, receipt, or workspace snapshot was
created. The explanation may identify the planned package ID/version and
producing construction identity; the package byte digest remains explicitly
post-pack evidence.

## 4. Construct the complete component/API set

PowerShell:

```powershell
$constructJson = dotnet run --project $cliProject --no-build -- construct `
  --workspace $referenceWorkspace `
  --request (Join-Path $referenceWorkspace 'requests/construct.yaml') `
  --format json
$construct = $constructJson | ConvertFrom-Json
$construct | Select-Object outcome, furthestPhase, effectState, primaryDisposition
```

Bash:

```bash
dotnet run --project "$cli_project" --no-build -- construct \
  --workspace "$reference_workspace" \
  --request "$reference_workspace/requests/construct.yaml" \
  --format json
```

Expected:

```text
outcome: succeeded
furthestPhase: completion
effectState: committed
primaryDisposition: complete
```

The result must reference:

- two independently identified consumer bundles;
- the exact resolution lock and construction identity;
- a complete generated/consumer-owned artifact manifest;
- the isolated component feed and exact package digest;
- evaluation, external-tool, runtime-isolation, and publication evidence;
- a final admission/publication receipt; and
- `.program-kit/workspace.snapshot.json`.

No final receipt means the output is not admitted, regardless of files present.

## 5. Relocate and run the ordinary consumer

The focused acceptance test automates clean relocation, locked local restore,
dependency allowlisting, PE-reference inspection, build/test/publish, process
startup, and black-box Status observation:

```powershell
dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj `
  --no-restore --no-build `
  --filter 'FullyQualifiedName~RuntimeIsolation'
```

Bash uses the same command with line continuations changed to `\`.

The test copies only generated consumer products and declared local feeds to a
new clean root. It must prove:

- restore uses only the generated explicit local config and clean cache;
- package/assets/dependency graphs exactly match the allowlist;
- no Program Kit, Spec Kit, AI, prompt, transcript, capability, `.specify`, or
  repository project reference is present;
- the published API starts as an ordinary process; and
- its status operation returns the exact consumer-declared behavior.

## 6. Prove invalid input produces guidance and no writes

Use a separate copy of the invalid fixture:

```powershell
$invalidSource = Join-Path $programKitRoot 'tests/Fixtures/Reference.Status/Invalid/MissingSelection'
$invalidWorkspace = Join-Path ([IO.Path]::GetTempPath()) ('program-kit-status-invalid-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath $invalidSource -Destination $invalidWorkspace -Recurse
$invalidJson = dotnet run --project $cliProject --no-build -- explain `
  --workspace $invalidWorkspace `
  --request (Join-Path $invalidWorkspace 'requests/explain.yaml') `
  --format json
$invalid = $invalidJson | ConvertFrom-Json
```

Expected:

```text
outcome: needs-input
effectState: none
primaryDisposition: provide-input
diagnostic: program-kit.kernel/PKRES0001
```

The result must group all independently known missing fields, provide a
stateless continuation with exact choices, and create no live output.

The contract suite also proves duplicate route, missing assembler, ambiguous
order, incompatible contract, unavailable package/tool, and recoverable
pipeline-failure fixtures against the IDs in `contracts/diagnostics.md`.

## 7. Evaluate drift without mutation and repair explicitly

Modify one generated-owned file after valid construction:

```powershell
$generatedProject = Join-Path $referenceWorkspace 'products/Reference.Status.Api/Reference.Status.Api.csproj'
Add-Content -LiteralPath $generatedProject -Value '<!-- deliberate drift -->'
$driftedDigest = (Get-FileHash -LiteralPath $generatedProject -Algorithm SHA256).Hash
$evaluateJson = dotnet run --project $cliProject --no-build -- evaluate `
  --workspace $referenceWorkspace `
  --request (Join-Path $referenceWorkspace 'requests/evaluate.yaml') `
  --format json
$evaluate = $evaluateJson | ConvertFrom-Json
```

Expected:

```text
outcome: blocked
effectState: none
primaryDisposition: repair
diagnostic: program-kit.kernel/PKWSP0001
```

Hash the drifted file again and verify evaluation did not change it. Obtain the
exact inline proposed repair request from the typed remediation; do not infer or
alter its fields. Materializing that returned value is a caller-owned action,
not an effect of `evaluate`.

```powershell
$repairDocument = $evaluate.diagnostics.items[0].remediations[0].request.document
$repairRequest = Join-Path $referenceWorkspace 'requests/repair.generated.json'
$repairDocument | ConvertTo-Json -Depth 100 -Compress |
  Set-Content -LiteralPath $repairRequest -NoNewline -Encoding utf8
$repairJson = dotnet run --project $cliProject --no-build -- construct `
  --workspace $referenceWorkspace `
  --request $repairRequest `
  --format json
$repair = $repairJson | ConvertFrom-Json
```

Expected repair:

```text
outcome: succeeded
effectState: committed
primaryDisposition: complete
```

A second evaluation must be exact. Consumer-owned source bytes must be
unchanged across drift, evaluation, and repair.

## 8. Prove repeatability and publication recovery

```powershell
dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj `
  --no-restore --no-build `
  --filter 'FullyQualifiedName~Repeatability|FullyQualifiedName~PublicationRecovery'
```

The repeatability matrix varies:

- short ASCII and deep space/Unicode workspace paths;
- `en-US`, `tr-TR`, and `nl-NL`;
- input, provider, contribution, filesystem, and scheduling order; and
- clean local package caches.

It compares relative-path manifests and every artifact classified
`canonical-byte`. Externally packed package output must satisfy its exact named
verifier and may be upgraded to `canonical-byte` only when the pinned fixture
proves byte equality.

Fault injection after every publication mutation boundary must leave no trusted
admission, report an honest effect state, preserve consumer-owned bytes, and
require a separately authorized complete/rollback repair.

## 9. Human product review

A fresh contributor records answers to:

1. What exact products and contract were integrated?
2. Which package, provider, profile, and contribution seam were selected?
3. Which files are generated-owned versus consumer-owned?
4. Why is the current set admitted, stale, drifted, or untrusted?
5. What evidence supports each deterministic/conformance claim?
6. What safe next action follows the selected failure?
7. Can the answers be traced from the Integration Resolution Explanation and
   workspace snapshot without treating either as new source truth?

Passing commands without these answers does not satisfy the one-hour product
criterion.

## Cleanup

The workspaces are disposable test data. Remove only the exact temporary paths
created in this guide after confirming they are beneath the operating system's
temporary directory. Generated consumer outputs inside the test workspace have
no publication outside that workspace.
