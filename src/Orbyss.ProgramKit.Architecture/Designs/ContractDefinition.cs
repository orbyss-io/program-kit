using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>A versioned public contract owned by one domain.</summary>
public sealed record ContractDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerDomainId,
    ContractKind Kind,
    SemanticVersion Version,
    ArtifactReference Schema,
    string Meaning,
    string CompatibilityPolicy);
