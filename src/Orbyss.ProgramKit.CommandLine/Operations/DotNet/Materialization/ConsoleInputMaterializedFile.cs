namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

internal sealed record ConsoleInputMaterializedFile(
    string RelativePath,
    ReadOnlyMemory<byte> Content);
