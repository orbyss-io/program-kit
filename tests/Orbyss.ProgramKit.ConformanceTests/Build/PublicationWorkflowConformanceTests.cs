using System.Diagnostics;
using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

[TestClass]
public sealed class PublicationWorkflowConformanceTests
{
    private const string Repository = "orbyss-io/program-kit";
    private const string RunId = "123456";
    private const string SourceCommit =
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    private const string WorkflowIdentity =
        ".github/workflows/program-kit-integration.yml";
    private const string CheckoutPin =
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1";
    private const string SetupDotNetPin =
        "actions/setup-dotnet@a98b56852c35b8e3190ac28c8c2271da59106c68";
    private const string DownloadArtifactPin =
        "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c";
    private const string NuGetLoginPin =
        "NuGet/login@8d196754b4036150537f80ac539e15c2f1028841";
    private static readonly JsonSerializerOptions IndentedJson =
        new() { WriteIndented = true };

    [TestMethod]
    public void PublicationHasOneExactHumanSuppliedRunInput()
    {
        string workflow = ReadWorkflow();
        string triggers = Slice(
            workflow,
            "on:\n",
            "\nconcurrency:");

        Assert.Contains("  workflow_dispatch:", triggers);
        Assert.Contains("      canonical_run_id:", triggers);
        Assert.Contains("        required: true", triggers);
        Assert.Contains("        type: string", triggers);
        Assert.AreEqual(1, Count(triggers, "        type: string"));
        Assert.DoesNotContain("push:", triggers);
        Assert.DoesNotContain("pull_request:", triggers);
        Assert.DoesNotContain("schedule:", triggers);
        Assert.DoesNotContain("tags:", triggers);
        Assert.Contains(
            "group: program-kit-nuget-publication",
            workflow);
        Assert.Contains("cancel-in-progress: false", workflow);
    }

    [TestMethod]
    public void ReadOnlyJobProvesRunArtifactBytesAndAttestationsFirst()
    {
        string verify = VerifyJob(ReadWorkflow());

        Assert.Contains("      actions: read", verify);
        Assert.Contains("      attestations: read", verify);
        Assert.Contains("      contents: read", verify);
        Assert.DoesNotContain(": write", verify);
        Assert.DoesNotContain("environment:", verify);
        Assert.Contains(
            "actions/runs/$runId",
            verify);
        Assert.Contains(
            "actions/runs/$runId/artifacts?per_page=100",
            verify);
        Assert.Contains(
            "build/Test-ProgramKitCanonicalBuildRun.ps1",
            verify);
        Assert.Contains("fetch-depth: 0", verify);
        Assert.Contains("git merge-base --is-ancestor", verify);
        Assert.Contains(
            "ref: ${{ steps.selection.outputs.source-commit }}",
            verify);
        Assert.Contains(
            "sparse-checkout: build/program-kit-release-packages.json",
            verify);
        Assert.Contains(
            "artifact-ids: ${{ steps.selection.outputs.artifact-id }}",
            verify);
        Assert.Contains("digest-mismatch: error", verify);
        Assert.Contains(
            "build/Test-ProgramKitCanonicalBuild.ps1",
            verify);
        Assert.Contains(
            "-SourceRepositoryRoot \"$env:SELECTED_SOURCE_ROOT\"",
            verify);
        Assert.Contains("gh attestation verify", verify);
        Assert.Contains(
            "--signer-workflow",
            verify);
        Assert.Contains("--signer-digest", verify);
        Assert.Contains("--source-digest", verify);
        Assert.Contains("--source-ref refs/heads/main", verify);
        Assert.Contains("--deny-self-hosted-runners", verify);
        Assert.DoesNotContain("NuGet/login", verify);
        Assert.DoesNotContain("NUGET_USER", verify);
    }

