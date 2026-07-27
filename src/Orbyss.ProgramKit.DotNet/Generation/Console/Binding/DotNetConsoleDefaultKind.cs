namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>Explicit disposition for a constructor parameter default.</summary>
public enum DotNetConsoleDefaultKind
{
    /// <summary>The source declares no default.</summary>
    None,

    /// <summary>The exact canonical source default is recorded.</summary>
    Canonical,
}
