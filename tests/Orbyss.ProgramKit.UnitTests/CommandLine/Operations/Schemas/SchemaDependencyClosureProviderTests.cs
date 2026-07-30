using Orbyss.ProgramKit.Architecture.Schemas;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.CommandLine.Composition;
using Orbyss.ProgramKit.CommandLine.Operations.Schemas;
using Orbyss.ProgramKit.Planning.Schemas;
using Orbyss.ProgramKit.Quality.Schemas;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Schemas;

[TestClass]
public sealed class SchemaDependencyClosureProviderTests
{
    [TestMethod]
    public void PlanningAlpha4ClosureContainsOnlyItsRegisteredTransitiveDependencies()
    {
        IProgramKitSchemaModule[] modules =
        [
            new ArtifactsSchemaModule(),
            new ArchitectureSchemaModule(),
            new PlanningSchemaModule(),
            new QualitySchemaModule(),
        ];
        ISchemaCatalog catalog = new SchemaCatalog(modules);
        SchemaDependencyClosureProvider sut = new(
            catalog,
            new SchemaDependencyClosureModuleFactory());
        var revision = modules[2].Resources.Single(static resource =>
            resource.SchemaReference.Identity.Name == "implementation-plan" &&
            resource.SchemaReference.Version.Value == "0.1.0-alpha.4")
            .SchemaReference;

        var closure = sut.Create(revision);

        Assert.AreSequenceEqual(
            [
                "pkid:schema:program-kit:artifact-definitions@0.1.0-alpha.2",
                "pkid:schema:program-kit:implementation-plan@0.1.0-alpha.4",
                "pkid:schema:program-kit:planning-definitions@0.1.0-alpha.4",
            ],
            closure.Resources
                .Select(static resource => string.Concat(
                    resource.SchemaReference.Identity.Value,
                    "@",
                    resource.SchemaReference.Version.Value))
                .Order(StringComparer.Ordinal)
                .ToArray());
    }

    [TestMethod]
    public void CatalogRejectsEveryUnregisteredExternalReference()
    {
        TestSchemaModule module = new(
            "network-reference",
            "https://schemas.orbyss.io/program-kit/test/network-reference.schema.json",
            """
            {
              "$schema": "https://json-schema.org/draft/2020-12/schema",
              "$id": "https://schemas.orbyss.io/program-kit/test/network-reference.schema.json",
              "$ref": "https://example.invalid/unregistered.schema.json"
            }
            """);

        var exception = Assert.ThrowsExactly<InvalidDataException>(
            () => new SchemaCatalog([module]));
        Assert.Contains(
            "https://example.invalid/unregistered.schema.json",
            exception.Message);
    }

    [TestMethod]
    public void ClosureRejectsRegisteredDependencyCycles()
    {
        TestSchemaModule first = new(
            "cycle-first",
            "https://schemas.orbyss.io/program-kit/test/cycle-first.schema.json",
            """
            {
              "$schema": "https://json-schema.org/draft/2020-12/schema",
              "$id": "https://schemas.orbyss.io/program-kit/test/cycle-first.schema.json",
              "$ref": "https://schemas.orbyss.io/program-kit/test/cycle-second.schema.json"
            }
            """);
        TestSchemaModule second = new(
            "cycle-second",
            "https://schemas.orbyss.io/program-kit/test/cycle-second.schema.json",
            """
            {
              "$schema": "https://json-schema.org/draft/2020-12/schema",
              "$id": "https://schemas.orbyss.io/program-kit/test/cycle-second.schema.json",
              "$ref": "https://schemas.orbyss.io/program-kit/test/cycle-first.schema.json"
            }
            """);
        ISchemaCatalog catalog = new SchemaCatalog([first, second]);
        SchemaDependencyClosureProvider sut = new(
            catalog,
            new SchemaDependencyClosureModuleFactory());

        var exception = Assert.ThrowsExactly<InvalidDataException>(
            () => sut.Create(first.Resources[0].SchemaReference));
        Assert.Contains("cycle is malformed", exception.Message);
    }
}
