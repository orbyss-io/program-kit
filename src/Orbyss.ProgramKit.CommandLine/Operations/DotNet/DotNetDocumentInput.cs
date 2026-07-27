using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet;

internal sealed record DotNetDocumentInput(
    ArtifactReference ShellRevision,
    OpenApiDocumentProjection? OpenApi,
    OpenConsoleDocument? OpenConsole,
    OpenWorkerDocument? OpenWorker);
