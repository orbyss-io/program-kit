using System.Text.Json;

namespace Orbyss.ProgramKit.ConformanceTests.Schemas;

[TestClass]
public sealed class CurrentWriterPkidGrammarConformanceTests
{
    private static readonly string[] CurrentWriterSchemas =
    [
        "schemas/artifacts/definitions-0.1.0-alpha.2.schema.json",
        "schemas/architecture/architecture-design-0.1.0-alpha.3.schema.json",
        "schemas/architecture/static-conformance-disposition-0.1.0-alpha.2.schema.json",
        "schemas/planning/definitions-0.1.0-alpha.5.schema.json",
        "schemas/planning/implementation-plan-0.1.0-alpha.5.schema.json",
    ];

    [TestMethod]
    public void CurrentWritersUseOnlyTheCanonicalFullPkidPattern()
    {
        List<string> failures = [];
        foreach (var relativePath in CurrentWriterSchemas)
        {
            var path = Path.Combine(
                ConformanceInputs.RepositoryRoot,
                relativePath.Replace('/', Path.DirectorySeparatorChar));
            using var document = JsonDocument.Parse(File.ReadAllBytes(path));
            Visit(document.RootElement, relativePath, failures);
        }

        Assert.HasCount(0, failures, string.Join(Environment.NewLine, failures));
    }

    private static void Visit(
        JsonElement value,
        string source,
        List<string> failures)
    {
        if (value.ValueKind == JsonValueKind.Object)
        {
            foreach (var property in value.EnumerateObject())
            {
                if (property.NameEquals("pattern") &&
                    property.Value.ValueKind == JsonValueKind.String)
                {
                    var pattern = property.Value.GetString()!;
                    if (pattern.StartsWith("^pkid:", StringComparison.Ordinal) &&
                        !string.Equals(
                            pattern,
                            ProgramKitIdentifier.CanonicalPattern,
                            StringComparison.Ordinal) &&
                        !IsKindPrefix(pattern))
                    {
                        failures.Add(string.Concat(
                            source,
                            " contains divergent PKID pattern ",
                            pattern));
                    }
                }

                Visit(property.Value, source, failures);
            }
        }
        else if (value.ValueKind == JsonValueKind.Array)
        {
            foreach (var item in value.EnumerateArray())
            {
                Visit(item, source, failures);
            }
        }
    }

    private static bool IsKindPrefix(string pattern) =>
        pattern.EndsWith(':') &&
        pattern.Count(static character => character == ':') == 2;
}
