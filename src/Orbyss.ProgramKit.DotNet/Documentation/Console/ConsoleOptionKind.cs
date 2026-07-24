namespace Orbyss.ProgramKit.DotNet.Documentation.Console;

/// <summary>Whether an option is a flag or consumes typed values.</summary>
public enum ConsoleOptionKind
{
    /// <summary>The option is presence-only.</summary>
    Flag,

    /// <summary>The option consumes one or more values.</summary>
    Value,
}
