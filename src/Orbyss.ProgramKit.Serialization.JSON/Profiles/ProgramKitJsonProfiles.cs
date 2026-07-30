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
                    "sha256:3292bc03c1b710d830cdfe98a63e99c2b47c045535f8dae1a9d022ef1500d032")),
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
                    "sha256:8e7336033d986dc469865917002ebff3a64109d2719d8d7ebc3bcf2a8d3c54de")),
            CanonicalJsonRfc8785,
            JsonProfileExtensibility.ExplicitContributions,
            StrictRules,
            JsonSerializationLimits.Default);
}
