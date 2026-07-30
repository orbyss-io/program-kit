using System.Diagnostics;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Xml.Linq;
using Orbyss.ProgramKit.ConformanceTests.Infrastructure;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

[TestClass]
public sealed class ConsumerFeedPackagingConformanceTests
{
    private const string ProductVersion = "0.1.0-alpha.3";
    private static readonly string[] ExpectedPhases =
    [
        "restore",
        "build",
        "aggregate-pack",
    ];
    private static readonly JsonSerializerOptions IndentedJson =
        new() { WriteIndented = true };

    [TestMethod]
    public void CanonicalManifestSelectsEveryFirstPartyProjectExactlyOnce()
    {
        string root = ConformanceInputs.RepositoryRoot;
        string manifestPath = Path.Combine(
            root,
            "build",
            "program-kit-release-packages.json");
        using JsonDocument document = JsonDocument.Parse(
            File.ReadAllText(manifestPath));
        JsonElement rootElement = document.RootElement;

        Assert.AreEqual(
            "0.1.0-alpha.1",
            rootElement.GetProperty("manifestVersion").GetString());
        Assert.AreEqual(
            ProductVersion,
            rootElement.GetProperty("productVersion").GetString());
        string[] selectedProjects = rootElement
            .GetProperty("packages")
            .EnumerateArray()
            .Select(package => Path.GetFullPath(
                Path.Combine(
                    root,
                    package
                        .GetProperty("projectPath")
                        .GetString()!
                        .Replace('/', Path.DirectorySeparatorChar))))
            .Order(StringComparer.Ordinal)
            .ToArray();
        string[] actualProjects = Directory
            .EnumerateFiles(
                Path.Combine(root, "src"),
                "*.csproj",
                SearchOption.AllDirectories)
            .Select(Path.GetFullPath)
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.AreSequenceEqual(actualProjects, selectedProjects);
        Assert.HasCount(
            selectedProjects.Length,
            selectedProjects.Distinct(StringComparer.Ordinal));
    }

    [TestMethod]
    public void CanonicalManifestMatchesProjectIdentitiesAndDependencyClosure()
    {
        string root = ConformanceInputs.RepositoryRoot;
        using JsonDocument document = JsonDocument.Parse(
            File.ReadAllText(Path.Combine(
                root,
                "build",
                "program-kit-release-packages.json")));
        JsonElement[] packages = document.RootElement
            .GetProperty("packages")
            .EnumerateArray()
            .ToArray();
        string[] packageIds = packages
            .Select(package => package.GetProperty("packageId").GetString()!)
            .ToArray();

        Assert.HasCount(
            packageIds.Length,
            packageIds.Distinct(StringComparer.Ordinal));
        foreach (JsonElement package in packages)
        {
            string projectPath = Path.GetFullPath(Path.Combine(
                root,
                package
                    .GetProperty("projectPath")
                    .GetString()!
                    .Replace('/', Path.DirectorySeparatorChar)));
            XDocument project = XDocument.Load(projectPath);
            string packageId = project
                .Descendants("PackageId")
                .Select(element => element.Value)
                .FirstOrDefault() ??
                Path.GetFileNameWithoutExtension(projectPath);
            Assert.AreEqual(
                package.GetProperty("packageId").GetString(),
                packageId);
            Assert.IsTrue(
                package.GetProperty(
                    "coordinatedVersionRequired").GetBoolean());

            string[] actualDependencies = project
                .Descendants("ProjectReference")
                .Select(reference => reference.Attribute("Include")!.Value)
                .Select(reference => Path.GetFullPath(Path.Combine(
                    Path.GetDirectoryName(projectPath)!,
                    reference)))
                .Select(referencePath =>
                {
                    XDocument dependency = XDocument.Load(referencePath);
                    return dependency
                        .Descendants("PackageId")
                        .Select(element => element.Value)
                        .FirstOrDefault() ??
                        Path.GetFileNameWithoutExtension(referencePath);
                })
                .Order(StringComparer.Ordinal)
                .ToArray();
            string[] expectedDependencies = package
                .GetProperty("firstPartyDependencies")
                .EnumerateArray()
                .Select(dependency => dependency.GetString()!)
                .Order(StringComparer.Ordinal)
                .ToArray();
            Assert.AreSequenceEqual(
                expectedDependencies,
                actualDependencies,
                packageId);
            foreach (string dependency in expectedDependencies)
            {
                Assert.Contains(dependency, packageIds);
            }
        }
    }

