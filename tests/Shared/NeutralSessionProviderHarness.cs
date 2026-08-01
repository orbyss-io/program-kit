using System.Collections.Generic;
using System.Text;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Providers;

namespace Orbyss.ProgramKit.Tests;

internal sealed class NeutralSessionProviderHarness : ISessionProviderAdapter
{
    private const string EmptyDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";
    private readonly bool corrupt;

    public NeutralSessionProviderHarness(bool corrupt = false)
    {
        this.corrupt = corrupt;
    }

    public SessionProviderManifest Manifest { get; } = new(
        "program-kit.session-provider-manifest/v1",
        Identity("session-provider", "neutral-harness"),
        Identity("session-provider-adapter", "neutral-repository-capability"),
        new GovernedIdentity("orbyss.program-kit", "session-integration-definition", "human-led-software-factory", "1.0.0", EmptyDigest),
        SessionBindingKind.ShellCli,
        new[] { "workspace" },
        new[] { new SessionProjectionDescriptor("session-capability", ".session-capabilities/program-kit.md", "text/markdown", ArtifactOwnership.GeneratedOwned, ClaimClass.CanonicalByte, "exact-admitted-digest-only") },
        new[] { "explain", "construct", "evaluate", "session-explain", "session-install", "session-verify", "session-remove" },
        Identity("diagnostic-catalog", "neutral-harness"),
        Identity("session-provider-conformance", "repository-workspace-v1"),
        SessionProviderSupport.Supported,
        "1.0.0",
        "1.0.0");

    public IReadOnlyList<ProjectedSessionArtifact> Project(SessionProjectionContext context)
    {
        string content = corrupt ? string.Empty : $"definition={context.Definition.Identity.StableKey}\nresult=program-kit.operation-result/v1\noperation=session-explain\neffect=none\n";
        return new[] { new ProjectedSessionArtifact(".session-capabilities/program-kit.md", "text/markdown", Encoding.UTF8.GetBytes(content)) };
    }

    private static GovernedIdentity Identity(string kind, string name) => new("orbyss.program-kit.tests", kind, name, "1.0.0", EmptyDigest);
}
