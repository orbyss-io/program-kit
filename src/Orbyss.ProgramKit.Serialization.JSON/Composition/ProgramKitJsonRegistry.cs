using System.Collections.Immutable;
using System.Text.Json.Serialization.Metadata;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

/// <summary>An immutable, host-scoped JSON registry whose options are read-only.</summary>
public sealed class ProgramKitJsonRegistry : IProgramKitJsonRegistry
{
    private readonly ImmutableDictionary<string, FrozenJsonProfile> runtimeProfiles;

    internal ProgramKitJsonRegistry(
        ImmutableArray<JsonSerializationProfile> profiles,
        ImmutableArray<JsonSerializationProfileSelection> selections,
        ImmutableDictionary<string, FrozenJsonProfile> runtimeProfiles)
    {
        Profiles = profiles;
        Selections = selections;
        this.runtimeProfiles = runtimeProfiles;
    }

    /// <inheritdoc />
    public ImmutableArray<JsonSerializationProfile> Profiles { get; }

    /// <inheritdoc />
    public ImmutableArray<JsonSerializationProfileSelection> Selections { get; }

    /// <inheritdoc />
    public JsonSerializationProfile GetProfile(
        JsonSerializationProfileRef profileReference) =>
        GetRuntimeProfile(profileReference).Descriptor;

    internal FrozenJsonProfile GetRuntimeProfile(
        JsonSerializationProfileRef profileReference)
    {
        if (profileReference is null)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "An exact JSON profile reference is required.",
                "/profile");
        }

        var key = ProgramKitJsonRegistryKey.Exact(profileReference);
        return runtimeProfiles.TryGetValue(key, out var profile)
            ? profile
            : throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.UnknownProfile,
                $"The exact JSON profile '{key}' is not registered.",
                "/profile");
    }

    /// <inheritdoc />
    public JsonTypeInfo<T> GetTypeInfo<T>(
        JsonSerializationProfileRef profileReference)
    {
        var runtimeProfile = GetRuntimeProfile(profileReference);
        if (!runtimeProfile.RootMetadataTargetTypes.Contains(typeof(T)))
        {
            throw MetadataFailure<T>(profileReference);
        }

        try
        {
            return runtimeProfile.Options.GetTypeInfo(typeof(T)) as JsonTypeInfo<T>
                ?? throw MetadataFailure<T>(profileReference);
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

    private static ProgramKitJsonException MetadataFailure<T>(
        JsonSerializationProfileRef profileReference,
        Exception? innerException = null) =>
        ProgramKitJsonException.Create(
            ProgramKitJsonDiagnosticIds.TypeMetadataUnavailable,
            $"No selected source-generated metadata describes '{typeof(T).FullName}' for profile '{profileReference.Identity.Value}'.",
            innerException: innerException);
}
