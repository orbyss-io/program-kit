namespace Orbyss.ProgramKit.Workbench.Operations.Versioning;

/// <summary>Default pure validator for policy-bound alpha ordinal proposals.</summary>
public sealed class AlphaVersionProgressionValidator :
    IAlphaVersionProgressionValidator
{
    private readonly IProgramKitSemanticValidator<AlphaVersionProgressionDocument>
        documentValidator;

    /// <summary>Initializes the validator with contract-owned structural validation.</summary>
    public AlphaVersionProgressionValidator(
        IProgramKitSemanticValidator<AlphaVersionProgressionDocument>
            documentValidator)
    {
        this.documentValidator = documentValidator ??
            throw new ArgumentNullException(nameof(documentValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(
        AlphaVersionProgressionDocument document)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.AddRange(documentValidator.Validate(document).Diagnostics);
        if (diagnostics.Count != 0 ||
            document?.Policy is null ||
            document.Proposal is null)
        {
            return ProgramKitValidationResult.From(diagnostics);
        }

        var proposal = document.Proposal;
        if (proposal.Intent != VersionIntent.OwnedArtifactRevision)
        {
            diagnostics.Add(Failure(
                "Alpha ordinal progression applies only to an explicitly owned artifact revision.",
                "/proposal/intent"));
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (proposal.CurrentVersion is null)
        {
            ValidateNewIdentity(document.Policy, proposal, diagnostics);
        }
        else
        {
            ValidateExistingIdentity(document.Policy, proposal, diagnostics);
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateNewIdentity(
        AlphaVersionProgressionPolicy policy,
        AlphaVersionProgressionProposal proposal,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var expected = ExpectedVersion(policy, policy.InitialOrdinal);
        if (!string.Equals(
                proposal.ProposedVersion.Value,
                expected,
                StringComparison.Ordinal) ||
            !proposal.CanonicalBytesChanged ||
            proposal.CompatibilityDisposition !=
                VersionCompatibilityDisposition.NewIdentity ||
            proposal.MigrationDisposition !=
                VersionMigrationDisposition.NotRequired ||
            !proposal.MigrationReferences.IsDefaultOrEmpty)
        {
            diagnostics.Add(Failure(
                "A new identity must explicitly propose the initial alpha ordinal, new-identity compatibility, changed bytes, and no migration.",
                "/proposal"));
        }
    }

    private static void ValidateExistingIdentity(
        AlphaVersionProgressionPolicy policy,
        AlphaVersionProgressionProposal proposal,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var currentOrdinal = proposal.CurrentOrdinal!.Value;
        var expectedCurrent = ExpectedVersion(policy, currentOrdinal);
        if (!string.Equals(
                proposal.CurrentVersion!.Value.Value,
                expectedCurrent,
                StringComparison.Ordinal))
        {
            diagnostics.Add(Failure(
                "The current version must match its explicit ordinal under the selected policy.",
                "/proposal/currentVersion"));
            return;
        }

        if (!proposal.CanonicalBytesChanged)
        {
            ValidateUnchanged(proposal, diagnostics);
            return;
        }

        if (currentOrdinal > int.MaxValue - policy.OrdinalStep)
        {
            diagnostics.Add(Failure(
                "The next alpha ordinal exceeds the supported integer range.",
                "/proposal/currentOrdinal"));
            return;
        }

        var expectedNext = ExpectedVersion(
            policy,
            currentOrdinal + policy.OrdinalStep);
        if (!string.Equals(
                proposal.ProposedVersion.Value,
                expectedNext,
                StringComparison.Ordinal) ||
            proposal.ProposedDigest == proposal.CurrentDigest!.Value ||
            proposal.CompatibilityDisposition is
                VersionCompatibilityDisposition.NewIdentity or
                VersionCompatibilityDisposition.Unchanged)
        {
            diagnostics.Add(Failure(
                "Changed canonical bytes must use the next alpha ordinal, a new digest, and an explicit compatible or incompatible classification.",
                "/proposal"));
        }

        ValidateMigration(proposal, diagnostics);
    }

    private static void ValidateUnchanged(
        AlphaVersionProgressionProposal proposal,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (proposal.ProposedVersion != proposal.CurrentVersion!.Value ||
            proposal.ProposedDigest != proposal.CurrentDigest!.Value ||
            proposal.CompatibilityDisposition !=
                VersionCompatibilityDisposition.Unchanged ||
            proposal.MigrationDisposition !=
                VersionMigrationDisposition.NotRequired ||
            !proposal.MigrationReferences.IsDefaultOrEmpty)
        {
            diagnostics.Add(Failure(
                "Unchanged canonical bytes must retain the exact version and digest and cannot claim migration.",
                "/proposal"));
        }
    }

    private static void ValidateMigration(
        AlphaVersionProgressionProposal proposal,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (proposal.CompatibilityDisposition ==
                VersionCompatibilityDisposition.Incompatible &&
            proposal.MigrationDisposition !=
                VersionMigrationDisposition.Required)
        {
            diagnostics.Add(Failure(
                "An incompatible changed revision requires an explicit migration.",
                "/proposal/migrationDisposition"));
        }

        var hasMigrations = !proposal.MigrationReferences.IsDefaultOrEmpty;
        var migrationRequired = proposal.MigrationDisposition ==
            VersionMigrationDisposition.Required;
        if (migrationRequired != hasMigrations)
        {
            diagnostics.Add(Failure(
                "Migration references must be present exactly when migration is required.",
                "/proposal/migrationReferences"));
        }
    }

    private static string ExpectedVersion(
        AlphaVersionProgressionPolicy policy,
        int ordinal) =>
        string.Concat(
            policy.CoreVersion.Value,
            "-",
            policy.PrereleaseLabel,
            ".",
            ordinal.ToString(System.Globalization.CultureInfo.InvariantCulture));

    private static ProgramKitDiagnostic Failure(
        string message,
        string path) =>
        WorkbenchDiagnostics.Error(
            WorkbenchDiagnosticIds.InvalidAlphaVersionProgressionProposal,
            message,
            path);
}
