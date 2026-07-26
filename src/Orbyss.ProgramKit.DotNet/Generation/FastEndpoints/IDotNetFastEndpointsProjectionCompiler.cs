using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation.FastEndpoints;

/// <summary>Compiles the optional FastEndpoints syntax projection.</summary>
public interface IDotNetFastEndpointsProjectionCompiler
{
    /// <summary>Compiles exact endpoint and parity-evidence outputs.</summary>
    ImmutableArray<GeneratedOutput> Compile(
        DotNetHostDefinition host,
        OpenApiDocumentProjection? document);
}
