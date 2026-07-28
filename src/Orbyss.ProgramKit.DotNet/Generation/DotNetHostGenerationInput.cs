using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Generation.Console.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Complete explicit typed input for one selected host generation.</summary>
public sealed record DotNetHostGenerationInput(
    DotNetShellDocument Shell,
    ArtifactReference ShellRevision,
    DotNetShellLockDocument Lock,
    ProgramKitIdentifier HostIdentity,
    OpenApiDocumentProjection? OpenApi,
    OpenConsoleDocument? OpenConsole,
    OpenWorkerDocument? OpenWorker,
    ArtifactReference? OpenConsoleDocumentRevision = null,
    DotNetConsoleGenerationInput? ConsoleGeneration = null);
