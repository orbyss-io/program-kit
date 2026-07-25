using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.ConformanceTests.Governance;

internal sealed class SelfHostedCompositeSchemaModule : IProgramKitSchemaModule
{
    private readonly ImmutableArray<IProgramKitSchemaModule> modules;

    public SelfHostedCompositeSchemaModule(
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
        new("pkid:catalog:program-kit:self-hosted-schema-set");

    public SemanticVersion Version { get; } = new("1.0.0");

    public ImmutableArray<ProgramKitSchemaResource> Resources { get; }

    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        var module = modules.Single(candidate =>
            candidate.Resources.Any(resource =>
                resource.SchemaReference == schemaReference));
        return module.OpenRead(schemaReference);
    }
}
