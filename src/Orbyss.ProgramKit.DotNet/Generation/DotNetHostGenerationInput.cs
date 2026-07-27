using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Complete explicit typed input for one selected host generation.</summary>
public sealed record DotNetHostGenerationInput(
    DotNetShellDocument Shell,
    ArtifactReference ShellRevision,
    DotNetShellLockDocument Lock,
    ProgramKitIdentifier HostIdentity,
    OpenApiDocumentProjection? OpenApi,
    OpenConsoleDocument? OpenConsole,
    OpenWorkerDocument? OpenWorker);
