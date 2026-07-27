using System.Security.Cryptography;
using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Migrations;
using Orbyss.ProgramKit.Artifacts.Versioning;
using Orbyss.ProgramKit.DotNet.Schemas;
using Orbyss.ProgramKit.SecretResolution.Contracts.Schemas;

namespace Orbyss.ProgramKit.UnitTests.Workbench.Operations.Versioning;

[TestClass]
public sealed class HostToolingOperationConvergenceVersionTests
{
    [TestMethod]
    public void VersionMapAndMigrationBindExactV1V2AndOperationsRevisions()
    {
        var programKitRoot = FindProgramKitRoot();
        var extensionRoot = Path.Combine(
            programKitRoot,
            "extensions",
            "host-tooling");
        using var mapJson = JsonDocument.Parse(File.ReadAllBytes(
            Path.Combine(extensionRoot, "operation-convergence-version-map.json")));
        using var migrationJson = JsonDocument.Parse(File.ReadAllBytes(
            Path.Combine(
                extensionRoot,
                "migrations",
                "dotnet-operation-binding-v1-to-v2.migration.json")));
        var map = ReadVersionMap(mapJson.RootElement);
        var migration = ReadMigration(migrationJson.RootElement);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        VersionMapDocumentValidator mapValidator =
            new(envelopeValidator);
        MigrationDefinitionValidator migrationValidator =
            new(envelopeValidator);

        var mapValidation = mapValidator.Validate(map);
        var migrationValidation = migrationValidator.Validate(migration);

        Assert.IsTrue(mapValidation.IsValid, Format(mapValidation));
        Assert.IsTrue(migrationValidation.IsValid, Format(migrationValidation));
        Assert.HasCount(21, map.Nodes);
        Assert.HasCount(19, map.Edges);
        Assert.AreEqual(
            MigrationLossPolicy.RejectLoss,
            migration.LossPolicy);
        Assert.IsTrue(migration.IsDeterministic);
        Assert.IsTrue(migration.IsIdempotent);

        var dotNetSchemas = new DotNetSchemaModule(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        var dotNetV1 = dotNetSchemas.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-shell" &&
            resource.SchemaReference.Version.Value == "1.0.0");
        var dotNetV2 = dotNetSchemas.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-shell" &&
            resource.SchemaReference.Version.Value == "2.0.0");
        Assert.AreEqual(
            Hash(Path.Combine(
                programKitRoot,
                "schemas",
                "dotnet",
                "dotnet-shell.schema.json")),
            dotNetV1.SchemaReference.Digest.Value);
        Assert.AreEqual(
            Hash(Path.Combine(
                programKitRoot,
                "schemas",
                "dotnet",
                "dotnet-shell-2.0.0.schema.json")),
            dotNetV2.SchemaReference.Digest.Value);
        Assert.AreEqual(dotNetV2.SchemaReference, migration.Target);
        Assert.IsTrue(dotNetV2.Compatibility.MigrationReferences.Any(
            reference =>
                reference.Identity.Value ==
                    "pkid:migration:program-kit:dotnet-operation-binding-v1-to-v2" &&
                reference.Digest.Value ==
                    string.Concat(
                        "sha256:",
                        HashRaw(Path.Combine(
                            extensionRoot,
                            "migrations",
                            "dotnet-operation-binding-v1-to-v2.migration.json")))));

        foreach (var fixture in migration.FixtureReferences)
        {
            var fixturePath = Path.Combine(
                extensionRoot,
                "migrations",
                "fixtures",
                string.Concat(fixture.Identity.Name, ".json"));
            Assert.AreEqual(
                fixture.Digest.Value,
                string.Concat("sha256:", HashRaw(fixturePath)));
        }