    [TestMethod]
    public void AggregatePackCannotRestoreOrBuildSelectedProjects()
    {
        string root = ConformanceInputs.RepositoryRoot;
        XDocument packProject = XDocument.Load(Path.Combine(
            root,
            "build",
            "ProgramKit.Pack.proj"));
        XElement target = packProject
            .Descendants("Target")
            .Single(element =>
                element.Attribute("Name")?.Value ==
                "PackManifestSelection");
        XElement pack = target.Descendants("MSBuild").Single();
        XAttribute? parallel = pack.Attribute("BuildInParallel");
        string? properties = pack.Attribute("Properties")?.Value;

        Assert.IsNotNull(parallel);
        Assert.AreEqual("true", parallel.Value);
        Assert.IsNotNull(properties);
        Assert.Contains("NoRestore=true", properties);
        Assert.Contains("NoBuild=true", properties);
        Assert.Contains("_IsPacking=true", properties);
        Assert.Contains("IncludeSymbols=false", properties);
        Assert.IsNotEmpty(target
            .Descendants("Error")
            .Where(error =>
                error.Attribute("Condition")?.Value.Contains(
                    "NoRestore",
                    StringComparison.Ordinal) == true));
        Assert.IsNotEmpty(target
            .Descendants("Error")
            .Where(error =>
                error.Attribute("Condition")?.Value.Contains(
                    "NoBuild",
                    StringComparison.Ordinal) == true));
    }

