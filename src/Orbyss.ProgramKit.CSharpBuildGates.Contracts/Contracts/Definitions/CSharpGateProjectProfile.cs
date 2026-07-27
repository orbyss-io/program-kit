using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>One exact project/target-framework dependency boundary.</summary>
public sealed record CSharpGateProjectProfile(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier ProjectId,
    string RepositoryRelativeProjectPath,
    ImmutableArray<string> TargetFrameworks,
    ImmutableArray<ProgramKitIdentifier> AllowedProjectDependencies,
    ImmutableArray<ArtifactReference> AllowedPackageDependencies);
