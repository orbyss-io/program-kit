using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation.ConfigurationProviders;

/// <summary>Explicit source generator registered for one exact provider revision.</summary>
public interface IDotNetConfigurationProviderGenerator
{
    /// <summary>The exact provider descriptor implemented by this generator.</summary>
    DotNetConfigurationProviderDescriptor Descriptor { get; }

    /// <summary>Renders one deterministic registration from validated canonical input.</summary>
    string RenderRegistration(DotNetConfigurationSource source);

    /// <summary>
    /// Renders one deterministic registration with optional host-owned adapter
    /// composition. ABI 1 generators remain valid through this default.
    /// </summary>
    string RenderRegistration(
        DotNetConfigurationSource source,
        DotNetHostDefinition host) =>
        RenderRegistration(source);

    /// <summary>Produces provider-specific deterministic support source.</summary>
    ImmutableArray<GeneratedOutput> Compile(
        DotNetConfigurationSource source,
        DotNetHostDefinition host) =>
        [];
}
