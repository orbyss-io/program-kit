# Orbyss building blocks

Program Kit is the AI extension that reasons about architecture and implementation. Orbyss Foundation and Orbyss Forms are independently versioned technical building blocks that Program Kit can recommend and compose. They are not an "Orbyss platform"; Orbyss is a software factory and AI consultancy.

The machine-readable source of truth is [orbyss-building-blocks.json](orbyss-building-blocks.json). Consult it during intake, architecture, planning, implementation, and managed .NET synchronization whenever a request selects .NET, authentication, APIs, tasks, domain events, forms, localization, or MCP.

## Decision order

1. Model the consumer's bounded contexts, journeys, business rules, security boundary, and operational constraints without assuming an Orbyss package.
2. Match required technical capabilities to a composition in the manifest.
3. Select the smallest package closure. Optional packages require an explicit need.
4. Record the Foundation and Forms versions independently in architecture evidence and central package management.
5. Preserve consumer ownership: building blocks implement technical mechanisms, never the product's business meaning.
6. Validate the generated consumer against the pinned published packages. Program Kit does not reach into either component repository or copy its source.

## Foundation

Repository: https://github.com/orbyss-io/dotnet-foundation

Foundation supplies application-neutral .NET/API building blocks: host composition, analyzers, authentication profiles, downstream credentials, domain events, background tasks, OpenAPI, public discovery, problem details, MCP transport, and the Keycloak administration adapter.

The host image is a composition substrate. It is not an application framework that owns business features. A consumer's feature package, configuration, routes, persistence, authorization policy, and deployment evidence remain consumer-owned.

Important rules:

- Keep `FoundationFeatureIdentity`, `AssemblyName`, `PackageId`, and `[ShellFeature]` identity aligned.
- Choose exactly one browser authentication profile: BFF cookie or SPA-PKCE.
- Treat DPoP, token exchange, client credentials, and downstream API support as explicit threat-model decisions.
- Use `Orbyss.Foundation.DomainEvents` for in-process domain events only. Durable cross-context or cross-service messages need a consumer-owned integration-event contract and transport.
- `Orbyss.Foundation.Mcp.AspNetCore` owns the authenticated Streamable HTTP transport. Bounded contexts contribute explicit tool catalogs.
- Configuration owned by these packages lives under the `Foundation` root.

## Forms and localization

Repository: https://github.com/orbyss-io/forms

Forms supplies semantic contracts, deterministic JSON Forms compilation, runtime rendering contracts, draft/submission operations, managed authoring, localization, storage adapters, MCP tool contributors, and thin Angular/React/Vue bindings.

Important rules:

- The consumer owns what fields, actions, lookup values, pricing, validation meaning, publication workflow, and authorization mean.
- Choose packages by lifecycle: immutable runtime, end-user operations, or trusted management. Do not install management packages into a public runtime without an explicit boundary.
- Choose one renderer binding and only the optional UI capabilities actually used.
- Choose one concrete storage adapter for each storage contract. In-memory adapters are for reference/testing and are not durable production storage.
- Forms and localization MCP contributors require Foundation MCP transport; they do not map their own transport.
- A compiled release is immutable and hash-bound. Changes create a new release and breaking changes require an explicit migration policy.

## Version and release independence

Program Kit's version describes AI-extension behavior. It never determines a Foundation or Forms version. The component pins in the manifest change only after:

- the component release is publicly available;
- Program Kit's consumer compatibility tests pass against that exact release;
- migrations and changed selection rules are reflected in this reference and the templates.

Do not test Program Kit by building component source. Likewise, changes to Program Kit must not trigger Foundation or Forms publication pipelines.

