using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Diagnostics;

/// <summary>Stable diagnostic identifiers owned by Orbyss.ProgramKit.Artifacts.</summary>
public static class ArtifactDiagnosticIds
{
    /// <summary>The identifier does not match the PKID grammar.</summary>
    public const string InvalidProgramKitIdentifier = "PKART001";

    /// <summary>The version is not a valid SemVer 2.0.0 version.</summary>
    public const string InvalidSemanticVersion = "PKART002";

    /// <summary>The version range is not a supported deterministic range.</summary>
    public const string InvalidSemanticVersionRange = "PKART003";

    /// <summary>The digest is not a lowercase SHA-256 digest.</summary>
    public const string InvalidSha256Digest = "PKART004";

    /// <summary>An exact reference violates identity, version, or digest semantics.</summary>
    public const string InvalidArtifactReference = "PKART005";

    /// <summary>A profile reference does not identify a profile.</summary>
    public const string InvalidProfileReference = "PKART006";

    /// <summary>An artifact envelope violates an envelope invariant.</summary>
    public const string InvalidArtifactEnvelope = "PKART010";

    /// <summary>Artifact identity metadata is incomplete or contradictory.</summary>
    public const string InvalidArtifactIdentity = "PKART011";

    /// <summary>Compatibility metadata is incomplete or contradictory.</summary>
    public const string InvalidCompatibility = "PKART012";

    /// <summary>Provenance metadata is incomplete or contradictory.</summary>
    public const string InvalidProvenance = "PKART013";

    /// <summary>Representation metadata is incomplete or contradictory.</summary>
    public const string InvalidRepresentation = "PKART014";

    /// <summary>Integrity metadata is incomplete or contradictory.</summary>
    public const string InvalidIntegrity = "PKART015";

    /// <summary>An artifact embeds its own exact reference and would create a digest cycle.</summary>
    public const string SelfReferentialArtifact = "PKART016";

    /// <summary>A versioned component manifest violates a semantic invariant.</summary>
    public const string InvalidComponentManifest = "PKART020";

    /// <summary>A version map violates a graph or revision invariant.</summary>
    public const string InvalidVersionMap = "PKART021";

    /// <summary>A version selection violates an exact-selection invariant.</summary>
    public const string InvalidVersionSelection = "PKART022";

    /// <summary>The same identity and version resolve to different digests.</summary>
    public const string RevisionDigestConflict = "PKART023";

    /// <summary>A version-intent inventory is incomplete or contradictory.</summary>
    public const string InvalidVersionIntentInventory = "PKART024";

    /// <summary>An alpha progression policy or explicit proposal is invalid.</summary>
    public const string InvalidAlphaVersionProgression = "PKART025";

    /// <summary>A migration definition violates a migration invariant.</summary>
    public const string InvalidMigrationDefinition = "PKART030";

    /// <summary>A migration assessment violates closure or disposition invariants.</summary>
    public const string InvalidMigrationAssessment = "PKART031";

    /// <summary>A terminal migration disposition and its actions are inconsistent.</summary>
    public const string InvalidMigrationDisposition = "PKART032";

    /// <summary>A schema module or resource descriptor is invalid.</summary>
    public const string InvalidSchemaModule = "PKART040";
}
