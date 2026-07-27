using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>Whether a reference is explicitly permitted or prohibited.</summary>
public enum ReferenceRuleDisposition
{
    /// <summary>The described reference is permitted.</summary>
    Allowed,

    /// <summary>The described reference is prohibited.</summary>
    Forbidden
}
