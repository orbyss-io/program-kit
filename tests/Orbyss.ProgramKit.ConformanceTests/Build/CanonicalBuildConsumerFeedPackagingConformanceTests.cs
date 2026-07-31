using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

[TestClass]
public sealed class CanonicalBuildConsumerFeedPackagingConformanceTests
{
    private static readonly JsonSerializerOptions CanonicalIndentedJson =
        new() { WriteIndented = true };
    private static readonly string[] IntegrationPhases =
    [
        "locked-restore",
        "unit-tests",
        "private-gate",
    ];
    private const string IntegrationProfileIdentity =
        "pkid:profile:program-kit:private-csharp-gate-exhaustive";
    private const string IntegrationProfileVersion = "1.0.1";
    private const string IntegrationProfileDigest =
        "sha256:2e383f220030e2933dca3e7af27543e73a28451506c183538d6d84aba689791f";
    private const string CanonicalRepository = "orbyss-io/program-kit";
    private const string CanonicalEvent = "push";
    private const string CanonicalBranch = "refs/heads/main";
    private const string CanonicalSourceCommit =
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    private const string CanonicalWorkflowIdentity =
        ".github/workflows/program-kit-integration.yml";
    private const string CanonicalWorkflowRevision =
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
    private const string CanonicalRunId = "123456";
    private const string CanonicalArtifactName =
        "program-kit-canonical-build-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    [TestMethod]
    public void IntegrationPlanIsFiniteAndBindsTheExhaustiveProfile()
    {
        string root = ConformanceInputs.RepositoryRoot;
        var result = RunPowerShell(
            Path.Combine(
                root,
                "build",
                "Invoke-ProgramKitIntegration.ps1"),
            ["-PlanOnly"]);

        Assert.AreEqual(0, result.ExitCode, result.Stderr);
        using JsonDocument plan = JsonDocument.Parse(result.Stdout);
        JsonElement rootElement = plan.RootElement;
        Assert.AreEqual(
            "0.1.0-alpha.1",
            rootElement.GetProperty("planVersion").GetString());
        JsonElement profile = rootElement.GetProperty("profile");
        Assert.AreEqual(
            IntegrationProfileIdentity,
            profile.GetProperty("identity").GetString());
        Assert.AreEqual(
            IntegrationProfileVersion,
            profile.GetProperty("version").GetString());
        Assert.AreEqual(
            IntegrationProfileDigest,
            profile.GetProperty("digest").GetString());

        JsonElement[] invocations = rootElement
            .GetProperty("invocations")
            .EnumerateArray()
            .ToArray();
        Assert.HasCount(3, invocations);
        Assert.AreSequenceEqual(
            IntegrationPhases,
            invocations
                .Select(invocation =>
                    invocation.GetProperty("phase").GetString())
                .ToArray());
        Assert.HasCount(
            1,
            invocations.Where(invocation =>
                invocation.GetProperty("executable").GetString() == "dotnet" &&
                invocation
                    .GetProperty("arguments")
                    .EnumerateArray()
                    .Any(argument => argument.GetString() == "restore")));
        string[] restoreArguments = invocations[0]
            .GetProperty("arguments")
            .EnumerateArray()
            .Select(argument => argument.GetString()!)
            .ToArray();
        Assert.Contains("--locked-mode", restoreArguments);
        string[] testArguments = invocations[1]
            .GetProperty("arguments")
            .EnumerateArray()
            .Select(argument => argument.GetString()!)
            .ToArray();
        Assert.Contains("--no-restore", testArguments);
        string[] gateArguments = invocations[2]
            .GetProperty("arguments")
            .EnumerateArray()
            .Select(argument => argument.GetString()!)
            .ToArray();
        Assert.AreEqual("Exhaustive", gateArguments[^1]);
    }

