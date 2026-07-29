using Orbyss.ProgramKit.CommandLine.Contracts;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Capabilities.Initialization;

internal sealed record CommandResult(
    CommandExitCode ExitCode,
    string Output,
    string Error);
