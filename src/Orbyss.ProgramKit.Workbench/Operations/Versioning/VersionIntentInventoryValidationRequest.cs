namespace Orbyss.ProgramKit.Workbench.Operations.Versioning;

/// <summary>Bounded inputs for validating one closed inventory observation.</summary>
/// <param name="Inventory">Explicit classified inventory.</param>
/// <param name="ObservedSources">Exact caller-observed version-bearing sources.</param>
/// <param name="MaximumSources">Maximum admitted inventory and observation size.</param>
public sealed record VersionIntentInventoryValidationRequest(
    VersionIntentInventoryDocument Inventory,
    ImmutableArray<VersionBearingSourceObservation> ObservedSources,
    int MaximumSources);
