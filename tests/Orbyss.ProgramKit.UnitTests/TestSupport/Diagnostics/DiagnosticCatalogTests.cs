using System.Collections.Immutable;
using System.Reflection;
using Orbyss.ProgramKit.Modularity;
using Orbyss.ProgramKit.Serialization.Json;

namespace Orbyss.ProgramKit.UnitTests.TestSupport.Diagnostics;

[TestClass]
public sealed class DiagnosticCatalogTests
{
    [TestMethod]
    public void UniversalDiagnosticCatalogsAreCompleteUniqueAndCanonicallyNamed()
    {
        AssertCatalog(
            typeof(ArtifactDiagnosticIds),
            ArtifactDiagnosticCatalog.Definitions,
            "PKART");
        AssertCatalog(
            typeof(ArchitectureDiagnosticIds),
            ArchitectureDiagnosticCatalog.Definitions,
            "PKARC");
        AssertCatalog(
            typeof(QualityDiagnosticIds),
            QualityDiagnosticCatalog.Definitions,
            "PKQLT");
        AssertCatalog(
            typeof(PlanningDiagnosticIds),
            PlanningDiagnosticCatalog.Definitions,
            "PKPLN");
        AssertCatalog(
            typeof(DevelopmentDiagnosticIds),
            DevelopmentDiagnosticCatalog.Definitions,
            "PKDEV");
        AssertCatalog(
            typeof(ModularityDiagnosticIds),
            ModularityDiagnosticCatalog.Definitions,
            "PKMOD");
        AssertCatalog(
            typeof(ProgramKitJsonDiagnosticIds),
            ProgramKitJsonDiagnosticCatalog.Definitions,
            "PKJSN");
    }

    private static void AssertCatalog(
        Type identifierType,
        ImmutableArray<ProgramKitDiagnosticDefinition> definitions,
        string prefix)
    {
        var expected = identifierType
            .GetFields(BindingFlags.Public | BindingFlags.Static)
            .Where(field => field.IsLiteral && field.FieldType == typeof(string))
            .Select(field => (string?)field.GetRawConstantValue())
            .Where(value => value is not null)
            .Cast<string>()
            .Order(StringComparer.Ordinal)
            .ToArray();
        var actual = definitions
            .Select(definition => definition.Id)
            .ToArray();

        Assert.HasCount(expected.Length, definitions);
        Assert.HasCount(expected.Length, actual.Distinct(StringComparer.Ordinal));
        Assert.AreSequenceEqual(expected, actual);
        foreach (var id in actual)
        {
            Assert.IsTrue(
                id.StartsWith(prefix, StringComparison.Ordinal)
                && id.Length == prefix.Length + 3
                && id.AsSpan(prefix.Length).IndexOfAnyExceptInRange('0', '9') < 0,
                id);
        }
    }
}
