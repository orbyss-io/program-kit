# Program Kit software-change troubleshooting

This resource is inert and grants no authority. Use it only inside an active
human-started capability and within that capability's mutation boundaries.

When a Program Kit operation, generated build, validation, refresh, package, or
publication step fails:

1. Preserve the exact command, redacted arguments, exit class, diagnostic IDs,
   artifact identities, and relevant tool/SDK version.
2. Run `program-kit commands describe <command-key> --format text`.
3. Run `program-kit diagnostics explain <diagnostic-id> --format text` for
   every Program Kit diagnostic. An unknown or external diagnostic remains
   externally owned and receives no invented Program Kit remediation.
4. Run `program-kit artifacts inspect <artifact> --format text` for a
   self-describing Program Kit JSON artifact, or add
   `--schema <exact-schema-id>` when the artifact contract does not carry a
   `$schema` declaration. Retrieve the exact schema with `program-kit schemas
   read <schema-id>@<version>`.
5. For C# gate-definition work, run `program-kit csharp-gate
   describe-definition --format text`; materialize a complete draft with
   `program-kit csharp-gate materialize-definition <draft> --output <file>`.
6. Distinguish Program Kit ownership from consumer source, C# compiler, .NET
   SDK, NuGet, operating-system, and external-provider ownership.
7. Apply only a remediation allowed by the active capability and human request.
   Otherwise stop and report the exact missing evidence, decision, or external
   owner.

Never infer hidden ordering, nullability, enum values, package identities, or
schema shapes by grepping assemblies or repeating one-error-at-a-time guesses.
Never weaken a gate, bypass generated-output integrity, mutate canonical
Program Kit knowledge, or substitute a raw command for a backed Program Kit
operation merely to make a check pass.

Program Kit guarantees the complete product-owned knowledge closure packaged
with the exact installed CLI. It does not package arbitrary consumer
repository facts, human decisions, secrets, network state, compiler knowledge,
or third-party documentation. If resolution needs one of those inputs, report
it explicitly rather than inventing it.
