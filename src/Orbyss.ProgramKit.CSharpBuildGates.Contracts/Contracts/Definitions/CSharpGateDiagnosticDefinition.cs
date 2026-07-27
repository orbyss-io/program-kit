using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>Stable diagnostic meaning owned by one exact rule revision.</summary>
public sealed record CSharpGateDiagnosticDefinition(
    string DiagnosticId,
    ProgramKitIdentifier SemanticOwnerId,
    ProgramKitIdentifier RuleId,
    SemanticVersion RuleRevision,
    string Title,
    string Category,
    CSharpGateDiagnosticSeverity DefaultSeverity,
    string MessageFormat);
