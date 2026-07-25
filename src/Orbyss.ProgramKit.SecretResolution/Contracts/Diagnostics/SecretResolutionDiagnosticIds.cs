namespace Orbyss.ProgramKit.SecretResolution.Contracts.Diagnostics;

/// <summary>Stable diagnostics emitted by secret-resolution validators.</summary>
public static class SecretResolutionDiagnosticIds
{
    /// <summary>A required value or initialized collection is absent.</summary>
    public const string MissingRequiredValue = "PKSEC001";
    /// <summary>An enum value is outside its finite set.</summary>
    public const string InvalidEnumValue = "PKSEC002";
    /// <summary>An exact artifact reference is absent or has the wrong semantic kind.</summary>
    public const string InvalidReference = "PKSEC003";
    /// <summary>Reference or locator metadata is not explicitly classified.</summary>
    public const string UnclassifiedReference = "PKSEC004";
    /// <summary>The selected resolver does not support the expected result kind.</summary>
    public const string UnsupportedResultKind = "PKSEC005";
    /// <summary>The selected resolver does not support the requested lifetime.</summary>
    public const string UnsupportedLifetime = "PKSEC006";
    /// <summary>The selected refresh, rotation, or consumer reaction is incompatible.</summary>
    public const string IncompatibleReaction = "PKSEC007";
    /// <summary>A configuration projection attempted to become a universal credential transport.</summary>
    public const string InvalidConfigurationProjection = "PKSEC008";
    /// <summary>Lifecycle or generation metadata is inconsistent.</summary>
    public const string InvalidLifecycle = "PKSEC009";
    /// <summary>A reaction was reported successful before a supported reaction succeeded.</summary>
    public const string FalseSuccess = "PKSEC010";
    /// <summary>A collection contains duplicate finite capabilities.</summary>
    public const string DuplicateCapability = "PKSEC011";

    /// <summary>Gets all owned diagnostic identifiers in stable order.</summary>
    public static ImmutableArray<string> All { get; } =
    [
        MissingRequiredValue,
        InvalidEnumValue,
        InvalidReference,
        UnclassifiedReference,
        UnsupportedResultKind,
        UnsupportedLifetime,
        IncompatibleReaction,
        InvalidConfigurationProjection,
        InvalidLifecycle,
        FalseSuccess,
        DuplicateCapability,
    ];
}
