using System.Collections.Immutable;
using System.Text.Json.Serialization.Metadata;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

/// <summary>Read-only exact profile and contribution selections for one shell.</summary>
public interface IProgramKitJsonRegistry
{
    /// <summary>Gets immutable profiles in stable exact-reference order.</summary>
    ImmutableArray<JsonSerializationProfile> Profiles { get; }

    /// <summary>Gets immutable selections in stable exact-profile order.</summary>
    ImmutableArray<JsonSerializationProfileSelection> Selections { get; }

    /// <summary>Gets an exact registered profile or fails with a stable diagnostic.</summary>
    JsonSerializationProfile GetProfile(JsonSerializationProfileRef profileReference);

    /// <summary>Gets selected source-generated metadata for one exact root contract.</summary>
    JsonTypeInfo<T> GetTypeInfo<T>(
        JsonSerializationProfileRef profileReference);
}
