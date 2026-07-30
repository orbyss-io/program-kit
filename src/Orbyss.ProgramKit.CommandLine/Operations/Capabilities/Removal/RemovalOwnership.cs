using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Removal;

/// <summary>Validated current or legacy ownership selected for removal.</summary>
internal sealed record RemovalOwnership(
    CapabilityInitializationLock? Current,
    CapabilityInitializationProviderLock[] Providers);
