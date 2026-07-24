using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Evidence;

namespace Orbyss.ProgramKit.Tasks.Schedules.Cronos.Descriptors;

/// <summary>Exact typed cron schedule intent for the cronos/0.13 dialect.</summary>
public sealed record CronosScheduleDescriptor(
    string Expression,
    CronosScheduleFormat Format,
    int? StableJitterSeed,
    string TimeZoneId,
    ArtifactReference Profile,
    CronosTimeZoneSelectionEvidence TimeZoneEvidence);
