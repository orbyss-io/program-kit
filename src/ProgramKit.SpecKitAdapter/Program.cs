using System;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Diagnostics;

namespace Orbyss.ProgramKit.SpecKitAdapter;

public static class Program
{
    public static int Main(string[] args)
    {
        if (args.Length == 1 && string.Equals(args[0], "--version", StringComparison.Ordinal))
        {
            Console.WriteLine(JsonSerializer.Serialize(new { schema = "program-kit.spec-kit-adapter-version/v1", adapter = "orbyss-program-kit-adapter", version = "0.1.0" }));
            return 0;
        }

        AdapterOperation operation = DetectOperation(args);
        bool json = DetectJson(args);
        JsonObject result;
        try
        {
            (string workspace, string requestPath) = ParsePaths(args);
            JsonObject request = CanonicalDocument.Parse(File.ReadAllBytes(requestPath)).AsObject();
            AdapterSchemaValidator.Validate("adapter-request.schema.json", request);
            if (!string.Equals(request["operation"]!.GetValue<string>(), Kebab(operation), StringComparison.Ordinal))
                throw new InvalidDataException("The command and request operation differ.");
            result = operation switch
            {
                AdapterOperation.Doctor => DoctorCommand.Execute(workspace, request),
                AdapterOperation.Activate => ActivateCommand.Execute(workspace, request),
                AdapterOperation.Disable => DisableCommand.Execute(workspace, request),
                AdapterOperation.Handoff => HandoffCommand.Execute(workspace, request),
                AdapterOperation.Validate => ValidateCommand.Execute(workspace, request),
                AdapterOperation.Prepare => new PrepareCommand().Execute(workspace, request),
                AdapterOperation.Explain => new ExplainCommand().Execute(workspace, request),
                AdapterOperation.Construct => new ConstructCommand().Execute(workspace, request),
                AdapterOperation.Evaluate => new EvaluateCommand().Execute(workspace, request),
                _ => AdapterResultWriter.Failure(operation, AdapterFailureKind.InvalidHandoff),
            };
        }
        catch (InvalidDataException)
        {
            result = AdapterResultWriter.Failure(operation, AdapterFailureKind.InvalidConfiguration);
        }
        catch (IOException)
        {
            result = AdapterResultWriter.Failure(operation, AdapterFailureKind.UnsafePath);
        }
        catch (Exception)
        {
            result = AdapterResultWriter.Failure(operation, AdapterFailureKind.ProcessFailure, "faulted");
        }

        AdapterSchemaValidator.Validate("adapter-result.schema.json", result);
        if (json)
        {
            using Stream stdout = Console.OpenStandardOutput();
            stdout.Write(CanonicalDocument.Encode(result));
        }
        else
        {
            Console.WriteLine($"operation: {Kebab(operation)}");
            Console.WriteLine($"outcome: {result["outcome"]!.GetValue<string>()}");
            Console.WriteLine($"primary disposition: {result["primaryDisposition"]!.GetValue<string>()}");
        }

        return result["outcome"]!.GetValue<string>() switch
        {
            "succeeded" or "not-applicable" => 0,
            "faulted" => 1,
            "needs-input" => 2,
            "blocked" => 3,
            "cancelled" => 130,
            _ => 1,
        };
    }

    private static (string Workspace, string Request) ParsePaths(string[] args)
    {
        string? workspace = null;
        string? request = null;
        for (int index = 1; index < args.Length; index++)
        {
            string option = args[index];
            if (option is not ("--workspace" or "--request" or "--format")) throw new InvalidDataException("Unknown adapter option.");
            if (++index >= args.Length || args[index].StartsWith("--", StringComparison.Ordinal)) throw new InvalidDataException("Missing adapter option value.");
            if (option == "--workspace")
            {
                if (workspace is not null) throw new InvalidDataException("Duplicate workspace option.");
                workspace = args[index];
            }
            else if (option == "--request")
            {
                if (request is not null) throw new InvalidDataException("Duplicate request option.");
                request = args[index];
            }
            else if (args[index] is not ("text" or "json")) throw new InvalidDataException("Unsupported output format.");
        }

        if (workspace is null || request is null) throw new InvalidDataException("Workspace and request are required.");
        string root = Path.GetFullPath(workspace);
        string path = Path.GetFullPath(request);
        if (!Directory.Exists(root)
            || !path.StartsWith(root.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar, OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal)
            || !File.Exists(path)
            || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
            throw new IOException("The adapter request path is unsafe.");
        return (root, path);
    }

    private static AdapterOperation DetectOperation(string[] args) => args.Length == 0 ? AdapterOperation.Doctor : args[0] switch
    {
        "doctor" => AdapterOperation.Doctor,
        "activate" => AdapterOperation.Activate,
        "disable" => AdapterOperation.Disable,
        "handoff" => AdapterOperation.Handoff,
        "validate" => AdapterOperation.Validate,
        "prepare" => AdapterOperation.Prepare,
        "explain" => AdapterOperation.Explain,
        "construct" => AdapterOperation.Construct,
        "evaluate" => AdapterOperation.Evaluate,
        "cleanup" => AdapterOperation.Cleanup,
        _ => AdapterOperation.Doctor,
    };

    private static bool DetectJson(string[] args)
    {
        for (int index = 0; index + 1 < args.Length; index++)
            if (args[index] == "--format" && args[index + 1] == "json") return true;
        return false;
    }

    private static string Kebab(AdapterOperation operation) => operation.ToString().ToLowerInvariant();
}
