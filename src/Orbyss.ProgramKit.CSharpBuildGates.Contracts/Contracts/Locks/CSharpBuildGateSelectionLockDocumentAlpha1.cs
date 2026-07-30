using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;

/// <summary>
/// Selection lock 0.1.0-alpha.1 with mechanically recomputed input and output
/// digest projections.
/// </summary>
public sealed record CSharpBuildGateSelectionLockDocumentAlpha1(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    ArtifactReference Disposition,
    ArtifactReference GateDefinition,
    ImmutableArray<ArtifactReference> AnalyzerComponents,
    ArtifactReference RuleCatalog,
    ImmutableArray<ArtifactReference> Recipes,
    ArtifactReference ActivationMatrix,
    ArtifactReference SuppressionLedger,
    ImmutableArray<ArtifactReference> OperationRevisions,
    ImmutableArray<CSharpGateLockedContent> ProjectInventory,
    ImmutableArray<CSharpGateLockedContent> PhysicalSourceInventory,
    ImmutableArray<CSharpGateLockedContent> GeneratedSourceInventory,
    ImmutableArray<CSharpGateLockedContent> ReferenceInventory,
    ImmutableArray<CSharpGateLockedContent> AdditionalFileInventory,
    ImmutableArray<CSharpGateLockedContent> AnalyzerConfigurationInventory,
    SemanticVersion SdkVersion,
    SemanticVersion CompilerRoslynVersion,
    SemanticVersion LanguageVersion,
    string TargetFramework,
    ImmutableArray<CSharpGateExpectedReceipt> ExpectedReceipts,
    Sha256Digest InputDigest,
    Sha256Digest OutputDigest);
