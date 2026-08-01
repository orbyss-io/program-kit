using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Definitions;
using Orbyss.ProgramKit.SessionIntegration.Providers;

namespace Orbyss.ProgramKit.Tests;

internal static class ClaudeTestContext
{
    public static SessionProjectionContext Create(SessionProviderManifest manifest)
    {
        SessionProjectionContext context = SessionIntegrationFixture.ProjectionContext();
        return context with
        {
            Request = context.Request with
            {
                ProviderSelection = new(
                    manifest.ProviderIdentity,
                    manifest.AdapterIdentity,
                    CanonicalSessionGuidance.Definition.Identity,
                    manifest.ConformanceProfile),
            },
        };
    }
}
