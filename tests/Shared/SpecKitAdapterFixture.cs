using System;
using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SpecKitAdapter.Configuration;

namespace Orbyss.ProgramKit.Tests;

internal static class SpecKitAdapterFixture
{
    public const string FeatureKey = "003-reference-status";

    public static string CreateWorkspace(bool restoreFactory = true)
    {
        string workspace = TestRepository.CreateEmptyWorkspace();
        string fixture = Path.Combine(TestRepository.Root, "tests", "Fixtures", "SpecKitAdapter", "Reference.Status");
        CopyDirectory(fixture, Path.Combine(workspace, "tests", "Fixtures", "SpecKitAdapter", "Reference.Status"));
        string config = Path.Combine(workspace, AdapterConfigResolver.ProjectConfigPath.Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(Path.GetDirectoryName(config)!);
        File.Copy(Path.Combine(fixture, "adapter-config.yml"), config);
        string featureRoot = Path.Combine(workspace, "specs", FeatureKey, "program-kit");
        Directory.CreateDirectory(featureRoot);
        File.Copy(Path.Combine(fixture, "handoff.yaml"), Path.Combine(featureRoot, "handoff.yaml"));
        File.Copy(Path.Combine(fixture, "handoff-review.json"), Path.Combine(featureRoot, "handoff-review.json"));
        File.WriteAllBytes(Path.Combine(workspace, "program-kit.yaml"), CanonicalJson.Encode(WorkspaceBootstrapFixture.ExactFactoryManifest()));
        if (restoreFactory)
        {
            string request = WorkspaceBootstrapFixture.WriteRequest(workspace, "restore.json", WorkspaceBootstrapFixture.RestoreRequest("factory"));
            var restored = TestRepository.RunCli("restore", "--workspace", workspace, "--request", request, "--format", "json");
            if (restored.ExitCode != 0) throw new InvalidOperationException(restored.StandardOutput + restored.StandardError);
        }

        return workspace;
    }

    public static JsonObject AdapterRequest(string operation) => new()
    {
        ["schema"] = "program-kit.spec-kit-adapter-request/v1",
        ["operation"] = operation,
        ["workspace"] = new JsonObject { ["identity"] = WorkspaceBootstrapFixture.WorkspaceIdentity() },
        ["feature"] = new JsonObject { ["key"] = FeatureKey },
        ["config"] = new JsonObject { ["logicalPath"] = AdapterConfigResolver.ProjectConfigPath },
        ["handoff"] = new JsonObject { ["logicalPath"] = $"specs/{FeatureKey}/program-kit/handoff.yaml" },
        ["review"] = new JsonObject { ["logicalPath"] = $"specs/{FeatureKey}/program-kit/handoff-review.json" },
        ["requestedEffect"] = "none",
        ["outputRoot"] = $"specs/{FeatureKey}/program-kit/generated",
    };

    public static string RepositoryFixture(string relative) => Path.Combine(
        TestRepository.Root,
        "tests",
        "Fixtures",
        "SpecKitAdapter",
        relative.Replace('/', Path.DirectorySeparatorChar));

    private static void CopyDirectory(string source, string destination)
    {
        Directory.CreateDirectory(destination);
        foreach (string file in Directory.EnumerateFiles(source)) File.Copy(file, Path.Combine(destination, Path.GetFileName(file)));
        foreach (string directory in Directory.EnumerateDirectories(source)) CopyDirectory(directory, Path.Combine(destination, Path.GetFileName(directory)));
    }
}