    [TestMethod]
    public void PackerPlanHasOneRestoreOneBuildAndOneAggregatePack()
    {
        string root = ConformanceInputs.RepositoryRoot;
        string output = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-feed-plan-",
                Guid.NewGuid().ToString("N")));
        ProcessStartInfo start = new("pwsh")
        {
            WorkingDirectory = root,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };
        start.ArgumentList.Add("-NoProfile");
        start.ArgumentList.Add("-File");
        start.ArgumentList.Add(Path.Combine(
            root,
            "build",
            "Invoke-PackConsumerFeed.ps1"));
        start.ArgumentList.Add("-OutputRoot");
        start.ArgumentList.Add(output);
        start.ArgumentList.Add("-PlanOnly");
        using Process process = Process.Start(start)!;
        string stdout = process.StandardOutput.ReadToEnd();
        string stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();

        Assert.AreEqual(0, process.ExitCode, stderr);
        Assert.IsFalse(Directory.Exists(output));
        using JsonDocument plan = JsonDocument.Parse(stdout);
        Assert.AreEqual(
            ProductVersion,
            plan.RootElement.GetProperty("productVersion").GetString());
        JsonElement[] invocations = plan.RootElement
            .GetProperty("invocations")
            .EnumerateArray()
            .ToArray();
        Assert.HasCount(3, invocations);
        Assert.AreSequenceEqual(
            ExpectedPhases,
            invocations
                .Select(invocation =>
                    invocation.GetProperty("phase").GetString())
                .ToArray());
        string[] packArguments = invocations[2]
            .GetProperty("arguments")
            .EnumerateArray()
            .Select(argument => argument.GetString()!)
            .ToArray();
        Assert.Contains("-property:NoRestore=true", packArguments);
        Assert.Contains("-property:NoBuild=true", packArguments);
        Assert.Contains("-maxCpuCount:4", packArguments);
    }

    [TestMethod]
    public void ColdProofConsumesCanonicalPackageSelectionWithoutCountOrVersionLiterals()
    {
        string root = ConformanceInputs.RepositoryRoot;
        string script = File.ReadAllText(Path.Combine(
            root,
            "build",
            "Invoke-ConsumerCliColdProof.ps1"));

        Assert.Contains("program-kit-release-packages.json", script);
        Assert.Contains("$releaseManifest.productVersion", script);
        Assert.DoesNotContain("$packages.Count -ne 29", script);
        Assert.DoesNotContain("@($lock.resources).Count -ne", script);
        Assert.DoesNotContain("$version = '0.1.0-alpha.", script);
        Assert.Contains("console-command-sketch.json", script);
        Assert.DoesNotContain(
            "Join-Path $consoleFixturePath 'console-input-request.json'",
            script);
        Assert.Contains("'dotnet', 'scaffold-console-request'", script);
        Assert.Contains("'csharp-gate', 'scaffold-lock'", script);
        Assert.Contains("'csharp-gate', 'bind'", script);
        Assert.Contains("ProgramKitVerifyGeneratedProject", script);
        Assert.Contains("'validate', $path", script);
        Assert.Contains("'artifacts', 'inspect', $path", script);
        Assert.Contains("sourceAndHelperLeakage = 'absent'", script);
    }

    [TestMethod]
    public void PublicConsumerFeedExcludesTransactionInputsAndReceipts()
    {
        string root = ConformanceInputs.RepositoryRoot;
        string script = File.ReadAllText(Path.Combine(
            root,
            "build",
            "Invoke-PackConsumerFeed.ps1"));

        Assert.Contains(
            "Remove-Item -LiteralPath $selectionPropsPath -Force",
            script);
        Assert.Contains(
            "Remove-Item -LiteralPath $receiptRootPath -Recurse -Force",
            script);
        Assert.Contains(
            "The public consumer-feed output contains unlisted transaction bytes.",
            script);
    }

    [TestMethod]
    public void HandoffArchiveIsDeterministicAndKeepsTheFlatFeedAuditable()
    {
        string root = CreateTemporaryRoot("program-kit-handoff-test-");
        try
        {
            string feed = WriteFeedFixture(root);
            string first = Path.Combine(root, "first");
            string second = Path.Combine(root, "second");

            RunHandoff(feed, first);
            RunHandoff(feed, second);

            string firstArchive = Directory
                .EnumerateFiles(first, "*.zip")
                .Single();
            string secondArchive = Directory
                .EnumerateFiles(second, "*.zip")
                .Single();
            Assert.AreEqual(FileDigest(firstArchive), FileDigest(secondArchive));
            using ZipArchive archive = ZipFile.OpenRead(firstArchive);
            string[] entries = archive.Entries
                .Select(entry => entry.FullName)
                .ToArray();
            Assert.AreSequenceEqual(
                entries.Order(StringComparer.Ordinal),
                entries);
            Assert.Contains(
                "feed/Orbyss.ProgramKit.CommandLine.0.1.0-alpha.3.nupkg",
                entries);
            Assert.Contains("package-manifest.json", entries);
            Assert.Contains("SHA256SUMS", entries);
            Assert.Contains("JTEST-PROMPT.md", entries);
            Assert.Contains(
                "0.1.0-alpha.3",
                File.ReadAllText(Path.Combine(first, "JTEST-PROMPT.md")));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public void HandoffRefusesModifiedPackageBytesWithoutPromotingOutput()
    {
        string root = CreateTemporaryRoot("program-kit-handoff-tamper-");
        try
        {
            string feed = WriteFeedFixture(root);
            File.AppendAllText(
                Path.Combine(
                    feed,
                    "feed",
                    "Orbyss.ProgramKit.CommandLine.0.1.0-alpha.3.nupkg"),
                "tamper",
                Encoding.UTF8);
            string output = Path.Combine(root, "output");

            var result = RunHandoff(
                feed,
                output,
                expectedSuccess: false);

            Assert.AreNotEqual(0, result.ExitCode);
            Assert.Contains(
                "Package evidence does not match",
                result.Stderr);
            Assert.IsFalse(Directory.Exists(output));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static string WriteFeedFixture(string root)
    {
        string feedRoot = Path.Combine(root, "feed-root");
        string packageRoot = Path.Combine(feedRoot, "feed");
        Directory.CreateDirectory(packageRoot);
        string filename =
            "Orbyss.ProgramKit.CommandLine.0.1.0-alpha.3.nupkg";
        string packagePath = Path.Combine(packageRoot, filename);
        File.WriteAllText(packagePath, "package", Encoding.UTF8);
        string packageDigest = FileDigest(packagePath);
        var manifest = new
        {
            manifestVersion = "0.1.0-alpha.1",
            productVersion = "0.1.0-alpha.3",
            sourcePackageManifestSha256 = string.Concat(
                "sha256:",
                new string('a', 64)),
            packages = new[]
            {
                new
                {
                    packageId = "Orbyss.ProgramKit.CommandLine",
                    version = "0.1.0-alpha.3",
                    filename,
                    sha256 = string.Concat("sha256:", packageDigest),
                    size = new FileInfo(packagePath).Length,
                    role = "tool",
                    firstPartyDependencies = Array.Empty<object>(),
                },
            },
        };
        string manifestPath = Path.Combine(
            feedRoot,
            "package-manifest.json");
        File.WriteAllText(
            manifestPath,
            string.Concat(
                JsonSerializer.Serialize(
                    manifest,
                    IndentedJson),
                "\n"),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        string[] checksumRows =
        [
            string.Concat(packageDigest, "  feed/", filename),
            string.Concat(
                FileDigest(manifestPath),
                "  package-manifest.json"),
        ];
        File.WriteAllText(
            Path.Combine(feedRoot, "SHA256SUMS"),
            string.Concat(
                string.Join("\n", checksumRows.Order(StringComparer.Ordinal)),
                "\n"),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        return feedRoot;
    }

    private static (int ExitCode, string Stdout, string Stderr) RunHandoff(
        string feed,
        string output,
        bool expectedSuccess = true)
    {
        string root = ConformanceInputs.RepositoryRoot;
        ProcessStartInfo start = new("pwsh")
        {
            WorkingDirectory = root,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };
        start.ArgumentList.Add("-NoProfile");
        start.ArgumentList.Add("-File");
        start.ArgumentList.Add(Path.Combine(
            root,
            "build",
            "New-ConsumerFeedHandoff.ps1"));
        start.ArgumentList.Add("-ConsumerFeedRoot");
        start.ArgumentList.Add(feed);
        start.ArgumentList.Add("-OutputRoot");
        start.ArgumentList.Add(output);
        using Process process = Process.Start(start)!;
        string stdout = process.StandardOutput.ReadToEnd();
        string stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();
        if (expectedSuccess)
        {
            Assert.AreEqual(0, process.ExitCode, stderr);
        }

        return (process.ExitCode, stdout, stderr);
    }

    private static string CreateTemporaryRoot(string prefix)
    {
        string path = Path.Combine(
            Path.GetTempPath(),
            string.Concat(prefix, Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(path);
        return path;
    }

    private static string FileDigest(string path) =>
        Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(path)));
}
