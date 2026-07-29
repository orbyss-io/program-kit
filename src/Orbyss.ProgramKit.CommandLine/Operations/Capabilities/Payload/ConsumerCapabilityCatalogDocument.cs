using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Payload;

/// <summary>Exact embedded consumer capability knowledge catalog.</summary>
internal sealed record ConsumerCapabilityCatalogDocument(
    string FormatVersion,
    string ProductVersion,
    ImmutableArray<string> Providers,
    ImmutableArray<CapabilityKnowledgeClosure> Capabilities);
