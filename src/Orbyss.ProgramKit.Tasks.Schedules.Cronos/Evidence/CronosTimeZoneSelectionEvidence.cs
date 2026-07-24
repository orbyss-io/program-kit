using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Tasks.Schedules.Cronos.Evidence;

/// <summary>Bounded environment and timezone-rule selection evidence.</summary>
public sealed record CronosTimeZoneSelectionEvidence(
    string DataSource,
    string DataVersion,
    DateTimeOffset HorizonStart,
    DateTimeOffset HorizonEnd,
    Sha256Digest ZoneRuleFingerprint);
