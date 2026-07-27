using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Tasks.Schedules.Cronos.TimeZones;

internal static class CronosTimeZoneRuleFingerprint
{
    internal static Sha256Digest Compute(
        TimeZoneInfo zone,
        string dataSource,
        string dataVersion,
        DateTimeOffset horizonStart,
        DateTimeOffset horizonEnd)
    {
        ArgumentNullException.ThrowIfNull(zone);
        if (string.IsNullOrWhiteSpace(dataSource) ||
            string.IsNullOrWhiteSpace(dataVersion) ||
            horizonStart >= horizonEnd)
        {
            throw new ArgumentException(
                "Timezone evidence requires a source, version, and positive bounded horizon.");
        }

        var builder = new StringBuilder();
        builder
            .Append(zone.Id).Append('\n')
            .Append(dataSource).Append('\n')
            .Append(dataVersion).Append('\n')
            .Append(horizonStart.UtcTicks.ToString(CultureInfo.InvariantCulture))
            .Append('\n')
            .Append(horizonEnd.UtcTicks.ToString(CultureInfo.InvariantCulture))
            .Append('\n')
            .Append(zone.BaseUtcOffset.Ticks.ToString(CultureInfo.InvariantCulture))
            .Append('\n')
            .Append(zone.SupportsDaylightSavingTime ? "1" : "0");
        foreach (var rule in zone.GetAdjustmentRules()
                     .Where(rule =>
                         rule.DateEnd >= horizonStart.Date &&
                         rule.DateStart <= horizonEnd.Date)
                     .OrderBy(static rule => rule.DateStart))
        {
            builder
                .Append('\n').Append(rule.DateStart.ToString("O", CultureInfo.InvariantCulture))
                .Append('|').Append(rule.DateEnd.ToString("O", CultureInfo.InvariantCulture))
                .Append('|').Append(rule.DaylightDelta.Ticks.ToString(CultureInfo.InvariantCulture))
                .Append('|').Append(Transition(rule.DaylightTransitionStart))
                .Append('|').Append(Transition(rule.DaylightTransitionEnd))
                .Append('|').Append(rule.BaseUtcOffsetDelta.Ticks.ToString(CultureInfo.InvariantCulture));
        }

        return Sha256Digest.Parse(
            string.Concat(
                "sha256:",
                Convert.ToHexStringLower(
                    SHA256.HashData(
                        Encoding.UTF8.GetBytes(builder.ToString())))));
    }

    private static string Transition(TimeZoneInfo.TransitionTime value) =>
        string.Join(
            ",",
            value.IsFixedDateRule ? "fixed" : "floating",
            value.Month.ToString(CultureInfo.InvariantCulture),
            value.Week.ToString(CultureInfo.InvariantCulture),
            value.Day.ToString(CultureInfo.InvariantCulture),
            ((int)value.DayOfWeek).ToString(CultureInfo.InvariantCulture),
            value.TimeOfDay.TimeOfDay.Ticks.ToString(CultureInfo.InvariantCulture));
}
