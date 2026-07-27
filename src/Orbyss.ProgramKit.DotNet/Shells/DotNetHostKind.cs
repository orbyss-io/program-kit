namespace Orbyss.ProgramKit.DotNet.Shells;

/// <summary>Supported generated .NET host kinds.</summary>
public enum DotNetHostKind
{
    /// <summary>ASP.NET Core HTTP API host.</summary>
    Api,

    /// <summary>Generic Host command-line application.</summary>
    Console,

    /// <summary>Generic Host background worker.</summary>
    Worker,
}
