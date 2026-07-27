using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Workbench.Operations.Schemas;

/// <summary>Validates JSON bytes against one exact explicitly supplied schema.</summary>
public interface IWorkbenchSchemaValidator
{
    /// <summary>Validates an instance without exposing a JSON DOM.</summary>
    ProgramKitValidationResult Validate(
        ReadOnlyMemory<byte> utf8Json,
        IProgramKitSchemaModule schemaModule,
        ArtifactReference schemaReference,
        JsonSerializationLimits limits);
}
