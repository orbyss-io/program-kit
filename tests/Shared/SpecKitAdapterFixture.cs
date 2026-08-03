using System;
using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SpecKitAdapter.Configuration;

namespace Orbyss.ProgramKit.Tests;

internal static class SpecKitAdapterFixture
{
    public const string FeatureKey = "003-reference-status";

    public static readonly SpecKitAdapterScenario ReferenceStatus = new(
        "Reference.Status",
        FeatureKey,
        "Reference.Status.Api",
        "/status",
        "reference-status",
        "reference-status-owner");

    public static readonly SpecKitAdapterScenario InventoryHealth = new(
        "Inventory.Health",
        "003-inventory-health",
        "Warehouse.Inventory.Api",
        "/inventory/health",
        "inventory-health",
        "inventory-health-owner");

    public static string CreateWorkspace(bool restoreFactory = true)
        => CreateWorkspace(ReferenceStatus, restoreFactory);

    public static string CreateWorkspace(SpecKitAdapterScenario scenario, bool restoreFactory = true)
    {
        string workspace = TestRepository.CreateEmptyWorkspace();
        StageReviewedFixture(workspace, scenario);
        File.WriteAllBytes(Path.Combine(workspace, "program-kit.yaml"), CanonicalJson.Encode(WorkspaceBootstrapFixture.ExactFactoryManifest()));
        if (restoreFactory)
        {
            string request = WorkspaceBootstrapFixture.WriteRequest(workspace, "restore.json", WorkspaceBootstrapFixture.RestoreRequest("factory"));
            var restored = TestRepository.RunCli("restore", "--workspace", workspace, "--request", request, "--format", "json");
            if (restored.ExitCode != 0) throw new InvalidOperationException(restored.StandardOutput + restored.StandardError);
        }

        return workspace;
    }

    public static void StageReviewedFixture(string workspace, SpecKitAdapterScenario scenario)
    {
        StageConsumerIntent(workspace, scenario);
        StageReviewedHandoff(workspace, scenario);
    }

    public static void StageConsumerIntent(string workspace, SpecKitAdapterScenario scenario)
    {
        string fixture = Path.Combine(TestRepository.Root, "tests", "Fixtures", "SpecKitAdapter", scenario.FixtureName);
        string consumerFixture = Path.Combine(workspace, "tests", "Fixtures", "SpecKitAdapter", scenario.FixtureName);
        Directory.CreateDirectory(consumerFixture);
        foreach (string name in new[] { "spec.md", "plan.md", "tasks.md" })
            File.Copy(Path.Combine(fixture, name), Path.Combine(consumerFixture, name));
        CopyDirectory(Path.Combine(fixture, "implementation"), Path.Combine(consumerFixture, "implementation"));
        string config = Path.Combine(workspace, AdapterConfigResolver.ProjectConfigPath.Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(Path.GetDirectoryName(config)!);
        File.Copy(Path.Combine(fixture, "adapter-config.yml"), config);
    }

    public static void StageReviewedHandoff(string workspace, SpecKitAdapterScenario scenario)
    {
        string fixture = Path.Combine(TestRepository.Root, "tests", "Fixtures", "SpecKitAdapter", scenario.FixtureName);
        string featureRoot = Path.Combine(workspace, "specs", scenario.FeatureKey, "program-kit");
        Directory.CreateDirectory(featureRoot);
        File.Copy(Path.Combine(fixture, "handoff.yaml"), Path.Combine(featureRoot, "handoff.yaml"));
        File.Copy(Path.Combine(fixture, "handoff-review.json"), Path.Combine(featureRoot, "handoff-review.json"));
    }

    public static JsonObject AdapterRequest(string operation)
        => AdapterRequest(ReferenceStatus, operation);

    public static JsonObject AdapterRequest(SpecKitAdapterScenario scenario, string operation) => new()
    {
        ["schema"] = "program-kit.spec-kit-adapter-request/v1",
        ["operation"] = operation,
        ["workspace"] = new JsonObject { ["identity"] = WorkspaceBootstrapFixture.WorkspaceIdentity() },
        ["feature"] = new JsonObject { ["key"] = scenario.FeatureKey },
        ["config"] = new JsonObject { ["logicalPath"] = AdapterConfigResolver.ProjectConfigPath },
        ["handoff"] = new JsonObject { ["logicalPath"] = $"specs/{scenario.FeatureKey}/program-kit/handoff.yaml" },
        ["review"] = new JsonObject { ["logicalPath"] = $"specs/{scenario.FeatureKey}/program-kit/handoff-review.json" },
        ["requestedEffect"] = "none",
        ["outputRoot"] = $"specs/{scenario.FeatureKey}/program-kit/generated",
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

internal sealed record SpecKitAdapterScenario(
    string FixtureName,
    string FeatureKey,
    string ApplicationName,
    string Route,
    string ArtifactPrefix,
    string IntentOwner);
