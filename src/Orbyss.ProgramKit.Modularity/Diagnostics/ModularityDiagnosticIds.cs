using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Modularity.Diagnostics;

/// <summary>Stable diagnostic identifiers owned by Orbyss.ProgramKit.Modularity.</summary>
public static class ModularityDiagnosticIds
{
    /// <summary>A registration descriptor is incomplete or invalid.</summary>
    public const string InvalidRegistrationDescriptor = "PKMOD001";

    /// <summary>A registration has an invalid contribution or middleware type.</summary>
    public const string InvalidRegistrationType = "PKMOD002";

    /// <summary>A stable registration identity occurs more than once.</summary>
    public const string DuplicateRegistrationIdentity = "PKMOD003";

    /// <summary>An ordering descriptor is incomplete or contradictory.</summary>
    public const string InvalidOrderingDescriptor = "PKMOD004";

    /// <summary>An explicit ordering dependency is absent from the applicable registry.</summary>
    public const string MissingOrderingDependency = "PKMOD005";

    /// <summary>Explicit ordering constraints contain a cycle.</summary>
    public const string OrderingCycle = "PKMOD006";

    /// <summary>A publication policy uses an undefined value.</summary>
    public const string InvalidPublicationPolicy = "PKMOD007";

    /// <summary>A domain-contribution handler failed.</summary>
    public const string ContributionHandlerFailure = "PKMOD008";

    /// <summary>A type-erased contribution invocation received the wrong contribution type.</summary>
    public const string ContributionTypeMismatch = "PKMOD009";

    /// <summary>A middleware next delegate was invoked more than once.</summary>
    public const string MiddlewareNextInvokedMoreThanOnce = "PKMOD010";

    /// <summary>A middleware next delegate escaped the invocation that owned it.</summary>
    public const string MiddlewareNextInvokedOutsideInvocation = "PKMOD011";

    /// <summary>A middleware returned while an invoked next delegate was still running.</summary>
    public const string MiddlewareNextNotAwaited = "PKMOD012";

    /// <summary>Gets every owned identifier in stable numeric order.</summary>
    public static ImmutableArray<string> All { get; } =
    [
        InvalidRegistrationDescriptor,
        InvalidRegistrationType,
        DuplicateRegistrationIdentity,
        InvalidOrderingDescriptor,
        MissingOrderingDependency,
        OrderingCycle,
        InvalidPublicationPolicy,
        ContributionHandlerFailure,
        ContributionTypeMismatch,
        MiddlewareNextInvokedMoreThanOnce,
        MiddlewareNextInvokedOutsideInvocation,
        MiddlewareNextNotAwaited,
    ];
}