    [TestMethod]
    public void ProtectedJobReverifiesBeforeTemporaryAuthentication()
    {
        string publish = PublishJob(ReadWorkflow());
        int reverify = publish.IndexOf(
            "build/Test-ProgramKitCanonicalBuild.ps1",
            StringComparison.Ordinal);
        int collision = publish.IndexOf(
            "Fail on an existing tag or release",
            StringComparison.Ordinal);
        int login = publish.IndexOf(
            NuGetLoginPin,
            StringComparison.Ordinal);
        int publication = publish.IndexOf(
            "build/Publish-ProgramKitCanonicalBuild.ps1",
            StringComparison.Ordinal);

        Assert.Contains("    needs: verify", publish);
        Assert.Contains(
            "    environment: program-kit-publication",
            publish);
        Assert.Contains("      actions: read", publish);
        Assert.Contains("      contents: write", publish);
        Assert.Contains("      id-token: write", publish);
        Assert.AreEqual(2, Count(publish, ": write"));
        Assert.Contains(
            "artifact-ids: ${{ needs.verify.outputs.artifact-id }}",
            publish);
        Assert.Contains("git merge-base --is-ancestor", publish);
        Assert.Contains(
            "ref: ${{ needs.verify.outputs.source-commit }}",
            publish);
        Assert.Contains(
            "-SourceRepositoryRoot \"$env:SELECTED_SOURCE_ROOT\"",
            publish);
        Assert.Contains("digest-mismatch: error", publish);
        Assert.IsTrue(
            reverify >= 0 &&
            reverify < collision &&
            collision < login &&
            login < publication);
        Assert.DoesNotContain("dotnet restore", publish);
        Assert.DoesNotContain("dotnet build", publish);
        Assert.DoesNotContain("dotnet test", publish);
        Assert.DoesNotContain("dotnet pack", publish);
        Assert.DoesNotContain("nuget pack", publish);
        Assert.DoesNotContain("--skip-duplicate", publish);
    }

    [TestMethod]
    public void PublisherUsesManifestBytesAndFailsLoudlyOnPartialPublication()
    {
        string publisher = ReadRepositoryFile(
            "build",
            "Publish-ProgramKitCanonicalBuild.ps1");

        Assert.Contains("package-manifest.json", publisher);
        Assert.Contains("SHA256SUMS", publisher);
        Assert.Contains("canonical-build-provenance.json", publisher);
        Assert.Contains("& dotnet nuget push", publisher);
        Assert.Contains(
            "'https://api.nuget.org/v3/index.json'",
            publisher);
        Assert.DoesNotContain("--skip-duplicate", publisher);
        Assert.Contains("Packages accepted before failure", publisher);
        Assert.Contains("'release'", publisher);
        Assert.Contains("'create'", publisher);
        Assert.Contains("'--target'", publisher);
        Assert.Contains("$SourceCommit", publisher);
        Assert.Contains("$releaseAssets", publisher);
        Assert.DoesNotContain("dotnet restore", publisher);
        Assert.DoesNotContain("dotnet build", publisher);
        Assert.DoesNotContain("dotnet test", publisher);
        Assert.DoesNotContain("dotnet pack", publisher);
        Assert.DoesNotContain("ZipFile", publisher);
        Assert.DoesNotContain("ZipArchive", publisher);
    }

