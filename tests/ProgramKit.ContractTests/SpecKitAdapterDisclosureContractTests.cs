using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Diagnostics;
using Orbyss.ProgramKit.SpecKitAdapter.Invocation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterDisclosureContractTests
{
    private const string Opaque = "opaque-secret-derived-fingerprint-7f0f21b15d6d4cf198d24aa62ea88ef1";

    [TestMethod]
    public void Process_failures_project_typed_safe_fallback_without_external_values()
    {
        JsonObject result = AdapterResultFactory.Failure(AdapterOperation.Construct, AdapterFailureKind.ProcessFailure, "faulted");
        AdapterSchemaValidator.Validate("adapter-result.schema.json", result);
        Assert.AreEqual("invocation", result["furthestStage"]!.GetValue<string>());
        Assert.AreEqual("indeterminate", result["effectState"]!.GetValue<string>());
        Assert.AreEqual("retry", result["primaryDisposition"]!.GetValue<string>());
        JsonObject diagnostic = result["diagnostics"]!["items"]![0]!.AsObject();
        Assert.AreEqual("orbyss.program-kit.spec-kit-adapter/PKSKA0010", diagnostic["id"]!.GetValue<string>());
        Assert.AreEqual("public", diagnostic["expected"]!["classification"]!.GetValue<string>());
        Assert.AreEqual("public", diagnostic["observed"]!["classification"]!.GetValue<string>());
        Assert.IsTrue(diagnostic["evidence"]!.AsArray().Count > 0);
        Assert.IsTrue(diagnostic["remediations"]![0]!["request"]!["arguments"]!.AsArray().Count > 0);
        Assert.AreEqual(3, result["disclosure"]!.AsArray().Count);
        string rendered = Encoding.UTF8.GetString(CanonicalDocument.Encode(result));
        Assert.IsFalse(rendered.Contains(Opaque, StringComparison.Ordinal));
        Assert.IsFalse(rendered.Contains("stderr payload", StringComparison.Ordinal));
        Assert.IsFalse(rendered.Contains("InvalidOperationException", StringComparison.Ordinal));
    }

    [TestMethod]
    public void External_secret_exception_path_and_command_values_are_withheld_by_classification()
    {
        foreach (SafeValue value in new[]
        {
            DisclosureFilter.External("external-token"),
            DisclosureFilter.PublicText("secret=do-not-disclose"),
            DisclosureFilter.PublicText("InvalidOperationException at Product.Run(file.cs:42)"),
            DisclosureFilter.PublicText("stderr: raw external output"),
            DisclosureFilter.PublicText("cmd /c remove-item C:\\protected"),
            DisclosureFilter.RepositoryPath("../protected/file"),
        })
        {
            Assert.AreEqual(SafeValueClassification.Withheld, value.Classification);
            Assert.IsNull(value.Value);
            Assert.IsFalse(string.IsNullOrWhiteSpace(value.RedactionReason));
            Assert.IsNotNull(value.PolicyReference);
        }
    }

    [TestMethod]
    public void Valid_child_result_remains_authoritative_while_stderr_is_ignored()
    {
        JsonObject authoritative = PublicResult("succeeded");
        StubProcessClient client = new(_ => Task.FromResult(new ProgramKitProcessResult(
            0,
            Encoding.UTF8.GetString(CanonicalDocument.Encode(authoritative)),
            $"stderr payload {Opaque}",
            OutputTruncated: false)));
        string workspace = CreateWorkspace();
        try
        {
            JsonObject result = new PublicProgramKitInvoker(client).Invoke(workspace, "prepare", "requests/prepare.json");
            CollectionAssert.AreEqual(CanonicalDocument.Encode(authoritative), CanonicalDocument.Encode(result));
            Assert.AreEqual(1, client.InvocationCount);
            Assert.IsFalse(CanonicalDocument.Encode(result).AsSpan().IndexOf(Encoding.UTF8.GetBytes(Opaque)) >= 0);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public void Malformed_truncated_timeout_exception_and_unsafe_operation_fail_closed()
    {
        string workspace = CreateWorkspace();
        try
        {
            AssertUntrusted(workspace, _ => Task.FromResult(new ProgramKitProcessResult(0, "not-json", Opaque, false)));
            AssertUntrusted(workspace, _ => Task.FromResult(new ProgramKitProcessResult(0, Encoding.UTF8.GetString(CanonicalDocument.Encode(PublicResult("succeeded"))), Opaque, true)));
            AssertUntrusted(workspace, _ => Task.FromException<ProgramKitProcessResult>(new OperationCanceledException(Opaque)));
            AssertUntrusted(workspace, _ => Task.FromException<ProgramKitProcessResult>(new InvalidOperationException($"{Opaque} C:\\protected")));
            AssertUntrusted(workspace, _ => Task.FromResult(new ProgramKitProcessResult(3, Encoding.UTF8.GetString(CanonicalDocument.Encode(PublicResult("succeeded"))), Opaque, false)));

            StubProcessClient forbiddenClient = new(_ => throw new AssertFailedException("Forbidden command launched a process."));
            Assert.ThrowsExactly<ProgramKitInvocationException>(() => new PublicProgramKitInvoker(forbiddenClient).Invoke(workspace, "construct;curl https://example.invalid", "requests/prepare.json"));
            Assert.AreEqual(0, forbiddenClient.InvocationCount);
        }
        finally
        {
            Directory.Delete(workspace, recursive: true);
        }
    }

    [TestMethod]
    public void Transport_uses_argument_vectors_without_shell_or_network_arguments()
    {
        ProgramKitProcessRequest request = new(
            "dotnet",
            new[] { "tool", "run", "program-kit", "--", "prepare", "--request", "requests/prepare.json", "--format", "json" },
            Environment.CurrentDirectory,
            TimeSpan.FromSeconds(1));
        System.Diagnostics.ProcessStartInfo start = ProgramKitProcessClient.CreateStartInfo(request);
        Assert.IsFalse(start.UseShellExecute);
        Assert.IsTrue(start.RedirectStandardOutput);
        Assert.IsTrue(start.RedirectStandardError);
        Assert.IsFalse(start.ArgumentList.Any(argument => argument.Contains("http://", StringComparison.OrdinalIgnoreCase) || argument.Contains("https://", StringComparison.OrdinalIgnoreCase)));
    }

    private static void AssertUntrusted(string workspace, Func<ProgramKitProcessRequest, Task<ProgramKitProcessResult>> behavior)
    {
        ProgramKitInvocationException exception = Assert.ThrowsExactly<ProgramKitInvocationException>(
            () => new PublicProgramKitInvoker(new StubProcessClient(behavior)).Invoke(workspace, "prepare", "requests/prepare.json"));
        Assert.IsNull(exception.InnerException);
        Assert.IsFalse(exception.Message.Contains(Opaque, StringComparison.Ordinal));
    }

    private static JsonObject PublicResult(string outcome) => new()
    {
        ["schema"] = AdapterCompatibility.Load().TranslationProfile.OperationResultSchema,
        ["outcome"] = outcome,
    };

    private static string CreateWorkspace()
    {
        string workspace = Path.Combine(Path.GetTempPath(), $"program-kit-adapter-disclosure-{Guid.NewGuid():N}");
        Directory.CreateDirectory(Path.Combine(workspace, "requests"));
        File.WriteAllText(Path.Combine(workspace, "requests", "prepare.json"), "{}");
        return workspace;
    }

    private sealed class StubProcessClient : IProgramKitProcessClient
    {
        private readonly Func<ProgramKitProcessRequest, Task<ProgramKitProcessResult>> behavior;

        public StubProcessClient(Func<ProgramKitProcessRequest, Task<ProgramKitProcessResult>> behavior)
        {
            this.behavior = behavior;
        }

        public int InvocationCount { get; private set; }

        public Task<ProgramKitProcessResult> RunAsync(ProgramKitProcessRequest request, CancellationToken cancellationToken)
        {
            InvocationCount++;
            return behavior(request);
        }
    }
}
