using System.Diagnostics;
using System.IO;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SpecKitAdapter.Configuration;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterBootstrapAcceptanceTests
{
    [TestMethod]
    public void Clean_consumer_completes_neutral_bootstrap_base_restore_and_base_doctor_under_two_seconds()
    {
        using SpecKitAdapterTestWorkspace consumer = SpecKitAdapterTestWorkspace.Create();
        string init = WorkspaceBootstrapFixture.WriteRequest(consumer.Root, "init.json", WorkspaceBootstrapFixture.InitRequest());
        Assert.AreEqual(0, TestRepository.RunCli("init", "--workspace", consumer.Root, "--request", init, "--format", "json").ExitCode);
        string restore = WorkspaceBootstrapFixture.WriteRequest(consumer.Root, "restore.json", WorkspaceBootstrapFixture.RestoreRequest("base"));
        Assert.AreEqual(0, TestRepository.RunCli("restore", "--workspace", consumer.Root, "--request", restore, "--format", "json").ExitCode);

        consumer.WriteText(".config/dotnet-tools.json", "{\"version\":1,\"isRoot\":true,\"tools\":{\"Orbyss.ProgramKit.Cli\":{\"version\":\"1.0.0-alpha.2\",\"commands\":[\"program-kit\"]}}}");
        consumer.WriteText(".specify/extensions/orbyss-program-kit-adapter/extension.yml", File.ReadAllText(Path.Combine(TestRepository.Root, "extensions", "orbyss-program-kit-adapter", "extension.yml")));
        consumer.WriteText(AdapterConfigResolver.ProjectConfigPath, File.ReadAllText(Path.Combine(TestRepository.Root, "extensions", "orbyss-program-kit-adapter", "config", "orbyss-program-kit-adapter-config.template.yml")));
        JsonObject request = new()
        {
            ["schema"] = "program-kit.spec-kit-adapter-request/v1",
            ["operation"] = "doctor",
            ["workspace"] = WorkspaceBootstrapFixture.WorkspaceIdentity(),
            ["config"] = new JsonObject { ["logicalPath"] = AdapterConfigResolver.ProjectConfigPath },
            ["requestedEffect"] = "none",
            ["outputRoot"] = "specs/base/program-kit/generated",
        };
        string doctorRequest = WorkspaceBootstrapFixture.WriteRequest(consumer.Root, "doctor.json", request);
        Stopwatch stopwatch = Stopwatch.StartNew();
        var doctor = TestRepository.RunAdapter("doctor", "--workspace", consumer.Root, "--request", doctorRequest, "--format", "json");
        stopwatch.Stop();
        Assert.AreEqual(0, doctor.ExitCode, doctor.StandardOutput + doctor.StandardError);
        Assert.AreEqual(string.Empty, doctor.StandardError);
        Assert.IsTrue(stopwatch.Elapsed < System.TimeSpan.FromSeconds(2), stopwatch.Elapsed.ToString());
        JsonObject result = CanonicalDocument.Parse(System.Text.Encoding.UTF8.GetBytes(doctor.StandardOutput)).AsObject();
        AdapterSchemaValidator.Validate("adapter-result.schema.json", result);
        JsonObject states = result["payload"]!["states"]!.AsObject();
        Assert.IsTrue(states["installed"]!.GetValue<bool>());
        Assert.IsTrue(states["available"]!.GetValue<bool>());
        Assert.IsFalse(states["selected"]!.GetValue<bool>());
        Assert.IsFalse(states["activated"]!.GetValue<bool>());
        Assert.IsFalse(states["authorized"]!.GetValue<bool>());
        Assert.IsFalse(Directory.Exists(consumer.PathOf("specs/base/program-kit")));
    }
}
