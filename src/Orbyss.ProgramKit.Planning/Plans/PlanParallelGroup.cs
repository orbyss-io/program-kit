using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Names work units that may run concurrently after their external dependencies are satisfied.</summary>
public sealed record PlanParallelGroup(
    string ParallelGroupId,
    ImmutableArray<string> WorkUnitIds);
