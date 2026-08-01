using System;
using Orbyss.ProgramKit.Cli.Commands;
using Orbyss.ProgramKit.Cli.Composition;
using Orbyss.ProgramKit.Cli.Parsing;
using Orbyss.ProgramKit.Cli.Rendering;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Operations;

namespace Orbyss.ProgramKit.Cli;

public static class Program
{
    public static int Main(string[] args)
    {
        CliParser parser = new();
        CliParseResult parsed = parser.Parse(args);
        OutputFormat format = DetectFormat(args);
        PublicCommand command = DetectCommand(args);
        OperationResult result;
        try
        {
            if (!parsed.Succeeded)
            {
                Diagnostic diagnostic = DiagnosticFactory.Create(
                    DiagnosticIds.MissingInput,
                    OperationPhase.Request,
                    "command-line",
                    parsed.Error ?? "Invalid command line.",
                    "Use the exact help contract and resubmit a complete command.");
                result = OperationResultFactory.Failure(command, OperationOutcome.Blocked, OperationPhase.Request, EffectState.None, PrimaryDisposition.ProvideInput, new[] { diagnostic });
            }
            else
            {
                CommandDispatcher dispatcher = new(ProgramKitComposition.CreateKernel(), ProgramKitComposition.CreateSessionServices());
                result = dispatcher.Execute(parsed.Invocation!);
                format = parsed.Invocation!.Format;
            }
        }
        catch (OperationCanceledException)
        {
            result = OperationResultFactory.Failure(command, OperationOutcome.Cancelled, OperationPhase.Request, EffectState.None, PrimaryDisposition.Stop, Array.Empty<Diagnostic>());
        }
        catch (Exception)
        {
            result = OperationResultFactory.Fallback(command, EffectState.None);
        }

        ResultRenderer.Write(result, format, Console.OpenStandardOutput());
        return result.Outcome switch
        {
            OperationOutcome.Succeeded => 0,
            OperationOutcome.Faulted => 1,
            OperationOutcome.NeedsInput => 2,
            OperationOutcome.Blocked => 3,
            OperationOutcome.Cancelled => 130,
            _ => 1,
        };
    }

    private static OutputFormat DetectFormat(string[] args)
    {
        for (int index = 0; index + 1 < args.Length; index++)
        {
            if (args[index] == "--format" && args[index + 1] == "json")
            {
                return OutputFormat.Json;
            }
        }

        return OutputFormat.Text;
    }

    private static PublicCommand DetectCommand(string[] args) => args.Length == 0 ? PublicCommand.Help : args[0] switch
    {
        "session" when args.Length > 1 => args[1] switch { "explain" => PublicCommand.SessionExplain, "install" => PublicCommand.SessionInstall, "verify" => PublicCommand.SessionVerify, "remove" => PublicCommand.SessionRemove, _ => PublicCommand.Help },
        "explain" => PublicCommand.Explain,
        "construct" => PublicCommand.Construct,
        "evaluate" => PublicCommand.Evaluate,
        "version" => PublicCommand.Version,
        _ => PublicCommand.Help,
    };
}
