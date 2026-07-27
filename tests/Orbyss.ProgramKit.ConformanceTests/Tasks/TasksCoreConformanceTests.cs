using System.Collections.Immutable;
using System.Reflection;
using System.Xml.Linq;
using Orbyss.ProgramKit.TasksCoreDomainConsumerFixture.Contracts;

namespace Orbyss.ProgramKit.ConformanceTests.Tasks;

[TestClass]
public sealed class TasksCoreConformanceTests
{
    private static readonly string[] ExpectedDiagnosticIds =
    [
        "PKTSK001",
        "PKTSK002",
        "PKTSK003",
        "PKTSK004",
        "PKTSK005",
        "PKTSK006",
        "PKTSK007",
        "PKTSK008",
    ];

    [TestMethod]
    public void TasksCoreDiagnosticsAreCompleteUniqueAndStable()
    {
        var constants = typeof(TasksCoreDiagnosticIds)
            .GetFields(BindingFlags.Public | BindingFlags.Static)
            .Where(static field =>
                field.IsLiteral &&
                field.FieldType == typeof(string))
            .Select(static field =>
                (string)(field.GetRawConstantValue() ??
                    throw new AssertFailedException(
                        "A Tasks.Core diagnostic constant has no value.")))
            .Order(StringComparer.Ordinal)
            .ToArray();
        var catalog = TasksCoreDiagnosticCatalog.Definitions;

        Assert.AreSequenceEqual(ExpectedDiagnosticIds, constants);
        Assert.AreSequenceEqual(
            ExpectedDiagnosticIds,
            catalog.Select(static definition => definition.Id));
        Assert.HasCount(
            catalog.Length,
            catalog.Select(static definition => definition.Id)
                .Distinct(StringComparer.Ordinal)
                .ToArray());
    }

    [TestMethod]
    public void DomainCoreFixtureReferencesOnlyTasksCoreAndItsApprovedClosure()
    {
        var project = XDocument.Parse(
            ConformanceInputs.Read(
                "TasksCoreDomainConsumer/TasksCoreDomainConsumer.csproj"));
        var references = project.Descendants("ProjectReference")
            .Select(static reference =>
                Path.GetFileNameWithoutExtension(
                    (string?)reference.Attribute("Include")))
            .ToArray();

        Assert.AreSequenceEqual(
            ["Orbyss.ProgramKit.Tasks.Core"],
            references);
        Assert.IsEmpty(project.Descendants("PackageReference"));
        Assert.IsEmpty(project.Descendants("FrameworkReference"));
        Assert.IsEmpty(project.Descendants("TargetFramework"));
        Assert.IsEmpty(project.Descendants("TargetFrameworks"));

        var source = string.Join(
            Environment.NewLine,
            ConformanceInputs.Files(
                    "TasksCoreDomainConsumer/Contracts",
                    "*.cs")
                .Select(File.ReadAllText));
        string[] forbidden =
        [
            "CShells",
            "Cronos",
            "JsonElement",
            "JsonNode",
            "Microsoft.Extensions",
            "Orbyss.ProgramKit.Tasks;",
            "Orbyss.ProgramKit.Tasks.InProcess",
            "Orbyss.ProgramKit.Tasks.Hosting",
        ];
        foreach (var token in forbidden)
        {
            Assert.DoesNotContain(token, source, token);
        }

        var fixtureReferences = typeof(DomainTaskCatalog).Assembly
            .GetReferencedAssemblies()
            .Select(static reference => reference.Name)
            .Where(static name =>
                name is not null &&
                name.StartsWith("Orbyss.ProgramKit.", StringComparison.Ordinal))
            .Cast<string>()
            .ToImmutableHashSet(StringComparer.Ordinal);
        Assert.IsTrue(
            fixtureReferences.SetEquals(
                [
                    "Orbyss.ProgramKit.Artifacts",
                    "Orbyss.ProgramKit.Tasks.Core",
                ]),
            string.Join(", ", fixtureReferences));
    }

    [TestMethod]
    public void FixtureDefinesVersionedImmediateBackgroundAndScheduledWork()
    {
        var immediate = DomainTaskCatalog.ImmediateRequest("immediate");
        var background = DomainTaskCatalog.BackgroundRequest("background");
        var schedule = DomainTaskCatalog.Schedule();
        var occurrence = new ArtifactReference(
            ProgramKitIdentifier.Parse(
                "pkid:task-occurrence:consumer:test-occurrence"),
            SemanticVersion.Parse("1.0.0"),
            Sha256Digest.Parse($"sha256:{new string('b', 64)}"));
        var scheduled = DomainTaskCatalog.ScheduledRequest(
            "scheduled",
            occurrence);

        Assert.AreEqual(
            DomainTaskCatalog.ImmediateDefinition.Revision,
            immediate.DefinitionRevision);
        Assert.AreEqual(
            DomainTaskCatalog.BackgroundDefinition.Revision,
            background.DefinitionRevision);
        Assert.AreEqual(
            DomainTaskCatalog.ScheduledDefinition.Revision,
            schedule.DefinitionRevision);
        Assert.AreEqual(occurrence, scheduled.OccurrenceRevision);
    }

    [TestMethod]
    public void TasksCoreContainsContractsOnlyAndReferencesArtifactsOnly()
    {
        var projectFile = ConformanceInputs.Files("Projects", "*.csproj")
            .Single(static path =>
                Path.GetFileNameWithoutExtension(path) ==
                "Orbyss.ProgramKit.Tasks.Core");
        var project = XDocument.Load(projectFile);
        var projectReferences = project.Descendants("ProjectReference")
            .Select(static reference =>
                Path.GetFileNameWithoutExtension(
                    (string?)reference.Attribute("Include")))
            .ToArray();

        Assert.AreSequenceEqual(
            ["Orbyss.ProgramKit.Artifacts"],
            projectReferences);
        Assert.IsEmpty(project.Descendants("PackageReference"));

        var source = ConformanceInputs.Files("Source", "*.cs")
            .Where(static path =>
                path.Replace('\\', '/').Contains(
                    "Orbyss.ProgramKit.Tasks.Core/",
                    StringComparison.Ordinal))
            .Select(File.ReadAllText);
        var allSource = string.Join(Environment.NewLine, source);
        string[] forbidden =
        [
            "IServiceCollection",
            "TimeProvider",
            "BackgroundService",
            "Channel<",
            "HealthCheck",
            "CShells",
            "Cronos",
            "JsonElement",
            "JsonNode",
        ];
        foreach (var token in forbidden)
        {
            Assert.DoesNotContain(token, allSource, token);
        }
    }
}
