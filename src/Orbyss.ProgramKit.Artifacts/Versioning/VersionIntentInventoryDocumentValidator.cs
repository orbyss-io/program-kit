using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Validates a closed explicit version-intent inventory.</summary>
public sealed class VersionIntentInventoryDocumentValidator :
    IProgramKitSemanticValidator<VersionIntentInventoryDocument>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(VersionIntentInventoryDocument value)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionIntentInventory,
                "A version-intent inventory is required.",
                string.Empty);
            return diagnostics.ToResult();
        }

        if (!IsNormalizedPath(value.RepositoryRoot, allowDot: true))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionIntentInventory,
                "The repository root must be a normalized relative path or '.'.",
                "/repositoryRoot");
        }

        ValidateSourceRoots(value.SourceRoots, diagnostics);
        ValidateEntries(value, diagnostics);
        DefaultArtifactEnvelopeValidator.ValidateReferences(
            value.CompletenessEvidence,
            "/completenessEvidence",
            expectedKind: null,
            requireAtLeastOne: true,
            ArtifactDiagnosticIds.InvalidVersionIntentInventory,
            diagnostics);
        return diagnostics.ToResult();
    }

    private static void ValidateSourceRoots(
        ImmutableArray<string> roots,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (roots.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionIntentInventory,
                "At least one finite source root is required.",
                "/sourceRoots");
            return;
        }

        var seen = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < roots.Length; index++)
        {
            var path = string.Concat("/sourceRoots/", index);
            if (!IsNormalizedPath(roots[index], allowDot: true) ||
                !seen.Add(roots[index]))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionIntentInventory,
                    "Source roots must be unique normalized relative paths.",
                    path);
            }
        }
    }

    private static void ValidateEntries(
        VersionIntentInventoryDocument inventory,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (inventory.Entries.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionIntentInventory,
                "At least one classified version-bearing source is required.",
                "/entries");
            return;
        }

        var paths = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < inventory.Entries.Length; index++)
        {
            var entry = inventory.Entries[index];
            var path = string.Concat("/entries/", index);
            if (entry is null)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionIntentInventory,
                    "A version-intent inventory entry is required.",
                    path);
                continue;
            }

            diagnostics.Add(ProgramKitIdentifier.Validate(
                entry.Identity.Value,
                ArtifactReferenceValidator.Path(path, "identity")));
            diagnostics.Add(ProgramKitIdentifier.Validate(
                entry.OwnerId.Value,
                ArtifactReferenceValidator.Path(path, "ownerId")));
            diagnostics.Add(Sha256Digest.Validate(
                entry.SourceDigest.Value,
                ArtifactReferenceValidator.Path(path, "sourceDigest")));
            if (!IsNormalizedPath(entry.SourcePath, allowDot: false) ||
                !paths.Add(entry.SourcePath))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionIntentInventory,
                    "Entry paths must be unique normalized repository-relative paths.",
                    ArtifactReferenceValidator.Path(path, "sourcePath"));
            }

            if (!IsWithinAnyRoot(entry.SourcePath, inventory.SourceRoots))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionIntentInventory,
                    "Every entry path must be contained by an explicit source root.",
                    ArtifactReferenceValidator.Path(path, "sourcePath"));
            }

            if (string.IsNullOrWhiteSpace(entry.CurrentValue) ||
                !Enum.IsDefined(entry.Intent) ||
                !Enum.IsDefined(entry.TransitionDisposition))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionIntentInventory,
                    "Every entry requires non-empty current text and defined intent and disposition.",
                    path);
                continue;
            }

            ValidateIntent(entry, path, diagnostics);
        }
    }

    private static void ValidateIntent(
        VersionIntentInventoryEntry entry,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var valid = entry.Intent switch
        {
            VersionIntent.ProductRelease =>
                entry.IsActive &&
                entry.OwnedRevisionOrdinal is null &&
                entry.TransitionDisposition ==
                    VersionTransitionDisposition.CoordinateProductRelease &&
                SemanticVersion.TryParse(entry.CurrentValue, out _),
            VersionIntent.OwnedArtifactRevision =>
                entry.IsActive &&
                entry.OwnedRevisionOrdinal is > 0 &&
                entry.TransitionDisposition ==
                    VersionTransitionDisposition.MigrateOwnedRevision &&
                SemanticVersion.TryParse(entry.CurrentValue, out _),
            VersionIntent.ExternalSelection =>
                entry.OwnedRevisionOrdinal is null &&
                entry.TransitionDisposition ==
                    VersionTransitionDisposition.PreserveExternalSelection,
            VersionIntent.HistoricalEvidenceRevision =>
                !entry.IsActive &&
                entry.OwnedRevisionOrdinal is null &&
                entry.TransitionDisposition ==
                    VersionTransitionDisposition.PreserveHistoricalEvidence,
            VersionIntent.FixtureRevision =>
                entry.OwnedRevisionOrdinal is null &&
                entry.TransitionDisposition ==
                    VersionTransitionDisposition.PreserveFixture,
            _ => false,
        };
        if (!valid)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionIntentInventory,
                "Intent, active state, owned ordinal, version text, and transition disposition are contradictory.",
                path);
        }
    }

    private static bool IsWithinAnyRoot(
        string path,
        ImmutableArray<string> roots) =>
        roots.Any(root =>
            string.Equals(root, ".", StringComparison.Ordinal) ||
            string.Equals(path, root, StringComparison.Ordinal) ||
            path.StartsWith(
                string.Concat(root, "/"),
                StringComparison.Ordinal));

    private static bool IsNormalizedPath(string? path, bool allowDot)
    {
        if (string.IsNullOrWhiteSpace(path) ||
            path.Contains('\\') ||
            path.Contains(':') ||
            path.StartsWith('/') ||
            path.EndsWith('/'))
        {
            return false;
        }

        if (allowDot && string.Equals(path, ".", StringComparison.Ordinal))
        {
            return true;
        }

        return path
            .Split('/', StringSplitOptions.None)
            .All(static segment =>
                segment.Length > 0 &&
                !string.Equals(segment, ".", StringComparison.Ordinal) &&
                !string.Equals(segment, "..", StringComparison.Ordinal));
    }
}
