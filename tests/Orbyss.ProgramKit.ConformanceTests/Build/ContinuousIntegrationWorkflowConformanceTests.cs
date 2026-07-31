using System.Text.RegularExpressions;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

[TestClass]
public sealed class ContinuousIntegrationWorkflowConformanceTests
{
    private const string CheckoutPin =
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1";
    private const string SetupDotNetPin =
        "actions/setup-dotnet@a98b56852c35b8e3190ac28c8c2271da59106c68";
    private const string AttestPin =
        "actions/attest@508db95dd578ae2727ebd6217d5ba78e4fbda05d";
    private const string UploadArtifactPin =
        "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a";
    private const string IntegrationProfileDigest =
        "sha256:2e383f220030e2933dca3e7af27543e73a28451506c183538d6d84aba689791f";

    [TestMethod]
    public void WorkflowCoversCombinedSourceAndTrustedMainWithoutPathFilters()
    {
        string workflow = ReadWorkflow();
        string triggers = Slice(
            workflow,
            "on:\n",
            "\npermissions:");

        Assert.Contains("  pull_request:\n    branches: [main]", triggers);
        Assert.Contains(
            "  merge_group:\n    types: [checks_requested]",
            triggers);
        Assert.Contains("  push:\n    branches: [main]", triggers);
        Assert.DoesNotContain("pull_request_target", workflow);
        Assert.DoesNotContain("workflow_run", workflow);
        Assert.DoesNotContain("paths:", triggers);
        Assert.DoesNotContain("paths-ignore:", triggers);
        Assert.DoesNotContain("tags:", triggers);
    }

    [TestMethod]
    public void RequiredIntegrationJobIsStableReadOnlyAndUsesDefaultCheckout()
    {
        string workflow = ReadWorkflow();
        string integration = IntegrationJob(workflow);

        Assert.Contains(
            "  integration:\n    name: Program Kit integration",
            integration);
        Assert.Contains("permissions:\n  contents: read", workflow);
        Assert.DoesNotContain("\n    permissions:", integration);
        Assert.Contains(CheckoutPin, integration);
        Assert.Contains("persist-credentials: false", integration);
        Assert.DoesNotContain("\n          ref:", integration);
        Assert.DoesNotContain("pull_request.head", integration);
        Assert.Contains(SetupDotNetPin, integration);
        Assert.Contains("global-json-file: global.json", integration);
        Assert.Contains(
            "pwsh -NoProfile -File build/Invoke-ProgramKitIntegration.ps1",
            integration);
        Assert.DoesNotContain("secrets.", integration);
    }

    [TestMethod]
    public void ConcurrencyCancelsOnlySupersededPullRequestRuns()
    {
        string workflow = ReadWorkflow();
        string concurrency = Slice(
            workflow,
            "concurrency:\n",
            "\njobs:");

        Assert.Contains(
            "github.event_name == 'pull_request'",
            concurrency);
        Assert.Contains(
            "github.event.pull_request.number || github.run_id",
            concurrency);
        Assert.Contains(
            "cancel-in-progress: ${{ github.event_name == 'pull_request' }}",
            concurrency);
    }

    [TestMethod]
    public void CanonicalBuildRequiresSuccessfulSameRunIntegrationOnMainPush()
    {
        string packageJob = CanonicalBuildJob(ReadWorkflow());

        Assert.Contains("    needs: integration", packageJob);
        Assert.Contains(
            "if: github.event_name == 'push' && github.ref == 'refs/heads/main' && needs.integration.result == 'success'",
            packageJob);
        Assert.Contains("runs-on: windows-latest", packageJob);
        Assert.DoesNotContain("continue-on-error:", packageJob);
        Assert.DoesNotContain("always()", packageJob);
        Assert.DoesNotContain("secrets.", packageJob);
        Assert.DoesNotContain("NuGet/login", packageJob);
        Assert.DoesNotContain("nuget push", packageJob);
    }

    [TestMethod]
    public void CanonicalBuildHasOnlyThePermissionsRequiredForAttestation()
    {
        string packageJob = CanonicalBuildJob(ReadWorkflow());
        string permissions = Slice(
            packageJob,
            "    permissions:\n",
            "    env:");

        Assert.Contains("      contents: read", permissions);
        Assert.Contains("      id-token: write", permissions);
        Assert.Contains("      attestations: write", permissions);
        Assert.Contains("      artifact-metadata: write", permissions);
        Assert.AreEqual(3, Count(permissions, ": write"));
        Assert.DoesNotContain("contents: write", permissions);
        Assert.DoesNotContain("packages: write", permissions);
        Assert.DoesNotContain("actions: write", permissions);
    }

