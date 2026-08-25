# Program Kit

Program Kit supplies reusable Spec Kit workflows and governance components for architecture-governed software delivery. Its first workflow turns an initial design into an architecture-governed Spec Kit project. Program Kit is maintained independently from the application repositories that consume it.

The executable behavior lives in a Spec Kit workflow. The bundle is the versioned distribution layer around that workflow and its governance extension.

## Install in a new repository

Prerequisites:

- Spec Kit `1.0.1` or a compatible `1.x` release.
- A supported coding-agent integration.
- Trust in this repository's catalog and release contents. Inspect them before marking the extension catalog install-allowed.

From the root of a new repository, initialize Spec Kit and register the three Program Kit catalogs:

```powershell
specify init . --integration codex --non-interactive

specify extension catalog add `
  https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/extensions.json `
  --name program-kit `
  --install-allowed

specify workflow catalog add `
  https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/workflows.json `
  --name program-kit

specify bundle catalog add `
  https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/bundles.json `
  --id program-kit `
  --policy install-allowed

# Spec Kit 1.0.1 workaround: preinstall the catalog workflow before the bundle.
specify workflow add program-kit-bootstrap
specify bundle install program-kit-bootstrap
```

Replace `codex` with the integration you use. The bundle itself is integration-agnostic.

### Spec Kit 1.0.1 compatibility note

Spec Kit 1.0.1's bundle adapter incorrectly routes a catalog workflow ID through its local-development installer. Preinstalling `program-kit-bootstrap` as shown above is the tested workaround: the bundle then recognizes the pinned workflow and installs the governance extension. Until Spec Kit fixes the adapter, remove the workflow separately with `specify workflow remove program-kit-bootstrap` if you uninstall the bundle.

Run the architecture bootstrap with the path to your initial design:

```powershell
specify workflow run program-kit-bootstrap `
  --input initial_design=./initial-design.md `
  --input integration=auto
```

The workflow pauses twice for human review. Continue a paused run after reviewing its generated artifacts:

```powershell
specify workflow status
specify workflow resume <run-id> --input assessment_verdict=approve
specify workflow resume <run-id> --input bootstrap_verdict=approve
```

In a new Codex session, you can simply provide this README and your initial design, then ask Codex to install the bundle and run `program-kit-bootstrap`.

## What it installs

- `program-kit-bootstrap` workflow: inventories the design, performs current research, creates the architecture baseline and decision backlog, evaluates tooling, and pauses at human review gates.
- `program-kit` extension: supplies reusable bootstrap and validation commands.
- Mandatory hooks after `speckit.specify` and `speckit.plan`, before `speckit.implement`, and after implementation to detect architecture drift.

## Governance model

- Project-specific architecture decisions require a human-approved ADR before becoming `Accepted`.
- Technologies discovered in an initial design begin as `Proposed`; mentioning a technology does not accept it.
- Generic engineering guardrails apply by default and are revalidated against current primary sources and project context during every bootstrap.
- The reusable software language is `Identity + Intent + Context -> Policies -> Decision -> Transition -> Effects -> Admission -> Outcome`.
- Required admission and optional observation are separate contracts. Invisible fire-and-forget behavior and ambiguous empty policy results are forbidden.

## Development and release

Run the local source checks and disposable install test:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Build all release artifacts:

```powershell
uv run --with "specify-cli==1.0.1" python ./scripts/build_release.py
```

Pushing a SemVer tag matching `VERSION` creates a GitHub release:

```powershell
git tag v0.1.2
git push origin v0.1.2
```

The release workflow validates all manifests and catalog metadata, creates deterministic ZIP files and SHA-256 checksums, generates GitHub build-provenance attestations, and publishes the assets. The CI and release actions are pinned to immutable commits; Dependabot proposes action updates.

## Release assets

- `program-kit-bootstrap-<version>.zip`: installable Spec Kit bundle.
- `program-kit-extension-<version>.zip`: standalone extension package.
- `program-kit-workflow-<version>.zip`: standalone workflow package.
- `SHA256SUMS`: exact artifact digests.

Verify a downloaded artifact:

```powershell
gh attestation verify program-kit-bootstrap-0.1.2.zip --repo orbyss-io/program-kit
Get-FileHash program-kit-bootstrap-0.1.2.zip -Algorithm SHA256
```

## License

Program Kit is open source under the [MIT License](LICENSE).
