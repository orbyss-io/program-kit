using System;
using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Manifest;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Projection;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode;

public sealed class ClaudeSessionProviderAdapter : ISessionProviderAdapter
{
    public SessionProviderManifest Manifest { get; } = new ClaudeProviderManifestLoader().LoadEmbedded();

    public IReadOnlyList<ProjectedSessionArtifact> Project(SessionProjectionContext context)
    {
        if (!string.Equals(context.Request.Scope, "workspace", StringComparison.Ordinal))
            throw new InvalidOperationException("Claude Code supports only workspace scope.");
        if (context.Definition.Identity != Manifest.DefinitionBinding)
            throw new InvalidOperationException("The Claude Code adapter requires its exact canonical definition binding.");
        return new[]
        {
            new ProjectedSessionArtifact(ClaudeProviderIdentities.SkillLogicalPath, "text/markdown", ClaudeSkillProjector.Project(context)),
        };
    }
}
