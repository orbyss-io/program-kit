using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Serialization.Json.Profiles;

/// <summary>Well-known exact Program Kit JSON profile descriptors.</summary>
public static class ProgramKitJsonProfiles
{
    private static readonly JsonSerializationRules StrictRules =
        new(
            SourceGeneratedMetadataOnly: true,
            SchemaDeclaredPropertyNames: true,
            CaseSensitiveReads: true,
            DisallowComments: true,
            DisallowTrailingCommas: true,
            DisallowUnmappedMembers: true,
            WriteNullProperties: true,
            StrictNumbers: true,
            DisallowReferencePreservation: true,
            RequireNfcStrings: true);

    /// <summary>Gets the exact strict RFC 8785-subset canonicalization profile.</summary>
    public static ProfileReference CanonicalJsonRfc8785 { get; } =
        new(
            new ProgramKitIdentifier(
                "pkid:profile:program-kit:canonical-json-rfc8785"),
            new SemanticVersion("1.0.0"),
            new Sha256Digest(
                "sha256:5f6b81547f1c025ec20fafbd5701b4506970cb58ca89e1679ebbe40a9551aa8b"));

    /// <summary>Gets the non-extensible bootstrap/profile-metadata profile.</summary>
    public static JsonSerializationProfile JsonMeta { get; } =
        new(
            new JsonSerializationProfileRef(
                new ProgramKitIdentifier("pkid:profile:program-kit:json-meta"),
                new SemanticVersion("1.0.0"),
                new Sha256Digest(
                    "sha256:16612d5e3719b01a0b2f88f9cab7b430f2f049afea78494b592b71ebb2efcdf9")),
            CanonicalJsonRfc8785,
            JsonProfileExtensibility.None,
            StrictRules,
            JsonSerializationLimits.Default);

    /// <summary>Gets the strict model-first Program Kit contract profile.</summary>
    public static JsonSerializationProfile JsonContracts { get; } =
        new(
            new JsonSerializationProfileRef(
                new ProgramKitIdentifier("pkid:profile:program-kit:json-contracts"),
                new SemanticVersion("1.0.0"),
                new Sha256Digest(
                    "sha256:11794e1c109d9989e3fa6fe7788eb608adbc14e8544641480431581319135457")),
            CanonicalJsonRfc8785,
            JsonProfileExtensibility.ExplicitContributions,
            StrictRules,
            JsonSerializationLimits.Default);
}
