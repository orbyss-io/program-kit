using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionCliReleaseBindingAcceptanceTests
{
    [TestMethod]
    public void Every_selected_cli_release_field_is_verified_before_admission()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        SessionRequestPaths requests = SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root);
        JsonObject baseline = CanonicalJson.Parse(File.ReadAllBytes(requests.Explain)).AsObject();

        IReadOnlyList<Action<JsonObject>> mutations = new Action<JsonObject>[]
        {
            request => request["cliRelease"]!["schema"] = "program-kit.cli-release-identity/v2",
            request => request["cliRelease"]!["canonicalProfile"] = "program-kit.canonical-json/v2",
            request => request["cliRelease"]!["packageId"] = "Different.Package",
            request => request["cliRelease"]!["packageVersion"] = "9.9.9",
            request => request["cliRelease"]!["packageSource"]!["digest"] = "sha256:" + new string('0', 64),
            request => request["cliRelease"]!["packageDigest"] = "sha256:" + new string('1', 64),
            request => request["cliRelease"]!["commandName"] = "different-command",
            request => request["cliRelease"]!["workspaceRelativeExecutable"] = ".program-kit/tools/missing-program-kit.exe",
            request => request["cliRelease"]!["executableDigest"] = "sha256:" + new string('2', 64),
            request => request["cliRelease"]!["reportedVersion"] = "9.9.9",
            request => request["cliRelease"]!["runtimeProfile"]!["digest"] = "sha256:" + new string('3', 64),
            request => request["cliRelease"]!["claimClass"] = "canonical-byte",
        };

        for (int index = 0; index < mutations.Count; index++)
        {
            JsonObject request = (JsonObject)baseline.DeepClone();
            mutations[index](request);
            string path = workspace.PathOf($"requests/cli-mismatch-{index}.json");
            File.WriteAllBytes(path, CanonicalJson.Encode(request));
            (int exitCode, string output, _) = TestRepository.RunCli("session", "explain", "--workspace", workspace.Root, "--request", path, "--format", "json");
            JsonNode result = JsonNode.Parse(output) ?? throw new InvalidDataException(output);
            Assert.AreEqual(3, exitCode, $"mutation {index}: {output}");
            Assert.AreEqual("program-kit.session/PKSES0001", result["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>(), $"mutation {index}: {output}");
            Assert.AreEqual("none", result["effectState"]!.GetValue<string>(), $"mutation {index}: {output}");
        }
    }

    [TestMethod]
    public void Missing_installed_package_evidence_is_an_exact_cli_mismatch()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        SessionRequestPaths requests = SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root);
        JsonObject request = CanonicalJson.Parse(File.ReadAllBytes(requests.Explain)).AsObject();
        string packageName = "orbyss.programkit.cli";
        string package = workspace.PathOf($".program-kit/tools/.store/{packageName}/1.0.0-alpha.1/{packageName}/1.0.0-alpha.1/{packageName}.1.0.0-alpha.1.nupkg");
        File.Delete(package);

        (int exitCode, string output, _) = TestRepository.RunCli("session", "explain", "--workspace", workspace.Root, "--request", requests.Explain, "--format", "json");
        JsonNode result = JsonNode.Parse(output) ?? throw new InvalidDataException(output);
        Assert.AreEqual(3, exitCode);
        Assert.AreEqual("program-kit.session/PKSES0001", result["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
        Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
    }
}
