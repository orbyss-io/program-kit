using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.CommandLine.Operations.Schemas;

/// <summary>Creates an immutable in-memory schema module for a verified closure.</summary>
public interface ISchemaDependencyClosureModuleFactory
{
    /// <summary>Creates one exact closure module.</summary>
    IProgramKitSchemaModule Create(
        ArtifactReference selectedRevision,
        ImmutableArray<SchemaCatalogEntry> entries);
}
