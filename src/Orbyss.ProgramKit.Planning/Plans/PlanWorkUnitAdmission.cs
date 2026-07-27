using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Pure classification of dependency-ready work-unit IDs.</summary>
public sealed record PlanWorkUnitAdmission(
    ImmutableArray<string> AdmissibleWorkUnitIds,
    ImmutableArray<string> BlockingReasons);
