using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>Exact RFC 8785 input-digest projection.</summary>
public sealed record CSharpGateLockInputProjection(
    ArtifactReference Definition,
    CSharpGateLockIntent LockIntent,
    SemanticVersion SdkVersion,
    SemanticVersion CompilerRoslynVersion,
    SemanticVersion LanguageVersion,
    string TargetFramework,
    ImmutableArray<CSharpGateLocalAssetBinding> LocalAssets);
