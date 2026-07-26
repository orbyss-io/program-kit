namespace Orbyss.ProgramKit.DevContainers.Contracts.Diagnostics;

/// <summary>Stable diagnostics for deterministic Dev Container generation.</summary>
public static class DevContainerDiagnosticIds
{
    /// <summary>The selected construction profile is invalid.</summary>
    public const string InvalidProfile = "PKDC001";

    /// <summary>A generated or referenced path is unsafe or ambiguous.</summary>
    public const string UnsafePath = "PKDC002";

    /// <summary>A feature is not exact, pinned, or structurally safe.</summary>
    public const string InvalidFeature = "PKDC003";

    /// <summary>A mount, port, user, or lifecycle declaration is invalid.</summary>
    public const string InvalidComposition = "PKDC004";

    /// <summary>Opaque content is unbound, secret-bearing, or not safe text.</summary>
    public const string UnsafeOpaqueContent = "PKDC005";

    /// <summary>Deterministic artifact generation failed.</summary>
    public const string GenerationFailure = "PKDC006";
}