    [TestMethod]
    public void CanonicalBuildProvenanceClosesTheCompletePackageSet()
    {
        string root = CreateCanonicalTemporaryRoot(
            "program-kit-canonical-build-");
        try
        {
            string canonicalBuild = WriteCanonicalBuildFixture(root);

            var written = RunCanonicalBuildCommand(
                "Write-ProgramKitCanonicalBuildProvenance.ps1",
                canonicalBuild);

            Assert.AreEqual(0, written.ExitCode, written.Stderr);
            using JsonDocument result = JsonDocument.Parse(written.Stdout);
            Assert.AreEqual(
                29,
                result.RootElement.GetProperty("packageCount").GetInt32());
            Assert.AreEqual(
                CanonicalArtifactName,
                result.RootElement
                    .GetProperty("artifactName")
                    .GetString());
            string provenancePath = Path.Combine(
                canonicalBuild,
                "canonical-build-provenance.json");
            using JsonDocument provenance = JsonDocument.Parse(
                File.ReadAllText(provenancePath));
            Assert.AreEqual(
                CanonicalRepository,
                provenance.RootElement
                    .GetProperty("repository")
                    .GetString());
            Assert.AreEqual(
                CanonicalSourceCommit,
                provenance.RootElement
                    .GetProperty("sourceCommit")
                    .GetString());
            Assert.HasCount(
                29,
                provenance.RootElement
                    .GetProperty("packages")
                    .EnumerateArray()
                    .ToArray());

            var verified = RunCanonicalBuildCommand(
                "Test-ProgramKitCanonicalBuild.ps1",
                canonicalBuild);

            Assert.AreEqual(0, verified.ExitCode, verified.Stderr);
            using JsonDocument verification = JsonDocument.Parse(
                verified.Stdout);
            Assert.AreEqual(
                CanonicalRunId,
                verification.RootElement.GetProperty("runId").GetString());
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public void CanonicalBuildVerifierRejectsModifiedPackageBytes()
    {
        string root = CreateCanonicalTemporaryRoot(
            "program-kit-canonical-build-tamper-");
        try
        {
            string canonicalBuild = WriteCanonicalBuildFixture(root);
            var written = RunCanonicalBuildCommand(
                "Write-ProgramKitCanonicalBuildProvenance.ps1",
                canonicalBuild);
            Assert.AreEqual(0, written.ExitCode, written.Stderr);
            string packagePath = Directory
                .EnumerateFiles(
                    Path.Combine(canonicalBuild, "feed"),
                    "*.nupkg")
                .First();
            File.AppendAllText(packagePath, "tamper", Encoding.UTF8);

            var verified = RunCanonicalBuildCommand(
                "Test-ProgramKitCanonicalBuild.ps1",
                canonicalBuild);

            Assert.AreNotEqual(0, verified.ExitCode);
            Assert.Contains(
                "Package evidence does not match exact bytes",
                verified.Stderr);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public void CanonicalBuildVerifierRejectsWrongExecutionMetadata()
    {
        string root = CreateCanonicalTemporaryRoot(
            "program-kit-canonical-build-metadata-");
        try
        {
            string canonicalBuild = WriteCanonicalBuildFixture(root);
            var written = RunCanonicalBuildCommand(
                "Write-ProgramKitCanonicalBuildProvenance.ps1",
                canonicalBuild);
            Assert.AreEqual(0, written.ExitCode, written.Stderr);

            var verified = RunCanonicalBuildCommand(
                "Test-ProgramKitCanonicalBuild.ps1",
                canonicalBuild,
                sourceCommit:
                    "cccccccccccccccccccccccccccccccccccccccc");

            Assert.AreNotEqual(0, verified.ExitCode);
            Assert.Contains(
                "differs from expected execution evidence",
                verified.Stderr);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public void CanonicalBuildVerifierRejectsUnlistedArtifactBytes()
    {
        string root = CreateCanonicalTemporaryRoot(
            "program-kit-canonical-build-extra-");
        try
        {
            string canonicalBuild = WriteCanonicalBuildFixture(root);
            var written = RunCanonicalBuildCommand(
                "Write-ProgramKitCanonicalBuildProvenance.ps1",
                canonicalBuild);
            Assert.AreEqual(0, written.ExitCode, written.Stderr);
            File.WriteAllText(
                Path.Combine(canonicalBuild, "unlisted.txt"),
                "unexpected",
                Encoding.UTF8);

            var verified = RunCanonicalBuildCommand(
                "Test-ProgramKitCanonicalBuild.ps1",
                canonicalBuild);

            Assert.AreNotEqual(0, verified.ExitCode);
            Assert.Contains(
                "missing or unexpected entries",
                verified.Stderr);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public void IntegrationAndProvenanceScriptsHaveNoPublicationSideEffects()
    {
        string root = ConformanceInputs.RepositoryRoot;
        string[] paths =
        [
            "Invoke-ProgramKitIntegration.ps1",
            "ProgramKitCanonicalBuildProvenance.psm1",
            "Write-ProgramKitCanonicalBuildProvenance.ps1",
            "Test-ProgramKitCanonicalBuild.ps1",
        ];
        string scripts = string.Join(
            "\n",
            paths.Select(path =>
                File.ReadAllText(Path.Combine(root, "build", path))));

        Assert.DoesNotContain("Publish-Module", scripts);
        Assert.DoesNotContain("dotnet nuget push", scripts);
        Assert.DoesNotContain("Invoke-WebRequest", scripts);
        Assert.DoesNotContain("Invoke-RestMethod", scripts);
        Assert.DoesNotContain("GITHUB_TOKEN", scripts);
        Assert.DoesNotContain("NUGET_API_KEY", scripts);
        Assert.DoesNotContain("ZipFile", scripts);
        Assert.DoesNotContain("ZipArchive", scripts);
        Assert.DoesNotContain("ExtractTo", scripts);
    }

    private static string WriteCanonicalBuildFixture(string temporaryRoot)
    {
        string repositoryRoot = ConformanceInputs.RepositoryRoot;
        string sourceManifestPath = Path.Combine(
            repositoryRoot,
            "build",
            "program-kit-release-packages.json");
        using JsonDocument sourceManifest = JsonDocument.Parse(
            File.ReadAllText(sourceManifestPath));
        string productVersion = sourceManifest.RootElement
            .GetProperty("productVersion")
            .GetString()!;
        string canonicalBuild = Path.Combine(
            temporaryRoot,
            "canonical-build");
        string feed = Path.Combine(canonicalBuild, "feed");
        Directory.CreateDirectory(feed);
        var packageEvidence = new List<object>();
        foreach (JsonElement selection in sourceManifest.RootElement
            .GetProperty("packages")
            .EnumerateArray())
        {
            string packageId = selection
                .GetProperty("packageId")
                .GetString()!;
            string role = selection.GetProperty("role").GetString()!;
            string filename = string.Concat(
                packageId,
                ".",
                productVersion,
                ".nupkg");
            string packagePath = Path.Combine(feed, filename);
            File.WriteAllText(
                packagePath,
                string.Concat("package:", packageId),
                new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
            object[] dependencies =
                role is "tool" or "build-integration"
                    ? []
                    : selection
                        .GetProperty("firstPartyDependencies")
                        .EnumerateArray()
                        .Select(dependency => (object)new
                        {
                            packageId = dependency.GetString(),
                            versionRange = productVersion,
                        })
                        .ToArray();
            packageEvidence.Add(new
            {
                packageId,
                version = productVersion,
                filename,
                sha256 = string.Concat(
                    "sha256:",
                    CanonicalFileDigest(packagePath)),
                size = new FileInfo(packagePath).Length,
                role,
                firstPartyDependencies = dependencies,
            });
        }

        var manifest = new
        {
            manifestVersion = "0.1.0-alpha.1",
            productVersion,
            sourcePackageManifestSha256 = string.Concat(
                "sha256:",
                CanonicalFileDigest(sourceManifestPath)),
            packages = packageEvidence,
        };
        string packageManifestPath = Path.Combine(
            canonicalBuild,
            "package-manifest.json");
        File.WriteAllText(
            packageManifestPath,
            string.Concat(
                JsonSerializer.Serialize(manifest, CanonicalIndentedJson),
                "\n"),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        string[] checksumRows = packageEvidence
            .Select(package =>
            {
                JsonElement element = JsonSerializer.SerializeToElement(
                    package);
                return string.Concat(
                    element
                        .GetProperty("sha256")
                        .GetString()!
                        .AsSpan(7),
                    "  feed/",
                    element.GetProperty("filename").GetString());
            })
            .Append(string.Concat(
                CanonicalFileDigest(packageManifestPath),
                "  package-manifest.json"))
            .Order(StringComparer.Ordinal)
            .ToArray();
        File.WriteAllText(
            Path.Combine(canonicalBuild, "SHA256SUMS"),
            string.Concat(string.Join("\n", checksumRows), "\n"),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        return canonicalBuild;
    }

    private static (
        int ExitCode,
        string Stdout,
        string Stderr) RunCanonicalBuildCommand(
            string scriptName,
            string canonicalBuild,
            string sourceCommit = CanonicalSourceCommit)
    {
        return RunPowerShell(
            Path.Combine(
                ConformanceInputs.RepositoryRoot,
                "build",
                scriptName),
            [
                "-CanonicalBuildRoot",
                canonicalBuild,
                "-Repository",
                CanonicalRepository,
                "-Event",
                CanonicalEvent,
                "-Branch",
                CanonicalBranch,
                "-SourceCommit",
                sourceCommit,
                "-WorkflowIdentity",
                CanonicalWorkflowIdentity,
                "-WorkflowRevision",
                CanonicalWorkflowRevision,
                "-RunId",
                CanonicalRunId,
                "-ArtifactName",
                CanonicalArtifactName,
                "-ProfileIdentity",
                IntegrationProfileIdentity,
                "-ProfileVersion",
                IntegrationProfileVersion,
                "-ProfileSha256",
                IntegrationProfileDigest,
            ]);
    }

    private static (
        int ExitCode,
        string Stdout,
        string Stderr) RunPowerShell(
            string script,
            IReadOnlyList<string> arguments)
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
        start.ArgumentList.Add(script);
        foreach (string argument in arguments)
        {
            start.ArgumentList.Add(argument);
        }

        using Process process = Process.Start(start)!;
        string stdout = process.StandardOutput.ReadToEnd();
        string stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();
        return (process.ExitCode, stdout, stderr);
    }

    private static string CreateCanonicalTemporaryRoot(string prefix)
    {
        string path = Path.Combine(
            Path.GetTempPath(),
            string.Concat(prefix, Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(path);
        return path;
    }

    private static string CanonicalFileDigest(string path) =>
        Convert.ToHexStringLower(
            SHA256.HashData(File.ReadAllBytes(path)));
}
