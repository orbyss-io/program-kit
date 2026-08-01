using System;
using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeSessionProviderAdapterTests
{
    [TestMethod]
    public void Adapter_projects_only_its_declared_workspace_owned_artifact()
    {
        ClaudeSessionProviderAdapter adapter = new();
        ProjectedSessionArtifact artifact = adapter.Project(ClaudeTestContext.Create(adapter.Manifest)).Single();
        Assert.AreEqual(adapter.Manifest.ProjectionDescriptors.Single().LogicalPath, artifact.LogicalPath);
        Assert.AreEqual(SessionProviderSupport.NotEvaluated, adapter.Manifest.SupportClaim);
        Assert.AreEqual("text/markdown", artifact.MediaType);
    }

    [TestMethod]
    public void Adapter_rejects_non_workspace_scope_without_effect()
    {
        ClaudeSessionProviderAdapter adapter = new();
        SessionProjectionContext context = ClaudeTestContext.Create(adapter.Manifest);
        context = context with { Request = context.Request with { Scope = "user" } };
        Assert.ThrowsExactly<InvalidOperationException>(() => adapter.Project(context));
    }
}
