using System.Collections.Immutable;
using Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

internal sealed record ConsoleInputMaterializationCandidate(
    DotNetConsoleInputMaterializationLock Lock,
    ImmutableArray<ConsoleInputMaterializedFile> Files,
    ImmutableArray<string> ReadOnlyRelativePaths);
