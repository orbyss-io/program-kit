using System.Collections.Immutable;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Xml.Linq;

namespace Orbyss.ProgramKit.ConformanceTests;

[TestClass]
public sealed class BuildSpineConformanceTests
{
    private static readonly ImmutableArray<string> ProductProjectNames =
    [
        "Orbyss.ProgramKit.Architecture",
        "Orbyss.ProgramKit.Artifacts",
        "Orbyss.ProgramKit.Development",
        "Orbyss.ProgramKit.Planning",
        "Orbyss.ProgramKit.Quality",
    ];

    [TestMethod]
    public void GlobalJsonPinsTheApprovedSdkWithoutFallback()
    {
        var globalJson = ConformanceInputs.Read("global.json");

        StringAssert.Contains(globalJson, "\"version\": \"10.0.302\"");
        StringAssert.Contains(globalJson, "\"rollForward\": \"disable\"");
        StringAssert.Contains(globalJson, "\"allowPrerelease\": false");
        StringAssert.Contains(globalJson, "\"MSTest.Sdk\": \"4.3.2\"");
        StringAssert.Contains(globalJson, "\"runner\": \"Microsoft.Testing.Platform\"");
        Assert.IsFalse(globalJson.Contains("8.0", StringComparison.Ordinal));
    }

    [TestMethod]
    public void DirectoryBuildPolicyMaterializesTheApprovedTargetProfile()
    {
        var document = XDocument.Parse(ConformanceInputs.Read("Directory.Build.props"));

        AssertProperty(document, "TargetFramework", "net10.0");
        AssertProperty(document, "LangVersion", "14.0");
        AssertProperty(document, "ProgramKitTargetProfileId", "pkid:profile:program-kit:dotnet-10");
        AssertProperty(document, "ProgramKitTargetProfileVersion", "1.0.0");
        AssertProperty(document, "ProgramKitSdkVersion", "10.0.302");
        AssertProperty(document, "ProgramKitSdkRollForward", "disable");
        AssertProperty(document, "ProgramKitAllowPrereleaseSdk", "false");
        AssertProperty(document, "Version", "0.1.0-alpha.1");
        AssertProperty(document, "Deterministic", "true");
        AssertProperty(document, "TreatWarningsAsErrors", "true");
        AssertProperty(document, "RestorePackagesWithLockFile", "true");
    }

    [TestMethod]
    public void BuildTargetsCannotOptOutOfTheCanonicalProfileAndPackExactDependencies()
    {
        var targets = ConformanceInputs.Read("Directory.Build.targets");

        Assert.IsFalse(
            targets.Contains("ProgramKitTargetProfileValidation", StringComparison.Ordinal));
        StringAssert.Contains(targets, "'$(TargetFramework)' != 'net10.0'");
        StringAssert.Contains(targets, "'$(LangVersion)' != '14.0'");
        StringAssert.Contains(targets, "'$(NETCoreSdkVersion)' != '10.0.302'");
        StringAssert.Contains(targets, "Code=\"PKNET001\"");
        StringAssert.Contains(targets, "Code=\"PKNET008\"");
        StringAssert.Contains(targets, "Code=\"PKPUB001\"");
        StringAssert.Contains(
            targets,
            "<ProjectVersion>[%(_ProjectReferencesWithVersions.ProjectVersion)]</ProjectVersion>");
        Assert.IsFalse(targets.Contains("PKDOT", StringComparison.Ordinal));
        Assert.IsFalse(targets.Contains("PKPKG", StringComparison.Ordinal));
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
            ["MSTest.Sdk"] = "[4.3.2]",
            ["JsonSchema.Net"] = "[9.3.0]",
            ["Microsoft.Extensions.DependencyInjection"] = "[10.0.10]",
            ["Microsoft.Extensions.DependencyInjection.Abstractions"] = "[10.0.10]",
            ["Microsoft.Extensions.Hosting.Abstractions"] = "[10.0.10]",
            ["Microsoft.Extensions.Diagnostics.HealthChecks"] = "[10.0.10]",
            ["Microsoft.Extensions.Diagnostics.HealthChecks.Abstractions"] = "[10.0.10]",
            ["CShells.Abstractions"] = "[0.0.28]",
            ["CShells.AspNetCore.Abstractions"] = "[0.0.28]",
            ["CShells"] = "[0.0.28]",
            ["CShells.AspNetCore"] = "[0.0.28]",
            ["Cronos"] = "[0.13.0]",
        };

