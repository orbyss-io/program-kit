using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.CommandLine.Operations.Schemas;

namespace Orbyss.ProgramKit.CommandLine.Operations.Validation;

/// <summary>Exact schema selector over the finite Program Kit module set.</summary>
public sealed class CommandSchemaSelector : ICommandSchemaSelector
{
    private readonly ISchemaCatalog catalog;
    private readonly ISchemaDependencyClosureProvider closureProvider;

    /// <summary>Initializes the selector from exact package-owned schema modules.</summary>
    public CommandSchemaSelector(
        ISchemaCatalog catalog,
        ISchemaDependencyClosureProvider closureProvider)
    {
        this.catalog = catalog ?? throw new ArgumentNullException(nameof(catalog));
        this.closureProvider = closureProvider ??
            throw new ArgumentNullException(nameof(closureProvider));
    }

    /// <inheritdoc />
    public IProgramKitSchemaModule Resolve(
        ReadOnlyMemory<byte> utf8Json,
        out ArtifactReference revision)
    {
        var schemaIdentity = SchemaIdentityReader.Read(utf8Json.Span);
        return Resolve(schemaIdentity, out revision);
    }

    /// <inheritdoc />
    public IProgramKitSchemaModule Resolve(
        string exactSchemaId,
        out ArtifactReference revision)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(exactSchemaId);
        var matches = catalog.Entries
            .Where(entry =>
                string.Equals(
                    entry.CanonicalUri,
                    exactSchemaId,
                    StringComparison.Ordinal) ||
                string.Equals(
                    entry.ExactId,
                    exactSchemaId,
                    StringComparison.Ordinal))
            .ToArray();
        if (matches.Length != 1)
        {
            throw new InvalidDataException(
                "The declared schema URI must resolve exactly once in the explicit module set.");
        }

        revision = matches[0].Resource.SchemaReference;
        return closureProvider.Create(revision);
    }
}
