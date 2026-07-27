namespace Orbyss.ProgramKit.Workbench.Operations.Versioning;

/// <summary>Adds semantic type and stable identity to one manifest requirement.</summary>
/// <param name="Id">Stable edge identity.</param>
/// <param name="SourceIdentity">Identity of the dependent manifest.</param>
/// <param name="TargetIdentity">Identity of the matching required contract.</param>
/// <param name="Kind">Semantic dependency kind.</param>
public sealed record VersionDependencyDeclaration(
    ProgramKitIdentifier Id,
    ProgramKitIdentifier SourceIdentity,
    ProgramKitIdentifier TargetIdentity,
    VersionDependencyKind Kind);
