using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>An exact consumer-owned generated-source classification.</summary>
public sealed record CSharpGateGeneratedSourceProfile(
    ProgramKitIdentifier Identity,
    ArtifactReference Generator,
    ProgramKitIdentifier OwnerId,
    string OwnershipMarker,
    ImmutableArray<string> LogicalHintPaths,
    ArtifactReference Manifest,
    ImmutableArray<CSharpGateContentItem> Inventory,
    ImmutableArray<ProgramKitIdentifier> ApplicableRuleIds);
