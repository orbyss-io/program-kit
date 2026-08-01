using System;
using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex;
using Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionProjectionDeterminismTests
{
    [TestMethod]
    public void Repeated_and_semantically_irrelevant_projection_inputs_are_byte_equal()
    {
        CodexSessionProviderAdapter adapter = new();
        SessionProjectionContext baseline = SessionIntegrationFixture.ProjectionContext();
        SessionProjectionContext permuted = baseline with { IncludeUserInterfaceMetadata = true };
        byte[] first = adapter.Project(baseline).Single().Content;
        byte[] second = adapter.Project(baseline).Single().Content;
        byte[] irrelevantPermutation = adapter.Project(permuted).Single().Content;
        Assert.IsTrue(first.AsSpan().SequenceEqual(second));
        Assert.IsTrue(first.AsSpan().SequenceEqual(irrelevantPermutation));

        SessionProviderConformanceReport left = new SessionProviderConformanceEvaluator().Evaluate(adapter, baseline);
        SessionProviderConformanceReport right = new SessionProviderConformanceEvaluator().Evaluate(adapter, permuted);
        Assert.AreEqual(left.ObservationDigest, right.ObservationDigest);
        Assert.AreEqual("sha256:26822f5b3c1d3f55bd25981f12605131bea313105d56a457e533e0fd00b0dd00", left.ObservationDigest);
    }
}
