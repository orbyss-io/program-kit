using Orbyss.ProgramKit.DotNet.Documentation;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet;

internal sealed record DotNetDocumentInput(
    IntegratorDocumentProvenance Provenance,
    OpenApiDocumentProjection? OpenApi,
    OpenConsoleDocument? OpenConsole,
    OpenWorkerDocument? OpenWorker);
