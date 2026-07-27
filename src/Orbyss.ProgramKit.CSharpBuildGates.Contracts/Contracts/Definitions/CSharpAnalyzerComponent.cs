using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>A selected analyzer component and its exact compatibility bounds.</summary>
public sealed record CSharpAnalyzerComponent(
    ProgramKitIdentifier Identity,
    CSharpAnalyzerComponentKind Kind,
    ProgramKitIdentifier SemanticOwnerId,
    CSharpAnalyzerArtifactSelection Artifact,
    ImmutableArray<ProgramKitIdentifier> RuleIds,
    ImmutableArray<ArtifactReference> ReceiptGeneratorRevisions,
    SemanticVersionRange SdkRange,
    SemanticVersionRange CompilerRoslynRange,
    SemanticVersionRange LanguageRange,
    SemanticVersionRange TargetFrameworkRange,
    SemanticVersionRange ProgramKitMechanicsRange);
