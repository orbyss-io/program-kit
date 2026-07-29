using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.CommandLine.Operations.Schemas;

/// <summary>
/// Explicitly composes a bounded set of schema modules so cross-module
/// references can be resolved without directory or assembly discovery.
/// </summary>
public sealed class CompositeSchemaModule : IProgramKitSchemaModule
{
    private readonly IProgramKitSchemaModule artifacts;
    private readonly IProgramKitSchemaModule csharpBuildGates;

    /// <summary>Creates the finite C# gate schema dependency closure.</summary>
    public CompositeSchemaModule(
        IProgramKitSchemaModule artifacts,
        IProgramKitSchemaModule csharpBuildGates)
    {
        this.artifacts = artifacts ??
            throw new ArgumentNullException(nameof(artifacts));
        this.csharpBuildGates = csharpBuildGates ??
            throw new ArgumentNullException(nameof(csharpBuildGates));
        Resources = artifacts.Resources
            .Select(resource =>
                resource with
                {
                    ResourceName = string.Concat(
                        artifacts.Identity.Name,
                        "-",
                        resource.ResourceName),
                })
            .Concat(csharpBuildGates.Resources.Select(resource =>
                resource with
                {
                    ResourceName = string.Concat(
                        csharpBuildGates.Identity.Name,
                        "-",
                        resource.ResourceName),
                }))
            .ToImmutableArray();
    }

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:command-line-composite-schemas");

    /// <inheritdoc />
    public SemanticVersion Version { get; } = new("0.1.0-alpha.1");

    /// <inheritdoc />
    public ImmutableArray<ProgramKitSchemaResource> Resources { get; }

    /// <inheritdoc />
    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        if (artifacts.Resources.Any(resource =>
                resource.SchemaReference == schemaReference))
        {
            return artifacts.OpenRead(schemaReference);
        }

        if (csharpBuildGates.Resources.Any(resource =>
                resource.SchemaReference == schemaReference))
        {
            return csharpBuildGates.OpenRead(schemaReference);
        }

        throw new KeyNotFoundException(
            string.Concat(
                "The exact composite schema is not registered: ",
                schemaReference.Identity.Value,
                "@",
                schemaReference.Version.Value));
    }
}
