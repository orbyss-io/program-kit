using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>One exact local asset supplied to offline gate binding.</summary>
public sealed record CSharpGateLocalAssetBinding(
    string RepositoryRelativePath,
    Sha256Digest Digest);
