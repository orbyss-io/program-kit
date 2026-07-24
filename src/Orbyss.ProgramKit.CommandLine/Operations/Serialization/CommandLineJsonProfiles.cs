using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Exact fixed JSON profiles owned by the command transport.</summary>
public static class CommandLineJsonProfiles
{
    /// <summary>Gets the non-extensible canonical diagnostic output profile.</summary>
    public static JsonSerializationProfile Diagnostics { get; } =
        new(
            new JsonSerializationProfileRef(
                new ProgramKitIdentifier(
                    "pkid:profile:program-kit:json-command-diagnostics"),
                new SemanticVersion("1.0.0"),
                new Sha256Digest(
                    "sha256:cb3e456ef3db3415f01c63b20b1e6c1e3be66c8f869b4dbd14e6198cf9f0c015")),
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

    /// <summary>
    /// Gets the fixed profile for workspace-package, package-root, and local-publish manifests.
    /// </summary>
    public static JsonSerializationProfile LocalOperations { get; } =
        new(
            new JsonSerializationProfileRef(
                new ProgramKitIdentifier(
                    "pkid:profile:program-kit:json-local-operations"),
                new SemanticVersion("1.0.0"),
                new Sha256Digest(
                    "sha256:a467fa50254b61031d95f671ad08d9e74101a856118826489a2c51dfe90525ce")),
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
