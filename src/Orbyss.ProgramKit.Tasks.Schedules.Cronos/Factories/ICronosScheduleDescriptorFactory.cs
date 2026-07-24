using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Descriptors;

namespace Orbyss.ProgramKit.Tasks.Schedules.Cronos.Factories;

/// <summary>Creates validated cronos/0.13 descriptors with bound zone evidence.</summary>
public interface ICronosScheduleDescriptorFactory
{
    /// <summary>Creates one exact descriptor from explicit selection inputs.</summary>
    CronosScheduleDescriptor Create(
        string expression,
        CronosScheduleFormat format,
        int? stableJitterSeed,
        string timeZoneId,
        ArtifactReference profile,
        string timeZoneDataSource,
        string timeZoneDataVersion,
        DateTimeOffset horizonStart,
        DateTimeOffset horizonEnd);
}
