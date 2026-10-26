# Framework reuse and native EF migrations

The approved repair addresses a planning error in which separate deployment credentials and no
startup DDL became a requirement for a custom SQL migration runner/journal. The private consumer
diagnostic remains a reported observation; this change uses fictional fixtures and maintained source.
It neither rewrites that consumer nor claims to reproduce its agent's reasoning.

## Guidance to inspect

- `extensions/program-kit-governance/references/programming-guardrails.md`: selected-framework
  mechanisms and extension points precede replacement infrastructure. Plans/tasks and semantic review
  must explain a concrete unmet requirement; graph/test success and assistant-written tasks cannot.
- `extensions/program-kit-dotnet/references/persistence-profiles.md`: provider-owned EF migrations,
  snapshot/history, native artifacts and design-time creation now belong to the actual selected
  persistence rule. Separate deployment credentials do not select a new engine. Legitimate SQL inside
  EF migrations and justified separate EF migration assemblies remain available.
- `extensions/program-kit-governance/scripts/phase_obligations.py` and its canonical registry:
  initial output surfaces the decision and focused lookup resolves the complete attributable rule.
  Standalone governance still handles absent optional technology references. No lifecycle gate,
  approval receipt, automated semantic verdict or new delivery engine was added.
- Plan/tasks templates and architecture/implementation commands challenge necessity as well as
  dependency directions. Lifecycle guidance now distinguishes read-only compatibility admission
  from schema-changing deployment.
- `docs/coding-context.md` and `docs/coding-evaluation.md`: current project/check commands, actual
  verification and ordinary review replace obsolete prepare/reconcile/checkpoint instructions.

## Native example and proof

The existing `extensions/program-kit-dotnet/references/examples/postgresql-lifecycle/README.md`
describes authoring/deployment and proof limits. `NativeMigrationContext` derives from the selected
Foundation base; its design factory is tooling-only. Runtime still uses real Foundation registration,
shell/unit leases and independent context disposal. The executable is a synthetic runtime probe,
not a new application migration engine. The original fixture SQL/journal remains explicitly separate.

`tests/validate_postgresql_lifecycle.py` now creates native EF migrations/snapshot in an isolated copy,
builds them, checks pending model changes, generates idempotent SQL and deploys/repeats through native
EF commands. Independent database observations cover EF history and runtime effects. Negative cases
cover missing schema, denied migration credentials, unreadable history, pending migration and denied
history/schema writes. Existing concurrency, foreign-object/owner and cleanup regressions remain.
The single inventory owns the focused command and its 300-second target/600-second hard timeout.

Run from this checkout:

```text
python scripts/run_validation.py --check validate_postgresql_lifecycle --reason "native EF/Foundation migrations, separate deployment and read-only admission"
python scripts/run_validation.py --suite Affected --changed-from 6c472846
```

Run Integrity first through `scripts/Test-ProgramKit.ps1`; use the existing prepared Python for
checks importing Spec Kit. The native qualifier needs the exact SDK in the managed global.json and
the existing Docker engine. A missing SDK is a limitation, not native workflow acceptance.

Synthetic phase tests exercise EF/PostgreSQL constraints plus an unjustified runner proposal,
framework reuse on an ordinary custom stack, SQLite deployment limitations, and preservation of
legitimate EF SQL/assembly extensions. They establish emitted guidance and read-only selection,
not arbitrary AI obedience or architecture judgment. The native validator supplies separate actual
compiled/database proof only when its run succeeds. SQL Server/SQLite runtime and bundle platform
qualification are outside this PostgreSQL example.

Execution results, original failures, timing and remaining limitations belong in the PR validation
summary with ignored local run links. Package CI independently proves exact archive installation on
Windows/Linux. Release preparation grants no tag or publication authority. The candidate remains
the unpublished 1.0.0-preview.1; consumed dependency profiles, pins and locks are unchanged.
