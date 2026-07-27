namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>Reference-nullability annotation carried by a structured CLR type.</summary>
public enum DotNetConsoleReferenceNullability
{
    /// <summary>The CLR type is not a reference type.</summary>
    NotApplicable,

    /// <summary>The CLR reference is non-nullable.</summary>
    NotNull,

    /// <summary>The CLR reference is nullable.</summary>
    Nullable,
}
