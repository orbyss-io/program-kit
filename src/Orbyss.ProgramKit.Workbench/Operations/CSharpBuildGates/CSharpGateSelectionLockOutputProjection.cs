using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>Exact RFC 8785 output-digest projection without outputDigest.</summary>
public sealed record CSharpGateSelectionLockOutputProjection(
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
    Sha256Digest InputDigest);
