using System.Diagnostics;
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
}
