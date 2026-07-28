using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Generation.Console.Compilation;
using Orbyss.ProgramKit.DotNet.Generation.Console.Contracts;
using Orbyss.ProgramKit.DotNet.Generation.Console.Projection;
using Orbyss.ProgramKit.DotNet.Generation.Console.Rendering;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Composition;

/// <summary>Creates the exact backed typed Console generation graph.</summary>
public static class DotNetConsoleGenerationComposition
{
    /// <summary>Creates one isolated typed Console generator.</summary>
    public static IDotNetConsoleHostGenerator Create() =>
        new DotNetConsoleHostGenerator(
            new DotNetConsoleBindingValidator(),
            new DotNetConsoleMetadataInspector(),
            new DotNetConsoleProjectionCompiler(),
            new DotNetConsoleHostRenderer(
                [
            new DotNetConsoleProjectRenderer(),
            new DotNetConsoleApplicationConfigurationRenderer(),
            new DotNetConsoleInformationRenderer(),
            new DotNetConsoleInvocationFailureRenderer(),
            new DotNetConsoleSettingsRenderer(),
                    new DotNetConsoleRequestFactoryRenderer(),
                    new DotNetConsoleCommandRenderer(),
                    new DotNetConsoleServiceAuditRenderer(),
                    new DotNetConsoleTypeRegistrarRenderer(),
                    new DotNetConsoleProgramRenderer(),
                ]),
            new DotNetConsoleCandidateCompiler());
}
