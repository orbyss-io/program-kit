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

    /// <summary>An exact configuration provider or generator is not registered.</summary>
    public const string UnknownConfigurationProvider = "PKNET008";

    /// <summary>A provider cannot satisfy the selected reload declaration.</summary>
    public const string UnsupportedProviderReload = "PKNET009";

    /// <summary>A provider package does not match the exact catalog closure.</summary>
    public const string ConfigurationProviderPackageMismatch = "PKNET010";

    /// <summary>Configuration provider selections duplicate or conflict.</summary>
    public const string ConfigurationProviderConflict = "PKNET011";

    /// <summary>Telemetry composition is unsafe, ambiguous, or unsupported.</summary>
    public const string InvalidTelemetryConfiguration = "PKNET012";

    /// <summary>A telemetry package does not match the exact reviewed selection.</summary>
    public const string TelemetryPackageMismatch = "PKNET013";

    /// <summary>Telemetry would duplicate framework instrumentation.</summary>
    public const string DuplicateTelemetryInstrumentation = "PKNET014";

    /// <summary>Telemetry could disclose sensitive or unbounded data.</summary>
    public const string UnsafeTelemetryData = "PKNET015";
}
