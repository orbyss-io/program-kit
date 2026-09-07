# Orbyss Foundation and Forms capability routing

Orbyss is a software factory and AI consultancy. Orbyss Foundation and Orbyss Forms are reusable, independently versioned building blocks; they are not a platform and Program Kit does not own their runtime source.

When one of the signals below is present, route the architecture and implementation work to the Program Kit .NET extension's full building-block reference:

`.specify/extensions/program-kit-dotnet/references/orbyss-building-blocks.md`

Its machine-readable package, version, and composition contract is:

`.specify/extensions/program-kit-dotnet/references/orbyss-building-blocks.json`

Use the references for:

- .NET APIs, modular hosts, problem details, OpenAPI, public discovery, background tasks, domain events, authentication, downstream credentials, Keycloak administration, or MCP;
- schema-driven forms, localization, form authoring, draft/submission operations, storage adapters, and Angular/React/Vue form rendering;
- determining the smallest package closure and recording Foundation and Forms versions independently.

Never infer that selecting a managed building block transfers business ownership to it. Consumer bounded contexts retain domain semantics, authorization meaning, workflows, pricing, validation policy, storage durability decisions, and release policy.

