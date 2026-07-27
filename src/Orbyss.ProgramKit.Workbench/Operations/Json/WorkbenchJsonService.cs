using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.Workbench.Operations.Json;

/// <summary>Default deterministic model-first JSON service.</summary>
public sealed class WorkbenchJsonService : IWorkbenchJsonService
{
    private readonly IProgramKitJsonSerializer serializer;

    /// <summary>Initializes the service with the only selected JSON mechanics.</summary>
    public WorkbenchJsonService(IProgramKitJsonSerializer serializer)
    {
        this.serializer = serializer ?? throw new ArgumentNullException(nameof(serializer));
    }

    /// <inheritdoc />
    public T Parse<T>(
        ReadOnlyMemory<byte> utf8Json,
        JsonSerializationProfileRef profileReference,
        JsonSerializationLimits limits) =>
        serializer.Read<T>(utf8Json, profileReference, limits);

    /// <inheritdoc />
    public WorkbenchResult<T> Validate<T>(
        ReadOnlyMemory<byte> utf8Json,
        JsonSerializationProfileRef profileReference,
        JsonSerializationLimits limits,
        IProgramKitSemanticValidator<T> validator)
    {
        ArgumentNullException.ThrowIfNull(validator);
        var value = serializer.Read<T>(utf8Json, profileReference, limits);
        var validation = validator.Validate(value);
        return validation.IsValid
            ? new WorkbenchResult<T>(value, validation)
            : new WorkbenchResult<T>(default, validation);
    }

    /// <inheritdoc />
    public CanonicalJsonValue Normalize<T>(
        ReadOnlyMemory<byte> utf8Json,
        JsonSerializationProfileRef profileReference,
        JsonSerializationLimits limits)
    {
        var value = serializer.Read<T>(utf8Json, profileReference, limits);
        return serializer.Write(value, profileReference, limits);
    }

    /// <inheritdoc />
    public Sha256Digest Digest<T>(
        ReadOnlyMemory<byte> utf8Json,
        JsonSerializationProfileRef profileReference,
        JsonSerializationLimits limits) =>
        Normalize<T>(utf8Json, profileReference, limits).Digest;
}