    [TestMethod]
    public void PublisherPlanUsesOnlyVerifiedManifestPackagesAndAssets()
    {
        string root = CreateTemporaryRoot(
            "program-kit-publication-plan-");
        try
        {
            string canonicalBuild = WritePublicationFixture(root);
            var result = RunPublisherPlan(canonicalBuild);

            Assert.AreEqual(0, result.ExitCode, result.Stderr);
            using JsonDocument plan = JsonDocument.Parse(result.Stdout);
            Assert.AreEqual(
                "0.1.0-alpha.1",
                plan.RootElement
                    .GetProperty("planVersion")
                    .GetString());
            Assert.HasCount(
                1,
                plan.RootElement
                    .GetProperty("packages")
                    .EnumerateArray()
                    .ToArray());
            Assert.HasCount(
                4,
                plan.RootElement
                    .GetProperty("releaseAssets")
                    .EnumerateArray()
                    .ToArray());
            Assert.AreEqual(
                "v0.1.0-alpha.3",
                plan.RootElement.GetProperty("tag").GetString());
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public void PublicationActionsArePinnedToReviewedImmutableCommits()
    {
        string workflow = ReadWorkflow();
        MatchCollection uses = Regex.Matches(
            workflow,
            @"uses: (?<action>[A-Za-z0-9-]+/[A-Za-z0-9-]+)@(?<sha>[0-9a-f]{40})");

        Assert.HasCount(8, uses);
        Assert.AreEqual(4, Count(workflow, CheckoutPin));
        Assert.AreEqual(1, Count(workflow, SetupDotNetPin));
        Assert.AreEqual(2, Count(workflow, DownloadArtifactPin));
        Assert.AreEqual(1, Count(workflow, NuGetLoginPin));
        Assert.IsFalse(Regex.IsMatch(
            workflow,
            @"uses:\s+[^@\s]+@v[0-9]"));
    }

    [TestMethod]
    public void RunVerifierAcceptsOneEligibleCanonicalBuild()
    {
        string root = CreateTemporaryRoot("program-kit-run-selection-");
        try
        {
            var paths = WriteRunFixture(root);

            var result = RunSelectionVerifier(
                paths.RunPath,
                paths.ArtifactsPath);

            Assert.AreEqual(0, result.ExitCode, result.Stderr);
            using JsonDocument selection = JsonDocument.Parse(result.Stdout);
            Assert.AreEqual(
                SourceCommit,
                selection.RootElement
                    .GetProperty("sourceCommit")
                    .GetString());
            Assert.AreEqual(
                "789012",
                selection.RootElement
                    .GetProperty("artifactId")
                    .GetString());
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public void RunVerifierRejectsPullRequestOrFailedRuns()
    {
        string root = CreateTemporaryRoot(
            "program-kit-run-ineligible-");
        try
        {
            var paths = WriteRunFixture(
                root,
                eventName: "pull_request",
                conclusion: "failure");

            var result = RunSelectionVerifier(
                paths.RunPath,
                paths.ArtifactsPath);

            Assert.AreNotEqual(0, result.ExitCode);
            Assert.Contains(
                "not an eligible successful main-push",
                result.Stderr);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public void RunVerifierRejectsAmbiguousHostedArtifacts()
    {
        string root = CreateTemporaryRoot(
            "program-kit-run-artifacts-");
        try
        {
            var paths = WriteRunFixture(root, artifactCount: 2);

            var result = RunSelectionVerifier(
                paths.RunPath,
                paths.ArtifactsPath);

            Assert.AreNotEqual(0, result.ExitCode);
            Assert.Contains(
                "exactly one canonical-build artifact",
                result.Stderr);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public void RunVerifierRejectsExpiredOrMisnamedArtifacts()
    {
        string root = CreateTemporaryRoot(
            "program-kit-run-expired-");
        try
        {
            var paths = WriteRunFixture(
                root,
                artifactExpired: true,
                artifactName: "program-kit-canonical-build-latest");

            var result = RunSelectionVerifier(
                paths.RunPath,
                paths.ArtifactsPath);

            Assert.AreNotEqual(0, result.ExitCode);
            Assert.Contains(
                "does not belong to the eligible canonical build",
                result.Stderr);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static (
        string RunPath,
        string ArtifactsPath) WriteRunFixture(
            string root,
            string eventName = "push",
            string conclusion = "success",
            int artifactCount = 1,
            bool artifactExpired = false,
            string? artifactName = null)
    {
        var repository = new Dictionary<string, object?>
        {
            ["full_name"] = Repository,
        };
        var run = new Dictionary<string, object?>
        {
            ["id"] = long.Parse(
                RunId,
                CultureInfo.InvariantCulture),
            ["run_attempt"] = 1,
            ["repository"] = repository,
            ["head_repository"] = repository,
            ["event"] = eventName,
            ["head_branch"] = "main",
            ["head_sha"] = SourceCommit,
            ["status"] = "completed",
            ["conclusion"] = conclusion,
            ["path"] = WorkflowIdentity,
        };
        var artifacts = new List<Dictionary<string, object?>>();
        for (int index = 0; index < artifactCount; index++)
        {
            artifacts.Add(new Dictionary<string, object?>
            {
                ["id"] = 789012 + index,
                ["name"] = artifactName ??
                    string.Concat(
                        "program-kit-canonical-build-",
                        SourceCommit),
                ["digest"] = string.Concat(
                    "sha256:",
                    new string('b', 64)),
                ["size_in_bytes"] = 4096,
                ["expired"] = artifactExpired,
                ["workflow_run"] = new Dictionary<string, object?>
                {
                    ["id"] = long.Parse(
                        RunId,
                        CultureInfo.InvariantCulture),
                    ["head_branch"] = "main",
                    ["head_sha"] = SourceCommit,
                },
            });
        }

        string runPath = Path.Combine(root, "run.json");
        string artifactsPath = Path.Combine(root, "artifacts.json");
        File.WriteAllText(
            runPath,
            JsonSerializer.Serialize(run, IndentedJson),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        File.WriteAllText(
            artifactsPath,
            JsonSerializer.Serialize(
                new Dictionary<string, object?>
                {
                    ["total_count"] = artifactCount,
                    ["artifacts"] = artifacts,
                },
                IndentedJson),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        return (runPath, artifactsPath);
    }

    private static string WritePublicationFixture(string root)
    {
        string canonicalBuild = Path.Combine(root, "canonical-build");
        string feed = Path.Combine(canonicalBuild, "feed");
        Directory.CreateDirectory(feed);
        const string filename =
            "Orbyss.ProgramKit.CommandLine.0.1.0-alpha.3.nupkg";
        File.WriteAllText(
            Path.Combine(feed, filename),
            "package",
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        File.WriteAllText(
            Path.Combine(canonicalBuild, "package-manifest.json"),
            JsonSerializer.Serialize(
                new
                {
                    productVersion = "0.1.0-alpha.3",
                    packages = new[]
                    {
                        new
                        {
                            packageId =
                                "Orbyss.ProgramKit.CommandLine",
                            filename,
                        },
                    },
                },
                IndentedJson),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        File.WriteAllText(
            Path.Combine(canonicalBuild, "SHA256SUMS"),
            "fixture\n",
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        File.WriteAllText(
            Path.Combine(
                canonicalBuild,
                "canonical-build-provenance.json"),
            JsonSerializer.Serialize(
                new
                {
                    productVersion = "0.1.0-alpha.3",
                    sourceCommit = SourceCommit,
                },
                IndentedJson),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        return canonicalBuild;
    }

    private static (
        int ExitCode,
        string Stdout,
        string Stderr) RunPublisherPlan(string canonicalBuild)
    {
        ProcessStartInfo start = new("pwsh")
        {
            WorkingDirectory = ConformanceInputs.RepositoryRoot,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };
        start.ArgumentList.Add("-NoProfile");
        start.ArgumentList.Add("-File");
        start.ArgumentList.Add(Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "build",
            "Publish-ProgramKitCanonicalBuild.ps1"));
        start.ArgumentList.Add("-CanonicalBuildRoot");
        start.ArgumentList.Add(canonicalBuild);
        start.ArgumentList.Add("-Repository");
        start.ArgumentList.Add(Repository);
        start.ArgumentList.Add("-SourceCommit");
        start.ArgumentList.Add(SourceCommit);
        start.ArgumentList.Add("-ProductVersion");
        start.ArgumentList.Add("0.1.0-alpha.3");
        start.ArgumentList.Add("-PlanOnly");
        using Process process = Process.Start(start)!;
        string stdout = process.StandardOutput.ReadToEnd();
        string stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();
        return (process.ExitCode, stdout, stderr);
    }

    private static (
        int ExitCode,
        string Stdout,
        string Stderr) RunSelectionVerifier(
            string runPath,
            string artifactsPath)
    {
        ProcessStartInfo start = new("pwsh")
        {
            WorkingDirectory = ConformanceInputs.RepositoryRoot,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };
        start.ArgumentList.Add("-NoProfile");
        start.ArgumentList.Add("-File");
        start.ArgumentList.Add(Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "build",
            "Test-ProgramKitCanonicalBuildRun.ps1"));
        start.ArgumentList.Add("-RunMetadataPath");
        start.ArgumentList.Add(runPath);
        start.ArgumentList.Add("-ArtifactMetadataPath");
        start.ArgumentList.Add(artifactsPath);
        start.ArgumentList.Add("-Repository");
        start.ArgumentList.Add(Repository);
        start.ArgumentList.Add("-RunId");
        start.ArgumentList.Add(RunId);
        start.ArgumentList.Add("-WorkflowIdentity");
        start.ArgumentList.Add(WorkflowIdentity);
        using Process process = Process.Start(start)!;
        string stdout = process.StandardOutput.ReadToEnd();
        string stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();
        return (process.ExitCode, stdout, stderr);
    }

    private static string ReadWorkflow() =>
        ReadRepositoryFile(
                ".github",
                "workflows",
                "publish-nuget.yml")
            .Replace("\r\n", "\n", StringComparison.Ordinal);

    private static string ReadRepositoryFile(params string[] segments) =>
        File.ReadAllText(Path.Combine(
            [ConformanceInputs.RepositoryRoot, .. segments]));

    private static string VerifyJob(string workflow) =>
        Slice(
            workflow,
            "  verify:\n",
            "\n  publish:");

    private static string PublishJob(string workflow) =>
        workflow[workflow.IndexOf(
            "  publish:\n",
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

    private static string CreateTemporaryRoot(string prefix)
    {
        string path = Path.Combine(
            Path.GetTempPath(),
            string.Concat(prefix, Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(path);
        return path;
    }
}
