using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.CommandLine.Operations.Schemas;

/// <summary>Builds finite offline transitive schema closures from registered dependencies.</summary>
public interface ISchemaDependencyClosureProvider
{
    /// <summary>Creates the exact registered closure for one selected revision.</summary>
    IProgramKitSchemaModule Create(ArtifactReference selectedRevision);
}
