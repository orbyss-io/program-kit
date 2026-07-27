namespace Orbyss.ProgramKit.Serialization.Json.Diagnostics;

/// <summary>Stable diagnostic identifiers owned by Serialization.JSON.</summary>
public static class ProgramKitJsonDiagnosticIds
{
    /// <summary>A profile reference or descriptor is invalid.</summary>
    public const string InvalidProfile = "PKJSN001";

    /// <summary>A frozen or freezing builder was mutated.</summary>
    public const string RegistryFrozen = "PKJSN002";

    /// <summary>An exact profile is not registered.</summary>
    public const string UnknownProfile = "PKJSN003";

    /// <summary>A contribution descriptor or selection is invalid.</summary>
    public const string InvalidContribution = "PKJSN004";

    /// <summary>Two unordered contributions claim the same target.</summary>
    public const string ContributionConflict = "PKJSN005";

    /// <summary>An ordering constraint references an unselected contribution.</summary>
    public const string OrderingGap = "PKJSN006";

    /// <summary>Contribution ordering contains a cycle.</summary>
    public const string OrderingCycle = "PKJSN007";

    /// <summary>One identity and version resolve to changed bytes.</summary>
    public const string RevisionDigestConflict = "PKJSN008";

    /// <summary>No selected source-generated metadata describes the requested type.</summary>
    public const string TypeMetadataUnavailable = "PKJSN009";

    /// <summary>The input is not one complete strict JSON value.</summary>
    public const string InvalidJson = "PKJSN010";

    /// <summary>An object contains duplicate decoded member names.</summary>
    public const string DuplicateMemberName = "PKJSN011";

    /// <summary>Input contains invalid UTF-8 or an invalid Unicode scalar sequence.</summary>
    public const string InvalidUnicode = "PKJSN012";

    /// <summary>A JSON string is not already Unicode NFC.</summary>
    public const string NonCanonicalUnicode = "PKJSN013";

    /// <summary>A number is outside the strict canonical subset.</summary>
    public const string InvalidNumber = "PKJSN014";

    /// <summary>The configured UTF-8 byte limit was exceeded.</summary>
    public const string ByteLimitExceeded = "PKJSN015";

    /// <summary>The configured nesting-depth limit was exceeded.</summary>
    public const string DepthLimitExceeded = "PKJSN016";

    /// <summary>The configured token limit was exceeded.</summary>
    public const string TokenLimitExceeded = "PKJSN017";

    /// <summary>The configured per-object member limit was exceeded.</summary>
    public const string MemberLimitExceeded = "PKJSN018";

    /// <summary>The configured complete-object buffered-byte limit was exceeded.</summary>
    public const string MemberBufferLimitExceeded = "PKJSN019";

    /// <summary>A contribution was selected for a non-extensible profile.</summary>
    public const string NonExtensibleProfile = "PKJSN020";

    /// <summary>Typed deserialization produced no model.</summary>
    public const string NullModel = "PKJSN021";
}
