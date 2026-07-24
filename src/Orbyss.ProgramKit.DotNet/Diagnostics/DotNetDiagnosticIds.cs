namespace Orbyss.ProgramKit.DotNet.Diagnostics;

/// <summary>Stable diagnostics emitted by the .NET Program Kit.</summary>
public static class DotNetDiagnosticIds
{
    /// <summary>The shell document is structurally or semantically invalid.</summary>
    public const string InvalidShell = "PKNET001";

    /// <summary>An exact artifact input is missing, stale, or unsafe.</summary>
    public const string InvalidArtifactInput = "PKNET002";

    /// <summary>A requested host is absent, ambiguous, or kind-incompatible.</summary>
    public const string InvalidHostSelection = "PKNET003";

    /// <summary>A generated host lock is incomplete or inconsistent.</summary>
    public const string InvalidHostLock = "PKNET004";

    /// <summary>Health exposure is unsafe or internally inconsistent.</summary>
    public const string InvalidHealthConfiguration = "PKNET005";

    /// <summary>An integrator document descriptor is inconsistent.</summary>
    public const string InvalidIntegratorDocument = "PKNET006";

    /// <summary>Generation could not produce the declared deterministic output.</summary>
    public const string GenerationFailed = "PKNET007";
}
