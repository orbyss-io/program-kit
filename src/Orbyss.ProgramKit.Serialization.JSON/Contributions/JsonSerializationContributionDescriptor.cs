using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Serialization.Json.Contributions;

/// <summary>An immutable, independently versioned JSON contribution descriptor.</summary>
public sealed record JsonSerializationContributionDescriptor(
    JsonSerializationContributionRef Reference,
    ProgramKitIdentifier OwningPackage,
    ProgramKitIdentifier ApplicableProfileId,
    SemanticVersionRange ApplicableProfileRange,
    JsonSerializationContributionKind Kind,
    ImmutableArray<string> TargetTypeFamilies,
    ImmutableArray<ProgramKitIdentifier> Before,
    ImmutableArray<ProgramKitIdentifier> After);
