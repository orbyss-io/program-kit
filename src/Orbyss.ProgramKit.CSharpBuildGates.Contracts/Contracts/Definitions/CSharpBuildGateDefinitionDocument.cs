using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>
/// Canonical consumer-owned C# build-gate definition 1.0.0. It contains only
/// finite typed values and exact references; no expression or discovery hook
/// is part of the contract.
/// </summary>
public sealed record CSharpBuildGateDefinitionDocument(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    Sha256Digest RevisionDigest,
    ProgramKitIdentifier OwnerId,
    ProgramKitIdentifier ConsumerPolicyId,
    ArtifactReference Disposition,
    ArtifactReference CompatibilityPolicy,
    ImmutableArray<CSharpSemanticOwner> SemanticOwners,
    ImmutableArray<CSharpAnalyzerComponent> AnalyzerComponents,
    CSharpGateRuleCatalog RuleCatalog,
    CSharpGateProfileCatalog Profiles,
    CSharpGateActivationMatrix ActivationMatrix,
    ImmutableArray<CSharpGateTemporaryActivationExceptionRecord> TemporaryExceptions,
    CSharpGateSuppressionLedger SuppressionLedger,
    CSharpGateAssurance Assurance);
