using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Schemas;

/// <summary>
/// Supplies explicitly registered schema descriptors and streams to a consumer
/// without coupling contract packages to a schema implementation.
/// </summary>
public interface IProgramKitSchemaModule
{
    /// <summary>Gets the stable module identity.</summary>
    ProgramKitIdentifier Identity { get; }

    /// <summary>Gets the independently versioned module contract.</summary>
    SemanticVersion Version { get; }

    /// <summary>Gets exact schema resources in deterministic registration order.</summary>
    ImmutableArray<ProgramKitSchemaResource> Resources { get; }

    /// <summary>Opens the exact selected schema resource for reading.</summary>
    Stream OpenRead(ArtifactReference schemaReference);
}
