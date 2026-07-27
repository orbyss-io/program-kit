using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Defines one compatibility expectation evaluated by a work unit.</summary>
public sealed record PlanCompatibilityRequirement(
    ProgramKitIdentifier SubjectId,
    SemanticVersionRange AcceptedVersions,
    string ExpectedDisposition);
