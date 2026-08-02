using System.IO;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class WorkspaceBootstrapContractTests
{
    [TestMethod]
    public void Init_is_neutral_idempotent_and_keeps_all_five_states_distinct()
    {
        string workspace = TestRepository.CreateEmptyWorkspace();
        try
        {
            string request = WorkspaceBootstrapFixture.WriteRequest(workspace, "init.json", WorkspaceBootstrapFixture.InitRequest());
            var first = TestRepository.RunCli("init", "--workspace", workspace, "--request", request, "--format", "json");
            Assert.AreEqual(0, first.ExitCode, first.StandardOutput + first.StandardError);
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, first.StandardOutput);
            JsonObject states = result["payload"]!["states"]!.AsObject();
            Assert.IsTrue(states["installed"]!.GetValue<bool>());
            Assert.IsTrue(states["available"]!.GetValue<bool>());
            Assert.IsFalse(states["selected"]!.GetValue<bool>());
            Assert.IsFalse(states["activated"]!.GetValue<bool>());
            Assert.IsFalse(states["authorized"]!.GetValue<bool>());
            JsonObject manifest = new Orbyss.ProgramKit.Kernel.Intake.RestrictedYamlParser().Parse(File.ReadAllBytes(Path.Combine(workspace, "program-kit.yaml"))).AsObject();
            ContractAssertions.AssertValid(ContractSchemaResources.WorkspaceManifestId, manifest);
            Assert.AreEqual(0, manifest["factory"]!["selections"]!.AsArray().Count);

            string before = TestRepository.DigestTree(workspace);
            var second = TestRepository.RunCli("init", "--workspace", workspace, "--request", request, "--format", "json");
            Assert.AreEqual(0, second.ExitCode, second.StandardOutput + second.StandardError);
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
            Assert.IsTrue(JsonNode.Parse(second.StandardOutput)!["payload"]!["unchanged"]!.GetValue<bool>());
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Catalog_is_exact_schema_valid_and_performs_zero_writes()
    {
        string workspace = TestRepository.CreateEmptyWorkspace();
        try
        {
            string request = WorkspaceBootstrapFixture.WriteRequest(workspace, "catalog.json", WorkspaceBootstrapFixture.CatalogRequest());
            string before = TestRepository.DigestTree(workspace);
            var execution = TestRepository.RunCli("catalog", "list", "--workspace", workspace, "--request", request, "--format", "json");
            Assert.AreEqual(0, execution.ExitCode, execution.StandardOutput + execution.StandardError);
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
            JsonObject catalog = result["payload"]!["catalog"]!.AsObject();
            ContractAssertions.AssertValid(ContractSchemaResources.DistributionCatalogId, catalog);
            Assert.IsTrue(catalog["providers"]!.AsArray().Count > 0);
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Base_restore_accepts_zero_profiles_while_factory_restore_requires_an_exact_selection()
    {
        string workspace = TestRepository.CreateEmptyWorkspace();
        try
        {
            string init = WorkspaceBootstrapFixture.WriteRequest(workspace, "init.json", WorkspaceBootstrapFixture.InitRequest());
            Assert.AreEqual(0, TestRepository.RunCli("init", "--workspace", workspace, "--request", init, "--format", "json").ExitCode);
            string request = WorkspaceBootstrapFixture.WriteRequest(workspace, "restore-base.json", WorkspaceBootstrapFixture.RestoreRequest("base"));
            var restored = TestRepository.RunCli("restore", "--workspace", workspace, "--request", request, "--format", "json");
            Assert.AreEqual(0, restored.ExitCode, restored.StandardOutput + restored.StandardError);
            JsonObject lockDocument = CanonicalJson.Parse(File.ReadAllBytes(Path.Combine(workspace, "program-kit.lock.json"))).AsObject();
            ContractAssertions.AssertValid(ContractSchemaResources.WorkspaceLockId, lockDocument);
            Assert.AreEqual(0, lockDocument["selections"]!.AsArray().Count);

            string factory = WorkspaceBootstrapFixture.WriteRequest(workspace, "restore-factory.json", WorkspaceBootstrapFixture.RestoreRequest("factory"));
            var refused = TestRepository.RunCli("restore", "--workspace", workspace, "--request", factory, "--format", "json");
            Assert.AreEqual(3, refused.ExitCode);
            JsonObject refusal = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, refused.StandardOutput);
            Assert.AreEqual("program-kit.kernel/PKRES0001", refusal["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
            Assert.AreEqual("none", refusal["effectState"]!.GetValue<string>());
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Factory_restore_resolves_only_exact_registered_profile_and_refuses_duplicate_aliases()
    {
        string workspace = TestRepository.CreateEmptyWorkspace();
        try
        {
            File.WriteAllBytes(Path.Combine(workspace, "program-kit.yaml"), CanonicalJson.Encode(WorkspaceBootstrapFixture.ExactFactoryManifest()));
            string request = WorkspaceBootstrapFixture.WriteRequest(workspace, "restore.json", WorkspaceBootstrapFixture.RestoreRequest("factory"));
            var exact = TestRepository.RunCli("restore", "--workspace", workspace, "--request", request, "--format", "json");
            Assert.AreEqual(0, exact.ExitCode, exact.StandardOutput + exact.StandardError);

            File.WriteAllBytes(Path.Combine(workspace, "program-kit.yaml"), CanonicalJson.Encode(WorkspaceBootstrapFixture.ExactFactoryManifest(duplicateAlias: true)));
            var duplicate = TestRepository.RunCli("restore", "--workspace", workspace, "--request", request, "--format", "json");
            Assert.AreEqual(3, duplicate.ExitCode);
            Assert.AreEqual("none", JsonNode.Parse(duplicate.StandardOutput)!["effectState"]!.GetValue<string>());
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }
}
