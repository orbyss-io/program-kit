using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Renders warning-clean source and project policy for one exact host.</summary>
public interface IDotNetHostSourceRenderer
{
    /// <summary>Renders all source and project outputs for one host.</summary>
    ImmutableArray<GeneratedOutput> Render(
        DotNetHostDefinition host,
        DotNetHostLock hostLock,
        ImmutableArray<DotNetFeatureSelection> features,
        OpenApiDocumentProjection? openApiDocument,
        OpenConsoleDocument? consoleDocument);
}