        CollectionAssert.AreEquivalent(expected.Keys.ToArray(), actual.Keys.ToArray());
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
        Assert.AreEqual(1, packageSources.Elements("clear").Count());

        var sources = packageSources.Elements("add").ToArray();
        Assert.AreEqual(1, sources.Length);
        Assert.AreEqual("nuget.org", RequiredAttribute(sources[0], "key"));
        Assert.AreEqual(
            "https://api.nuget.org/v3/index.json",
            RequiredAttribute(sources[0], "value"));
    }

    [TestMethod]
    public void SolutionContainsOnlyTheFiveUniversalPackagesAndTwoTestProjects()
    {
        var solution = ConformanceInputs.Read("ProgramKit.sln");
        var projectLines = solution
            .Split('\n', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Where(line => line.StartsWith("Project(", StringComparison.Ordinal))
            .ToArray();

        Assert.AreEqual(7, projectLines.Length);
        foreach (var productProjectName in ProductProjectNames)
        {
            Assert.AreEqual(
                1,
                projectLines.Count(line => line.Contains(
                    $"\"{productProjectName}\"",
                    StringComparison.Ordinal)));
        }

        Assert.AreEqual(
            2,
            projectLines.Count(line => line.Contains(
                "Orbyss.ProgramKit.UnitTests",
                StringComparison.Ordinal)
                || line.Contains(
                    "Orbyss.ProgramKit.ConformanceTests",
                    StringComparison.Ordinal)));
    }

    [TestMethod]
    public void ProductProjectsDoNotOverrideOrMultitargetTheCanonicalFramework()
    {
        var projectFiles = ConformanceInputs.Files("Projects", "*.csproj");

        Assert.AreEqual(5, projectFiles.Length);
        foreach (var projectFile in projectFiles)
        {
            var project = XDocument.Load(projectFile);
            Assert.IsFalse(project.Descendants("TargetFrameworks").Any(), projectFile);
            Assert.IsFalse(project.Descendants("TargetFramework").Any(), projectFile);
            Assert.IsFalse(project.ToString().Contains("net8.0", StringComparison.Ordinal), projectFile);
        }
    }

    [TestMethod]
    public void UniversalProjectFilesHaveOnlyTheApprovedFirstPartyReferenceGraph()
    {
        var expected = new Dictionary<string, ImmutableHashSet<string>>(StringComparer.Ordinal)
        {
            ["Orbyss.ProgramKit.Artifacts"] = [],
            ["Orbyss.ProgramKit.Architecture"] = ["Orbyss.ProgramKit.Artifacts"],
            ["Orbyss.ProgramKit.Quality"] = ["Orbyss.ProgramKit.Artifacts"],
            ["Orbyss.ProgramKit.Planning"] =
                ["Orbyss.ProgramKit.Artifacts", "Orbyss.ProgramKit.Quality"],
            ["Orbyss.ProgramKit.Development"] =
                ["Orbyss.ProgramKit.Artifacts", "Orbyss.ProgramKit.Planning"],
        };

        foreach (var projectFile in ConformanceInputs.Files("Projects", "*.csproj"))
        {
            var document = XDocument.Load(projectFile);
            var projectName = Path.GetFileNameWithoutExtension(projectFile);
            Assert.IsTrue(expected.TryGetValue(projectName, out var expectedReferences), projectName);
            Assert.AreEqual("Microsoft.NET.Sdk", document.Root?.Attribute("Sdk")?.Value, projectName);
            Assert.IsFalse(document.Descendants("PackageReference").Any(), projectName);
            Assert.IsFalse(document.Descendants("FrameworkReference").Any(), projectName);

            var actualReferences = document
                .Descendants("ProjectReference")
                .Select(reference => RequiredAttribute(reference, "Include"))
                .Select(reference => Path.GetFileNameWithoutExtension(reference)
                    ?? throw new AssertFailedException(
                        $"{projectName}: could not derive a project name from {reference}."))
                .ToImmutableHashSet(StringComparer.Ordinal);
            Assert.IsTrue(
                expectedReferences.SetEquals(actualReferences),
                $"{projectName}: expected [{string.Join(", ", expectedReferences)}], " +
                $"observed [{string.Join(", ", actualReferences)}].");
        }
    }

    [TestMethod]
    public void UniversalAssemblyReferencesFollowTheApprovedGraph()
    {
        var allowed = new Dictionary<string, ImmutableHashSet<string>>(StringComparer.Ordinal)
        {
            ["Orbyss.ProgramKit.Artifacts"] = [],
            ["Orbyss.ProgramKit.Architecture"] = ["Orbyss.ProgramKit.Artifacts"],
            ["Orbyss.ProgramKit.Quality"] = ["Orbyss.ProgramKit.Artifacts"],
            ["Orbyss.ProgramKit.Planning"] =
                ["Orbyss.ProgramKit.Artifacts", "Orbyss.ProgramKit.Quality"],
            ["Orbyss.ProgramKit.Development"] =
                ["Orbyss.ProgramKit.Artifacts", "Orbyss.ProgramKit.Planning"],
        };

        foreach (var pair in allowed)
        {
            var references = Assembly
                .Load(pair.Key)
                .GetReferencedAssemblies()
                .Select(reference => reference.Name)
                .Where(name => name is not null &&
                    name.StartsWith("Orbyss.ProgramKit.", StringComparison.Ordinal))
                .Cast<string>()
                .ToImmutableHashSet(StringComparer.Ordinal);

            Assert.IsTrue(
                pair.Value.SetEquals(references),
                $"{pair.Key}: expected [{string.Join(", ", pair.Value)}], " +
                $"observed [{string.Join(", ", references)}].");
        }
    }

    [TestMethod]
    public void UniversalSourceContainsNoForbiddenRuntimeOrSerializationDependency()
    {
        var forbidden = new[]
        {
            "CShells",
            "JsonDocument",
            "JsonElement",
            "JsonNode",
            "JsonSerializer",
            "Newtonsoft.Json",
            "Orbyss.DomainSemanticEngine",
            "ReleaseCycle",
        };

        foreach (var sourceFile in ConformanceInputs.Files("Source", "*.cs"))
        {
            var source = File.ReadAllText(sourceFile);
            foreach (var token in forbidden)
            {
                Assert.IsFalse(
                    source.Contains(token, StringComparison.Ordinal),
                    $"{sourceFile} contains forbidden token {token}.");
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
                Assert.IsFalse(
                    schema.Contains(token, StringComparison.Ordinal),
                    $"{schemaFile} contains forbidden Release Cycle token {token}.");
            }
        }

        foreach (var projectName in ProductProjectNames)
        {
            Assert.IsFalse(projectName.Contains(".Cli", StringComparison.Ordinal));
            Assert.IsFalse(projectName.Contains(".Capabilities", StringComparison.Ordinal));
            Assert.IsFalse(projectName.Contains(".Release", StringComparison.Ordinal));
        }
    }

    [TestMethod]
    public void EveryOwnedSchemaDeclaresDraft202012AndAnExactProgramKitIdentity()
    {
        var schemaFiles = ConformanceInputs
            .Files("Schemas", "*.schema.json");

        Assert.IsGreaterThanOrEqualTo(5, schemaFiles.Length);
        foreach (var schemaFile in schemaFiles)
        {
            var schema = File.ReadAllText(schemaFile);
            StringAssert.Contains(
                schema,
                "\"$schema\": \"https://json-schema.org/draft/2020-12/schema\"");
            StringAssert.Contains(schema, "\"$id\": \"https://schemas.orbyss.io/program-kit/");
            StringAssert.Contains(
                schema,
                "\"x-program-kit-identity\": \"pkid:schema:program-kit:");
            StringAssert.Contains(schema, "\"x-program-kit-version\": \"1.0.0\"");
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
        Assert.AreEqual(1, elements.Length, name);
        Assert.AreEqual(expected, elements[0].Value, name);
    }

    private static string RequiredAttribute(XElement element, string name)
    {
        return element.Attribute(name)?.Value
            ?? throw new AssertFailedException($"Missing {name} on {element.Name}.");
    }
}
