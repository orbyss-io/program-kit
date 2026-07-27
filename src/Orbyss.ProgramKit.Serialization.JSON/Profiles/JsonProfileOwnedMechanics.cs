using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Metadata;

namespace Orbyss.ProgramKit.Serialization.Json.Profiles;

/// <summary>
/// Binds one fixed profile revision to source-generated metadata and converters
/// versioned by the profile-owning package.
/// </summary>
public sealed class JsonProfileOwnedMechanics
{
    /// <summary>Initializes one exact consumer-owned profile mechanics set.</summary>
    public JsonProfileOwnedMechanics(
        JsonSerializationProfileRef profile,
        ProgramKitIdentifier owningPackage,
        JsonSerializerContext context,
        params JsonProfileOwnedConverter[] converters)
        : this(
            profile,
            owningPackage,
            context,
            isBuiltIn: false,
            converters: converters)
    {
    }

    internal JsonProfileOwnedMechanics(
        JsonSerializationProfileRef profile,
        ProgramKitIdentifier owningPackage,
        JsonSerializerContext context,
        bool isBuiltIn,
        params JsonProfileOwnedConverter[] converters)
    {
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(context);
        ArgumentNullException.ThrowIfNull(converters);
        if (!ProgramKitIdentifier.Validate(profile.Identity.Value).IsValid ||
            profile.Identity.Kind != "profile" ||
            !SemanticVersion.Validate(profile.Version.Value).IsValid ||
            !Sha256Digest.Validate(profile.Digest.Value).IsValid)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "Profile-owned metadata requires an exact profile identity, version, and digest.",
                "/profile");
        }

        if (!ProgramKitIdentifier.Validate(owningPackage.Value).IsValid ||
            owningPackage.Kind != "package")
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "Profile-owned metadata requires a valid owning package identity.",
                "/owningPackage");
        }

        Profile = profile;
        OwningPackage = owningPackage;
        Context = context;
        IsBuiltIn = isBuiltIn;
        RuntimeTargetTypes =
            JsonContributionTargetContract.GetSourceGeneratedContextTargets(context);
        TargetTypeIdentities = RuntimeTargetTypes
            .Select(JsonTargetTypeIdentity.For)
            .ToImmutableArray();
        Converters = [.. converters];
        ConverterTargetTypes = Converters
            .SelectMany(static converter => converter.RuntimeTargetTypes)
            .ToImmutableArray();
        ConverterTargetTypeIdentities = Converters
            .SelectMany(static converter => converter.TargetTypeIdentities)
            .ToImmutableArray();
    }

    /// <summary>Gets the exact owning profile revision.</summary>
    public JsonSerializationProfileRef Profile { get; }

    /// <summary>Gets the package that owns these profile mechanics.</summary>
    public ProgramKitIdentifier OwningPackage { get; }

    /// <summary>Gets the profile-owned source-generated context.</summary>
    public JsonSerializerContext Context { get; }

    /// <summary>Gets exact closed metadata target types.</summary>
    public ImmutableArray<Type> RuntimeTargetTypes { get; }

    /// <summary>Gets stable metadata target identities.</summary>
    public ImmutableArray<string> TargetTypeIdentities { get; }

    /// <summary>Gets profile-owned converters in first-match order.</summary>
    public ImmutableArray<JsonProfileOwnedConverter> Converters { get; }

    /// <summary>Gets ordered converter runtime target claims.</summary>
    public ImmutableArray<Type> ConverterTargetTypes { get; }

    /// <summary>Gets ordered converter target identities.</summary>
    public ImmutableArray<string> ConverterTargetTypeIdentities { get; }

    internal bool IsBuiltIn { get; }
}
