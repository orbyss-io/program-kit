# Versioned live test fixtures

`catalog.json` lists use cases by stable ID and version. Each version lives in
`<use-case>/v<version>/`, with its scenario manifest and disposable-project input
under `fixture/`. Commit these inputs; keep generated runs, logs and receipts in
the ignored `artifacts/live-acceptance/` tree.

From the repository root, list or verify a selected fixture without starting an agent:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'tests'
python -m live.v2.fixture_catalog --list
python -m live.v2.fixture_catalog --fixture price-calculator-approved-intake --version 1
```

The resolver returns the scenario directory and its content authority for the
runner to bind into phase-specific authorization. Choosing a fixture does not
authorize a paid run. The existing building-block runner accepts scenario paths.
Workflow cases use the explicit phases described in
[workflow-live-acceptance.md](../../../docs/workflow-live-acceptance.md), which
preserve real human gates and never replace the agent's selection with a template.

Add another use case by creating its version directory and manifest, then adding
one catalog entry. Once a version is used as evidence, preserve its content and
add a new version for changed input. Runs must copy inputs to a disposable project
and preserve the selected fixture's ID, version and digest in evidence.
