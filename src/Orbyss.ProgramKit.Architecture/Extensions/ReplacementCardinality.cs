using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Extensions;

/// <summary>Allowed cardinality for a replacement extension.</summary>
public enum ReplacementCardinality
{
    /// <summary>Exactly one implementation must be selected.</summary>
    ExactlyOne,

    /// <summary>Zero or one implementation may be selected.</summary>
    ZeroOrOne
}
