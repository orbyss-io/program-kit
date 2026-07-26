using System.Collections.Immutable;
using System.Reflection;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Text;
using System.Text.Json;
using System.Xml.Linq;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

[TestClass]
public sealed class BuildSpineConformanceTests
{
    private static readonly ImmutableArray<string> ProductProjectNames =
    [
        "Orbyss.ProgramKit.Architecture",
        "Orbyss.ProgramKit.Artifacts",
        "Orbyss.ProgramKit.CapabilityBundle",
        "Orbyss.ProgramKit.CommandLine",
        "Orbyss.ProgramKit.Development",
        "Orbyss.ProgramKit.DevContainers",
        "Orbyss.ProgramKit.DotNet",
        "Orbyss.ProgramKit.Modularity",
        "Orbyss.ProgramKit.Modularity.InProcess",
        "Orbyss.ProgramKit.Operations",
        "Orbyss.ProgramKit.Planning",
        "Orbyss.ProgramKit.Quality",
        "Orbyss.ProgramKit.SecretResolution",
        "Orbyss.ProgramKit.Serialization.JSON",
        "Orbyss.ProgramKit.Tasks",
        "Orbyss.ProgramKit.Tasks.Core",
        "Orbyss.ProgramKit.Tasks.Hosting",
        "Orbyss.ProgramKit.Tasks.InProcess",
        "Orbyss.ProgramKit.Tasks.Schedules",
        "Orbyss.ProgramKit.Tasks.Schedules.Cronos",
        "Orbyss.ProgramKit.Workbench",
    ];

    private static readonly ImmutableArray<string> ObservatoryFixtureProjectNames =
    [
        "ObservatoryScheduling.Api",
        "ObservatoryScheduling.Console",
        "ObservatoryScheduling.Constraints.DarknessWindow",
        "ObservatoryScheduling.Core",
        "ObservatoryScheduling.Scheduling.Api",
        "ObservatoryScheduling.Scheduling.FirstAvailable",
        "ObservatoryScheduling.Tests",
        "ObservatoryScheduling.Visibility.Static",
        "ObservatoryScheduling.Worker",
    ];

    [TestMethod]
    public void GlobalJsonPinsTheApprovedSdkWithoutFallback()
    {
        var globalJson = ConformanceInputs.Read("global.json");

        Assert.Contains("\"version\": \"10.0.302\"", globalJson);
        Assert.Contains("\"rollForward\": \"disable\"", globalJson);
        Assert.Contains("\"allowPrerelease\": false", globalJson);
        Assert.Contains("\"MSTest.Sdk\": \"4.3.2\"", globalJson);
        Assert.Contains("\"runner\": \"Microsoft.Testing.Platform\"", globalJson);
        Assert.DoesNotContain("8.0", globalJson);
    }

    [TestMethod]
    public void DirectoryBuildPolicyMaterializesTheApprovedTargetProfile()
    {
        var document = XDocument.Parse(ConformanceInputs.Read("Directory.Build.props"));

        AssertProperty(document, "TargetFramework", "net10.0");
        AssertProperty(document, "LangVersion", "14.0");
        AssertProperty(document, "ProgramKitTargetProfileId", "pkid:profile:program-kit:dotnet-10");
        AssertProperty(document, "ProgramKitTargetProfileVersion", "1.0.0");
        AssertProperty(document, "ProgramKitCurrentWorkUnit", "PK-W090");
        AssertProperty(document, "ProgramKitSdkVersion", "10.0.302");
        AssertProperty(document, "ProgramKitSdkRollForward", "disable");
        AssertProperty(document, "ProgramKitAllowPrereleaseSdk", "false");
        AssertProperty(document, "Version", "0.1.0-alpha.1");
        AssertProperty(document, "Deterministic", "true");
        AssertProperty(document, "TreatWarningsAsErrors", "true");
        AssertProperty(document, "CodeAnalysisTreatWarningsAsErrors", "true");
        AssertProperty(document, "MSBuildTreatWarningsAsErrors", "true");
        AssertProperty(document, "RestoreTreatWarningsAsErrors", "true");
        AssertProperty(document, "NoWarn", "__ProgramKitNoWarningSuppression__");
        AssertProperty(
            document,
            "WarningsNotAsErrors",
            "__ProgramKitNoWarningDemotion__");
        AssertProperty(
            document,
            "MSBuildWarningsAsMessages",
            "__ProgramKitNoMSBuildWarningDemotion__");
        AssertProperty(document, "WarningLevel", "9999");
        AssertProperty(document, "AnalysisLevel", "latest-recommended");
        AssertProperty(document, "EnableNETAnalyzers", "true");
        AssertProperty(document, "RunAnalyzers", "true");
        AssertProperty(document, "RunAnalyzersDuringBuild", "true");
        AssertProperty(document, "OptimizeImplicitlyTriggeredBuild", "false");
        AssertProperty(document, "EnforceCodeStyleInBuild", "true");
        AssertProperty(document, "RestorePackagesWithLockFile", "true");
        AssertProperty(document, "NuGetAudit", "true");
        AssertProperty(document, "NuGetAuditMode", "all");
        AssertProperty(document, "NuGetAuditLevel", "low");

        var gateReferences = document
            .Descendants("ProjectReference")
            .Where(reference => RequiredAttribute(reference, "OutputItemType") == "Analyzer")
            .ToArray();
        Assert.ContainsSingle(gateReferences);
        Assert.AreEqual(
            "$(ProgramKitCSharpGateProjectPath)",
            RequiredAttribute(gateReferences[0], "Include"));
        Assert.AreEqual(
            "false",
            RequiredAttribute(gateReferences[0], "ReferenceOutputAssembly"));
        Assert.AreEqual("all", RequiredAttribute(gateReferences[0], "PrivateAssets"));
    }

