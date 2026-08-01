using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Cli.Parsing;

public enum OutputFormat
{
    Text,
    Json,
}

public sealed record CliInvocation(
    PublicCommand Command,
    string? Workspace,
    string? Request,
    OutputFormat Format);
