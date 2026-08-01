using System;
using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex.Projection;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.Codex;

public sealed class CodexSessionProviderAdapter : ISessionProviderAdapter
{
    public SessionProviderManifest Manifest { get; } =
        new CodexSessionProviderManifestLoader().LoadEmbedded();

    public IReadOnlyList<ProjectedSessionArtifact> Project(SessionProjectionContext context)
    {
        if (!string.Equals(context.Request.Scope, "workspace", StringComparison.Ordinal))
            throw new InvalidOperationException("Codex supports only workspace scope.");
        return new[]
        {
            new ProjectedSessionArtifact(".agents/skills/program-kit/SKILL.md", "text/markdown", CodexSkillProjector.Project(context)),
        };
    }
}
