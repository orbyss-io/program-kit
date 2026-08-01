using System.Collections.Generic;
using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex;
using Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class CodexProviderConformanceAcceptanceTests
{
    [TestMethod]
    public void Reference_adapter_reports_valid_stale_incompatible_and_corrupted_cases_exactly()
    {
        SessionProjectionContext context = SessionIntegrationFixture.ProjectionContext();
        SessionProviderConformanceEvaluator evaluator = new();
        CodexSessionProviderAdapter reference = new();
        Assert.IsTrue(evaluator.Evaluate(reference, context).Conforms);

        GovernedIdentity staleDefinition = reference.Manifest.DefinitionBinding with { Revision = "0.9.0" };
        SessionProviderConformanceReport stale = evaluator.Evaluate(new AdapterOverride(reference, reference.Manifest with { DefinitionBinding = staleDefinition }), context);
        Assert.IsFalse(stale.Conforms);
        CollectionAssert.Contains(stale.Failures.Select(static item => item.Code).ToArray(), "definition-binding");

        SessionProviderConformanceReport incompatible = evaluator.Evaluate(new AdapterOverride(reference, reference.Manifest with { SupportClaim = SessionProviderSupport.Incompatible }), context);
        Assert.IsFalse(incompatible.Conforms);
        CollectionAssert.Contains(incompatible.Failures.Select(static item => item.Code).ToArray(), "support");

        SessionProviderConformanceReport corrupted = evaluator.Evaluate(new AdapterOverride(reference, reference.Manifest, corrupt: true), context);
        Assert.IsFalse(corrupted.Conforms);
        CollectionAssert.Contains(corrupted.Failures.Select(static item => item.Code).ToArray(), "content");
    }

    private sealed class AdapterOverride : ISessionProviderAdapter
    {
        private readonly ISessionProviderAdapter inner;
        private readonly bool corrupt;

        public AdapterOverride(ISessionProviderAdapter inner, SessionProviderManifest manifest, bool corrupt = false)
        {
            this.inner = inner;
            Manifest = manifest;
            this.corrupt = corrupt;
        }

        public SessionProviderManifest Manifest { get; }

        public IReadOnlyList<ProjectedSessionArtifact> Project(SessionProjectionContext context)
        {
            IReadOnlyList<ProjectedSessionArtifact> projected = inner.Project(context);
            return corrupt ? projected.Select(static item => item with { Content = System.Array.Empty<byte>() }).ToArray() : projected;
        }
    }
}
