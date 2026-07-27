using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>One exact repository-relative content item.</summary>
public sealed record CSharpGateContentItem(
    string RepositoryRelativePath,
    Sha256Digest Digest);
