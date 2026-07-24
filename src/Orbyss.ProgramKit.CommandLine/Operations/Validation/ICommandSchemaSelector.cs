using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.CommandLine.Operations.Validation;

/// <summary>Selects one exact schema only from explicitly registered modules.</summary>
public interface ICommandSchemaSelector
{
    /// <summary>Resolves the artifact's declared schema URI exactly once.</summary>
    IProgramKitSchemaModule Resolve(
        ReadOnlyMemory<byte> utf8Json,
        out ArtifactReference revision);
}
