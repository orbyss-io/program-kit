using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.Tasks.Schedules.Calculation;

internal static class ScheduleOccurrenceFactory
{
    internal static TaskOccurrence Create(
        TaskScheduleDefinition schedule,
        long sequence,
        DateTimeOffset scheduledFor,
        DateTimeOffset evaluatedAt)
    {
        var stableBytes = Encoding.UTF8.GetBytes(
            string.Join(
                "\n",
                schedule.Revision.Identity.Value,
                schedule.Revision.Version.Value,
                schedule.Revision.Digest.Value,
                sequence.ToString(CultureInfo.InvariantCulture),
                scheduledFor.UtcTicks.ToString(CultureInfo.InvariantCulture)));
        var hash = Convert.ToHexString(SHA256.HashData(stableBytes))
            .ToLowerInvariant();
        return new TaskOccurrence(
            new ArtifactReference(
                ProgramKitIdentifier.Parse(
                    string.Concat(
                        "pkid:task-occurrence:program-kit:",
                        hash)),
                schedule.Revision.Version,
                Sha256Digest.Parse(string.Concat("sha256:", hash))),
            schedule.Revision,
            schedule.DefinitionRevision,
            schedule.DescriptorRevision,
            schedule.OccurrenceCalculatorProfile,
            sequence,
            scheduledFor,
            evaluatedAt);
    }
}
