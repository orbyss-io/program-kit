using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Providers.DotNet;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex;
using Orbyss.ProgramKit.SessionIntegration.Publication;


namespace Orbyss.ProgramKit.Cli.Composition;

public static class ProgramKitComposition
{
    public static ProgramKitKernel CreateKernel() => new(new[] { new DotNetFactoryProvider() });

    public static SessionIntegrationServices CreateSessionServices() => new(new SessionProviderRegistry(new[] { new CodexSessionProviderAdapter() }), CliReleaseIdentityProvider.InvokedVersion);
}
