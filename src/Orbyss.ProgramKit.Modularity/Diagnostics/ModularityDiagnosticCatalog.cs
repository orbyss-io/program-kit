using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;

namespace Orbyss.ProgramKit.Modularity.Diagnostics;

/// <summary>The immutable diagnostic catalog owned by Orbyss.ProgramKit.Modularity.</summary>
public static class ModularityDiagnosticCatalog
{
    /// <summary>Gets definitions ordered by stable diagnostic identifier.</summary>
    public static ImmutableArray<ProgramKitDiagnosticDefinition> Definitions { get; } =
    [
        Error(
            ModularityDiagnosticIds.InvalidRegistrationDescriptor,
            "Invalid modularity registration descriptor"),
        Error(
            ModularityDiagnosticIds.InvalidRegistrationType,
            "Invalid modularity registration type"),
        Error(
            ModularityDiagnosticIds.DuplicateRegistrationIdentity,
            "Duplicate modularity registration identity"),
        Error(
            ModularityDiagnosticIds.InvalidOrderingDescriptor,
            "Invalid modularity ordering descriptor"),
        Error(
            ModularityDiagnosticIds.MissingOrderingDependency,
            "Missing modularity ordering dependency"),
        Error(
            ModularityDiagnosticIds.OrderingCycle,
            "Cyclic modularity ordering constraints"),
        Error(
            ModularityDiagnosticIds.InvalidPublicationPolicy,
            "Invalid domain-contribution publication policy"),
        Error(
            ModularityDiagnosticIds.ContributionHandlerFailure,
            "Domain-contribution handler failure"),
        Error(
            ModularityDiagnosticIds.ContributionTypeMismatch,
            "Domain-contribution type mismatch"),
        Error(
            ModularityDiagnosticIds.MiddlewareNextInvokedMoreThanOnce,
            "Middleware next delegate invoked more than once"),
        Error(
            ModularityDiagnosticIds.MiddlewareNextInvokedOutsideInvocation,
            "Middleware next delegate invoked outside its owning invocation"),
        Error(
            ModularityDiagnosticIds.MiddlewareNextNotAwaited,
            "Middleware returned before its next delegate completed"),
    ];

    private static ProgramKitDiagnosticDefinition Error(string id, string title) =>
        new(id, ProgramKitDiagnosticSeverity.Error, title);
}
