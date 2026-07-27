using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.UnitTests.Artifacts.Validation;

internal sealed class CSharpBuildGateCompositeSchemaModule :
    IProgramKitSchemaModule
{
    private readonly ImmutableArray<IProgramKitSchemaModule> modules;

    internal CSharpBuildGateCompositeSchemaModule(
        ImmutableArray<IProgramKitSchemaModule> modules)
    {
        this.modules = modules;
        Resources = modules
            .SelectMany(module => module.Resources.Select(resource =>
                resource with
                {
                    ResourceName = string.Concat(
                        module.Identity.Name,
                        "-",
                        resource.ResourceName),
                }))
            .ToImmutableArray();
    }

    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:csharp-build-gate-test-schemas");

    public SemanticVersion Version { get; } = new("1.0.0");

    public ImmutableArray<ProgramKitSchemaResource> Resources { get; }

    public Stream OpenRead(ArtifactReference schemaReference)
    {
        var module = modules.Single(candidate =>
            candidate.Resources.Any(resource =>
                resource.SchemaReference == schemaReference));
        return module.OpenRead(schemaReference);
    }
}
