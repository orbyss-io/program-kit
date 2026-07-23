using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;
namespace Orbyss.ProgramKit.Architecture;

/// <summary>
/// Versioned structural guidance. A catalog informs human design judgment; it
/// never makes an architecture decision or grants implementation authority.
/// Identity and version make the semantic descriptor self-describing; when
/// durable, they must equal the authoritative enclosing artifact metadata.
/// </summary>
public sealed record StructuralPatternCatalog(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    string Purpose,
    ImmutableArray<StructuralPatternDefinition> Patterns);

/// <summary>One structural pattern with both mechanical and human checks.</summary>
public sealed record StructuralPatternDefinition(
    ProgramKitIdentifier Identity,
    string Name,
    string Problem,
    ImmutableArray<string> ApplicabilityCriteria,
    ImmutableArray<string> TradeOffs,
    ImmutableArray<StructuralPatternExample> Examples,
    ImmutableArray<string> MechanicalChecks,
    ImmutableArray<string> HumanChecks);

/// <summary>A bounded illustration of a structural pattern.</summary>
public sealed record StructuralPatternExample(
    string Name,
    string Context,
    string Application,
    string Consequence);
