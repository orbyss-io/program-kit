namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Finite successful materialization status.</summary>
public enum ConsoleInputMaterializationStatus
{
    /// <summary>A new owned output was created.</summary>
    Created,

    /// <summary>The current evaluated result was byte-identical.</summary>
    Unchanged,

    /// <summary>A clean owned output was atomically refreshed.</summary>
    Updated,
}
