using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Development.Diagnostics;

/// <summary>Stable diagnostic identifiers emitted by Development validators.</summary>
public static class DevelopmentDiagnosticIds
{
    /// <summary>Diagnostic PKDEV001.</summary>
    public const string Pkdev001 = "PKDEV001";
    /// <summary>Diagnostic PKDEV002.</summary>
    public const string Pkdev002 = "PKDEV002";
    /// <summary>Diagnostic PKDEV003.</summary>
    public const string Pkdev003 = "PKDEV003";
    /// <summary>Diagnostic PKDEV004.</summary>
    public const string Pkdev004 = "PKDEV004";
    /// <summary>Diagnostic PKDEV005.</summary>
    public const string Pkdev005 = "PKDEV005";
    /// <summary>Diagnostic PKDEV006.</summary>
    public const string Pkdev006 = "PKDEV006";
    /// <summary>Diagnostic PKDEV007.</summary>
    public const string Pkdev007 = "PKDEV007";
    /// <summary>Diagnostic PKDEV101.</summary>
    public const string Pkdev101 = "PKDEV101";
    /// <summary>Diagnostic PKDEV102.</summary>
    public const string Pkdev102 = "PKDEV102";
    /// <summary>Diagnostic PKDEV103.</summary>
    public const string Pkdev103 = "PKDEV103";
    /// <summary>Diagnostic PKDEV104.</summary>
    public const string Pkdev104 = "PKDEV104";
    /// <summary>Diagnostic PKDEV105.</summary>
    public const string Pkdev105 = "PKDEV105";
    /// <summary>Diagnostic PKDEV106.</summary>
    public const string Pkdev106 = "PKDEV106";
    /// <summary>Diagnostic PKDEV107.</summary>
    public const string Pkdev107 = "PKDEV107";
    /// <summary>Diagnostic PKDEV108.</summary>
    public const string Pkdev108 = "PKDEV108";
    /// <summary>Diagnostic PKDEV201.</summary>
    public const string Pkdev201 = "PKDEV201";
    /// <summary>Diagnostic PKDEV202.</summary>
    public const string Pkdev202 = "PKDEV202";
    /// <summary>Diagnostic PKDEV203.</summary>
    public const string Pkdev203 = "PKDEV203";
    /// <summary>Diagnostic PKDEV204.</summary>
    public const string Pkdev204 = "PKDEV204";
    /// <summary>Diagnostic PKDEV205.</summary>
    public const string Pkdev205 = "PKDEV205";
    /// <summary>Diagnostic PKDEV206.</summary>
    public const string Pkdev206 = "PKDEV206";
    /// <summary>Diagnostic PKDEV207.</summary>
    public const string Pkdev207 = "PKDEV207";
    /// <summary>Diagnostic PKDEV208.</summary>
    public const string Pkdev208 = "PKDEV208";
    /// <summary>Diagnostic PKDEV209.</summary>
    public const string Pkdev209 = "PKDEV209";
    /// <summary>Diagnostic PKDEV301.</summary>
    public const string Pkdev301 = "PKDEV301";
    /// <summary>Diagnostic PKDEV302.</summary>
    public const string Pkdev302 = "PKDEV302";
    /// <summary>Diagnostic PKDEV303.</summary>
    public const string Pkdev303 = "PKDEV303";
    /// <summary>Diagnostic PKDEV304.</summary>
    public const string Pkdev304 = "PKDEV304";
    /// <summary>Diagnostic PKDEV305.</summary>
    public const string Pkdev305 = "PKDEV305";
    /// <summary>Diagnostic PKDEV306.</summary>
    public const string Pkdev306 = "PKDEV306";
    /// <summary>Diagnostic PKDEV307.</summary>
    public const string Pkdev307 = "PKDEV307";

    /// <summary>Gets every owned identifier in stable numeric order.</summary>
    public static ImmutableArray<string> All { get; } =
    [
        Pkdev001, Pkdev002, Pkdev003, Pkdev004, Pkdev005, Pkdev006, Pkdev007,
        Pkdev101, Pkdev102, Pkdev103, Pkdev104, Pkdev105, Pkdev106, Pkdev107, Pkdev108,
        Pkdev201, Pkdev202, Pkdev203, Pkdev204, Pkdev205, Pkdev206, Pkdev207, Pkdev208,
        Pkdev209,
        Pkdev301, Pkdev302, Pkdev303, Pkdev304, Pkdev305, Pkdev306, Pkdev307,
    ];
}
