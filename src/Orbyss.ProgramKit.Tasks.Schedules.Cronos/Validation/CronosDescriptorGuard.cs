using Cronos;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Descriptors;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.TimeZones;

namespace Orbyss.ProgramKit.Tasks.Schedules.Cronos.Validation;

internal static class CronosDescriptorGuard
{
    internal static TimeZoneInfo Validate(CronosScheduleDescriptor descriptor)
    {
        ArgumentNullException.ThrowIfNull(descriptor);
        if (string.IsNullOrWhiteSpace(descriptor.Expression) ||
            string.IsNullOrWhiteSpace(descriptor.TimeZoneId) ||
            descriptor.TimeZoneEvidence.HorizonStart >=
                descriptor.TimeZoneEvidence.HorizonEnd)
        {
            throw new ArgumentException(
                "A Cronos descriptor requires expression, timezone, and bounded evidence.",
                nameof(descriptor));
        }

        _ = Parse(descriptor);
        var zone = TimeZoneInfo.FindSystemTimeZoneById(descriptor.TimeZoneId);
        var actual = CronosTimeZoneRuleFingerprint.Compute(
            zone,
            descriptor.TimeZoneEvidence.DataSource,
            descriptor.TimeZoneEvidence.DataVersion,
            descriptor.TimeZoneEvidence.HorizonStart,
            descriptor.TimeZoneEvidence.HorizonEnd);
        if (actual != descriptor.TimeZoneEvidence.ZoneRuleFingerprint)
        {
            throw new InvalidOperationException(
                "The selected timezone rules do not match the descriptor fingerprint; a new provider selection and migration assessment are required.");
        }

        return zone;
    }

    internal static CronExpression Parse(CronosScheduleDescriptor descriptor)
    {
        var format = descriptor.Format switch
        {
            CronosScheduleFormat.Standard => CronFormat.Standard,
            CronosScheduleFormat.IncludeSeconds => CronFormat.IncludeSeconds,
            _ => throw new ArgumentOutOfRangeException(
                nameof(descriptor),
                "The Cronos format selection is invalid."),
        };
        return descriptor.StableJitterSeed is { } seed
            ? CronExpression.Parse(descriptor.Expression, format, seed)
            : CronExpression.Parse(descriptor.Expression, format);
    }
}
