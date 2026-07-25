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
                    "sha256:d0bd4543338254a4fd0c59a138d6a5717ba012b8cd84882b933a48fa92eca8a2")),
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
