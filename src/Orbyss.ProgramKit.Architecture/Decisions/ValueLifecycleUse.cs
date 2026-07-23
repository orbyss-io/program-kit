using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>Ways a value can require a contract-owned artifact.</summary>
public enum ValueLifecycleUse
{
    /// <summary>The value is validated.</summary>
    Validated,

    /// <summary>The value crosses a contract boundary.</summary>
    Exchanged,

    /// <summary>The value is stored beyond an invocation.</summary>
    Persisted,

    /// <summary>The value participates in equality or ordering.</summary>
    Compared,

    /// <summary>The value contributes to a digest.</summary>
    Digested
}
