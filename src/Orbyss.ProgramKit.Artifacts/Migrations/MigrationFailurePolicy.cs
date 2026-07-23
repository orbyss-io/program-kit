using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Migrations;

/// <summary>The behavior required when a migration cannot complete.</summary>
public enum MigrationFailurePolicy
{
    /// <summary>Fail before writing a target value.</summary>
    FailBeforeWrite,

    /// <summary>Roll back target writes atomically.</summary>
    AtomicRollback,

    /// <summary>Preserve the source, reject the target, and report the failure.</summary>
    PreserveSourceAndReport,
}
