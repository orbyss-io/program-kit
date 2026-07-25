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
                    "sha256:bfe7d3f4c2b76048b4d962373f4d0b5f76a5e3f6f5b072b31672f13a7afa9403")),
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
