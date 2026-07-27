namespace Orbyss.ProgramKit.Operations.Contracts.Diagnostics;

/// <summary>Stable diagnostics emitted by Operations validators.</summary>
public static class OperationsDiagnosticIds
{
    /// <summary>An exact artifact reference is invalid.</summary>
    public const string InvalidReference = "PKOPS001";
    /// <summary>An exact reference has the wrong semantic kind.</summary>
    public const string InvalidReferenceKind = "PKOPS002";
    /// <summary>An exact registration occurs more than once.</summary>
    public const string DuplicateRegistration = "PKOPS003";
    /// <summary>A required value is absent.</summary>
    public const string MissingRequiredValue = "PKOPS004";
    /// <summary>An enum value is outside its closed set.</summary>
    public const string InvalidEnumValue = "PKOPS005";
    /// <summary>An explicit catalog relation does not close.</summary>
    public const string CatalogClosureFailure = "PKOPS006";
    /// <summary>Competing registrations claim one stable identity.</summary>
    public const string ConflictingRegistration = "PKOPS007";
    /// <summary>Declared mechanical policies are inconsistent.</summary>
    public const string InvalidPolicyCombination = "PKOPS008";
    /// <summary>Invocation carriage does not match its descriptor.</summary>
    public const string InvalidInvocation = "PKOPS009";
    /// <summary>Result carriage does not match its descriptor.</summary>
    public const string InvalidResult = "PKOPS010";
    /// <summary>Progress carriage does not match bounded progress policy.</summary>
    public const string InvalidProgress = "PKOPS011";
    /// <summary>A transport-failure contract is unsafe or inconsistent.</summary>
    public const string InvalidTransportFailure = "PKOPS012";

    /// <summary>Gets every owned diagnostic identifier in stable order.</summary>
    public static ImmutableArray<string> All { get; } =
    [
        InvalidReference,
        InvalidReferenceKind,
        DuplicateRegistration,
        MissingRequiredValue,
        InvalidEnumValue,
        CatalogClosureFailure,
        ConflictingRegistration,
        InvalidPolicyCombination,
        InvalidInvocation,
        InvalidResult,
        InvalidProgress,
        InvalidTransportFailure,
    ];
}
