using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Generates exact ASP.NET Core transport authentication and authorization.</summary>
public interface IDotNetSecurityProjectionCompiler
{
    /// <summary>Generates isolated runtime source for one selected security profile.</summary>
    ImmutableArray<GeneratedOutput> Compile(DotNetHostDefinition host);

    /// <summary>Renders authentication, handlers, and named-policy registration.</summary>
    string RenderRegistration(DotNetHostDefinition host);

    /// <summary>Renders authentication and exact operation authorization middleware.</summary>
    string RenderMiddleware(DotNetHostDefinition host);
}
