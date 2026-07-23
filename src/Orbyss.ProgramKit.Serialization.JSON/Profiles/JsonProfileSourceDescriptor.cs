using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Serialization.Json.Profiles;

/// <summary>
/// The typed, self-reference-free source whose exact LF/UTF-8/no-BOM bytes bind
/// one built-in profile digest.
/// </summary>
public sealed record JsonProfileSourceDescriptor(
    [property: JsonPropertyName("$schema")] Uri Schema,
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    JsonProfileSourceKind ProfileKind,
    ProfileReference? CanonicalizationProfile,
    JsonProfileExtensibility Extensibility,
    ImmutableArray<string> Rules,
    JsonSerializationLimits MaximumLimits,
    ImmutableArray<string> BuiltInMetadataTargets,
    ImmutableArray<string> BuiltInConverterTargets,
    ImmutableArray<JsonOwnedMechanicsSource> OwnedMechanicsSources,
    string DigestRule);