    [TestMethod]
    public void BuildTargetsCannotOptOutOfTheCanonicalProfileAndPackExactDependencies()
    {
        var targets = ConformanceInputs.Read("Directory.Build.targets");

        Assert.DoesNotContain("ProgramKitTargetProfileValidation", targets);
        Assert.Contains("'$(TargetFramework)' != 'net10.0'", targets);
        Assert.Contains("'$(LangVersion)' != '14.0'", targets);
        Assert.Contains("'$(NETCoreSdkVersion)' != '10.0.302'", targets);
        Assert.Contains("Code=\"PKNET001\"", targets);
        Assert.Contains("Code=\"PKNET008\"", targets);
        Assert.Contains("Code=\"PKPUB001\"", targets);
        for (var diagnostic = 101; diagnostic <= 158; diagnostic++)
        {
            if (diagnostic == 154)
            {
                continue;
            }

            Assert.Contains($"Code=\"PKCS{diagnostic}\"", targets);
        }

        Assert.DoesNotContain("Code=\"PKCS154\"", targets);
        Assert.Contains(
            "<ProjectVersion>[%(_ProjectReferencesWithVersions.ProjectVersion)]</ProjectVersion>",
            targets);
        Assert.DoesNotContain("PKDOT", targets);
        Assert.DoesNotContain("PKPKG", targets);
    }

    [TestMethod]
    public void EveryApprovedExternalPackageHasOneExactCentralSelection()
    {
        var document = XDocument.Parse(ConformanceInputs.Read("Directory.Packages.props"));
        var actual = document
            .Descendants("PackageVersion")
            .ToDictionary(
                element => RequiredAttribute(element, "Include"),
                element => RequiredAttribute(element, "Version"),
                StringComparer.Ordinal);

        var expected = new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["Azure.Extensions.AspNetCore.Configuration.Secrets"] = "[1.5.1]",
            ["MSTest.Sdk"] = "[4.3.2]",
            ["JsonSchema.Net"] = "[9.3.0]",
            ["Microsoft.AspNetCore.Authentication.JwtBearer"] = "[10.0.10]",
            ["Microsoft.AspNetCore.Authentication.OpenIdConnect"] = "[10.0.10]",
            ["Microsoft.AspNetCore.Components.WebAssembly"] = "[10.0.10]",
            ["Microsoft.AspNetCore.Components.WebAssembly.Authentication"] = "[10.0.10]",
            ["Microsoft.AspNetCore.TestHost"] = "[10.0.10]",
            ["Microsoft.Playwright"] = "[1.61.0]",
            ["Microsoft.Extensions.Configuration.Json"] = "[10.0.10]",
            ["Microsoft.Extensions.Configuration.KeyPerFile"] = "[10.0.10]",
            ["Microsoft.Extensions.DependencyInjection"] = "[10.0.10]",
            ["Microsoft.Extensions.DependencyInjection.Abstractions"] = "[10.0.10]",
            ["Microsoft.Extensions.Hosting"] = "[10.0.10]",
            ["Microsoft.Extensions.Hosting.Abstractions"] = "[10.0.10]",
            ["Microsoft.Extensions.Options.ConfigurationExtensions"] = "[10.0.10]",
            ["Microsoft.Extensions.Options.DataAnnotations"] = "[10.0.10]",
            ["Microsoft.Extensions.Diagnostics.HealthChecks"] = "[10.0.10]",
            ["Microsoft.Extensions.Diagnostics.HealthChecks.Abstractions"] = "[10.0.10]",
            ["OpenTelemetry.Exporter.OpenTelemetryProtocol"] = "[1.17.0]",
            ["OpenTelemetry.Extensions.Hosting"] = "[1.17.0]",
            ["OpenTelemetry.Instrumentation.AspNetCore"] = "[1.17.0]",
            ["OpenTelemetry.Instrumentation.Http"] = "[1.17.0]",
            ["CShells.Abstractions"] = "[0.0.28]",
            ["CShells.AspNetCore.Abstractions"] = "[0.0.28]",
            ["CShells"] = "[0.0.28]",
            ["CShells.AspNetCore"] = "[0.0.28]",
            ["CShells.FastEndpoints"] = "[0.0.28]",
            ["FastEndpoints"] = "[7.2.0]",
            ["Cronos"] = "[0.13.0]",
            ["TUnit"] = "[1.60.0]",
        };

