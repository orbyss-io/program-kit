using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>
/// Question 2: whether values are validated, exchanged, persisted, compared,
/// or digested.
/// </summary>
public sealed record ValueLifecycleAnswer(
    ImmutableArray<ValueLifecycleUse> Uses,
    string Rationale);
