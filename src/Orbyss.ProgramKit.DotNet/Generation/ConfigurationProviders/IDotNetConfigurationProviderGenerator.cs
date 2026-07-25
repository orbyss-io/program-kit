using Orbyss.ProgramKit.DotNet.Configuration;

namespace Orbyss.ProgramKit.DotNet.Generation.ConfigurationProviders;

/// <summary>Explicit source generator registered for one exact provider revision.</summary>
public interface IDotNetConfigurationProviderGenerator
{
    /// <summary>The exact provider descriptor implemented by this generator.</summary>
    DotNetConfigurationProviderDescriptor Descriptor { get; }

    /// <summary>Renders one deterministic registration from validated canonical input.</summary>
    string RenderRegistration(DotNetConfigurationSource source);
}
