using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.CommandLine.Operations.Schemas;

/// <summary>Immutable exact-byte schema module for one verified dependency closure.</summary>
public sealed class DependencyClosureSchemaModule : IProgramKitSchemaModule
{
    private readonly ImmutableDictionary<string, ReadOnlyMemory<byte>> content;

    /// <summary>Creates an exact module from catalog-verified entries.</summary>
    public DependencyClosureSchemaModule(
        ArtifactReference selectedRevision,
        ImmutableArray<SchemaCatalogEntry> entries)
    {
        ArgumentNullException.ThrowIfNull(selectedRevision);
        Identity = new ProgramKitIdentifier(
            string.Concat(
                "pkid:catalog:program-kit:schema-closure.",
                selectedRevision.Identity.Name));
        Resources = entries
            .Select((entry, index) =>
                entry.Resource with
                {
                    ResourceName = string.Concat(
                        index.ToString(
                            "D4",
                            System.Globalization.CultureInfo.InvariantCulture),
                        "-",
                        entry.Resource.ResourceName),
                })
            .ToImmutableArray();
        content = entries.ToImmutableDictionary(
            static entry => ExactKey(entry.Resource.SchemaReference),
            static entry => entry.Content,
            StringComparer.Ordinal);
    }

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; }

    /// <inheritdoc />
    public SemanticVersion Version { get; } = new("0.1.0-alpha.1");

    /// <inheritdoc />
    public ImmutableArray<ProgramKitSchemaResource> Resources { get; }

    /// <inheritdoc />
    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        return content.TryGetValue(ExactKey(schemaReference), out var bytes)
            ? new MemoryStream(bytes.ToArray(), writable: false)
            : throw new KeyNotFoundException(
                string.Concat(
                    "The exact schema is outside the selected dependency closure: ",
                    schemaReference.Identity.Value,
                    "@",
                    schemaReference.Version.Value));
    }

    private static string ExactKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}
