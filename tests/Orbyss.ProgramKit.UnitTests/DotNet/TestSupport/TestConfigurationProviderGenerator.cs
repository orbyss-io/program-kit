using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Generation.ConfigurationProviders;

namespace Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

internal sealed class TestConfigurationProviderGenerator(
    DotNetConfigurationProviderDescriptor descriptor) :
    IDotNetConfigurationProviderGenerator
{
    public DotNetConfigurationProviderDescriptor Descriptor { get; } =
        descriptor;

    public string RenderRegistration(DotNetConfigurationSource source) =>
        string.Concat("// explicit test adapter: ", source.Identity.Value);
}
