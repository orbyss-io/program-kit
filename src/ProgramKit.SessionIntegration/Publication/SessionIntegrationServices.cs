using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Authority;
using Orbyss.ProgramKit.SessionIntegration.Definitions;
using Orbyss.ProgramKit.SessionIntegration.Policy;
using Orbyss.ProgramKit.SessionIntegration.Providers;

namespace Orbyss.ProgramKit.SessionIntegration.Publication;

public sealed class SessionIntegrationServices
{
    public SessionIntegrationServices(SessionProviderRegistry providers, string cliVersion)
    {
        Providers = providers;
        CliVersion = cliVersion;
    }

    public SessionProviderRegistry Providers { get; }
    public string CliVersion { get; }
    public CanonicalSessionIntegrationDefinition Definition => CanonicalSessionGuidance.Definition;
    public SourceAuthoringGuard SourceGuard { get; } = new();
    public RequestBoundAuthorityValidator Authority { get; } = new();
    public NamespacedArtifactSetPublisher Publisher { get; } = new();
}
