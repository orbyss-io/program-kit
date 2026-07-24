namespace Orbyss.ProgramKit.Tasks.Schedules.Cronos.Descriptors;

/// <summary>Explicit selected Cronos field format.</summary>
public enum CronosScheduleFormat
{
    /// <summary>Five-field minute precision.</summary>
    Standard,
    /// <summary>Six-field format including seconds.</summary>
    IncludeSeconds,
}
