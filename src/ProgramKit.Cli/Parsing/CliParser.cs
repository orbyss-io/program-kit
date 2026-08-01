using System;
using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Cli.Parsing;

public sealed record CliParseResult(CliInvocation? Invocation, string? Error)
{
    public bool Succeeded => Invocation is not null;
}

public sealed class CliParser
{
    public CliParseResult Parse(string[] arguments)
    {
        if (arguments.Length == 0)
        {
            return new(null, "A command is required.");
        }

        if (!TryCommand(arguments[0], out PublicCommand command))
        {
            return new(null, $"Unknown command: {arguments[0]}");
        }

        Dictionary<string, string> options = new(StringComparer.Ordinal);
        bool endOfOptions = false;
        for (int index = 1; index < arguments.Length; index++)
        {
            string token = arguments[index];
            if (token == "--")
            {
                if (endOfOptions)
                {
                    return new(null, "Duplicate end-of-options marker.");
                }

                endOfOptions = true;
                continue;
            }

            if (!token.StartsWith("--", StringComparison.Ordinal) || endOfOptions)
            {
                return new(null, $"Unexpected positional argument: {token}");
            }

            if (token is not ("--workspace" or "--request" or "--format"))
            {
                return new(null, $"Unknown option: {token}");
            }

            if (options.ContainsKey(token))
            {
                return new(null, $"Duplicate option: {token}");
            }

            if (++index >= arguments.Length)
            {
                return new(null, $"Missing value for {token}.");
            }

            options[token] = arguments[index];
            endOfOptions = false;
        }

        bool factoryCommand = command is PublicCommand.Explain or PublicCommand.Construct or PublicCommand.Evaluate;
        if (factoryCommand && (!options.ContainsKey("--workspace") || !options.ContainsKey("--request")))
        {
            return new(null, "Factory commands require --workspace and --request.");
        }

        if (!factoryCommand && (options.ContainsKey("--workspace") || options.ContainsKey("--request")))
        {
            return new(null, "Utility commands do not accept workspace or request options.");
        }

        string formatValue = options.GetValueOrDefault("--format", "text");
        OutputFormat format = formatValue switch
        {
            "text" => OutputFormat.Text,
            "json" => OutputFormat.Json,
            _ => (OutputFormat)(-1),
        };
        if (!Enum.IsDefined(format))
        {
            return new(null, "--format must be exactly text or json.");
        }

        return new(new CliInvocation(command, options.GetValueOrDefault("--workspace"), options.GetValueOrDefault("--request"), format), null);
    }

    private static bool TryCommand(string value, out PublicCommand command)
    {
        command = value switch
        {
            "explain" => PublicCommand.Explain,
            "construct" => PublicCommand.Construct,
            "evaluate" => PublicCommand.Evaluate,
            "help" => PublicCommand.Help,
            "version" => PublicCommand.Version,
            _ => (PublicCommand)(-1),
        };
        return Enum.IsDefined(command);
    }
}
