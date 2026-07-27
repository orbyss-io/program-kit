using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>Exact stable-ordered rule and diagnostic catalogs.</summary>
public sealed record CSharpGateRuleCatalog(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    ImmutableArray<CSharpGateRuleDefinition> Rules,
    ImmutableArray<CSharpGateDiagnosticDefinition> Diagnostics);
