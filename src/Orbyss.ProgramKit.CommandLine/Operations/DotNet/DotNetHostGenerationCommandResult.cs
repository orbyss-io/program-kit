using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet;

/// <summary>Exact selected inputs and locks from one completed host generation.</summary>
public sealed record DotNetHostGenerationCommandResult(
    DotNetShellDocument Shell,
    ArtifactReference ShellRevision,
    DotNetShellLockDocument ShellLock,
    DotNetHostDefinition Host,
    DotNetHostLock HostLock);
