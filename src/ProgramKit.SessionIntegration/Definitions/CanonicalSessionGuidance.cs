using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;

namespace Orbyss.ProgramKit.SessionIntegration.Definitions;

public static class CanonicalSessionGuidance
{
    private const string EmptyDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";

    public static CanonicalSessionIntegrationDefinition Definition { get; } = new(
        "program-kit.session-integration-definition/v1",
        "program-kit.canonical-json/v1",
        new GovernedIdentity("orbyss.program-kit", "session-integration-definition", "human-led-software-factory", "1.0.0", EmptyDigest),
        new[]
        {
            Binding("explain", EffectState.None), Binding("construct", EffectState.Committed), Binding("evaluate", EffectState.None),
        },
        new[]
        {
            Binding("session-explain", EffectState.None), Binding("session-install", EffectState.Committed), Binding("session-verify", EffectState.None), Binding("session-remove", EffectState.Committed),
        },
        new ArtifactReference(
            new GovernedIdentity("orbyss.program-kit", "session-guidance", "human-led-software-factory", "1.0.0", EmptyDigest),
            "text/markdown", "canonical/session-guidance.md", EmptyDigest, ArtifactOwnership.GeneratedOwned),
        EmptyDigest,
        "1.0.0");

    public static IReadOnlyList<string> WorkflowSteps { get; } = new[]
    {
        "Classify intent as known, incomplete-known, or unknown without inventing consumer semantics.",
        "Use explain before effects whenever meaning, provider resolution, or authority is incomplete.",
        "Preserve clarified answers in the canonical request whose digest is reviewed.",
        "Treat provider selection as explicit and never select from installed ambient state.",
        "Ask the human for the exact request-bound authority named by a typed result.",
        "Invoke construct only with a current exact grant; never widen, refresh, or reuse a grant.",
        "Use evaluate for read-only current-state assessment and never repair from diagnostic prose.",
        "Treat operation-result/v1 JSON fields and diagnostic identities as authoritative.",
        "Leave unknown custom implementation intent explicit and human-owned.",
    };

    private static SessionOperationBinding Binding(string name, EffectState effect) => new(name, ProtocolIdentities.Operation(name), effect);
}
