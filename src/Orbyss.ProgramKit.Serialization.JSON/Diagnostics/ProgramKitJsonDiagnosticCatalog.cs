using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;

namespace Orbyss.ProgramKit.Serialization.Json.Diagnostics;

/// <summary>The immutable Serialization.JSON diagnostic catalog.</summary>
public static class ProgramKitJsonDiagnosticCatalog
{
    /// <summary>Gets definitions ordered by stable identifier.</summary>
    public static ImmutableArray<ProgramKitDiagnosticDefinition> Definitions { get; } =
    [
        Error(ProgramKitJsonDiagnosticIds.InvalidProfile, "Invalid JSON profile"),
        Error(ProgramKitJsonDiagnosticIds.RegistryFrozen, "JSON registry is frozen"),
        Error(ProgramKitJsonDiagnosticIds.UnknownProfile, "Unknown JSON profile"),
        Error(ProgramKitJsonDiagnosticIds.InvalidContribution, "Invalid JSON contribution"),
        Error(ProgramKitJsonDiagnosticIds.ContributionConflict, "JSON contribution conflict"),
        Error(ProgramKitJsonDiagnosticIds.OrderingGap, "JSON contribution ordering gap"),
        Error(ProgramKitJsonDiagnosticIds.OrderingCycle, "JSON contribution ordering cycle"),
        Error(ProgramKitJsonDiagnosticIds.RevisionDigestConflict, "JSON revision digest conflict"),
        Error(ProgramKitJsonDiagnosticIds.TypeMetadataUnavailable, "JSON type metadata unavailable"),
        Error(ProgramKitJsonDiagnosticIds.InvalidJson, "Invalid strict JSON"),
        Error(ProgramKitJsonDiagnosticIds.DuplicateMemberName, "Duplicate JSON member name"),
        Error(ProgramKitJsonDiagnosticIds.InvalidUnicode, "Invalid JSON Unicode"),
        Error(ProgramKitJsonDiagnosticIds.NonCanonicalUnicode, "Non-canonical JSON Unicode"),
        Error(ProgramKitJsonDiagnosticIds.InvalidNumber, "Invalid strict JCS number"),
        Error(ProgramKitJsonDiagnosticIds.ByteLimitExceeded, "JSON byte limit exceeded"),
        Error(ProgramKitJsonDiagnosticIds.DepthLimitExceeded, "JSON depth limit exceeded"),
        Error(ProgramKitJsonDiagnosticIds.TokenLimitExceeded, "JSON token limit exceeded"),
        Error(ProgramKitJsonDiagnosticIds.MemberLimitExceeded, "JSON member limit exceeded"),
        Error(
            ProgramKitJsonDiagnosticIds.MemberBufferLimitExceeded,
            "JSON member buffer limit exceeded"),
        Error(ProgramKitJsonDiagnosticIds.NonExtensibleProfile, "JSON profile is non-extensible"),
        Error(ProgramKitJsonDiagnosticIds.NullModel, "JSON model was null"),
    ];

    private static ProgramKitDiagnosticDefinition Error(string id, string title) =>
        new(id, ProgramKitDiagnosticSeverity.Error, title);
}
