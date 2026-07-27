using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Diagnostics;

/// <summary>Stable Program Kit C# build-gate mechanics diagnostics.</summary>
public static class CSharpBuildGateDiagnosticIds
{
    /// <summary>Missing or unsupported contract.</summary>
    public const string Pkcg001 = "PKCG001";
    /// <summary>Unstable, duplicate, or missing finite collection.</summary>
    public const string Pkcg002 = "PKCG002";
    /// <summary>Invalid semantic ownership.</summary>
    public const string Pkcg003 = "PKCG003";
    /// <summary>Reserved or colliding diagnostic identity.</summary>
    public const string Pkcg004 = "PKCG004";
    /// <summary>Invalid analyzer artifact selection.</summary>
    public const string Pkcg005 = "PKCG005";
    /// <summary>Invalid exact path or inventory.</summary>
    public const string Pkcg006 = "PKCG006";
    /// <summary>Invalid rule, profile, or component relationship.</summary>
    public const string Pkcg007 = "PKCG007";
    /// <summary>Invalid activation matrix.</summary>
    public const string Pkcg008 = "PKCG008";
    /// <summary>Invalid temporary exception.</summary>
    public const string Pkcg009 = "PKCG009";
    /// <summary>Invalid or unreconciled suppression.</summary>
    public const string Pkcg010 = "PKCG010";
    /// <summary>Invalid selection lock.</summary>
    public const string Pkcg011 = "PKCG011";
    /// <summary>Invalid receipt or verification evidence.</summary>
    public const string Pkcg012 = "PKCG012";
    /// <summary>Invalid assurance, compatibility, migration, or budget.</summary>
    public const string Pkcg013 = "PKCG013";

    /// <summary>All mechanics identifiers in stable order.</summary>
    public static ImmutableArray<string> All { get; } =
    [
        Pkcg001,
        Pkcg002,
        Pkcg003,
        Pkcg004,
        Pkcg005,
        Pkcg006,
        Pkcg007,
        Pkcg008,
        Pkcg009,
        Pkcg010,
        Pkcg011,
        Pkcg012,
        Pkcg013,
    ];
}
