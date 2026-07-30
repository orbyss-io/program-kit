using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.CommandLine.Operations.Schemas;

namespace Orbyss.ProgramKit.CommandLine.Composition;

/// <summary>Composition-owned construction of immutable schema closure modules.</summary>
public sealed class SchemaDependencyClosureModuleFactory :
    ISchemaDependencyClosureModuleFactory
{
    /// <inheritdoc />
    public IProgramKitSchemaModule Create(
        ArtifactReference selectedRevision,
        ImmutableArray<SchemaCatalogEntry> entries) =>
        new DependencyClosureSchemaModule(selectedRevision, entries);
}
