namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Catalog;

/// <summary>One exact capability availability row parsed from the canonical index.</summary>
public sealed record CapabilityIndexEntry(
    string CapabilityId,
    string FlowCategory,
    string Status,
    string? CanonicalDefinition,
    string? ProviderAdapterTemplate,
    string Notes);
