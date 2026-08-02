using System;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Authority;
using Orbyss.ProgramKit.SessionIntegration.Providers;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ConstructAuthorityBindingTests
{
    [TestMethod]
    public void Changed_input_target_operation_or_provider_invalidates_construct_authority()
    {
        SessionInvocationBinding binding = SessionInvocationBinding.Create("sha256:" + new string('a', 64), "construct", "workspace-a", "provider-a", new[] { "component/a", "application/a" }, "grant-a");
        RequestBoundAuthorityGrant grant = new("program-kit.request-bound-authority-grant/v1", "grant-a", "workspace-a", "construct", "committed", binding.BindingDigest, "provider-a", "workspace", Instant.AddMinutes(-1), Instant.AddMinutes(1), false, false);
        RequestBoundAuthorityValidator validator = new();
        validator.Demand(Demand(binding), grant);

        Assert.ThrowsExactly<UnauthorizedAccessException>(() => validator.Demand(Demand(binding with { CanonicalInputFingerprint = Digest('b') }), grant));
        Assert.ThrowsExactly<UnauthorizedAccessException>(() => validator.Demand(Demand(binding with { Operation = "evaluate" }), grant));
        Assert.ThrowsExactly<UnauthorizedAccessException>(() => validator.Demand(Demand(binding with { WorkspaceIdentity = "workspace-b" }), grant));
        Assert.ThrowsExactly<UnauthorizedAccessException>(() => validator.Demand(Demand(binding with { ProviderIdentity = "provider-b" }), grant));
    }

    private static readonly DateTimeOffset Instant = new(2026, 8, 1, 12, 0, 0, TimeSpan.Zero);
    private static AuthorityDemand Demand(SessionInvocationBinding binding) => new(binding.WorkspaceIdentity, binding.Operation, RequestedEffect.Committed, binding.BindingDigest, binding.ProviderIdentity, "workspace", Instant);
    private static string Digest(char value) => "sha256:" + new string(value, 64);
}
