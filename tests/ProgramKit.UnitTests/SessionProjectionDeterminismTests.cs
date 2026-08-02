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
        Assert.AreEqual("sha256:75e6c138ce46a1906ba30adc5d7835484d1d02390386604aaf441cdf8ee33167", windowsReport.ObservationDigest);
        Assert.AreEqual("sha256:2faf690449b67030cf4e9181183b23174492bed2849d4593578c586c17295462", linuxReport.ObservationDigest);
        Assert.AreEqual(OperatingSystem.IsWindows() ? windowsReport.ObservationDigest : linuxReport.ObservationDigest, left.ObservationDigest);
    }

    private static SessionProjectionContext WithExecutable(SessionProjectionContext context, string executable) =>
        context with { Request = context.Request with { CliRelease = context.Request.CliRelease with { WorkspaceRelativeExecutable = executable } } };
}
