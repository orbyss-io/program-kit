using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.Schemas;

/// <summary>Finite offline catalog of explicitly composed Program Kit schemas.</summary>
public interface ISchemaCatalog
{
    /// <summary>Gets every registered schema in exact identity order.</summary>
    ImmutableArray<SchemaCatalogEntry> Entries { get; }

    /// <summary>Resolves one exact <c>identity@version</c> selection.</summary>
    SchemaCatalogEntry Resolve(string exactId);

    /// <summary>Renders the complete finite catalog.</summary>
    byte[] Render(string format);
}
