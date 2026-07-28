using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Diagnostics;

/// <summary>The immutable diagnostic catalog owned by Orbyss.ProgramKit.Artifacts.</summary>
public static class ArtifactDiagnosticCatalog
{
    /// <summary>Gets definitions ordered by stable diagnostic identifier.</summary>
    public static ImmutableArray<ProgramKitDiagnosticDefinition> Definitions { get; } =
    [
        Error(ArtifactDiagnosticIds.InvalidProgramKitIdentifier, "Invalid Program Kit identifier"),
        Error(ArtifactDiagnosticIds.InvalidSemanticVersion, "Invalid semantic version"),
        Error(ArtifactDiagnosticIds.InvalidSemanticVersionRange, "Invalid semantic version range"),
        Error(ArtifactDiagnosticIds.InvalidSha256Digest, "Invalid SHA-256 digest"),
        Error(ArtifactDiagnosticIds.InvalidArtifactReference, "Invalid exact artifact reference"),
        Error(ArtifactDiagnosticIds.InvalidProfileReference, "Invalid exact profile reference"),
        Error(ArtifactDiagnosticIds.InvalidArtifactEnvelope, "Invalid artifact envelope"),
        Error(ArtifactDiagnosticIds.InvalidArtifactIdentity, "Invalid artifact identity"),
        Error(ArtifactDiagnosticIds.InvalidCompatibility, "Invalid compatibility metadata"),
        Error(ArtifactDiagnosticIds.InvalidProvenance, "Invalid artifact provenance"),
        Error(ArtifactDiagnosticIds.InvalidRepresentation, "Invalid artifact representation"),
        Error(ArtifactDiagnosticIds.InvalidIntegrity, "Invalid artifact integrity"),
        Error(ArtifactDiagnosticIds.SelfReferentialArtifact, "Self-referential artifact"),
        Error(ArtifactDiagnosticIds.InvalidComponentManifest, "Invalid component manifest"),
        Error(ArtifactDiagnosticIds.InvalidVersionMap, "Invalid version map"),
        Error(ArtifactDiagnosticIds.InvalidVersionSelection, "Invalid version selection"),
        Error(ArtifactDiagnosticIds.RevisionDigestConflict, "Conflicting revision digest"),
        Error(
            ArtifactDiagnosticIds.InvalidVersionIntentInventory,
            "Invalid version-intent inventory"),
        Error(
            ArtifactDiagnosticIds.InvalidAlphaVersionProgression,
            "Invalid alpha version progression"),
        Error(ArtifactDiagnosticIds.InvalidMigrationDefinition, "Invalid migration definition"),
        Error(ArtifactDiagnosticIds.InvalidMigrationAssessment, "Invalid migration assessment"),
        Error(ArtifactDiagnosticIds.InvalidMigrationDisposition, "Invalid migration disposition"),
        Error(ArtifactDiagnosticIds.InvalidSchemaModule, "Invalid schema module"),
    ];

    private static ProgramKitDiagnosticDefinition Error(string id, string title) =>
        new(id, ProgramKitDiagnosticSeverity.Error, title);
}
