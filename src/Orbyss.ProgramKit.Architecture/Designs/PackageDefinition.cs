using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>An independently versioned package boundary.</summary>
public sealed record PackageDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    SemanticVersion Version,
    ImmutableArray<ProgramKitIdentifier> ProjectIds,
    ImmutableArray<ProgramKitIdentifier> PackageDependencyIds,
    ImmutableArray<ProgramKitIdentifier> PublicContractIds,
    string CompatibilityBoundary);
