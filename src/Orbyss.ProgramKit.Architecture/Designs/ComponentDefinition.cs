using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>A deployable, activatable, or supporting architecture component.</summary>
public sealed record ComponentDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    ComponentKind Kind,
    string Purpose,
    ImmutableArray<ProgramKitIdentifier> ProvidesContractIds,
    ImmutableArray<ProgramKitIdentifier> ConsumesContractIds,
    bool IsActivatable,
    string CompatibilityBoundary);
