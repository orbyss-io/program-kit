using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>One decision intentionally left open by a design.</summary>
public sealed record UnresolvedDecision(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    string Question,
    string DecisionNeededBy,
    string BlockingEffect);
