using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>A finite compilation-observable rule contract.</summary>
public sealed record CSharpGateRuleDefinition(
    ProgramKitIdentifier Identity,
    SemanticVersion Revision,
    CSharpGateRuleKind Kind,
    ProgramKitIdentifier SemanticOwnerId,
    ArtifactReference SourceContract,
    string DiagnosticId,
    string Title,
    string Category,
    CSharpGateDiagnosticSeverity DefaultSeverity,
    string Rationale,
    string Remediation,
    string CompilationObservableClaim,
    CSharpGateRuleLayer Layer,
    ImmutableArray<string> ClaimsOutsideRule,
    ImmutableArray<ProgramKitIdentifier> ProjectProfileIds,
    ImmutableArray<ProgramKitIdentifier> SourceProfileIds,
    CSharpGateSuppressionDisposition SuppressionDisposition,
    ArtifactReference PositiveFixture,
    ArtifactReference NegativeFixture,
    ArtifactReference Compatibility,
    ArtifactReference Migration,
    ArtifactReference? Deprecation,
    ArtifactReference? Retirement,
    ArtifactReference? Supersession,
    string LocationContract,
    string MessageContract,
    int FocusedBudgetMilliseconds,
    int FullBudgetMilliseconds);
