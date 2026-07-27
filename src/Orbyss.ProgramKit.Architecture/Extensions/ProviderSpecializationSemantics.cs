using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Extensions;

/// <summary>Required semantics for a provider specialization.</summary>
public sealed record ProviderSpecializationSemantics(
    ProgramKitIdentifier BaseProviderId,
    ImmutableArray<ArtifactReference> AddedContracts,
    string CompatibilitySemantics,
    string FallbackSemantics);
