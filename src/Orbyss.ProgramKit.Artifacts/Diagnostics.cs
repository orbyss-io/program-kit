using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts;

/// <summary>Classifies a Program Kit diagnostic without coupling it to a host or transport.</summary>
public enum ProgramKitDiagnosticSeverity
{
    /// <summary>Additional deterministic information that does not affect validity.</summary>
    Information,

    /// <summary>A condition that deserves attention but does not make the value invalid.</summary>
    Warning,

    /// <summary>A conformance failure.</summary>
    Error,
}

/// <summary>A stable, transport-independent validation diagnostic.</summary>
/// <param name="Id">The stable diagnostic identifier.</param>
/// <param name="Severity">The diagnostic severity.</param>
/// <param name="Message">The culture-invariant diagnostic message.</param>
/// <param name="Path">The JSON Pointer-like path to the invalid value.</param>
public sealed record ProgramKitDiagnostic(
    string Id,
    ProgramKitDiagnosticSeverity Severity,
    string Message,
    string Path);

/// <summary>Defines one stable diagnostic family independently of an occurrence.</summary>
/// <param name="Id">The stable diagnostic identifier.</param>
/// <param name="DefaultSeverity">The default severity.</param>
/// <param name="Title">The stable culture-invariant title.</param>
public sealed record ProgramKitDiagnosticDefinition(
    string Id,
    ProgramKitDiagnosticSeverity DefaultSeverity,
    string Title);

/// <summary>The immutable result of semantic validation.</summary>
public sealed record ProgramKitValidationResult
{
    private ProgramKitValidationResult(ImmutableArray<ProgramKitDiagnostic> diagnostics)
    {
        Diagnostics = diagnostics;
    }

    /// <summary>A valid result with no diagnostics.</summary>
    public static ProgramKitValidationResult Valid { get; } =
        new(ImmutableArray<ProgramKitDiagnostic>.Empty);

    /// <summary>Gets diagnostics in deterministic discovery order.</summary>
    public ImmutableArray<ProgramKitDiagnostic> Diagnostics { get; }

    /// <summary>Gets whether the result contains no error diagnostics.</summary>
    public bool IsValid =>
        Diagnostics.IsDefaultOrEmpty ||
        !Diagnostics.Any(static diagnostic =>
            diagnostic.Severity == ProgramKitDiagnosticSeverity.Error);

    /// <summary>Creates a result from diagnostics while preserving their supplied order.</summary>
    public static ProgramKitValidationResult From(
        IEnumerable<ProgramKitDiagnostic> diagnostics)
    {
        ArgumentNullException.ThrowIfNull(diagnostics);
        return new ProgramKitValidationResult(diagnostics.ToImmutableArray());
    }

    /// <summary>Combines results in the supplied order.</summary>
    public static ProgramKitValidationResult Combine(
        params ProgramKitValidationResult[] results)
    {
        ArgumentNullException.ThrowIfNull(results);

        if (results.Length == 0)
        {
            return Valid;
        }

        var builder = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        foreach (var result in results)
        {
            ArgumentNullException.ThrowIfNull(result);
            builder.AddRange(result.Diagnostics);
        }

        return new ProgramKitValidationResult(builder.MoveToImmutable());
    }
}

/// <summary>Validates cross-field semantics for an immutable Program Kit contract.</summary>
/// <typeparam name="T">The contract type.</typeparam>
public interface IProgramKitSemanticValidator<in T>
{
    /// <summary>Validates <paramref name="value"/> without consulting ambient state.</summary>
    ProgramKitValidationResult Validate(T value);
}

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

    /// <summary>A migration definition violates a migration invariant.</summary>
    public const string InvalidMigrationDefinition = "PKART030";

    /// <summary>A migration assessment violates closure or disposition invariants.</summary>
    public const string InvalidMigrationAssessment = "PKART031";

    /// <summary>A terminal migration disposition and its actions are inconsistent.</summary>
    public const string InvalidMigrationDisposition = "PKART032";

    /// <summary>A schema module or resource descriptor is invalid.</summary>
    public const string InvalidSchemaModule = "PKART040";
}

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
        Error(ArtifactDiagnosticIds.InvalidMigrationDefinition, "Invalid migration definition"),
        Error(ArtifactDiagnosticIds.InvalidMigrationAssessment, "Invalid migration assessment"),
        Error(ArtifactDiagnosticIds.InvalidMigrationDisposition, "Invalid migration disposition"),
        Error(ArtifactDiagnosticIds.InvalidSchemaModule, "Invalid schema module"),
    ];

    private static ProgramKitDiagnosticDefinition Error(string id, string title) =>
        new(id, ProgramKitDiagnosticSeverity.Error, title);
}
