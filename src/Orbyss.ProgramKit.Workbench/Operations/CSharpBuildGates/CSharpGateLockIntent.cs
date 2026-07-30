using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>
/// Human-supplied selection-lock values that cannot be inferred from one gate
/// definition and its explicitly named repository assets.
/// </summary>
public sealed record CSharpGateLockIntent(
    [property: JsonPropertyName("$schema")] string Schema,
    SemanticVersion Version,
    ProgramKitIdentifier LockIdentity,
    ArtifactReference Disposition,
    ImmutableArray<ArtifactReference> Recipes,
    ImmutableArray<ArtifactReference> OperationRevisions,
    SemanticVersion SdkVersion,
    SemanticVersion CompilerRoslynVersion,
    SemanticVersion LanguageVersion,
    string TargetFramework,
    ProgramKitIdentifier ReceiptIdentityNamespace,
    ImmutableArray<CSharpGateLockLocalAssetIntent> LocalAssets);
