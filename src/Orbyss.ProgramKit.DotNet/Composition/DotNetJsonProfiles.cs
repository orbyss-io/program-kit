using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.DotNet.Composition;

/// <summary>Exact JSON profiles owned by the .NET Program Kit.</summary>
public static class DotNetJsonProfiles
{
    /// <summary>Gets the fixed non-extensible shell bootstrap profile.</summary>
    public static JsonSerializationProfile ShellBootstrap { get; } =
        new(
            new JsonSerializationProfileRef(
                new ProgramKitIdentifier(
                    "pkid:profile:program-kit:json-dotnet-shell"),
                new SemanticVersion("2.0.0"),
                new Sha256Digest(
                    "sha256:c25bcbb1a5363f76207d58dcbee43f088c63beff730b156b5b5d37a1f5b031d2")),
            ProgramKitJsonProfiles.CanonicalJsonRfc8785,
            JsonProfileExtensibility.None,
            new JsonSerializationRules(
                SourceGeneratedMetadataOnly: true,
                SchemaDeclaredPropertyNames: true,
                CaseSensitiveReads: true,
                DisallowComments: true,
                DisallowTrailingCommas: true,
                DisallowUnmappedMembers: true,
                WriteNullProperties: true,
                StrictNumbers: true,
                DisallowReferencePreservation: true,
                RequireNfcStrings: true),
            JsonSerializationLimits.Default);
}
