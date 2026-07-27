using System.Collections.Immutable;

namespace Orbyss.ProgramKit.UnitTests.Architecture.Schemas;

internal sealed class ArchitectureCompositeSchemaModule :
    IProgramKitSchemaModule
{
    private readonly ImmutableArray<IProgramKitSchemaModule> modules;

    internal ArchitectureCompositeSchemaModule(
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
        new("pkid:catalog:program-kit:architecture-v2-test");

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
