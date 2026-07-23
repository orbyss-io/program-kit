using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Modularity.Ordering;

/// <summary>
/// Gives one explicit handler or middleware registration an exact revision,
/// owner, and deterministic ordering contract.
/// </summary>
/// <param name="Registration">The exact registration identity and revision.</param>
/// <param name="OwnerId">The domain, package, or feature that owns the registration.</param>
/// <param name="Order">The explicit ordering descriptor.</param>
public sealed record ModularityRegistrationDescriptor(
    ArtifactReference Registration,
    ProgramKitIdentifier OwnerId,
    ModularityOrderDescriptor Order);
