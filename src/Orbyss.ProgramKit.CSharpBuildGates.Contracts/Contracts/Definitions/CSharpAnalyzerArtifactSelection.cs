using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>An exact local or packaged analyzer selection.</summary>
public sealed record CSharpAnalyzerArtifactSelection(
    CSharpAnalyzerArtifactKind Kind,
    string? RepositoryRelativeProjectPath,
    ArtifactReference? Package,
    string AssemblyFileName,
    Sha256Digest AssemblyDigest,
    bool IsPackable,
    bool HasRuntimeAssets,
    bool HasBuildTransitiveAssets);
