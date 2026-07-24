namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Catalog;

/// <summary>Renders the canonical capability index as a non-authoritative catalog.</summary>
public interface ICapabilityCatalogRenderer
{
    /// <summary>Renders one explicit index and optional output path.</summary>
    ValueTask<ReadOnlyMemory<byte>> RenderAsync(
        string indexPath,
        string outputPath,
        CancellationToken cancellationToken);
}
