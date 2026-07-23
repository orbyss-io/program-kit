using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>
/// The nine mandatory cross-cutting boundary statements of an architecture
/// design. Keeping them named prevents a design from silently omitting one.
/// </summary>
public sealed record ArchitectureBoundarySet(
    BoundaryDefinition Security,
    BoundaryDefinition Authority,
    BoundaryDefinition Secrets,
    BoundaryDefinition Persistence,
    BoundaryDefinition Failure,
    BoundaryDefinition Concurrency,
    BoundaryDefinition Cancellation,
    BoundaryDefinition Observability,
    BoundaryDefinition Compatibility);
