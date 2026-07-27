using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Generates exact ASP.NET Core transport-failure composition.</summary>
public interface IDotNetTransportFailureProjectionCompiler
{
    /// <summary>Generates runtime source for one selected transport-failure profile.</summary>
    ImmutableArray<GeneratedOutput> Compile(DotNetHostDefinition host);

    /// <summary>Renders ordered singleton handler registration.</summary>
    string RenderRegistration(DotNetHostDefinition host);

    /// <summary>Renders exception and optional status-code middleware.</summary>
    string RenderMiddleware(DotNetHostDefinition host);
}