    [TestMethod]
    public void CanonicalBuildPacksOnceThenVerifiesAttestsAndUploads()
    {
        string packageJob = CanonicalBuildJob(ReadWorkflow());
        int pack = packageJob.IndexOf(
            "build/Invoke-PackConsumerFeed.ps1",
            StringComparison.Ordinal);
        int write = packageJob.IndexOf(
            "build/Write-ProgramKitCanonicalBuildProvenance.ps1",
            StringComparison.Ordinal);
        int verify = packageJob.IndexOf(
            "build/Test-ProgramKitCanonicalBuild.ps1",
            StringComparison.Ordinal);
        int attest = packageJob.IndexOf(
            AttestPin,
            StringComparison.Ordinal);
        int upload = packageJob.IndexOf(
            UploadArtifactPin,
            StringComparison.Ordinal);

        Assert.AreEqual(
            1,
            Count(packageJob, "build/Invoke-PackConsumerFeed.ps1"));
        Assert.IsTrue(
            pack >= 0 &&
            pack < write &&
            write < verify &&
            verify < attest &&
            attest < upload);
        Assert.Contains(
            "program-kit-canonical-build-${{ github.sha }}",
            packageJob);
        Assert.Contains(
            "WORKFLOW_REVISION: ${{ github.workflow_sha }}",
            packageJob);
        Assert.Contains(IntegrationProfileDigest, packageJob);
        Assert.Contains("feed/*.nupkg", packageJob);
        Assert.Contains("canonical-build-provenance.json", packageJob);
        Assert.Contains("if-no-files-found: error", packageJob);
        Assert.Contains("compression-level: 0", packageJob);
        Assert.DoesNotContain("overwrite: true", packageJob);
    }

    [TestMethod]
    public void RunnerTemporaryRootIsBoundOnlyInsideCanonicalBuildSteps()
    {
        string workflow = ReadWorkflow();
        string packageJob = CanonicalBuildJob(workflow);
        string jobConfiguration = Slice(
            packageJob,
            "  canonical-build:\n",
            "    steps:\n");
        const string binding =
            "CANONICAL_BUILD_ROOT: ${{ runner.temp }}/program-kit-canonical-build";

        Assert.DoesNotContain(binding, jobConfiguration);
        Assert.AreEqual(5, Count(packageJob, binding));
    }

    [TestMethod]
    public void OfficialActionsArePinnedToReviewedImmutableCommits()
    {
        string workflow = ReadWorkflow();
        MatchCollection uses = Regex.Matches(
            workflow,
            @"uses: (?<action>actions/[a-z0-9-]+)@(?<sha>[0-9a-f]{40})");

        Assert.HasCount(6, uses);
        foreach (Match use in uses)
        {
            Assert.IsTrue(use.Success);
            Assert.AreEqual(40, use.Groups["sha"].Value.Length);
        }

        Assert.AreEqual(2, Count(workflow, CheckoutPin));
        Assert.AreEqual(2, Count(workflow, SetupDotNetPin));
        Assert.AreEqual(1, Count(workflow, AttestPin));
        Assert.AreEqual(1, Count(workflow, UploadArtifactPin));
        Assert.IsFalse(Regex.IsMatch(
            workflow,
            @"uses:\s+[^@\s]+@v[0-9]"));
    }

    private static string ReadWorkflow() =>
        File.ReadAllText(Path.Combine(
                ConformanceInputs.RepositoryRoot,
                ".github",
                "workflows",
                "program-kit-integration.yml"))
            .Replace("\r\n", "\n", StringComparison.Ordinal);

    private static string IntegrationJob(string workflow) =>
        Slice(
            workflow,
            "  integration:\n",
            "\n  canonical-build:");

    private static string CanonicalBuildJob(string workflow) =>
        workflow[workflow.IndexOf(
            "  canonical-build:\n",
            StringComparison.Ordinal)..];

    private static string Slice(
        string value,
        string startMarker,
        string endMarker)
    {
        int start = value.IndexOf(
            startMarker,
            StringComparison.Ordinal);
        Assert.IsGreaterThanOrEqualTo(0, start);
        int end = value.IndexOf(
            endMarker,
            start,
            StringComparison.Ordinal);
        Assert.IsGreaterThan(start, end);
        return value[start..end];
    }

    private static int Count(string source, string value)
    {
        int count = 0;
        int offset = 0;
        while ((offset = source.IndexOf(
                   value,
                   offset,
                   StringComparison.Ordinal)) >= 0)
        {
            count++;
            offset += value.Length;
        }

        return count;
    }
}
