using System.Text.Json;
using System.Text.Json.Serialization.Metadata;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Serialization;

/// <summary>Default typed serializer over one immutable shell-scoped registry.</summary>
public sealed class ProgramKitJsonSerializer : IProgramKitJsonSerializer
{
    private readonly IProgramKitJsonRegistry registry;
    private readonly IProgramKitJsonCanonicalizer canonicalizer;

    /// <summary>Initializes a serializer over an already frozen registry.</summary>
    public ProgramKitJsonSerializer(
        IProgramKitJsonRegistry registry,
        IProgramKitJsonCanonicalizer canonicalizer)
    {
        ArgumentNullException.ThrowIfNull(registry);
        ArgumentNullException.ThrowIfNull(canonicalizer);
        this.registry = registry;
        this.canonicalizer = canonicalizer;
    }

    /// <inheritdoc />
    public T Read<T>(
        ReadOnlyMemory<byte> utf8Json,
        JsonSerializationProfileRef profileReference,
        JsonSerializationLimits limits)
    {
        var profile = registry.GetProfile(profileReference);
        var selectedLimits = SelectLimits(profile, limits);
        var typeInfo = GetTypeInfo<T>(profileReference);
        CanonicalJsonValue canonical;
        try
        {
            canonical = canonicalizer.Canonicalize(
                utf8Json.Span,
                selectedLimits);
        }
        catch (ProgramKitJsonException exception)
        {
            var failure = StrictJsonReadFailureLocator.Locate(
                typeInfo,
                exception.Diagnostic.Path);
            throw ProgramKitJsonException.Create(
                exception.Diagnostic.Id,
                failure.Message(exception.Diagnostic.Message),
                failure.Path,
                exception);
        }

        try
        {
            var value = JsonSerializer.Deserialize(canonical.ToArray(), typeInfo);
            return value is not null
                ? value
                : throw NullModel<T>(typeInfo);
        }
        catch (ProgramKitJsonException)
        {
            throw;
        }
        catch (Exception exception)
            when (exception is JsonException or ArgumentException)
        {
            var failure = StrictJsonReadFailureLocator.Locate(
                canonical.ToArray(),
                typeInfo,
                exception as JsonException);
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidJson,
                failure.Message(
                    "The JSON value does not satisfy the selected strict source-generated contract."),
                failure.Path,
                innerException: exception);
        }
        catch (NotSupportedException exception)
        {
            throw MetadataFailure<T>(profileReference, exception);
        }
        catch (Exception exception)
            when (JsonExceptionBoundary.IsNonFatal(exception))
        {
            var failure = StrictJsonReadFailureLocator.Locate(
                canonical.ToArray(),
                typeInfo,
                exception as JsonException);
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidJson,
                failure.Message(
                    "The selected converter rejected the JSON value."),
                failure.Path,
                innerException: exception);
        }
    }

    /// <inheritdoc />
    public CanonicalJsonValue Write<T>(
        T value,
        JsonSerializationProfileRef profileReference,
        JsonSerializationLimits limits)
    {
        if (value is null)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.NullModel,
                $"A null '{typeof(T).FullName}' model cannot be written.");
        }

        var profile = registry.GetProfile(profileReference);
        var selectedLimits = SelectLimits(profile, limits);
        var typeInfo = GetTypeInfo<T>(profileReference);
        try
        {
            var serialized = new BoundedJsonBufferWriter(
                selectedLimits.MaxUtf8Bytes);
            using (var writer = new Utf8JsonWriter(
                serialized,
                new JsonWriterOptions
                {
                    Encoder = typeInfo.Options.Encoder,
                    Indented = false,
                    MaxDepth = selectedLimits.MaxDepth,
                    SkipValidation = false,
                }))
            {
                JsonSerializer.Serialize(writer, value, typeInfo);
                writer.Flush();
            }

            return canonicalizer.Canonicalize(
                serialized.WrittenSpan,
                selectedLimits);
        }
        catch (ProgramKitJsonException)
        {
            throw;
        }
        catch (JsonByteLimitExceededException exception)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.ByteLimitExceeded,
                "The serialized JSON exceeds the configured UTF-8 byte limit.",
                innerException: exception);
        }
        catch (Exception exception)
            when (exception is JsonException or ArgumentException)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidJson,
                $"The '{typeof(T).FullName}' model could not be written as strict JSON.",
                innerException: exception);
        }
        catch (NotSupportedException exception)
        {
            throw MetadataFailure<T>(profileReference, exception);
        }
        catch (Exception exception)
            when (JsonExceptionBoundary.IsNonFatal(exception))
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidJson,
                $"The converter selected for '{typeof(T).FullName}' failed while writing strict JSON.",
                innerException: exception);
        }
    }

    private JsonTypeInfo<T> GetTypeInfo<T>(
        JsonSerializationProfileRef profileReference)
    {
        try
        {
            return registry.GetTypeInfo<T>(profileReference);
        }
        catch (ProgramKitJsonException)
        {
            throw;
        }
        catch (Exception exception)
            when (exception is NotSupportedException or InvalidOperationException)
        {
            throw MetadataFailure<T>(profileReference, exception);
        }
    }

    private static JsonSerializationLimits SelectLimits(
        JsonSerializationProfile profile,
        JsonSerializationLimits requested)
    {
        if (requested is null)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "Explicit JSON operation limits are required.",
                "/limits");
        }

        requested.EnsureValid();
        if (!requested.FitsWithin(profile.MaximumLimits))
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "Requested JSON limits cannot exceed the selected profile maximum.",
                "/limits");
        }

        return requested;
    }

    private static ProgramKitJsonException MetadataFailure<T>(
        JsonSerializationProfileRef? profileReference,
        Exception? innerException = null) =>
        ProgramKitJsonException.Create(
            ProgramKitJsonDiagnosticIds.TypeMetadataUnavailable,
            $"No selected source-generated metadata describes '{typeof(T).FullName}'" +
            (profileReference is null
                ? "."
                : $" for profile '{profileReference.Identity.Value}'."),
            innerException: innerException);

    private static ProgramKitJsonException NullModel<T>(
        JsonTypeInfo<T> typeInfo)
    {
        var failure = StrictJsonReadFailureLocator.Locate(
            typeInfo,
            diagnosticPath: null);
        return ProgramKitJsonException.Create(
            ProgramKitJsonDiagnosticIds.NullModel,
            failure.Message(
                "Strict typed deserialization produced no model."),
            failure.Path);
    }
}
