using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

/// <summary>Exact local foreign-OpenAPI input and reviewed Kiota C# options.</summary>
public sealed record KiotaForeignClientGenerationRequest(
    string OpenApiPath,
    string OutputRoot,
    string ToolManifestPath,
    string ToolPackagePath,
    string NamespaceName,
    string ClassName,
    ImmutableArray<string> IncludePatterns,
    ImmutableArray<string> ExcludePatterns);
