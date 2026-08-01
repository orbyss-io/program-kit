using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.SessionIntegration;

namespace Orbyss.ProgramKit.SessionIntegration.Providers;

public sealed record ProjectedSessionArtifact(string LogicalPath, string MediaType, byte[] Content);

public sealed record SessionProjectionContext(
    CanonicalSessionIntegrationDefinition Definition,
    SessionIntegrationRequest Request,
    bool IncludeUserInterfaceMetadata);

public interface ISessionProviderAdapter
{
    SessionProviderManifest Manifest { get; }
    IReadOnlyList<ProjectedSessionArtifact> Project(SessionProjectionContext context);
}
