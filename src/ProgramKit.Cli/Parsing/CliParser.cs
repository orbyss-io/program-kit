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

        PublicCommand command;
        int optionStart;
        if (string.Equals(arguments[0], "session", StringComparison.Ordinal))
        {
            if (arguments.Length < 2) return new(null, "A session lifecycle operation is required.");
            if (!TrySessionCommand(arguments[1], out command)) return new(null, "Unknown session lifecycle operation.");
            optionStart = 2;
        }
        else if (string.Equals(arguments[0], "catalog", StringComparison.Ordinal))
        {
            if (arguments.Length < 2) return new(null, "A catalog operation is required.");
            if (!string.Equals(arguments[1], "list", StringComparison.Ordinal)) return new(null, "Unknown catalog operation.");
            command = PublicCommand.CatalogList;
            optionStart = 2;
        }
        else if (string.Equals(arguments[0], "authority", StringComparison.Ordinal))
        {
            if (arguments.Length < 2) return new(null, "An authority operation is required.");
            if (!string.Equals(arguments[1], "record", StringComparison.Ordinal)) return new(null, "Unknown authority operation.");
            command = PublicCommand.AuthorityRecord;
            optionStart = 2;
        }
        else
        {
            if (!TryCommand(arguments[0], out command)) return new(null, "Unknown command.");
            optionStart = 1;
        }

        Dictionary<string, string> options = new(StringComparer.Ordinal);
        bool endOfOptions = false;
        for (int index = optionStart; index < arguments.Length; index++)
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
                return new(null, "Unexpected positional argument.");
            }

            if (token is not ("--workspace" or "--request" or "--format"))
            {
                return new(null, "Unknown option.");
            }

            if (options.ContainsKey(token))
            {
                return new(null, $"Duplicate option: {token}");
            }

            if (++index >= arguments.Length)
            {
                return new(null, $"Missing value for {token}.");
            }

            if (arguments[index].StartsWith("--", StringComparison.Ordinal))
            {
                return new(null, "An option value is missing.");
            }

            options[token] = arguments[index];
            endOfOptions = false;
        }

        bool factoryCommand = command is not (PublicCommand.Help or PublicCommand.Version);
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

    private static bool TrySessionCommand(string value, out PublicCommand command)
    {
        command = value switch
        {
            "explain" => PublicCommand.SessionExplain,
            "install" => PublicCommand.SessionInstall,
            "verify" => PublicCommand.SessionVerify,
            "remove" => PublicCommand.SessionRemove,
            _ => (PublicCommand)(-1),
        };
        return Enum.IsDefined(command);
    }

    private static bool TryCommand(string value, out PublicCommand command)
    {
        command = value switch
        {
            "explain" => PublicCommand.Explain,
            "construct" => PublicCommand.Construct,
            "evaluate" => PublicCommand.Evaluate,
            "init" => PublicCommand.Init,
            "restore" => PublicCommand.Restore,
            "prepare" => PublicCommand.Prepare,
            "help" => PublicCommand.Help,
            "version" => PublicCommand.Version,
            _ => (PublicCommand)(-1),
        };
        return Enum.IsDefined(command);
    }

}
