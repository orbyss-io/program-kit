using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;
using Orbyss.ProgramKit.DotNet.Locks;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Writes generated documents through their exact canonical profiles.</summary>
public interface IDotNetDocumentWriter
{
    /// <summary>Writes OpenAPI 3.2.0.</summary>
    ReadOnlyMemory<byte> Write(OpenApiDocumentProjection document);

    /// <summary>Writes Open Console 1.0.0.</summary>
    ReadOnlyMemory<byte> Write(OpenConsoleDocument document);

    /// <summary>Writes Open Worker 1.0.0.</summary>
    ReadOnlyMemory<byte> Write(OpenWorkerDocument document);

    /// <summary>Writes the selected deterministic shell lock.</summary>
    ReadOnlyMemory<byte> Write(DotNetShellLockDocument document);

    /// <summary>Writes the exact Console command-dispatch lock.</summary>
    ReadOnlyMemory<byte> Write(DotNetConsoleCommandDispatchLockDocument document);

    /// <summary>Writes deterministic Console command-dispatch evidence.</summary>
    ReadOnlyMemory<byte> Write(DotNetConsoleCommandDispatchEvidenceDocument document);
}
