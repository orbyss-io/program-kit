using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Extensions;

/// <summary>Required semantics for a replacement extension point.</summary>
public sealed record ReplacementSemantics(
    ReplacementCardinality Cardinality,
    string SelectionRule,
    string FallbackSemantics,
    string FailureSemantics);
