using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>A relationship between one canonical artifact and a derived projection.</summary>
public sealed record CanonicalProjectionRelationship(
    ProgramKitIdentifier ProjectionId,
    ProgramKitIdentifier CanonicalId,
    string ProjectionRule,
    string LossPolicy,
    bool IsRegenerable);
