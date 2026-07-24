using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Descriptors;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Evidence;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.TimeZones;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Validation;

namespace Orbyss.ProgramKit.Tasks.Schedules.Cronos.Factories;

/// <summary>Default evidence-binding cronos/0.13 descriptor factory.</summary>
public sealed class CronosScheduleDescriptorFactory :
    ICronosScheduleDescriptorFactory
{
    /// <inheritdoc />
    public CronosScheduleDescriptor Create(
        string expression,
        CronosScheduleFormat format,
        int? stableJitterSeed,
        string timeZoneId,
        ArtifactReference profile,
        string timeZoneDataSource,
        string timeZoneDataVersion,
        DateTimeOffset horizonStart,
        DateTimeOffset horizonEnd)
    {
        ArgumentNullException.ThrowIfNull(profile);
        var zone = TimeZoneInfo.FindSystemTimeZoneById(timeZoneId);
        var evidence = new CronosTimeZoneSelectionEvidence(
            timeZoneDataSource,
            timeZoneDataVersion,
            horizonStart,
            horizonEnd,
            CronosTimeZoneRuleFingerprint.Compute(
                zone,
                timeZoneDataSource,
                timeZoneDataVersion,
                horizonStart,
                horizonEnd));
        var descriptor = new CronosScheduleDescriptor(
            expression,
            format,
            stableJitterSeed,
            timeZoneId,
            profile,
            evidence);
        _ = CronosDescriptorGuard.Validate(descriptor);
        return descriptor;
    }
}
