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

        SessionProjectionContext windows = WithExecutable(baseline, ".program-kit/tools/program-kit.exe");
        SessionProjectionContext linux = WithExecutable(baseline, ".program-kit/tools/program-kit");
        SessionProviderConformanceReport windowsReport = new SessionProviderConformanceEvaluator().Evaluate(adapter, windows);
        SessionProviderConformanceReport linuxReport = new SessionProviderConformanceEvaluator().Evaluate(adapter, linux);
        Assert.AreEqual("sha256:79a5e640f855a9437e31653fb615a0f92c2c3447a319478d2a0e41e42d0756f1", windowsReport.ObservationDigest);
        Assert.AreEqual("sha256:d84d2dd99738842948f96871f347ff41f909924a3de023a54de9f87d8975dabc", linuxReport.ObservationDigest);
        Assert.AreEqual(OperatingSystem.IsWindows() ? windowsReport.ObservationDigest : linuxReport.ObservationDigest, left.ObservationDigest);
    }

    private static SessionProjectionContext WithExecutable(SessionProjectionContext context, string executable) =>
        context with { Request = context.Request with { CliRelease = context.Request.CliRelease with { WorkspaceRelativeExecutable = executable } } };
}
