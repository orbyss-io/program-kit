using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Commands.Parsing;

internal static class CommandInvocationValidator
{
    internal static void Validate(CommandInvocation invocation)
    {
        var hasArguments = invocation.Arguments.Length > 0;
        var hasManifest = invocation.Options.ContainsKey("manifest");
        if (invocation.Descriptor.Key is "validate" or "check")
        {
            if (hasArguments == hasManifest)
            {
                throw new CommandInvocationException(
                    "Exactly one explicit artifact input or '--manifest' is required.",
                    "/input");
            }
        }
    }
}
