using System;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Authority;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionAuthorityGrantTests
{
    private static readonly DateTimeOffset Instant = new(2026, 8, 1, 12, 0, 0, TimeSpan.Zero);

    [TestMethod]
    public void Effect_bearing_request_requires_an_exact_one_use_grant()
    {
        RequestBoundAuthorityValidator validator = new();
        AuthorityDemand demand = Demand();
        Assert.ThrowsExactly<UnauthorizedAccessException>(() => validator.Demand(demand, null));
        validator.Demand(demand, Grant());

        Assert.ThrowsExactly<UnauthorizedAccessException>(() => validator.Demand(demand with { RequestIdentity = Digest('b') }, Grant()));
        Assert.ThrowsExactly<UnauthorizedAccessException>(() => validator.Demand(demand with { Operation = "session-remove" }, Grant()));
        Assert.ThrowsExactly<UnauthorizedAccessException>(() => validator.Demand(demand with { WorkspaceIdentity = "other" }, Grant()));
        Assert.ThrowsExactly<UnauthorizedAccessException>(() => validator.Demand(demand, Grant() with { NotAfter = Instant.AddSeconds(-1) }));
        Assert.ThrowsExactly<UnauthorizedAccessException>(() => validator.Demand(demand, Grant() with { Consumed = true }));
        Assert.ThrowsExactly<UnauthorizedAccessException>(() => validator.Demand(demand, Grant() with { Revoked = true }));
    }

    [TestMethod]
    public void Read_only_request_rejects_ambient_or_supplied_authority()
    {
        RequestBoundAuthorityValidator validator = new();
        AuthorityDemand demand = Demand() with { Effect = RequestedEffect.None, Operation = "session-explain" };
        validator.Demand(demand, null);
        Assert.ThrowsExactly<UnauthorizedAccessException>(() => validator.Demand(demand, Grant()));
    }

    private static AuthorityDemand Demand() => new("workspace-a", "session-install", RequestedEffect.Committed, Digest('a'), "codex", "1", Instant);

    private static RequestBoundAuthorityGrant Grant() => new(
        "program-kit.request-bound-authority-grant/v1", "grant-001", "workspace-a", "session-install",
        "committed", Digest('a'), "codex", "1", Instant.AddMinutes(-1), Instant.AddMinutes(1), false, false);

    private static string Digest(char value) => $"sha256:{new string(value, 64)}";
}
