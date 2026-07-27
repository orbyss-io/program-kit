using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Serialization.Json.Profiles;

/// <summary>An immutable, digest-bound JSON serialization profile descriptor.</summary>
public sealed record JsonSerializationProfile(
    JsonSerializationProfileRef Reference,
    ProfileReference CanonicalizationProfile,
    JsonProfileExtensibility Extensibility,
    JsonSerializationRules Rules,
    JsonSerializationLimits MaximumLimits);
