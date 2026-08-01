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
        string expectedObservationDigest = OperatingSystem.IsWindows()
            ? "sha256:a3489d215f54322f33df2e40bc41c1df45433a160dbd399dbe353226157b2225"
            : "sha256:f2ea82bf0e87f78efc934f76b5594398549d635e069368de1b69d040e2501160";
        Assert.AreEqual(expectedObservationDigest, left.ObservationDigest);
    }
}
