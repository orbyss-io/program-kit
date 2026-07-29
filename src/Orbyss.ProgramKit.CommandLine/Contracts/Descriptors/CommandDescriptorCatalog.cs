using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;

/// <summary>Approved exact command grammar for the bootstrap CLI.</summary>
public static class CommandDescriptorCatalog
{
    private static readonly IReadOnlySet<string> HostKinds =
        new HashSet<string>(["api", "console", "worker"], StringComparer.Ordinal);

    private static readonly IReadOnlySet<string> GraphFormats =
        new HashSet<string>(["text", "json", "dot"], StringComparer.Ordinal);

    private static readonly IReadOnlySet<string> MarkdownFormat =
        new HashSet<string>(["markdown"], StringComparer.Ordinal);

    private static readonly IReadOnlySet<string> DiagnosticFormats =
        new HashSet<string>(["text", "json"], StringComparer.Ordinal);

    private static readonly IReadOnlySet<string> CapabilityProviders =
        new HashSet<string>(["claude", "codex"], StringComparer.Ordinal);

    private static readonly IReadOnlySet<string> TextOrJsonFormats =
        new HashSet<string>(["json", "text"], StringComparer.Ordinal);

    /// <summary>Gets every W050 command descriptor in exact ordinal order.</summary>
    public static ImmutableArray<CommandDescriptor> All { get; } =
    [
        Create(
            "validate",
            ["validate"],
            [new("artifact", false, true)],
            [new("manifest", true, false), Diagnostics()],
            "Validate one or more Program Kit artifacts against their registered schemas.",
            "Read-only; validation grants no authority and changes no artifact.",
            "program-kit validate artifact.json"),
        Create(
            "normalize",
            ["normalize"],
            [new("artifact", true, false)],
            [new("output", true, true), Diagnostics()],
            "Canonicalize one JSON artifact.",
            "Writes only the explicit output; it does not approve or adopt the artifact.",
            "program-kit normalize artifact.json --output canonical.json"),
        Create(
            "digest",
            ["digest"],
            [new("artifact", true, false)],
            [Diagnostics()],
            "Compute the canonical JSON SHA-256 digest of one artifact.",
            "Read-only.",
            "program-kit digest artifact.json"),
        Create(
            "render",
            ["render"],
            [new("artifact", true, false)],
            [
                new("format", true, true, MarkdownFormat),
                new("output", true, true),
                Diagnostics(),
            ],
            "Render one supported Program Kit artifact.",
            "Writes only the explicit output and grants no publication authority.",
            "program-kit render artifact.json --format markdown --output artifact.md"),
        Create(
            "graph",
            ["graph"],
            [new("design", true, false)],
            [new("format", true, false, GraphFormats), Diagnostics()],
            "Render one design dependency graph.",
            "Read-only unless an explicit output operation owns the result.",
            "program-kit graph design.json --format text"),
        Create(
            "versions.map",
            ["versions", "map"],
            [],
            [
                new("manifest", true, true),
                new("output", true, true),
                Diagnostics(),
            ],
            "Create an exact version map from a supplied manifest.",
            "Uses only supplied version evidence and does not select a version.",
            "program-kit versions map --manifest manifest.json --output version-map.json"),
        Create(
            "versions.assess",
            ["versions", "assess"],
            [],
            [
                new("observed", true, true),
                new("target", true, true),
                new("output", true, true),
                Diagnostics(),
            ],
            "Assess an observed and target version selection.",
            "Read-only assessment; it does not approve migration or publication.",
            "program-kit versions assess --observed observed.json --target target.json --output assessment.json"),
        Create(
            "check",
            ["check"],
            [new("artifact", false, false)],
            [
                new("manifest", true, false),
                new("profile", true, false),
                Diagnostics(),
            ],
            "Run one finite Program Kit check profile.",
            "Read-only verification over explicit inputs.",
            "program-kit check artifact.json --profile routine"),
        Create(
            "dotnet.materialize-console-inputs",
            ["dotnet", "materialize-console-inputs"],
            [new("request", true, false)],
            [
                new("workspace-root", true, true),
                new("output", true, true),
                new("build-consumer", false, true),
                Diagnostics(),
            ],
            "Build one explicit Console integration project and materialize its complete generation-input closure.",
            "Writes only Program Kit-owned materialized output and explicitly authorized ordinary project build output; it never edits consumer source.",
            "program-kit dotnet materialize-console-inputs console-input-request.json --workspace-root . --output .program-kit/console-inputs --build-consumer"),
        Create(
            "dotnet.generate-host",
            ["dotnet", "generate-host"],
            [new("kind", true, false, HostKinds)],
            [
                new("shell", true, true),
                new("host", true, true),
                new("artifact-manifest", true, true),
                new("output", true, true),
                Diagnostics(),
            ],
            "Generate one API, Console, or worker .NET host.",
            "Writes generated output only under the explicit output contract.",
            "program-kit dotnet generate-host console --shell shell.json --host pkid:host:example:console --artifact-manifest inputs.json --output generated"),
        Create(
            "dotnet.verify-host",
            ["dotnet", "verify-host"],
            [],
            [
                new("root", true, true),
                Diagnostics(),
            ],
            "Verify one integrity-sealed generated .NET host.",
            "Read-only verification.",
            "program-kit dotnet verify-host --root generated/Example.Console"),
        Create(
            "dotnet.refresh-host",
            ["dotnet", "refresh-host"],
            [],
            [
                new("request", true, true),
                new("preview", false, false),
                new("build-consumer", false, false),
                new("repair-generated-output", false, false),
                Diagnostics(),
            ],
            "Refresh one generated .NET host from an explicit request.",
            "Mutation is bounded by the request and explicit repair flags.",
            "program-kit dotnet refresh-host --request program-kit.host-generation.json --preview"),
        Create(
            "dotnet.generate-client",
            ["dotnet", "generate-client"],
            [],
            [
                new("openapi", true, true),
                new("tool-manifest", true, true),
                new("tool-package", true, true),
                new("namespace-name", true, true),
                new("class-name", true, true),
                new("output", true, true),
                Diagnostics(),
            ],
            "Generate one pinned Kiota client from explicit inputs.",
            "Writes only the explicit generated-client output.",
            "program-kit dotnet generate-client --openapi api.json --tool-manifest .config/dotnet-tools.json --tool-package microsoft.openapi.kiota.nupkg --namespace-name Example.Client --class-name ApiClient --output generated-client"),
        Create(
            "packages.prepare-local",
            ["packages", "prepare-local"],
            [],
            [
                new("workspace-manifest", true, true),
                new("output", true, true),
                Diagnostics(),
            ],
            "Prepare an exact local first-party package root.",
            "Local packaging only; no feed publication authority.",
            "program-kit packages prepare-local --workspace-manifest workspace-packages.json --output packages"),
        Create(
            "dotnet.publish-local",
            ["dotnet", "publish-local"],
            [],
            [
                new("shell", true, true),
                new("host", true, true),
                new("artifact-manifest", true, true),
                new("package-manifest", true, true),
                new("output", true, true),
                Diagnostics(),
            ],
            "Publish one selected generated .NET host to a local output.",
            "Local output only; no deployment, feed, or release authority.",
            "program-kit dotnet publish-local --shell shell.json --host pkid:host:example:api --artifact-manifest inputs.json --package-manifest packages/local-package-root-manifest.json --output published"),
        Create(
            "capabilities.render-catalog",
            ["capabilities", "render-catalog"],
            [new("index", true, false)],
            [new("output", true, true), Diagnostics()],
            "Render the repository authoring capability index.",
            "Authoring-only projection; not the consumer readiness catalog.",
            "program-kit capabilities render-catalog .agent-capabilities/capabilities/INDEX.md --output README.md"),
        Create(
            "capabilities.verify-bundle",
            ["capabilities", "verify-bundle"],
            [new("bundle", true, false)],
            [Diagnostics()],
            "Verify one content-only CapabilityBundle package.",
            "Read-only package verification.",
            "program-kit capabilities verify-bundle Orbyss.ProgramKit.CapabilityBundle.0.1.0-alpha.2.nupkg"),
        Create(
            "capabilities.initialize",
            ["capabilities", "initialize"],
            [],
            [
                new("provider", true, true, CapabilityProviders),
                new("workspace-root", true, true),
                Diagnostics(),
            ],
            "Initialize or refresh thin provider wrappers from this installed CLI.",
            "Writes only owned wrappers and the workspace lock; installation does not grant capability authority.",
            "program-kit capabilities initialize --provider codex --workspace-root ."),
        Create(
            "capabilities.catalog",
            ["capabilities", "catalog"],
            [],
            [
                new("workspace-root", true, true),
                new("format", true, false, TextOrJsonFormats),
                Diagnostics(),
            ],
            "Show release availability, role, registration, and freshness separately.",
            "Read-only.",
            "program-kit capabilities catalog --workspace-root . --format text"),
        Create(
            "capabilities.preflight",
            ["capabilities", "preflight"],
            [new("capability-id", true, false)],
            [
                new("workspace-root", true, true),
                new("format", true, false, TextOrJsonFormats),
                Diagnostics(),
            ],
            "Verify one capability's complete installed knowledge closure and active registration.",
            "Read-only and fail-closed; readiness grants no authority.",
            "program-kit capabilities preflight design-software --workspace-root . --format text"),
        Create(
            "capabilities.read",
            ["capabilities", "read"],
            [new("capability-id", true, false)],
            [new("workspace-root", true, true), Diagnostics()],
            "Return one ready capability's exact canonical Markdown bytes.",
            "Read-only; the returned guidance does not grant authority.",
            "program-kit capabilities read design-software --workspace-root ."),
        Create(
            "capabilities.read-resource",
            ["capabilities", "read-resource"],
            [new("resource-id", true, false)],
            [new("workspace-root", true, true), Diagnostics()],
            "Return one allow-listed supporting resource at exact packaged bytes.",
            "Read-only; supporting resources are inert and cannot be invoked as capabilities.",
            "program-kit capabilities read-resource software-change-troubleshooting --workspace-root ."),
        Create(
            "commands.describe",
            ["commands", "describe"],
            [new("command-key", true, false)],
            [new("format", true, false, TextOrJsonFormats), Diagnostics()],
            "Describe one finite backed Program Kit command.",
            "Read-only; command description does not authorize execution.",
            "program-kit commands describe dotnet.generate-host --format text"),
        Create(
            "schemas.list",
            ["schemas", "list"],
            [],
            [new("format", true, false, TextOrJsonFormats), Diagnostics()],
            "List every explicitly registered package-owned schema.",
            "Read-only and offline.",
            "program-kit schemas list --format text"),
        Create(
            "schemas.read",
            ["schemas", "read"],
            [new("schema-id", true, false)],
            [Diagnostics()],
            "Return one exact registered schema resource.",
            "Read-only, offline, and allow-list only.",
            "program-kit schemas read pkid:schema:program-kit:csharp-build-gate-definition@0.1.0-alpha.2"),
        Create(
            "diagnostics.explain",
            ["diagnostics", "explain"],
            [new("diagnostic-id", true, false)],
            [new("format", true, false, TextOrJsonFormats), Diagnostics()],
            "Explain ownership, evidence, remediation, and stop behavior for a diagnostic.",
            "Read-only; unknown or external diagnostics receive no invented Program Kit remediation.",
            "program-kit diagnostics explain PKCLI008 --format text"),
        Create(
            "artifacts.inspect",
            ["artifacts", "inspect"],
            [new("artifact", true, false)],
            [
                new("schema", true, false),
                new("format", true, false, TextOrJsonFormats),
                Diagnostics(),
            ],
            "Inspect and validate one explicit Program Kit artifact without changing it.",
            "Read-only; inspection does not repair, migrate, normalize, or approve.",
            "program-kit artifacts inspect gate-definition.json --schema pkid:schema:program-kit:csharp-build-gate-definition@0.1.0-alpha.2 --format text"),
        Create(
            "csharp-gate.validate-definition",
            ["csharp-gate", "validate-definition"],
            [new("definition", true, false)],
            [Diagnostics()],
            "Validate one canonical C# gate definition.",
            "Read-only validation.",
            "program-kit csharp-gate validate-definition gate-definition.json"),
        Create(
            "csharp-gate.render-definition",
            ["csharp-gate", "render-definition"],
            [new("definition", true, false)],
            [new("output", true, true), Diagnostics()],
            "Render one valid C# gate definition.",
            "Writes only the explicit output.",
            "program-kit csharp-gate render-definition gate-definition.json --output gate.md"),
        Create(
            "csharp-gate.scaffold",
            ["csharp-gate", "scaffold"],
            [new("request", true, false)],
            [new("output", true, true), Diagnostics()],
            "Scaffold an explicitly selected consumer analyzer.",
            "Writes only the requested scaffold and invents no gate selection.",
            "program-kit csharp-gate scaffold scaffold-request.json --output Analyzer"),
        Create(
            "csharp-gate.bind",
            ["csharp-gate", "bind"],
            [new("request", true, false)],
            [new("output", true, true), Diagnostics()],
            "Bind an exact C# gate selection.",
            "Writes only the explicit binding output and grants no approval.",
            "program-kit csharp-gate bind binding-request.json --output gate"),
        Create(
            "csharp-gate.verify",
            ["csharp-gate", "verify"],
            [new("request", true, false)],
            [new("output", true, true), Diagnostics()],
            "Verify an exact C# gate execution request.",
            "Read-only verification apart from explicit evidence output.",
            "program-kit csharp-gate verify verification-request.json --output evidence"),
        Create(
            "csharp-gate.describe-definition",
            ["csharp-gate", "describe-definition"],
            [],
            [new("format", true, false, TextOrJsonFormats), Diagnostics()],
            "Describe gate-definition schemas, conditions, order keys, and public analyzer selections.",
            "Read-only; no gate choice or approval is inferred.",
            "program-kit csharp-gate describe-definition --format text"),
        Create(
            "csharp-gate.materialize-definition",
            ["csharp-gate", "materialize-definition"],
            [new("draft", true, false)],
            [new("output", true, true), Diagnostics()],
            "Validate and canonicalize one complete gate-definition draft.",
            "Writes canonical bytes only; no missing semantic or human value is invented.",
            "program-kit csharp-gate materialize-definition draft.json --output gate-definition.json"),
    ];

    private static CommandOptionDefinition Diagnostics() =>
        new("diagnostics", true, false, DiagnosticFormats);

    private static CommandDescriptor Create(
        string key,
        ImmutableArray<string> path,
        ImmutableArray<CommandArgumentDefinition> arguments,
        ImmutableArray<CommandOptionDefinition> options,
        string description,
        string authority,
        string example) =>
        new(
            key,
            path,
            arguments,
            options,
            description,
            authority,
            example);
}
