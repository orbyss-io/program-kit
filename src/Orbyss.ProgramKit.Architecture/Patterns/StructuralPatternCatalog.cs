using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Patterns;

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
