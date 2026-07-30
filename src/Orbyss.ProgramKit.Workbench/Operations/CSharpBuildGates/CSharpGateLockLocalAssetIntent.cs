namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>
/// One explicit repository asset not already inventoried by the definition.
/// </summary>
public sealed record CSharpGateLockLocalAssetIntent(
    CSharpGateLockInventoryKind Kind,
    string RepositoryRelativePath);
