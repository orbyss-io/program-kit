using System;
using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex.Projection;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.Codex;

public sealed class CodexSessionProviderAdapter : ISessionProviderAdapter
{
    private const string EmptyDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";

    public SessionProviderManifest Manifest { get; } = new(
        "program-kit.session-provider-manifest/v1",
        Identity("session-provider", "codex"),
        Identity("session-provider-adapter", "codex-repository-skill"),
        Identity("session-integration-definition", "human-led-software-factory"),
        SessionBindingKind.ShellCli,
        new[] { "workspace" },
        new[] { new SessionProjectionDescriptor("session-capability", ".agents/skills/program-kit/SKILL.md", "text/markdown", ArtifactOwnership.GeneratedOwned, ClaimClass.CanonicalByte, "exact-admitted-digest-only") },
        new[] { "explain", "construct", "evaluate", "session-explain", "session-install", "session-verify", "session-remove" },
        new GovernedIdentity("orbyss.program-kit.codex", "diagnostic-catalog", "session-provider", "1.0.0", EmptyDigest),
        Identity("session-provider-conformance", "repository-skill-v1"),
        SessionProviderSupport.Supported,
        "1.0.0",
        "1.0.0");

    public IReadOnlyList<ProjectedSessionArtifact> Project(SessionProjectionContext context)
    {
        if (!string.Equals(context.Request.Scope, "workspace", StringComparison.Ordinal)) throw new InvalidOperationException("Codex supports only workspace scope.");
        return new[]
        {
            new ProjectedSessionArtifact(".agents/skills/program-kit/SKILL.md", "text/markdown", CodexSkillProjector.Project(context)),
        };
    }

    private static GovernedIdentity Identity(string kind, string name) => new("orbyss.program-kit", kind, name, "1.0.0", EmptyDigest);
}
