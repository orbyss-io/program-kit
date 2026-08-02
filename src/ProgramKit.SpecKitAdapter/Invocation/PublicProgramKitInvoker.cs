using System;
using System.IO;
using System.Text.Json.Nodes;
using System.Threading;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.SpecKitAdapter.Invocation;

public interface IPublicProgramKitInvoker
{
    JsonObject Invoke(string workspaceRoot, string command, string requestLogicalPath);
}

public sealed class PublicProgramKitInvoker : IPublicProgramKitInvoker
{
    private readonly ProgramKitProcessClient client = new();

    public JsonObject Invoke(string workspaceRoot, string command, string requestLogicalPath)
    {
        ProgramKitProcessRequest request = new(
            "dotnet",
            new[] { "tool", "run", "program-kit", "--", command, "--workspace", workspaceRoot, "--request", requestLogicalPath, "--format", "json" },
            workspaceRoot,
            TimeSpan.FromMinutes(2));
        ProgramKitProcessResult result = client.RunAsync(request, CancellationToken.None).GetAwaiter().GetResult();
        if (result.OutputTruncated) throw new IOException("The Program Kit child process did not return one complete result.");
        JsonObject document = CanonicalDocument.Parse(System.Text.Encoding.UTF8.GetBytes(result.StandardOutput)).AsObject();
        string expectedSchema = AdapterCompatibility.Load().TranslationProfile.OperationResultSchema;
        string outcome = document["outcome"]?.GetValue<string>() ?? string.Empty;
        int expectedExitCode = outcome switch { "succeeded" => 0, "faulted" => 1, "needs-input" => 2, "blocked" => 3, "cancelled" => 130, _ => -1 };
        if (document["schema"]?.GetValue<string>() != expectedSchema || result.ExitCode != expectedExitCode)
            throw new IOException("The Program Kit child result schema, outcome, and exit code are inconsistent.");
        return document;
    }
}