        Assert.AreSequenceEqual(
            expected.Keys.Order(StringComparer.Ordinal),
            actual.Keys.Order(StringComparer.Ordinal));
        foreach (var pair in expected)
        {
            Assert.AreEqual(pair.Value, actual[pair.Key], pair.Key);
        }
    }

    [TestMethod]
    public void NuGetConfigurationClearsAmbientSources()
    {
        var document = XDocument.Parse(ConformanceInputs.Read("NuGet.Config"));
        var packageSources = document.Root?.Element("packageSources");

        Assert.IsNotNull(packageSources);
        Assert.ContainsSingle(packageSources.Elements("clear"));

        var sources = packageSources.Elements("add").ToArray();
        Assert.ContainsSingle(sources);
        Assert.AreEqual("nuget.org", RequiredAttribute(sources[0], "key"));
        Assert.AreEqual(
            "https://api.nuget.org/v3/index.json",
            RequiredAttribute(sources[0], "value"));
    }

    [TestMethod]
    public void SolutionContainsTheApprovedW052PackagesFixtureTestsAndCSharpGate()
    {
        var solution = ConformanceInputs.Read("ProgramKit.sln");
        var projectLines = solution
            .Split('\n', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Where(line => line.StartsWith("Project(", StringComparison.Ordinal))
            .Where(line => line.Contains(".csproj\"", StringComparison.Ordinal))
            .ToArray();

        Assert.HasCount(35, projectLines);
        foreach (var productProjectName in ProductProjectNames)
        {
            Assert.ContainsSingle(
                projectLines.Where(line => line.Contains(
                    $"\"{productProjectName}\"",
                    StringComparison.Ordinal)));
        }

        foreach (var fixtureProjectName in ObservatoryFixtureProjectNames)
        {
            Assert.ContainsSingle(
                projectLines.Where(line => line.Contains(
                    $"\"{fixtureProjectName}\"",
                    StringComparison.Ordinal)));
        }

        Assert.HasCount(
            5,
            projectLines.Where(line => line.Contains(
                "Orbyss.ProgramKit.UnitTests",
                StringComparison.Ordinal)
                || line.Contains(
                    "Orbyss.ProgramKit.ConformanceTests",
                    StringComparison.Ordinal)
                || line.Contains(
                    "ObservatoryScheduling.Tests",
                    StringComparison.Ordinal)));
        Assert.ContainsSingle(
            projectLines.Where(line => line.Contains(
                "\"Orbyss.ProgramKit.CSharpGate\"",
                StringComparison.Ordinal)));
        Assert.ContainsSingle(
            projectLines.Where(line => line.Contains(
                "\"SecurityConsumer\"",
                StringComparison.Ordinal)));
        Assert.ContainsSingle(
            projectLines.Where(line => line.Contains(
                "\"PublicBrowserVerification\"",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public void ProductProjectsDoNotOverrideOrMultitargetTheCanonicalFramework()
    {
        var projectFiles = ConformanceInputs.Files("Projects", "*.csproj");

        Assert.HasCount(21, projectFiles);
        foreach (var projectFile in projectFiles)
        {
            var project = XDocument.Load(projectFile);
            Assert.IsEmpty(project.Descendants("TargetFrameworks"), projectFile);
            Assert.IsEmpty(project.Descendants("TargetFramework"), projectFile);
            Assert.DoesNotContain("net8.0", project.ToString(), projectFile);
        }
    }

    [TestMethod]
    public void OwnedProjectsKeepEveryOwnedSourceInTheDefaultCompileInventory()
    {
        var programKitRoot = Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit");
        var projectFiles = ProductProjectNames
            .Select(projectName => Path.Combine(
                programKitRoot,
                "src",
                projectName,
                $"{projectName}.csproj"))
            .Append(Path.Combine(
                programKitRoot,
                "tools",
                "Orbyss.ProgramKit.CSharpGate",
                "Orbyss.ProgramKit.CSharpGate.csproj"))
            .Append(Path.Combine(
                programKitRoot,
                "tests",
                "Orbyss.ProgramKit.UnitTests",
                "Orbyss.ProgramKit.UnitTests.csproj"))
            .Append(Path.Combine(
                programKitRoot,
                "tests",
                "Orbyss.ProgramKit.ConformanceTests",
                "Orbyss.ProgramKit.ConformanceTests.csproj"))
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.HasCount(24, projectFiles);
        foreach (var buildFile in new[]
                 {
                     Path.Combine(programKitRoot, "Directory.Build.props"),
                     Path.Combine(programKitRoot, "Directory.Build.targets"),
                 })
        {
            AssertCompileInventoryPolicy(
                XDocument.Load(buildFile),
                buildFile,
                allowFixtureExclusion: false);
        }

        foreach (var projectFile in projectFiles)
        {
            Assert.IsTrue(File.Exists(projectFile), projectFile);
            var isConformanceProject = string.Equals(
                Path.GetFileNameWithoutExtension(projectFile),
                "Orbyss.ProgramKit.ConformanceTests",
                StringComparison.Ordinal);
            AssertCompileInventoryPolicy(
                XDocument.Load(projectFile),
                projectFile,
                isConformanceProject);

            var projectDirectory = Path.GetDirectoryName(projectFile)
                ?? throw new AssertFailedException(
                    $"Could not locate the project directory for {projectFile}.");
            var ownedSources = Directory
                .EnumerateFiles(projectDirectory, "*.cs", SearchOption.AllDirectories)
                .Where(sourceFile => IsOwnedSource(projectDirectory, sourceFile))
                .Select(sourceFile => Path.GetRelativePath(projectDirectory, sourceFile))
                .Order(StringComparer.Ordinal)
                .ToArray();

            Assert.IsGreaterThan(
                0,
                ownedSources.Length,
                $"{projectFile} must own at least one C# source file.");
            foreach (var ownedSource in ownedSources)
            {
                Assert.IsFalse(
                    IsPathUnderDirectory(ownedSource, "Fixtures"),
                    $"{projectFile}: owned source {ownedSource} is excluded from Compile.");
            }
        }
    }

    [TestMethod]
    public void ProductProjectFilesHaveOnlyTheApprovedReferenceGraph()
    {
        var expectedProjects =
            new Dictionary<string, ImmutableHashSet<string>>(StringComparer.Ordinal)
            {
                ["Orbyss.ProgramKit.Artifacts"] = [],
                ["Orbyss.ProgramKit.CapabilityBundle"] = [],
                ["Orbyss.ProgramKit.Operations"] = ["Orbyss.ProgramKit.Artifacts"],
                ["Orbyss.ProgramKit.SecretResolution"] =
                ["Orbyss.ProgramKit.Artifacts"],
                ["Orbyss.ProgramKit.Architecture"] = ["Orbyss.ProgramKit.Artifacts"],
                ["Orbyss.ProgramKit.Quality"] = ["Orbyss.ProgramKit.Artifacts"],
                ["Orbyss.ProgramKit.Planning"] =
                ["Orbyss.ProgramKit.Artifacts", "Orbyss.ProgramKit.Quality"],
                ["Orbyss.ProgramKit.Development"] =
                ["Orbyss.ProgramKit.Artifacts", "Orbyss.ProgramKit.Planning"],
                ["Orbyss.ProgramKit.DevContainers"] =
                ["Orbyss.ProgramKit.Artifacts"],
                ["Orbyss.ProgramKit.CommandLine"] =
                [
                    "Orbyss.ProgramKit.DotNet",
                    "Orbyss.ProgramKit.Operations",
                    "Orbyss.ProgramKit.SecretResolution",
                    "Orbyss.ProgramKit.Workbench",
                ],
                ["Orbyss.ProgramKit.DotNet"] =
                [
                    "Orbyss.ProgramKit.Architecture",
                    "Orbyss.ProgramKit.Operations",
                    "Orbyss.ProgramKit.Planning",
                    "Orbyss.ProgramKit.Quality",
                    "Orbyss.ProgramKit.SecretResolution",
                    "Orbyss.ProgramKit.Serialization.JSON",
                    "Orbyss.ProgramKit.Tasks",
                    "Orbyss.ProgramKit.Tasks.Core",
                    "Orbyss.ProgramKit.Tasks.Schedules",
                    "Orbyss.ProgramKit.Workbench",
                ],
                ["Orbyss.ProgramKit.Modularity"] = ["Orbyss.ProgramKit.Artifacts"],
                ["Orbyss.ProgramKit.Modularity.InProcess"] =
                ["Orbyss.ProgramKit.Modularity"],
                ["Orbyss.ProgramKit.Serialization.JSON"] =
                ["Orbyss.ProgramKit.Artifacts"],
                ["Orbyss.ProgramKit.Tasks.Core"] =
                ["Orbyss.ProgramKit.Artifacts"],
                ["Orbyss.ProgramKit.Tasks"] =
                [
                    "Orbyss.ProgramKit.Modularity",
                    "Orbyss.ProgramKit.Tasks.Core",
                ],
                ["Orbyss.ProgramKit.Tasks.InProcess"] =
                ["Orbyss.ProgramKit.Tasks"],
                ["Orbyss.ProgramKit.Tasks.Hosting"] =
                ["Orbyss.ProgramKit.Tasks"],
                ["Orbyss.ProgramKit.Tasks.Schedules"] =
                ["Orbyss.ProgramKit.Tasks.Core"],
                ["Orbyss.ProgramKit.Tasks.Schedules.Cronos"] =
                ["Orbyss.ProgramKit.Tasks.Schedules"],
                ["Orbyss.ProgramKit.Workbench"] =
                [
                    "Orbyss.ProgramKit.Artifacts",
                    "Orbyss.ProgramKit.Architecture",
                    "Orbyss.ProgramKit.Development",
                    "Orbyss.ProgramKit.Planning",
                    "Orbyss.ProgramKit.Quality",
                    "Orbyss.ProgramKit.Serialization.JSON",
                ],
            };
        var expectedPackages =
            new Dictionary<string, ImmutableHashSet<string>>(StringComparer.Ordinal)
            {
                ["Orbyss.ProgramKit.Artifacts"] = [],
                ["Orbyss.ProgramKit.CapabilityBundle"] = [],
                ["Orbyss.ProgramKit.Operations"] = [],
                ["Orbyss.ProgramKit.SecretResolution"] = [],
                ["Orbyss.ProgramKit.Architecture"] = [],
                ["Orbyss.ProgramKit.Quality"] = [],
                ["Orbyss.ProgramKit.Planning"] = [],
                ["Orbyss.ProgramKit.Development"] = [],
                ["Orbyss.ProgramKit.DevContainers"] = [],
                ["Orbyss.ProgramKit.CommandLine"] = [],
                ["Orbyss.ProgramKit.DotNet"] = [],
                ["Orbyss.ProgramKit.Modularity"] = [],
                ["Orbyss.ProgramKit.Modularity.InProcess"] = [],
                ["Orbyss.ProgramKit.Serialization.JSON"] =
                ["Microsoft.Extensions.DependencyInjection.Abstractions"],
                ["Orbyss.ProgramKit.Tasks.Core"] = [],
                ["Orbyss.ProgramKit.Tasks"] =
                ["Microsoft.Extensions.DependencyInjection.Abstractions"],
                ["Orbyss.ProgramKit.Tasks.InProcess"] = [],
                ["Orbyss.ProgramKit.Tasks.Hosting"] =
                [
                    "Microsoft.Extensions.DependencyInjection",
                    "Microsoft.Extensions.Diagnostics.HealthChecks",
                    "Microsoft.Extensions.Diagnostics.HealthChecks.Abstractions",
                    "Microsoft.Extensions.Hosting.Abstractions",
                ],
                ["Orbyss.ProgramKit.Tasks.Schedules"] = [],
                ["Orbyss.ProgramKit.Tasks.Schedules.Cronos"] = ["Cronos"],
                ["Orbyss.ProgramKit.Workbench"] = ["JsonSchema.Net"],
            };

        foreach (var projectFile in ConformanceInputs.Files("Projects", "*.csproj"))
        {
            var document = XDocument.Load(projectFile);
            var projectName = Path.GetFileNameWithoutExtension(projectFile);
            var expectedReferences = expectedProjects[projectName];
            Assert.IsNotNull(document.Root, projectName);
            var sdkAttribute = document.Root.Attribute("Sdk");
            Assert.IsNotNull(sdkAttribute, projectName);
            Assert.AreEqual("Microsoft.NET.Sdk", sdkAttribute.Value, projectName);
            Assert.IsEmpty(document.Descendants("FrameworkReference"), projectName);
            Assert.IsEmpty(document.Descendants("Reference"), projectName);
            Assert.IsEmpty(document.Descendants("COMReference"), projectName);
            Assert.IsEmpty(document.Descendants("COMFileReference"), projectName);
            Assert.IsEmpty(document.Descendants("AddModules"), projectName);

            var actualReferences = document
                .Descendants("ProjectReference")
                .Select(reference => RequiredAttribute(reference, "Include"))
                .Select(reference => Path.GetFileNameWithoutExtension(reference)
                    ?? throw new AssertFailedException(
                        $"{projectName}: could not derive a project name from {reference}."))
                .ToImmutableHashSet(StringComparer.Ordinal);
            Assert.AreSequenceEqual(
                expectedReferences.Order(StringComparer.Ordinal),
                actualReferences.Order(StringComparer.Ordinal),
                $"{projectName}: expected [{string.Join(", ", expectedReferences)}], " +
                $"observed [{string.Join(", ", actualReferences)}].");

            var expectedPackageReferences = expectedPackages[projectName];
            var actualPackageReferences = document
                .Descendants("PackageReference")
                .Select(reference => RequiredAttribute(reference, "Include"))
                .ToImmutableHashSet(StringComparer.Ordinal);
            Assert.AreSequenceEqual(
                expectedPackageReferences.Order(StringComparer.Ordinal),
                actualPackageReferences.Order(StringComparer.Ordinal),
                $"{projectName}: expected packages " +
                $"[{string.Join(", ", expectedPackageReferences)}], observed " +
                $"[{string.Join(", ", actualPackageReferences)}].");
        }
    }

    [TestMethod]
    public void UniversalAssemblyReferencesFollowTheApprovedGraph()
    {
        var allowed = new Dictionary<string, ImmutableHashSet<string>>(StringComparer.Ordinal)
        {
            ["Orbyss.ProgramKit.Artifacts"] = [],
            ["Orbyss.ProgramKit.CapabilityBundle"] = [],
            ["Orbyss.ProgramKit.Operations"] = ["Orbyss.ProgramKit.Artifacts"],
            ["Orbyss.ProgramKit.SecretResolution"] =
                ["Orbyss.ProgramKit.Artifacts"],
            ["Orbyss.ProgramKit.Architecture"] = ["Orbyss.ProgramKit.Artifacts"],
            ["Orbyss.ProgramKit.Quality"] = ["Orbyss.ProgramKit.Artifacts"],
            ["Orbyss.ProgramKit.Planning"] =
                ["Orbyss.ProgramKit.Artifacts", "Orbyss.ProgramKit.Quality"],
            ["Orbyss.ProgramKit.Development"] =
                ["Orbyss.ProgramKit.Artifacts", "Orbyss.ProgramKit.Planning"],
            ["Orbyss.ProgramKit.CommandLine"] =
                [
                    "Orbyss.ProgramKit.Architecture",
                    "Orbyss.ProgramKit.Artifacts",
                    "Orbyss.ProgramKit.Development",
                    "Orbyss.ProgramKit.DotNet",
                    "Orbyss.ProgramKit.Operations",
                    "Orbyss.ProgramKit.Planning",
                    "Orbyss.ProgramKit.Quality",
                    "Orbyss.ProgramKit.SecretResolution",
                    "Orbyss.ProgramKit.Serialization.JSON",
                    "Orbyss.ProgramKit.Tasks.Core",
                    "Orbyss.ProgramKit.Tasks.Schedules",
                    "Orbyss.ProgramKit.Workbench",
                ],
            ["Orbyss.ProgramKit.DotNet"] =
                [
                    "Orbyss.ProgramKit.Artifacts",
                    "Orbyss.ProgramKit.Operations",
                    "Orbyss.ProgramKit.SecretResolution",
                    "Orbyss.ProgramKit.Serialization.JSON",
                    "Orbyss.ProgramKit.Workbench",
                ],
            ["Orbyss.ProgramKit.Modularity"] = ["Orbyss.ProgramKit.Artifacts"],
            ["Orbyss.ProgramKit.Modularity.InProcess"] =
                [
                    "Orbyss.ProgramKit.Artifacts",
                    "Orbyss.ProgramKit.Modularity",
                ],
            ["Orbyss.ProgramKit.Serialization.JSON"] =
                ["Orbyss.ProgramKit.Artifacts"],
            ["Orbyss.ProgramKit.Tasks.Core"] =
                ["Orbyss.ProgramKit.Artifacts"],
            ["Orbyss.ProgramKit.Tasks"] =
                [
                    "Orbyss.ProgramKit.Artifacts",
                    "Orbyss.ProgramKit.Modularity",
                    "Orbyss.ProgramKit.Tasks.Core",
                ],
            ["Orbyss.ProgramKit.Tasks.InProcess"] =
                [
                    "Orbyss.ProgramKit.Artifacts",
                    "Orbyss.ProgramKit.Modularity",
                    "Orbyss.ProgramKit.Tasks",
                    "Orbyss.ProgramKit.Tasks.Core",
                ],
            ["Orbyss.ProgramKit.Tasks.Hosting"] =
                [
                    "Orbyss.ProgramKit.Artifacts",
                    "Orbyss.ProgramKit.Tasks",
                    "Orbyss.ProgramKit.Tasks.Core",
                ],
            ["Orbyss.ProgramKit.Tasks.Schedules"] =
                [
                    "Orbyss.ProgramKit.Artifacts",
                    "Orbyss.ProgramKit.Tasks.Core",
                ],
            ["Orbyss.ProgramKit.Tasks.Schedules.Cronos"] =
                [
                    "Orbyss.ProgramKit.Artifacts",
                    "Orbyss.ProgramKit.Tasks.Core",
                ],
            ["Orbyss.ProgramKit.Workbench"] =
                [
                    "Orbyss.ProgramKit.Architecture",
                    "Orbyss.ProgramKit.Artifacts",
                    "Orbyss.ProgramKit.Serialization.JSON",
                ],
        };

        foreach (var pair in allowed)
        {
            var references = pair.Key ==
                "Orbyss.ProgramKit.Tasks.Schedules.Cronos"
                    ? ReadProgramKitAssemblyReferences(
                        Path.Combine(
                            AppContext.BaseDirectory,
                            string.Concat(pair.Key, ".dll")))
                    : Assembly.Load(pair.Key)
                        .GetReferencedAssemblies()
                        .Select(reference => reference.Name)
                        .Where(name => name is not null &&
                            name.StartsWith(
                                "Orbyss.ProgramKit.",
                                StringComparison.Ordinal))
                        .Cast<string>()
                        .ToImmutableHashSet(StringComparer.Ordinal);

            Assert.AreSequenceEqual(
                pair.Value.Order(StringComparer.Ordinal),
                references.Order(StringComparer.Ordinal),
                $"{pair.Key}: expected [{string.Join(", ", pair.Value)}], " +
                $"observed [{string.Join(", ", references)}].");
        }
    }

    private static ImmutableHashSet<string> ReadProgramKitAssemblyReferences(
        string assemblyPath)
    {
        using var stream = File.OpenRead(assemblyPath);
        using var peReader = new PEReader(stream);
        var metadata = peReader.GetMetadataReader();
        return metadata
            .AssemblyReferences
            .Select(handle => metadata.GetAssemblyReference(handle))
            .Select(reference => metadata.GetString(reference.Name))
            .Where(name => name.StartsWith(
                "Orbyss.ProgramKit.",
                StringComparison.Ordinal))
            .ToImmutableHashSet(StringComparer.Ordinal);
    }

    [TestMethod]
    public void ProductSourceContainsNoForbiddenRuntimeOrSerializationDependency()
    {
        var forbidden = new[]
        {
            "Newtonsoft.Json",
            "Orbyss.DomainSemanticEngine",
            "ReleaseCycle",
        };

        foreach (var sourceFile in ConformanceInputs.Files("Source", "*.cs"))
        {
            var source = File.ReadAllText(sourceFile);
            var normalizedSourceFile = sourceFile.Replace('\\', '/');
            var isDotNetSource = normalizedSourceFile.Contains(
                "Orbyss.ProgramKit.DotNet/",
                StringComparison.Ordinal);
            foreach (var token in forbidden)
            {
                Assert.DoesNotContain(
                    token,
                    source,
                    $"{sourceFile} contains forbidden token {token}.");
            }

            if (!isDotNetSource)
            {
                Assert.DoesNotContain(
                    "CShells",
                    source,
                    $"{sourceFile} uses CShells outside the DotNet host-generation package.");
            }

            if (!normalizedSourceFile.Contains(
                    "Orbyss.ProgramKit.Serialization.JSON",
                    StringComparison.Ordinal) &&
                !normalizedSourceFile.Contains(
                    "Orbyss.ProgramKit.DotNet/Composition/",
                    StringComparison.Ordinal) &&
                !normalizedSourceFile.Contains(
                    "Orbyss.ProgramKit.CommandLine/Operations/Serialization/",
                    StringComparison.Ordinal))
            {
                string[] forbiddenSerializerMechanics =
                [
                    "JsonSerializer.Serialize",
                    "JsonSerializer.Deserialize",
                    "JsonSerializerOptions",
                    "JsonSerializerContext",
                ];
                foreach (var token in forbiddenSerializerMechanics)
                {
                    Assert.DoesNotContain(
                        token,
                        source,
                        $"{sourceFile} uses {token} outside Serialization.JSON.");
                }
            }

            if ((source.Contains("JsonElement", StringComparison.Ordinal) ||
                 source.Contains("JsonDocument", StringComparison.Ordinal) ||
                 source.Contains("JsonNode", StringComparison.Ordinal)) &&
                !normalizedSourceFile.Contains(
                    "Orbyss.ProgramKit.Serialization.JSON",
                    StringComparison.Ordinal) &&
                !normalizedSourceFile.Contains(
                    "Orbyss.ProgramKit.Workbench/Operations/Schemas/",
                    StringComparison.Ordinal))
            {
                Assert.Fail(
                    $"{sourceFile} exposes or uses a JSON DOM outside the exact Workbench schema adapter exception.");
            }
        }
    }

    [TestMethod]
    public void UniversalSchemasAndProjectSurfaceContainNoReleaseCycleBehavior()
    {
        var forbidden = new[]
        {
            "ReleaseCycle",
            "release-cycle",
            "ArtifactFeedTransport",
            "artifact-feed-transport",
            "PublishPackage",
            "DeployPackage",
            "PromotePackage",
        };

        foreach (var schemaFile in ConformanceInputs.Files("Schemas", "*.json"))
        {
            var schema = File.ReadAllText(schemaFile);
            foreach (var token in forbidden)
            {
                Assert.DoesNotContain(
                    token,
                    schema,
                    $"{schemaFile} contains forbidden Release Cycle token {token}.");
            }
        }

        foreach (var projectName in ProductProjectNames)
        {
            Assert.DoesNotContain(".Cli", projectName);
            Assert.DoesNotContain(".Capabilities", projectName);
            Assert.DoesNotContain(".Release", projectName);
        }
    }

    [TestMethod]
    public void EveryOwnedSchemaDeclaresDraft202012AndAnExactProgramKitIdentity()
    {
        var schemaFiles = ConformanceInputs
            .Files("Schemas", "*.schema.json")
            .Where(schemaFile =>
            {
                var normalized = schemaFile.Replace('\\', '/');
                return !normalized.Contains("/vendor/", StringComparison.Ordinal)
                    && !normalized.Contains(
                        "/dev-containers/",
                        StringComparison.Ordinal);
            })
            .ToImmutableArray();

        Assert.IsGreaterThanOrEqualTo(5, schemaFiles.Length);
        foreach (var schemaFile in schemaFiles)
        {
            var schema = File.ReadAllText(schemaFile);
            using var document = JsonDocument.Parse(schema);
            var root = document.RootElement;
            var schemaId = root.GetProperty("$id").GetString();
            var schemaVersion =
                root.GetProperty("x-program-kit-version").GetString();
            Assert.Contains(
                "\"$schema\": \"https://json-schema.org/draft/2020-12/schema\"",
                schema);
            Assert.Contains(
                "\"$id\": \"https://schemas.orbyss.io/program-kit/",
                schema);
            Assert.Contains(
                "\"x-program-kit-identity\": \"pkid:schema:program-kit:",
                schema);
            Assert.IsTrue(
                Version.TryParse(schemaVersion, out _),
                $"{schemaFile} must declare a valid schema version.");
            Assert.Contains(
                string.Concat("/", schemaVersion, "/"),
                schemaId!,
                $"{schemaFile} must bind its version to its exact $id.");
            Assert.IsTrue(
                HasTopLevelReference(schema)
                || HasTopLevelClosedObject(schema)
                || HasTopLevelDefinitionsLibrary(schema),
                $"{schemaFile} must delegate through a top-level $ref, close its root object, " +
                "or be an explicit $defs-only schema library.");
        }
    }

    private static bool HasTopLevelReference(string json) =>
        HasTopLevelProperty(json, "$ref", JsonTokenType.String);

    private static bool HasTopLevelClosedObject(string json) =>
        HasTopLevelProperty(json, "additionalProperties", JsonTokenType.False);

    private static bool HasTopLevelDefinitionsLibrary(string json) =>
        HasTopLevelProperty(json, "$defs", JsonTokenType.StartObject)
        && !HasTopLevelProperty(json, "type", JsonTokenType.String);

    private static void AssertCompileInventoryPolicy(
        XDocument document,
        string buildFile,
        bool allowFixtureExclusion)
    {
        foreach (var propertyName in new[]
                 {
                     "EnableDefaultItems",
                     "EnableDefaultCompileItems",
                 })
        {
            var invalidSelections = document
                .Descendants(propertyName)
                .Where(element => !string.Equals(
                    element.Value.Trim(),
                    "true",
                    StringComparison.OrdinalIgnoreCase))
                .ToArray();
            Assert.IsEmpty(
                invalidSelections,
                $"{buildFile}: {propertyName} may only be explicitly set to true.");
        }

        Assert.IsEmpty(
            document.Descendants("DefaultItemExcludes"),
            $"{buildFile}: DefaultItemExcludes may not alter the source inventory.");
        Assert.IsEmpty(
            document.Descendants("DefaultExcludesInProjectFolder"),
            $"{buildFile}: DefaultExcludesInProjectFolder may not alter the source inventory.");

        var compileRemovals = document
            .Descendants("Compile")
            .Where(element => element.Attribute("Remove") is not null)
            .ToArray();
        if (!allowFixtureExclusion)
        {
            Assert.IsEmpty(
                compileRemovals,
                $"{buildFile}: Compile Remove entries are forbidden.");
            return;
        }

        Assert.ContainsSingle(
            compileRemovals,
            $"{buildFile}: the conformance fixture exclusion must be the only Compile removal.");
        Assert.ContainsSingle(
            compileRemovals[0].Attributes(),
            $"{buildFile}: the conformance fixture exclusion cannot be conditional or decorated.");
        Assert.AreEqual(
            @"Fixtures\**\*.cs",
            RequiredAttribute(compileRemovals[0], "Remove"),
            $"{buildFile}: only fixture probe sources may be excluded from Compile.");
    }

    private static bool IsOwnedSource(string projectDirectory, string sourceFile)
    {
        var relativePath = Path.GetRelativePath(projectDirectory, sourceFile);
        return !IsPathUnderDirectory(relativePath, "bin")
            && !IsPathUnderDirectory(relativePath, "obj")
            && !IsPathUnderDirectory(relativePath, "Fixtures");
    }

    private static bool IsPathUnderDirectory(string relativePath, string directoryName)
    {
        return relativePath
            .Split(
                [Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar],
                StringSplitOptions.RemoveEmptyEntries)
            .Any(segment => string.Equals(
                segment,
                directoryName,
                StringComparison.OrdinalIgnoreCase));
    }

    private static bool HasTopLevelProperty(
        string json,
        string propertyName,
        JsonTokenType expectedValueToken)
    {
        var reader = new Utf8JsonReader(Encoding.UTF8.GetBytes(json));
        Assert.IsTrue(reader.Read() && reader.TokenType == JsonTokenType.StartObject);
        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            Assert.AreEqual(JsonTokenType.PropertyName, reader.TokenType);
            var currentName = reader.GetString();
            Assert.IsTrue(reader.Read());
            if (string.Equals(currentName, propertyName, StringComparison.Ordinal))
            {
                return reader.TokenType == expectedValueToken;
            }

            reader.Skip();
        }

        return false;
    }

    private static void AssertProperty(XDocument document, string name, string expected)
    {
        var elements = document.Descendants(name).ToArray();
        Assert.ContainsSingle(elements, name);
        Assert.AreEqual(expected, elements[0].Value, name);
    }

    private static string RequiredAttribute(XElement element, string name)
    {
        return element.Attribute(name)?.Value
            ?? throw new AssertFailedException($"Missing {name} on {element.Name}.");
    }
}
