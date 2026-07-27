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

    /// <summary>Gets every W050 command descriptor in exact ordinal order.</summary>
    public static ImmutableArray<CommandDescriptor> All { get; } =
    [
        Create(
            "validate",
            ["validate"],
            [new("artifact", false, true)],
            [new("manifest", true, false), Diagnostics()]),
        Create(
            "normalize",
            ["normalize"],
            [new("artifact", true, false)],
            [new("output", true, true), Diagnostics()]),
        Create(
            "digest",
            ["digest"],
            [new("artifact", true, false)],
            [Diagnostics()]),
        Create(
            "render",
            ["render"],
            [new("artifact", true, false)],
            [
                new("format", true, true, MarkdownFormat),
                new("output", true, true),
                Diagnostics(),
            ]),
        Create(
            "graph",
            ["graph"],
            [new("design", true, false)],
            [new("format", true, false, GraphFormats), Diagnostics()]),
        Create(
            "versions.map",
            ["versions", "map"],
            [],
            [
                new("manifest", true, true),
                new("output", true, true),
                Diagnostics(),
            ]),
        Create(
            "versions.assess",
            ["versions", "assess"],
            [],
            [
                new("observed", true, true),
                new("target", true, true),
                new("output", true, true),
                Diagnostics(),
            ]),
        Create(
            "check",
            ["check"],
            [new("artifact", false, false)],
            [
                new("manifest", true, false),
                new("profile", true, false),
                Diagnostics(),
            ]),
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
            ]),
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
            ]),
        Create(
            "packages.prepare-local",
            ["packages", "prepare-local"],
            [],
            [
                new("workspace-manifest", true, true),
                new("output", true, true),
                Diagnostics(),
            ]),
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
            ]),
        Create(
            "capabilities.render-catalog",
            ["capabilities", "render-catalog"],
            [new("index", true, false)],
            [new("output", true, true), Diagnostics()]),
        Create(
            "capabilities.verify-bundle",
            ["capabilities", "verify-bundle"],
            [new("bundle", true, false)],
            [Diagnostics()]),
        Create(
            "capabilities.initialize",
            ["capabilities", "initialize"],
            [],
            [
                new("provider", true, true, CapabilityProviders),
                new("workspace-root", true, true),
                new("program-kit-root", true, true),
                Diagnostics(),
            ]),
    ];

    private static CommandOptionDefinition Diagnostics() =>
        new("diagnostics", true, false, DiagnosticFormats);

    private static CommandDescriptor Create(
        string key,
        ImmutableArray<string> path,
        ImmutableArray<CommandArgumentDefinition> arguments,
        ImmutableArray<CommandOptionDefinition> options) =>
        new(key, path, arguments, options);
}
