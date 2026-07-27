namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>Language-neutral command source selected by a constructor parameter.</summary>
public enum DotNetConsoleBindingSourceKind
{
    /// <summary>The value comes from a positional argument.</summary>
    Argument,

    /// <summary>The value comes from a canonical long option.</summary>
    Option,
}
