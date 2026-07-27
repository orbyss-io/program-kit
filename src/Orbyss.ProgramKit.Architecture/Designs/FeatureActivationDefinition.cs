using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>A stable feature activation identity and its configuration ownership.</summary>
public sealed record FeatureActivationDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier FeatureId,
    ProgramKitIdentifier OwnerId,
    ProgramKitIdentifier? ConfigurationId,
    string SelectionSemantics,
    string FailureSemantics);
