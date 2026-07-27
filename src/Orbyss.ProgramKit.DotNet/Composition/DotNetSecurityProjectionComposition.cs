using Orbyss.ProgramKit.DotNet.Generation;

namespace Orbyss.ProgramKit.DotNet.Composition;

/// <summary>Closed construction point for the .NET security compiler.</summary>
public static class DotNetSecurityProjectionComposition
{
    /// <summary>Creates the reviewed security projection compiler.</summary>
    public static IDotNetSecurityProjectionCompiler Create() =>
        new DotNetSecurityProjectionCompiler();
}
