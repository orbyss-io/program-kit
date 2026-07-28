using System.Collections.Immutable;
using System.Reflection;
using System.Xml.Linq;

namespace Orbyss.ProgramKit.ConformanceTests.Dependencies;

[TestClass]
public sealed class WorkbenchDependencyConformanceTests
{
    private static readonly string[] ExpectedDiagnosticIds =
    [
        "PKVER001",
        "PKVER002",
        "PKVER003",
        "PKVER004",
        "PKVER005",
        "PKWB001",
        "PKWB002",
        "PKWB003",
        "PKWB004",
        "PKWB005",
        "PKWB006",
        "PKWB007",
    ];
    private static readonly string[] ExpectedDomExceptionFiles =
    [
        "Orbyss.ProgramKit.Workbench/Operations/Schemas/JsonSchemaNetReflection.cs",
        "Orbyss.ProgramKit.Workbench/Operations/Schemas/JsonSchemaWorkbenchValidator.cs",
    ];

    [TestMethod]
    public void WorkbenchDiagnosticsAreCompleteUniqueAndStable()
    {
        var constants = typeof(WorkbenchDiagnosticIds)
            .GetFields(BindingFlags.Public | BindingFlags.Static)
            .Where(static field => field.IsLiteral && field.FieldType == typeof(string))
            .Select(static field => (string)(field.GetRawConstantValue() ??
                throw new AssertFailedException("A diagnostic constant has no value.")))
            .Order(StringComparer.Ordinal)
            .ToArray();
        var catalog = WorkbenchDiagnosticCatalog.Definitions;

        Assert.AreSequenceEqual(ExpectedDiagnosticIds, constants);
        Assert.AreSequenceEqual(
            ExpectedDiagnosticIds,
            catalog.Select(static definition => definition.Id).ToArray());
        Assert.HasCount(
            catalog.Length,
            catalog.Select(static definition => definition.Id)
                .Distinct(StringComparer.Ordinal)
                .ToArray());
        var artifactIds = typeof(ArtifactDiagnosticIds)
            .GetFields(BindingFlags.Public | BindingFlags.Static)
            .Where(static field => field.IsLiteral && field.FieldType == typeof(string))
            .Select(static field => (string)(field.GetRawConstantValue() ??
                throw new AssertFailedException("An artifact diagnostic has no value.")));
        Assert.IsEmpty(constants.Intersect(artifactIds, StringComparer.Ordinal));
    }

    [TestMethod]
    public void WorkbenchJsonDomUseIsLimitedToTheInternalSchemaAdapter()
    {
        var actual = ConformanceInputs.Files("Source", "*.cs")
            .Where(static sourceFile =>
            {
                var source = File.ReadAllText(sourceFile);
                return source.Contains("JsonElement", StringComparison.Ordinal) ||
                    source.Contains("JsonDocument", StringComparison.Ordinal) ||
                    source.Contains("JsonNode", StringComparison.Ordinal);
            })
            .Select(static sourceFile =>
            {
                var normalized = sourceFile.Replace('\\', '/');
                var marker = "/ConformanceInputs/Source/";
                var index = normalized.IndexOf(marker, StringComparison.Ordinal);
                return index < 0
                    ? normalized
                    : normalized[(index + marker.Length)..];
            })
            .Where(static relativePath =>
                relativePath.StartsWith(
                    "Orbyss.ProgramKit.Workbench/",
                    StringComparison.Ordinal))
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.AreSequenceEqual(ExpectedDomExceptionFiles, actual);
    }

    [TestMethod]
    public void WorkbenchPinsJsonSchemaAsRuntimeOnlyAndRejectsItsUnselectedAnalyzer()
    {
        var projectFile = ConformanceInputs.Files("Projects", "*.csproj")
            .Single(static path =>
                Path.GetFileNameWithoutExtension(path) ==
                "Orbyss.ProgramKit.Workbench");
        var project = XDocument.Load(projectFile);
        var packageReference = project.Descendants("PackageReference")
            .Single(static element =>
                string.Equals(
                    (string?)element.Attribute("Include"),
                    "JsonSchema.Net",
                    StringComparison.Ordinal));

        Assert.AreEqual("compile", (string?)packageReference.Attribute("ExcludeAssets"));
        Assert.AreEqual("analyzers", (string?)packageReference.Attribute("PrivateAssets"));
        var targets = ConformanceInputs.Read("Directory.Build.targets");
        Assert.Contains("RemoveProgramKitUnselectedHumanizerAnalyzer", targets);
        Assert.Contains("humanizer.core/3.0.10/analyzers", targets);
        Assert.Contains("NuGetPackageId)' == 'Humanizer.Core'", targets);
        Assert.Contains("NuGetPackageVersion)' == '3.0.10'", targets);
    }
}
