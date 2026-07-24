namespace Orbyss.ProgramKit.Tasks.Diagnostics;

/// <summary>Stable diagnostics owned by task composition and coordination.</summary>
public static class TaskDiagnosticIds
{
    /// <summary>A registration is structurally invalid.</summary>
    public const string InvalidRegistration = "PKTAS001";
    /// <summary>The same stable identity has conflicting exact registrations.</summary>
    public const string ConflictingRegistration = "PKTAS002";
    /// <summary>A required definition, handler, feature, or calculator is missing.</summary>
    public const string MissingRegistrationDependency = "PKTAS003";
    /// <summary>A handler does not support the selected definition revision.</summary>
    public const string IncompatibleHandler = "PKTAS004";
    /// <summary>Middleware ordering contains an unknown identity or cycle.</summary>
    public const string InvalidMiddlewareOrder = "PKTAS005";
    /// <summary>The task registry is accessed before it freezes.</summary>
    public const string RegistryNotFrozen = "PKTAS006";
    /// <summary>A registration was attempted after registry freeze.</summary>
    public const string RegistrationAfterFreeze = "PKTAS007";
    /// <summary>A task activation could not be resolved exactly.</summary>
    public const string ActivationResolutionFailed = "PKTAS008";
}