        Assert.AreEqual(
            migration.ImplementationReference.Digest.Value,
            string.Concat(
                "sha256:",
                HashRaw(Path.Combine(
                    extensionRoot,
                    "migrations",
                    "dotnet-operation-binding-v1-to-v2.md"))));
    }

    [TestMethod]
    public void ConfigurationMigrationBindsExactV2V3AndOwnerGuidance()
    {
        var programKitRoot = FindProgramKitRoot();
        var extensionRoot = Path.Combine(
            programKitRoot,
            "extensions",
            "host-tooling");
        var migrationPath = Path.Combine(
            extensionRoot,
            "migrations",
            "dotnet-configuration-v2-to-v3.migration.json");
        using var migrationJson = JsonDocument.Parse(
            File.ReadAllBytes(migrationPath));
        var migration = ReadMigration(migrationJson.RootElement);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        MigrationDefinitionValidator validator =
            new(envelopeValidator);

        var validation = validator.Validate(migration);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.HasCount(2, migration.FixtureReferences);
        Assert.AreEqual(
            MigrationLossPolicy.RejectLoss,
            migration.LossPolicy);
        var module = new DotNetSchemaModule(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        var versionThree = module.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-shell" &&
            resource.SchemaReference.Version.Value == "3.0.0");
        Assert.AreEqual(versionThree.SchemaReference, migration.Target);
        Assert.AreEqual(
            versionThree.SchemaReference.Digest.Value,
            Hash(Path.Combine(
                programKitRoot,
                "schemas",
                "dotnet",
                "dotnet-shell-3.0.0.schema.json")));
        Assert.IsTrue(versionThree.Compatibility.MigrationReferences.Any(
            reference =>
                reference.Identity.Value ==
                    "pkid:migration:program-kit:dotnet-configuration-v2-to-v3" &&
                reference.Digest.Value ==
                    string.Concat("sha256:", HashRaw(migrationPath))));
        Assert.AreEqual(
            migration.ImplementationReference.Digest.Value,
            string.Concat(
                "sha256:",
                HashRaw(Path.Combine(
                    extensionRoot,
                    "guidance",
                    "dotnet-configuration-v2-to-v3.md"))));

        foreach (var fixture in migration.FixtureReferences)
        {
            var fixturePath = Path.Combine(
                extensionRoot,
                "migrations",
                "fixtures",
                string.Concat(fixture.Identity.Name, ".json"));
            Assert.AreEqual(
                fixture.Digest.Value,
                string.Concat("sha256:", HashRaw(fixturePath)));
        }
    }

    [TestMethod]
    public void ProviderCatalogMigrationBindsExactV3V4AndReviewedGuidance()
    {
        var programKitRoot = FindProgramKitRoot();
        var extensionRoot = Path.Combine(
            programKitRoot,
            "extensions",
            "host-tooling");
        var migrationPath = Path.Combine(
            extensionRoot,
            "migrations",
            "dotnet-configuration-v3-to-v4.migration.json");
        using var migrationJson = JsonDocument.Parse(
            File.ReadAllBytes(migrationPath));
        var migration = ReadMigration(migrationJson.RootElement);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        MigrationDefinitionValidator validator =
            new(envelopeValidator);

        var validation = validator.Validate(migration);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.HasCount(2, migration.FixtureReferences);
        var module = new DotNetSchemaModule(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        var versionFour = module.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-shell" &&
            resource.SchemaReference.Version.Value == "4.0.0");
        Assert.AreEqual(versionFour.SchemaReference, migration.Target);
        Assert.AreEqual(
            versionFour.SchemaReference.Digest.Value,
            Hash(Path.Combine(
                programKitRoot,
                "schemas",
                "dotnet",
                "dotnet-shell-4.0.0.schema.json")));
        Assert.IsTrue(versionFour.Compatibility.MigrationReferences.Any(
            reference =>
                reference.Identity.Value ==
                    "pkid:migration:program-kit:dotnet-configuration-v3-to-v4" &&
                reference.Digest.Value ==
                    string.Concat("sha256:", HashRaw(migrationPath))));
        Assert.AreEqual(
            migration.ImplementationReference.Digest.Value,
            string.Concat(
                "sha256:",
                HashRaw(Path.Combine(
                    extensionRoot,
                    "guidance",
                    "dotnet-configuration-v3-to-v4.md"))));

        foreach (var fixture in migration.FixtureReferences)
        {
            var fixturePath = Path.Combine(
                extensionRoot,
                "migrations",
                "fixtures",
                string.Concat(fixture.Identity.Name, ".json"));
            Assert.AreEqual(
                fixture.Digest.Value,
                string.Concat("sha256:", HashRaw(fixturePath)));
        }
    }

    [TestMethod]
    public void TelemetryMigrationBindsExactV4V5AndReviewedGuidance()
    {
        var programKitRoot = FindProgramKitRoot();
        var extensionRoot = Path.Combine(
            programKitRoot,
            "extensions",
            "host-tooling");
        var migrationPath = Path.Combine(
            extensionRoot,
            "migrations",
            "dotnet-telemetry-v4-to-v5.migration.json");
        using var migrationJson = JsonDocument.Parse(
            File.ReadAllBytes(migrationPath));
        var migration = ReadMigration(migrationJson.RootElement);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        MigrationDefinitionValidator validator =
            new(envelopeValidator);

        var validation = validator.Validate(migration);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.HasCount(2, migration.FixtureReferences);
        var module = new DotNetSchemaModule(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        var versionFive = module.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-shell" &&
            resource.SchemaReference.Version.Value == "5.0.0");
        Assert.AreEqual(versionFive.SchemaReference, migration.Target);
        Assert.AreEqual(
            versionFive.SchemaReference.Digest.Value,
            Hash(Path.Combine(
                programKitRoot,
                "schemas",
                "dotnet",
                "dotnet-shell-5.0.0.schema.json")));
        Assert.IsTrue(versionFive.Compatibility.MigrationReferences.Any(
            reference =>
                reference.Identity.Value ==
                    "pkid:migration:program-kit:dotnet-telemetry-v4-to-v5" &&
                reference.Digest.Value ==
                    string.Concat("sha256:", HashRaw(migrationPath))));
        Assert.AreEqual(
            migration.ImplementationReference.Digest.Value,
            string.Concat(
                "sha256:",
                HashRaw(Path.Combine(
                    extensionRoot,
                    "guidance",
                    "dotnet-telemetry-v4-to-v5.md"))));

        foreach (var fixture in migration.FixtureReferences)
        {
            var fixturePath = Path.Combine(
                extensionRoot,
                "migrations",
                "fixtures",
                string.Concat(fixture.Identity.Name, ".json"));
            Assert.AreEqual(
                fixture.Digest.Value,
                string.Concat("sha256:", HashRaw(fixturePath)));
        }
    }

    [TestMethod]
    public void TransportFailureMigrationBindsExactV5V6AndReviewedGuidance()
    {
        var programKitRoot = FindProgramKitRoot();
        var extensionRoot = Path.Combine(
            programKitRoot,
            "extensions",
            "host-tooling");
        var migrationPath = Path.Combine(
            extensionRoot,
            "migrations",
            "dotnet-transport-failures-v5-to-v6.migration.json");
        using var migrationJson = JsonDocument.Parse(
            File.ReadAllBytes(migrationPath));
        var migration = ReadMigration(migrationJson.RootElement);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        MigrationDefinitionValidator validator =
            new(envelopeValidator);

        var validation = validator.Validate(migration);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.HasCount(2, migration.FixtureReferences);
        var module = new DotNetSchemaModule(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        var versionSix = module.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-shell" &&
            resource.SchemaReference.Version.Value == "6.0.0");
        Assert.AreEqual(versionSix.SchemaReference, migration.Target);
        Assert.AreEqual(
            versionSix.SchemaReference.Digest.Value,
            Hash(Path.Combine(
                programKitRoot,
                "schemas",
                "dotnet",
                "dotnet-shell-6.0.0.schema.json")));
        Assert.IsTrue(versionSix.Compatibility.MigrationReferences.Any(
            reference =>
                reference.Identity.Value ==
                    "pkid:migration:program-kit:dotnet-transport-failures-v5-to-v6" &&
                reference.Digest.Value ==
                    string.Concat("sha256:", HashRaw(migrationPath))));
        Assert.AreEqual(
            migration.ImplementationReference.Digest.Value,
            string.Concat(
                "sha256:",
                HashRaw(Path.Combine(
                    extensionRoot,
                    "guidance",
                    "dotnet-transport-failures-v5-to-v6.md"))));

        foreach (var fixture in migration.FixtureReferences)
        {
            var fixturePath = Path.Combine(
                extensionRoot,
                "migrations",
                "fixtures",
                string.Concat(fixture.Identity.Name, ".json"));
            Assert.AreEqual(
                fixture.Digest.Value,
                string.Concat("sha256:", HashRaw(fixturePath)));
        }
    }

    [TestMethod]
    public void SecurityMigrationBindsExactV6V7AndReviewedGuidance()
    {
        var programKitRoot = FindProgramKitRoot();
        var extensionRoot = Path.Combine(
            programKitRoot,
            "extensions",
            "host-tooling");
        var migrationPath = Path.Combine(
            extensionRoot,
            "migrations",
            "dotnet-security-v6-to-v7.migration.json");
        using var migrationJson = JsonDocument.Parse(
            File.ReadAllBytes(migrationPath));
        var migration = ReadMigration(migrationJson.RootElement);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        MigrationDefinitionValidator validator =
            new(envelopeValidator);

        var validation = validator.Validate(migration);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.HasCount(2, migration.FixtureReferences);
        var module = new DotNetSchemaModule(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        var versionSeven = module.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-shell" &&
            resource.SchemaReference.Version.Value == "7.0.0");
        Assert.AreEqual(versionSeven.SchemaReference, migration.Target);
        Assert.AreEqual(
            versionSeven.SchemaReference.Digest.Value,
            Hash(Path.Combine(
                programKitRoot,
                "schemas",
                "dotnet",
                "dotnet-shell-7.0.0.schema.json")));
        Assert.IsTrue(versionSeven.Compatibility.MigrationReferences.Any(
            reference =>
                reference.Identity.Value ==
                    "pkid:migration:program-kit:dotnet-security-v6-to-v7" &&
                reference.Digest.Value ==
                    string.Concat("sha256:", HashRaw(migrationPath))));
        Assert.AreEqual(
            migration.ImplementationReference.Digest.Value,
            string.Concat(
                "sha256:",
                HashRaw(Path.Combine(
                    extensionRoot,
                    "guidance",
                    "dotnet-security-v6-to-v7.md"))));

        foreach (var fixture in migration.FixtureReferences)
        {
            var fixturePath = Path.Combine(
                extensionRoot,
                "migrations",
                "fixtures",
                string.Concat(fixture.Identity.Name, ".json"));
            Assert.AreEqual(
                fixture.Digest.Value,
                string.Concat("sha256:", HashRaw(fixturePath)));
        }
    }

    [TestMethod]
    public void PublicBrowserMigrationBindsExactV7V8AndReviewedGuidance()
    {
        var programKitRoot = FindProgramKitRoot();
        var extensionRoot = Path.Combine(
            programKitRoot,
            "extensions",
            "host-tooling");
        var migrationPath = Path.Combine(
            extensionRoot,
            "migrations",
            "dotnet-public-browser-v7-to-v8.migration.json");
        using var migrationJson = JsonDocument.Parse(
            File.ReadAllBytes(migrationPath));
        var migration = ReadMigration(migrationJson.RootElement);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        MigrationDefinitionValidator validator =
            new(envelopeValidator);

        var validation = validator.Validate(migration);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.HasCount(2, migration.FixtureReferences);
        var module = new DotNetSchemaModule(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        var versionEight = module.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-shell" &&
            resource.SchemaReference.Version.Value == "8.0.0");
        Assert.AreEqual(versionEight.SchemaReference, migration.Target);
        Assert.AreEqual(
            versionEight.SchemaReference.Digest.Value,
            Hash(Path.Combine(
                programKitRoot,
                "schemas",
                "dotnet",
                "dotnet-shell-8.0.0.schema.json")));
        Assert.IsTrue(versionEight.Compatibility.MigrationReferences.Any(
            reference =>
                reference.Identity.Value ==
                    "pkid:migration:program-kit:dotnet-public-browser-v7-to-v8" &&
                reference.Digest.Value ==
                    string.Concat("sha256:", HashRaw(migrationPath))));
        Assert.AreEqual(
            migration.ImplementationReference.Digest.Value,
            string.Concat(
                "sha256:",
                HashRaw(Path.Combine(
                    extensionRoot,
                    "guidance",
                    "dotnet-public-browser-v7-to-v8.md"))));

        foreach (var fixture in migration.FixtureReferences)
        {
            var fixturePath = Path.Combine(
                extensionRoot,
                "migrations",
                "fixtures",
                string.Concat(fixture.Identity.Name, ".json"));
            Assert.AreEqual(
                fixture.Digest.Value,
                string.Concat("sha256:", HashRaw(fixturePath)));
        }
    }

    [TestMethod]
    public void OAuthServiceClientMigrationBindsExactV8V9AndReviewedGuidance()
    {
        var programKitRoot = FindProgramKitRoot();
        var extensionRoot = Path.Combine(
            programKitRoot,
            "extensions",
            "host-tooling");
        var migrationPath = Path.Combine(
            extensionRoot,
            "migrations",
            "dotnet-oauth-service-clients-v8-to-v9.migration.json");
        using var migrationJson = JsonDocument.Parse(
            File.ReadAllBytes(migrationPath));
        var migration = ReadMigration(migrationJson.RootElement);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        MigrationDefinitionValidator validator =
            new(envelopeValidator);

        var validation = validator.Validate(migration);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.HasCount(2, migration.FixtureReferences);
        var module = new DotNetSchemaModule(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        var versionNine = module.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-shell" &&
            resource.SchemaReference.Version.Value == "9.0.0");
        Assert.AreEqual(versionNine.SchemaReference, migration.Target);
        Assert.AreEqual(
            versionNine.SchemaReference.Digest.Value,
            Hash(Path.Combine(
                programKitRoot,
                "schemas",
                "dotnet",
                "dotnet-shell-9.0.0.schema.json")));
        Assert.IsTrue(versionNine.Compatibility.MigrationReferences.Any(
            reference =>
                reference.Identity.Value ==
                    "pkid:migration:program-kit:dotnet-oauth-service-clients-v8-to-v9" &&
                reference.Digest.Value ==
                    string.Concat("sha256:", HashRaw(migrationPath))));
        Assert.AreEqual(
            migration.ImplementationReference.Digest.Value,
            string.Concat(
                "sha256:",
                HashRaw(Path.Combine(
                    extensionRoot,
                    "guidance",
                    "dotnet-oauth-service-clients-v8-to-v9.md"))));

        foreach (var fixture in migration.FixtureReferences)
        {
            var fixturePath = Path.Combine(
                extensionRoot,
                "migrations",
                "fixtures",
                string.Concat(fixture.Identity.Name, ".json"));
            Assert.AreEqual(
                fixture.Digest.Value,
                string.Concat("sha256:", HashRaw(fixturePath)));
        }
    }

    [TestMethod]
    public void AzureKeyVaultMigrationBindsExactV9V10AndReviewedGuidance()
    {
        var programKitRoot = FindProgramKitRoot();
        var extensionRoot = Path.Combine(
            programKitRoot,
            "extensions",
            "host-tooling");
        var migrationPath = Path.Combine(
            extensionRoot,
            "migrations",
            "dotnet-azure-key-vault-v9-to-v10.migration.json");
        using var migrationJson = JsonDocument.Parse(
            File.ReadAllBytes(migrationPath));
        var migration = ReadMigration(migrationJson.RootElement);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        MigrationDefinitionValidator validator =
            new(envelopeValidator);

        var validation = validator.Validate(migration);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.HasCount(2, migration.FixtureReferences);
        var module = new DotNetSchemaModule(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        var versionTen = module.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-shell" &&
            resource.SchemaReference.Version.Value == "10.0.0");
        Assert.AreEqual(versionTen.SchemaReference, migration.Target);
        Assert.AreEqual(
            versionTen.SchemaReference.Digest.Value,
            Hash(Path.Combine(
                programKitRoot,
                "schemas",
                "dotnet",
                "dotnet-shell-10.0.0.schema.json")));
        Assert.IsTrue(versionTen.Compatibility.MigrationReferences.Any(
            reference =>
                reference.Identity.Value ==
                    "pkid:migration:program-kit:dotnet-azure-key-vault-v9-to-v10" &&
                reference.Digest.Value ==
                    string.Concat("sha256:", HashRaw(migrationPath))));
        Assert.AreEqual(
            migration.ImplementationReference.Digest.Value,
            string.Concat(
                "sha256:",
                HashRaw(Path.Combine(
                    extensionRoot,
                    "guidance",
                    "dotnet-azure-key-vault-v9-to-v10.md"))));

        foreach (var fixture in migration.FixtureReferences)
        {
            var fixturePath = Path.Combine(
                extensionRoot,
                "migrations",
                "fixtures",
                string.Concat(fixture.Identity.Name, ".json"));
            Assert.AreEqual(
                fixture.Digest.Value,
                string.Concat("sha256:", HashRaw(fixturePath)));
        }
    }

    [TestMethod]
    public void FastEndpointsMigrationBindsExactV10V11AndReviewedGuidance()
    {
        var programKitRoot = FindProgramKitRoot();
        var extensionRoot = Path.Combine(
            programKitRoot,
            "extensions",
            "host-tooling");
        var migrationPath = Path.Combine(
            extensionRoot,
            "migrations",
            "dotnet-fastendpoints-v10-to-v11.migration.json");
        using var migrationJson = JsonDocument.Parse(
            File.ReadAllBytes(migrationPath));
        var migration = ReadMigration(migrationJson.RootElement);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        MigrationDefinitionValidator validator =
            new(envelopeValidator);

        var validation = validator.Validate(migration);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.HasCount(2, migration.FixtureReferences);
        var module = new DotNetSchemaModule(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        var versionEleven = module.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-shell" &&
            resource.SchemaReference.Version.Value == "11.0.0");
        Assert.AreEqual(versionEleven.SchemaReference, migration.Target);
        Assert.AreEqual(
            versionEleven.SchemaReference.Digest.Value,
            Hash(Path.Combine(
                programKitRoot,
                "schemas",
                "dotnet",
                "dotnet-shell-11.0.0.schema.json")));
        Assert.IsTrue(versionEleven.Compatibility.MigrationReferences.Any(
            reference =>
                reference.Identity.Value ==
                    "pkid:migration:program-kit:dotnet-fastendpoints-v10-to-v11" &&
                reference.Digest.Value ==
                    string.Concat("sha256:", HashRaw(migrationPath))));
        Assert.AreEqual(
            migration.ImplementationReference.Digest.Value,
            string.Concat(
                "sha256:",
                HashRaw(Path.Combine(
                    extensionRoot,
                    "guidance",
                    "dotnet-fastendpoints-v10-to-v11.md"))));

        foreach (var fixture in migration.FixtureReferences)
        {
            var fixturePath = Path.Combine(
                extensionRoot,
                "migrations",
                "fixtures",
                string.Concat(fixture.Identity.Name, ".json"));
            Assert.AreEqual(
                fixture.Digest.Value,
                string.Concat("sha256:", HashRaw(fixturePath)));
        }
    }

    [TestMethod]
    public void ProviderCatalogMigrationBindsExactV1V2AndReviewedGuidance()
    {
        var programKitRoot = FindProgramKitRoot();
        var extensionRoot = Path.Combine(
            programKitRoot,
            "extensions",
            "host-tooling");
        var migrationPath = Path.Combine(
            extensionRoot,
            "migrations",
            "dotnet-configuration-provider-catalog-v1-to-v2.migration.json");
        using var migrationJson = JsonDocument.Parse(
            File.ReadAllBytes(migrationPath));
        var migration = ReadMigration(migrationJson.RootElement);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        MigrationDefinitionValidator validator =
            new(envelopeValidator);

        var validation = validator.Validate(migration);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.HasCount(2, migration.FixtureReferences);
        var module = new DotNetSchemaModule(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        var versionTwo = module.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:dotnet-configuration-provider-catalog" &&
            resource.SchemaReference.Version.Value == "2.0.0");
        Assert.AreEqual(versionTwo.SchemaReference, migration.Target);
        Assert.Contains(
            new ArtifactReference(
                new ProgramKitIdentifier(
                    "pkid:migration:program-kit:dotnet-configuration-provider-catalog-v1-to-v2"),
                new SemanticVersion("1.0.0"),
                new Sha256Digest(
                    string.Concat("sha256:", HashRaw(migrationPath)))),
            versionTwo.Compatibility.MigrationReferences);
        Assert.AreEqual(
            migration.ImplementationReference.Digest.Value,
            Hash(Path.Combine(
                extensionRoot,
                "guidance",
                "dotnet-configuration-provider-catalog-v1-to-v2.md")));
    }

    [TestMethod]
    public void SecretResolutionVersionMapBindsAllInitialSchemaRevisions()
    {
        var programKitRoot = FindProgramKitRoot();
        using var mapJson = JsonDocument.Parse(File.ReadAllBytes(
            Path.Combine(
                programKitRoot,
                "extensions",
                "host-tooling",
                "secret-resolution-version-map.json")));
        var map = ReadVersionMap(mapJson.RootElement);
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        VersionMapDocumentValidator validator =
            new(envelopeValidator);
        SecretResolutionSchemaModule module = new();

        var validation = validator.Validate(map);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.HasCount(3, map.Nodes);
        Assert.IsEmpty(map.Edges);
        Assert.AreSequenceEqual(
            module.Resources
                .Select(static resource => resource.SchemaReference)
                .OrderBy(static reference => reference.Identity.Value)
                .ToArray(),
            map.Nodes
                .Select(static node => node.Revision)
                .OrderBy(static reference => reference.Identity.Value)
                .ToArray());
    }

    private static VersionMapDocument ReadVersionMap(JsonElement root) =>
        new(
            root.GetProperty("nodes")
                .EnumerateArray()
                .Select(ReadNode)
                .ToImmutableArray(),
            root.GetProperty("edges")
                .EnumerateArray()
                .Select(ReadEdge)
                .ToImmutableArray());

    private static VersionRevisionNode ReadNode(JsonElement value) =>
        new(
            ReadReference(value.GetProperty("revision")),
            ReadBoundaryKind(value.GetProperty("kind").GetString()!),
            new ProgramKitIdentifier(value.GetProperty("ownerId").GetString()!),
            value.GetProperty("evidenceReferences")
                .EnumerateArray()
                .Select(ReadReference)
                .ToImmutableArray());

    private static VersionDependencyEdge ReadEdge(JsonElement value) =>
        new(
            new ProgramKitIdentifier(value.GetProperty("id").GetString()!),
            ReadReference(value.GetProperty("source")),
            new ProgramKitIdentifier(
                value.GetProperty("targetIdentity").GetString()!),
            ReadDependencyKind(value.GetProperty("kind").GetString()!),
            new SemanticVersionRange(
                value.GetProperty("acceptedRange").GetString()!),
            ReadReference(value.GetProperty("resolution")),
            value.GetProperty("exposure").GetString() == "public"
                ? DependencyExposure.Public
                : DependencyExposure.Private,
            value.GetProperty("compatibilityDimensions")
                .EnumerateArray()
                .Select(static item => item.GetString() switch
                {
                    "wire-read" => CompatibilityDimension.WireRead,
                    "wire-write" => CompatibilityDimension.WireWrite,
                    "source-api" => CompatibilityDimension.SourceApi,
                    _ => throw new InvalidDataException(
                        "Unexpected compatibility dimension."),
                })
                .ToImmutableArray(),
            value.GetProperty("evidenceReferences")
                .EnumerateArray()
                .Select(ReadReference)
                .ToImmutableArray());

    private static MigrationDefinition ReadMigration(JsonElement value) =>
        new(
            new ProgramKitIdentifier(
                value.GetProperty("sourceIdentity").GetString()!),
            new SemanticVersionRange(
                value.GetProperty("sourceRange").GetString()!),
            ReadReference(value.GetProperty("target")),
            MigrationMode.SourceGuidance,
            value.GetProperty("preconditions")
                .EnumerateArray()
                .Select(static precondition => new MigrationPrecondition(
                    precondition.GetProperty("code").GetString()!,
                    precondition.GetProperty("description").GetString()!,
                    precondition.GetProperty("evidenceReferences")
                        .EnumerateArray()
                        .Select(ReadReference)
                        .ToImmutableArray()))
                .ToImmutableArray(),
            MigrationLossPolicy.RejectLoss,
            value.GetProperty("isDeterministic").GetBoolean(),
            value.GetProperty("isIdempotent").GetBoolean(),
            MigrationFailurePolicy.PreserveSourceAndReport,
            ReadReference(value.GetProperty("implementationReference")),
            value.GetProperty("fixtureReferences")
                .EnumerateArray()
                .Select(ReadReference)
                .ToImmutableArray());

    private static ArtifactReference ReadReference(JsonElement value) =>
        new(
            new ProgramKitIdentifier(value.GetProperty("identity").GetString()!),
            new SemanticVersion(value.GetProperty("version").GetString()!),
            new Sha256Digest(value.GetProperty("digest").GetString()!));

    private static VersionBoundaryKind ReadBoundaryKind(string value) =>
        value switch
        {
            "schema" => VersionBoundaryKind.Schema,
            _ => throw new InvalidDataException("Unexpected boundary kind."),
        };

    private static VersionDependencyKind ReadDependencyKind(string value) =>
        value switch
        {
            "migrates" => VersionDependencyKind.Migrates,
            "uses-contract" => VersionDependencyKind.UsesContract,
            _ => throw new InvalidDataException("Unexpected dependency kind."),
        };

    private static string Hash(string path) =>
        string.Concat("sha256:", HashRaw(path));

    private static string HashRaw(string path) =>
        Convert.ToHexString(
                SHA256.HashData(File.ReadAllBytes(path)))
            .ToLowerInvariant();

    private static string FindProgramKitRoot()
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(current.FullName, "ProgramKit.sln")))
            {
                return current.FullName;
            }

            current = current.Parent;
        }

        throw new DirectoryNotFoundException(
            "The Program Kit repository root could not be found.");
    }

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(static diagnostic =>
                string.Concat(
                    diagnostic.Id,
                    " ",
                    diagnostic.Path,
                    " ",
                    diagnostic.Message)));
}
