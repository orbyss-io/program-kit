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
        OperationExecutionTracker.Start(command);
        OperationResult result;
        try
        {
            if (!parsed.Succeeded)
            {
                Diagnostic diagnostic = DiagnosticFactory.Create(
                    DiagnosticIds.MissingInput,
                    OperationPhase.Request,
                    DisclosureFilter.PublicText("command-line"),
                    DisclosureFilter.PublicText(parsed.Error ?? "Invalid command line."),
                    DisclosureFilter.PublicText("Use the exact help contract and resubmit a complete command."));
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
            OperationExecutionSnapshot state = OperationExecutionTracker.Snapshot(command);
            result = OperationResultFactory.Failure(command, OperationOutcome.Cancelled, state.Phase, state.Effect, PrimaryDisposition.Stop, Array.Empty<Diagnostic>());
        }
        catch (Exception)
        {
            OperationExecutionSnapshot state = OperationExecutionTracker.Snapshot(command);
            result = OperationResultFactory.Fallback(command, state.Phase, state.Effect);
        }

        try
        {
            ResultRenderer.Write(result, format, Console.OpenStandardOutput());
        }
        catch (Exception)
        {
            OperationExecutionSnapshot state = OperationExecutionTracker.Snapshot(command);
            FallbackResultWriter.Write(command, state.Phase, state.Effect, Console.OpenStandardOutput());
            return 1;
        }

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
