using System;
using System.Collections.Generic;
using System.Linq;
using Orbyss.ProgramKit.Contracts.Identity;

namespace Orbyss.ProgramKit.Contracts.Operations;

public enum ArtifactOwnership
{
    GeneratedOwned,
    SeededHandoff,
    ConsumerOwned,
}

public enum ClaimClass
{
    CanonicalByte,
    VerifiedEquivalent,
    CustomBounded,
}

public enum SafeValueClassification
{
    Public,
    RepositoryRelative,
    Withheld,
}

public enum SafeValueKind
{
    Text,
    WholeNumber,
    Flag,
    Identity,
    Digest,
    LogicalPath,
    Redacted,
}

public sealed record SafeValue
{
    public SafeValue(
        SafeValueClassification classification,
        SafeValueKind valueKind,
        string? value,
        string? redactionReason = null,
        GovernedIdentity? policyReference = null)
    {
        bool withheld = classification == SafeValueClassification.Withheld;
        if (withheld != (value is null)
            || withheld != !string.IsNullOrWhiteSpace(redactionReason)
            || withheld != (policyReference is not null))
        {
            throw new ArgumentException("Withheld safe values require no value and require exact redaction reason and policy reference; visible values require only a bounded value.");
        }

        if (value?.Length > 500)
        {
            throw new ArgumentOutOfRangeException(nameof(value), "Safe diagnostic values are bounded to 500 characters.");
        }

        Classification = classification;
        ValueKind = valueKind;
        Value = value;
        RedactionReason = redactionReason;
        PolicyReference = policyReference;
    }

    public SafeValueClassification Classification { get; }

    public SafeValueKind ValueKind { get; }

    public string? Value { get; }

    public string? RedactionReason { get; }

    public GovernedIdentity? PolicyReference { get; }
}

public sealed record ArtifactReference(
    GovernedIdentity Identity,
    string MediaType,
    string LogicalPath,
    string Digest,
    ArtifactOwnership Ownership);

public sealed record TraceReference(
    ArtifactReference Source,
    string DocumentPointer,
    string ClaimKind);

public sealed record ExactSelection(
    string Role,
    GovernedIdentity Selected,
    GovernedIdentity SelectionAuthority,
    TraceReference? Trace = null);

public sealed record EvaluationContext(
    DateTimeOffset Instant,
    GovernedIdentity Source,
    string Assurance);

public sealed record EvidenceReference(
    GovernedIdentity Identity,
    GovernedIdentity Subject,
    GovernedIdentity Profile,
    ArtifactReference Artifact,
    string Freshness);

public sealed record PolicyWaiver
{
    public PolicyWaiver(
        GovernedIdentity identity,
        GovernedIdentity authority,
        IReadOnlyList<GovernedIdentity> rules,
        IReadOnlyList<GovernedIdentity> subjects,
        PublicCommand operation,
        GovernedIdentity profile,
        RequestedEffect maximumEffect,
        SafeValue risk,
        IReadOnlyList<SafeValue> controls,
        IReadOnlyList<EvidenceReference> evidence,
        ArtifactReference revocationRecord,
        DateTimeOffset expiresAt)
    {
        if (rules.Count == 0 || subjects.Count == 0 || controls.Count == 0 || evidence.Count == 0
            || rules.Concat(subjects).Any(static item => item.Name.Contains('*', StringComparison.Ordinal))
            || expiresAt == DateTimeOffset.MaxValue)
        {
            throw new ArgumentException("A waiver requires finite exact rules, subjects, controls, evidence, revocation, and expiry; wildcards and non-expiring waivers are invalid.");
        }

        Identity = identity;
        Authority = authority;
        Rules = rules;
        Subjects = subjects;
        Operation = operation;
        Profile = profile;
        MaximumEffect = maximumEffect;
        Risk = risk;
        Controls = controls;
        Evidence = evidence;
        RevocationRecord = revocationRecord;
        ExpiresAt = expiresAt;
    }

    public GovernedIdentity Identity { get; }
    public GovernedIdentity Authority { get; }
    public IReadOnlyList<GovernedIdentity> Rules { get; }
    public IReadOnlyList<GovernedIdentity> Subjects { get; }
    public PublicCommand Operation { get; }
    public GovernedIdentity Profile { get; }
    public RequestedEffect MaximumEffect { get; }
    public SafeValue Risk { get; }
    public IReadOnlyList<SafeValue> Controls { get; }
    public IReadOnlyList<EvidenceReference> Evidence { get; }
    public ArtifactReference RevocationRecord { get; }
    public DateTimeOffset ExpiresAt { get; }
}

public sealed record GateResult
{
    public GateResult(
        GovernedIdentity gate,
        string mode,
        string status,
        IReadOnlyList<GovernedIdentity> subjects,
        IReadOnlyList<EvidenceReference> evidence,
        IReadOnlyList<string> diagnosticIds,
        PolicyWaiver? waiver = null)
    {
        if (string.Equals(status, "waived", StringComparison.Ordinal) != (waiver is not null))
        {
            throw new ArgumentException("A waived gate requires one exact waiver, and a non-waived gate cannot carry one.");
        }

        Gate = gate;
        Mode = mode;
        Status = status;
        Subjects = subjects;
        Evidence = evidence;
        DiagnosticIds = diagnosticIds;
        Waiver = waiver;
    }

    public GovernedIdentity Gate { get; }
    public string Mode { get; }
    public string Status { get; }
    public IReadOnlyList<GovernedIdentity> Subjects { get; }
    public IReadOnlyList<EvidenceReference> Evidence { get; }
    public IReadOnlyList<string> DiagnosticIds { get; }
    public PolicyWaiver? Waiver { get; }
}
