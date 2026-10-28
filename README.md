# Program Kit

<!-- latest-published-release:start -->
Latest available release: **[v0.14.3](https://github.com/orbyss-io/program-kit/releases/tag/v0.14.3)**. Before installing, follow the [current installation instructions](#install-in-a-repository), including initializer corrections. [Check the latest release](https://github.com/orbyss-io/program-kit/releases/latest) for the kit version.
<!-- latest-published-release:end -->

The source candidate is **1.0.0-preview.1**. Its preview assets become installable after
publication; the published release above remains the available stable version.

Program Kit adds extensible, customizable architecture and engineering knowledge to
Spec Kit's native specify, clarify, plan, tasks, analyze and implement phases. Skills
help the user and agent make informed decisions. Focused scripts handle useful
mechanical work such as diagram export, validation and selected scaffolding.

A product-intake conversation establishes product intent, constitution, consequential
ADRs, technologies, domain/C4 architecture, journeys and an outcome roadmap. Existing
architecture files can be supplied as input. Once the user and agent agree, continue
to the first feature intake and ordinary Spec Kit work.

Plans and tasks carry meaningful choices and agreed human review points. The agent
must stop at an agreed review boundary and obtain the user's decision before dependent
work continues. Missing toolkit receipts, hashes or hidden checkpoint state do not
independently prevent progress. Revisit a decision when its meaning changes.

Use relevant knowledge progressively. Curated defaults offer a convenient engineering
route; users can research other technologies and document local overrides. Selected
SDK contracts, compiler/analyzer checks, security and behavioral tests still apply.
A passing script establishes only what it actually checked.

## Install in a repository

Use a normal user-owned terminal for installation and updates. On Windows, agent-owned
initialization can leave `.agents` or `.specify` inaccessible to the human account; see
[Windows setup](docs/codex-desktop-windows.md). Initialization starts no coding agent.

Prerequisites are Git, shared Python >=3.11, a supported public Spec Kit `>=1.1.1,<2`
and the selected coding integration. CI tests the exact Spec Kit 1.2.1 pin. The selected
resolver interpreter needs `PyYAML>=6,<7` and `packaging>=23`. The initializers diagnose
missing prerequisites and report their exact selected executable.

Device/global tool installation and upgrades are human-owned. Agents detect a mismatch,
explain its dependent action and provide an inspectable device-appropriate preparation
script. Agents may restore declared project packages using installed device tools.
See the [device policy](extensions/program-kit-governance/references/device-toolchain-policy.md).

The repository can already contain software and documentation. Initialize its Git work
tree yourself before installing. Inspect the release and catalogs before trusting them.
For the preview, select its exact version explicitly after it is published.

### Windows

```powershell
Invoke-WebRequest `
  https://github.com/orbyss-io/program-kit/releases/download/v1.0.0-preview.1/Initialize-ProgramKit-1.0.0-preview.1.cmd `
  -OutFile Initialize-ProgramKit.cmd
.\Initialize-ProgramKit.cmd codex
```

The command initializer works with PowerShell AllSigned without lowering execution
policy. For a custom tool location, set `PROGRAM_KIT_SPECIFY`, `PROGRAM_KIT_GIT` or
`SPECKIT_PYTHON` to the existing shared executable in that terminal. Preserve the stage
and underlying diagnostic if setup fails; do not mask it with another local tool copy.

### Bash on Linux, macOS, or WSL

```bash
curl -fL \
  https://github.com/orbyss-io/program-kit/releases/download/v1.0.0-preview.1/Initialize-ProgramKit-1.0.0-preview.1.sh \
  -o Initialize-ProgramKit.sh
bash ./Initialize-ProgramKit.sh codex
```

Replace `codex` with the selected Spec Kit integration. The installer uses the actual
release component archives through native Spec Kit catalogs. The small composition
archive and complete tooling archive have separate responsibilities and share the
verified release inventory. Keep extension, preset and bundle catalogs available when
installing a native composition; its archive does not contain every primitive.

### Start product intake

Open the consumer repository in your coding assistant and invoke
`speckit.program-kit-governance.product-intake` (Codex skill:
`$speckit-program-kit-governance-product-intake`). Describe the idea naturally and select
existing architecture documents as useful input. Follow Program Kit's grilling method.

Review the synthesis, constitution and consequential decisions with the human. Use a
small language-neutral map for domain/C4 content by default, with readable ADRs and
explanations. Diagram views are generated from that model. Scale detail to the product;
local alternatives do not need a qualification ceremony. Preparing architecture does
not establish runtime compatibility or acceptance of an implemented feature.

Continue with `speckit.program-kit-governance.specification-intake`, then the native
Spec Kit phases. Material unanswered decisions pause dependent work; independent work
can continue. The user's explicit review decisions belong in the ordinary documents
and conversation, not a second approval database.

### Existing 0.x consumers

The preview is a deliberate re-onboarding boundary. Existing consumers repeat product
intake and may select their architecture files as input. Old workflow approvals,
checkpoints and receipts are not converted into new authority. Keep application code,
Spec Kit artifacts, architecture documents, ADRs and user customizations. Inspect the
installation boundary before replacing toolkit-owned files. No automatic 0.x semantic
migration or elaborate migration guide is supplied.

Subsequent preview releases preserve ongoing authored product and specification work.
Any later breaking change requires an explicit announcement. Published historical
release bytes remain immutable.

## Knowledge and optional engineering tools

Program Kit supplies focused references at the relevant phase. Read detailed examples
when they affect a concrete choice. Extend or override knowledge in the consumer's
normal architecture documents, plans and repository instructions. Record why a local
choice applies and what actual checks will establish it.

Choosing our recommended stack provides its coherent default instructions and helpers.
Using the knowledge does not require adopting every generator or runner. A scaffold or
composition helper validates the contracts needed for its own operation. A running
application is required only when the selected operation or test needs it.

### .NET profile

The .NET guidance and selected Foundation composition offer reusable engineering
patterns. Foundation, Forms and Localization are independently developed software:
[Foundation](https://github.com/orbyss-io/dotnet-foundation),
[Forms](https://github.com/orbyss-io/forms) and
[Localization](https://github.com/orbyss-io/localization).
Retain exact selected dependency versions and locks. Knowledge from another software
version cannot silently establish the behavior of the selected one. Optional recipe
qualification establishes the generator's supported output; users can choose another
approach and verify their actual implementation.

## Vertical slices and modularity

Deliver useful user outcomes through coherent vertical slices. Discuss the proposed
scope, dependencies, tests and human review points before implementation. Keep shared
engineering work proportional to the first outcome that needs it. Domain ownership,
lifecycles, boundaries and policies inform decisions throughout the phases.

Application engineering remains visible in native project files, source, tests and
selected `eng/`/deployment inputs. Builds and deployment must not depend on AI or
Program Kit authoring state. See [consumer engineering](docs/consumer-engineering.md).
The future downloadable pack ecosystem remains a separate feature in
[#57](https://github.com/orbyss-io/program-kit/issues/57).

## Development and release

Use the repository [development skill](.agents/skills/program-kit-development/SKILL.md)
and [validation procedure](docs/validation.md). Ordinary development runs:

```powershell
./scripts/Test-ProgramKit.ps1 -Python <prepared-python>
python scripts/run_validation.py --suite Affected --changed-from <base>
```

The inventory selects affected contracts; it does not authorize a full runtime matrix,
paid coding agents or device installation. Failures, missing prerequisites, timeouts
and budget overruns remain visible. Known local Firefox limitations remain documented.
Use synthetic examples. Private consumer material and local execution records stay
out of commits and GitHub.

Package CI builds once, then checks clean Windows/Linux installation, installed helpers
and applicable security contracts. Publication promotes those exact inspected bytes
only after native human approval. Preview versions are prereleases and are not promoted
as the stable latest release. See [releasing](docs/releasing.md). A version bump, commit
or green local test never authorizes publication.

## Release assets

Native component ZIPs contain governance knowledge/skills, building-block helpers,
.NET engineering resources and the template preset. `program-kit-<version>.zip` is the
small native composition; `program-kit-tooling-<version>.zip` carries complete local
installation tooling. Exact initializer assets, release notes, checksums and candidate
metadata accompany the selected release. No native carrier may exceed 512 entries.
Package hashes protect distribution integrity; they are not authoring approval gates.

## UI experience and public discovery

Apply selected UI, branding, accessibility and localization guidance to the product's
actual needs. Research current tools and honor user review of consequential branding.
Install only the project dependencies and runtime capabilities the product selects.

## Consumer repair feedback

For explicitly scoped repair observations, use the installed repair-request guidance.
Contributor intake follows the repository-only repair evaluator and
[maintenance procedure](docs/maintenance/repair-feedback.md). Ordinary phase hooks do
not poll chats, contact consumers or start agents. Keep private observations local;
public submissions require their own explicit authorization.

## License

[MIT](LICENSE).
