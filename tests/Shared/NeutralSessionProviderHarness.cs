using System.Collections.Generic;
using System.Text;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Definitions;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

namespace Orbyss.ProgramKit.Tests;

internal sealed class NeutralSessionProviderHarness : ISessionProviderAdapter
{
    private readonly bool corrupt;

    public NeutralSessionProviderHarness(bool corrupt = false)
    {
        this.corrupt = corrupt;
    }

    public SessionProviderManifest Manifest { get; } = new(
        "program-kit.session-provider-manifest/v1",
        "program-kit.canonical-json/v1",
        Identity("session-provider", "neutral-harness"),
        Identity("session-provider-adapter", "neutral-repository-capability"),
        CanonicalSessionGuidance.Definition.Identity,
        SessionBindingKind.ShellCli,
        new[] { "workspace" },
        new SessionProviderSurface("Neutral", "repository-capability", "1.0.0", new[] { "1.0.0" }, "repository-skill", "automatic-or-fresh-session", "json-stdout"),
        new[] { new SessionProjectionDescriptor("session-capability", ".session-capabilities/program-kit.md", "text/markdown", ArtifactOwnership.GeneratedOwned, ClaimClass.CanonicalByte, "exact-admitted-digest-only") },
        new[] { "explain", "construct", "evaluate", "session-explain", "session-install", "session-verify", "session-remove" },
        Identity("diagnostic-catalog", "neutral-harness"),
        SessionProviderConformanceProfiles.RepositoryWorkspaceV1.Identity,
        SessionProviderSupport.Supported,
        "1.0.0",
        "1.0.0");

    public IReadOnlyList<ProjectedSessionArtifact> Project(SessionProjectionContext context)
    {
        string content = corrupt ? string.Empty : $"definition={context.Definition.Identity.StableKey}\nresult=program-kit.operation-result/v2\nauthority=request-bound\ndisclosure=classified\nnormalization=canonical-json\nfresh-session=separately-classified\noperation=session-explain\neffect=none\n";
        return new[] { new ProjectedSessionArtifact(".session-capabilities/program-kit.md", "text/markdown", Encoding.UTF8.GetBytes(content)) };
    }

    private static GovernedIdentity Identity(string kind, string name) =>
        new("orbyss.program-kit.tests", kind, name, "1.0.0", "sha256:7dd82b3d342d17683e72370452053bd29482927ae0073d3d239bab92d6a309f3");
}
