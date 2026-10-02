# Coordinated Spec Kit source fix

`spec-kit-1.0.1-python-runtime.patch` targets the maintained
[GitHub Spec Kit source](https://github.com/github/spec-kit/tree/9118ed15a0ba65053469a94c560ea5d233f75884)
at commit `9118ed15a0ba65053469a94c560ea5d233f75884` (tag `v1.0.1`). It changes the
core command generator, constitution template, native hooks/scripts, Codex
dispatch adapter and command-step artifact contract, with core-owned tests.
It is a source patch, not an edit to installed consumer files or the user's CLI.
The upstream license remains applicable.

From a separate clone of that exact source, apply and review the patch:

```powershell
git switch -c codex/program-kit-python-runtime
git rev-parse HEAD
git apply --check '<program-kit-checkout>/patches/spec-kit-1.0.1-python-runtime.patch'
git apply '<program-kit-checkout>/patches/spec-kit-1.0.1-python-runtime.patch'
```

Regenerated Python commands bind an absolute, validated Python >=3.11 executable
with PyYAML >=6. `SPECKIT_PYTHON` is an explicit selection; otherwise the first
`python` on PATH is resolved and validated. `.specify/python-runtime.json` records
that selection. Native helper scripts consult the same record. Generation fails
on missing dependencies rather than choosing another environment. A relocated
repository or intentional interpreter change requires explicit regeneration of
the local integration instructions and a reviewed runtime-record migration;
absolute paths are not a portability claim.

Codex dispatch captures both streams and a schema-constrained final result.
Command steps retain process success separately from worker outcome. Optional
`required_artifacts` and `artifact_validator` contracts fail a worker step when
output is absent or rejected; subsequent semantic validators and human gates
remain independent. Bootstrap declares artifact checks for every producer.

The Program Kit regression fixture applies the source patch to a disposable copy
of the exact installed 1.0.1 baseline and tests generated consumers. It never
changes that installed package. It excludes upstream tests/docs when reconstructing
the wheel layout; the separate source checkout runs the core-owned tests.

This patch has not been submitted or released upstream. Before Program Kit
publication, land/distribute the core fix, choose and pin its actual released
version in CI/Release/install guidance, and run the real installation/upgrade
gates with it. Do not treat the patched test fixture as a public Spec Kit update.
Unpatched 1.0.1 intentionally fails the new production dispatch preflight.
