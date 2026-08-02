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
        if (result.ExitCode != 0 || result.OutputTruncated) throw new IOException("The Program Kit child process did not return one complete successful result.");
        JsonObject document = CanonicalDocument.Parse(System.Text.Encoding.UTF8.GetBytes(result.StandardOutput)).AsObject();
        const string expectedSchema = "program-kit.operation-result/v2";
        if (document["schema"]?.GetValue<string>() != expectedSchema || document["outcome"]?.GetValue<string>() != "succeeded")
            throw new IOException("The Program Kit child result is incompatible or unsuccessful.");
        return document;
    }
}
