using System.Collections.Generic;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;

namespace Orbyss.ProgramKit.Contracts.SessionIntegration;

public static class SessionOperationContracts
{
    public const string Schema = "program-kit.operation-result/v2";
    public static GovernedIdentity Explain { get; } = Identity("session-explain");
    public static GovernedIdentity Install { get; } = Identity("session-install");
    public static GovernedIdentity Verify { get; } = Identity("session-verify");
    public static GovernedIdentity Remove { get; } = Identity("session-remove");

    public static GovernedIdentity For(SessionLifecycleOperation operation) => operation switch
    {
        SessionLifecycleOperation.Explain => Explain,
        SessionLifecycleOperation.Install => Install,
        SessionLifecycleOperation.Verify => Verify,
        SessionLifecycleOperation.Remove => Remove,
        _ => throw new System.ArgumentOutOfRangeException(nameof(operation)),
    };

    private static GovernedIdentity Identity(string name) => new("orbyss.program-kit", "operation-contract", name, "1", $"sha256:{new string('0', 64)}");
}

public sealed record SessionOperationPayload(
    SessionIntegrationState State,
    SessionAvailability SessionAvailability,
    string Provider,
    string Scope,
    IReadOnlyList<SessionProjectionArtifact> Projections,
    JsonObject? Details = null);
