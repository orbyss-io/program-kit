using System;
using System.Text.Json.Nodes;
using System.Threading;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.SpecKitAdapter.Invocation;

public interface IPublicProgramKitInvoker
{
    JsonObject Invoke(string workspaceRoot, string command, string requestLogicalPath);
}

public sealed class ProgramKitInvocationException : Exception
{
    public ProgramKitInvocationException() : base("The Program Kit invocation did not return a trusted complete result.") { }
}

public sealed class PublicProgramKitInvoker : IPublicProgramKitInvoker
{
    private readonly IProgramKitProcessClient client;

    public PublicProgramKitInvoker(IProgramKitProcessClient? client = null)
    {
        this.client = client ?? new ProgramKitProcessClient();
    }

    public JsonObject Invoke(string workspaceRoot, string command, string requestLogicalPath)
    {
        try
        {
            if (command is not ("prepare" or "explain" or "construct" or "evaluate"))
                throw new ProgramKitInvocationException();
            LogicalPathPolicy.Resolve(workspaceRoot, requestLogicalPath);
            ProgramKitProcessRequest request = new(
                "dotnet",
                new[] { "tool", "run", "program-kit", "--", command, "--workspace", workspaceRoot, "--request", requestLogicalPath, "--format", "json" },
                workspaceRoot,
                TimeSpan.FromMinutes(2));
            ProgramKitProcessResult result = client.RunAsync(request, CancellationToken.None).GetAwaiter().GetResult();
            if (result.OutputTruncated) throw new ProgramKitInvocationException();
            JsonObject document = CanonicalDocument.Parse(System.Text.Encoding.UTF8.GetBytes(result.StandardOutput)).AsObject();
            string expectedSchema = AdapterCompatibility.Load().TranslationProfile.OperationResultSchema;
            string outcome = document["outcome"]?.GetValue<string>() ?? string.Empty;
            int expectedExitCode = outcome switch { "succeeded" => 0, "faulted" => 1, "needs-input" => 2, "blocked" => 3, "cancelled" => 130, _ => -1 };
            if (document["schema"]?.GetValue<string>() != expectedSchema || result.ExitCode != expectedExitCode)
                throw new ProgramKitInvocationException();
            return document;
        }
        catch (ProgramKitInvocationException)
        {
            throw;
        }
        catch
        {
            throw new ProgramKitInvocationException();
        }
    }
}
