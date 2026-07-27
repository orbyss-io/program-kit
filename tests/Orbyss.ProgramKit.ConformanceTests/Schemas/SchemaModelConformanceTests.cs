using System.Reflection;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;

namespace Orbyss.ProgramKit.ConformanceTests.Schemas;

[TestClass]
public sealed class SchemaModelConformanceTests
{
    private static readonly ModelSchemaBinding[] Bindings =
    [
        Root<ArtifactEnvelope<string>>("artifacts/artifact-envelope.schema.json"),
        Nested<ArtifactContract>(
            "artifacts/artifact-envelope.schema.json",
            "properties",
            "contract"),
        Nested<ArtifactIdentity>(
            "artifacts/artifact-envelope.schema.json",
            "properties",
            "artifact"),
        Nested<ArtifactCompatibility>(
            "artifacts/artifact-envelope.schema.json",
            "properties",
            "compatibility"),
        Nested<ArtifactProvenance>(
            "artifacts/artifact-envelope.schema.json",
            "properties",
            "provenance"),
        Nested<ArtifactRepresentation>(
            "artifacts/artifact-envelope.schema.json",
            "properties",
            "representation"),
        Nested<ArtifactIntegrity>(
            "artifacts/artifact-envelope.schema.json",
            "properties",
            "integrity"),
        Root<VersionedComponentManifest>(
            "artifacts/versioned-component-manifest.schema.json"),
        Root<VersionMapDocument>("artifacts/version-map.schema.json"),
        Root<VersionSelectionDocument>("artifacts/version-selection.schema.json"),
        Root<MigrationDefinition>("artifacts/migration-definition.schema.json"),
        Root<MigrationAssessment>("artifacts/migration-assessment.schema.json"),
        Root<ArchitectureDesignDocument>(
            "architecture/architecture-design.schema.json"),
        Root<ArchitectureDesignDocumentV2>(
            "architecture/architecture-design-2.0.0.schema.json"),
        Root<StaticConformanceDisposition>(
            "architecture/static-conformance-disposition.schema.json"),
        Root<CSharpBuildGateDefinitionDocument>(
            "csharp-build-gates/csharp-build-gate-definition-1.0.0.schema.json"),
        Root<CSharpBuildGateSelectionLockDocument>(
            "csharp-build-gates/csharp-build-gate-selection-lock-1.0.0.schema.json"),
        Root<CSharpGateSuppressionLedger>(
            "csharp-build-gates/csharp-build-gate-suppression-ledger-1.0.0.schema.json"),
        Root<CSharpGateParticipationReceiptDocument>(
            "csharp-build-gates/csharp-build-gate-participation-receipt-1.0.0.schema.json"),
        Root<CSharpBuildGateVerificationEvidenceDocument>(
            "csharp-build-gates/csharp-build-gate-verification-evidence-1.0.0.schema.json"),
        Root<ArtifactDecision>("architecture/artifact-decision.schema.json"),
        Root<DotNetTargetProfile>(
            "architecture/dotnet-target-profile.schema.json"),
        Root<StructuralPatternCatalog>(
            "architecture/structural-pattern-catalog.schema.json"),
        Root<TestSpecification>("quality/test-specification.schema.json"),
        Root<ExecutionProfile>("quality/execution-profile.schema.json"),
        Root<TestEvidence>("quality/test-evidence.schema.json"),
        Root<IndependentReview>("quality/independent-review.schema.json"),
        Root<ImplementationPlanDocument>(
            "planning/implementation-plan-2.0.0.schema.json"),
        Root<ImplementationPlanDocumentV3>(
            "planning/implementation-plan-3.0.0.schema.json"),
        Nested<PlanWorkUnit>(
            "planning/definitions-2.0.0.schema.json",
            "$defs",
            "planWorkUnit"),
        Nested<PlannedArtifactReference>(
            "planning/definitions-2.0.0.schema.json",
            "$defs",
            "plannedArtifactReference"),
        Nested<PlanWorkUnitV3>(
            "planning/definitions-3.0.0.schema.json",
            "$defs",
            "planWorkUnit"),
        Root<DesignPlanApprovalRecord>(
            "planning/design-plan-approval.schema.json"),
        Root<OperationContractDescriptor>(
            "operations/operation-contract-descriptor.schema.json"),
        Root<OperationContractCatalog>(
            "operations/operation-contract-catalog.schema.json"),
        Root<OperationInvocationDocument>(
            "operations/operation-invocation.schema.json"),
        Root<OperationProgressDocument>(
            "operations/operation-progress.schema.json"),
        Root<OperationResultDocument>(
            "operations/operation-result.schema.json"),
        Nested<OperationResultContract>(
            "operations/definitions.schema.json",
            "$defs",
            "resultContract"),
        Nested<RelatedOperationContract>(
            "operations/definitions.schema.json",
            "$defs",
            "relatedOperationContract"),
        Nested<OperationDeprecation>(
            "operations/definitions.schema.json",
            "$defs",
            "deprecation"),
        Nested<OperationDiagnosticDocument>(
            "operations/definitions.schema.json",
            "$defs",
            "operationDiagnosticDocument"),
        Root<CapabilityAvailabilitySnapshot>(
            "development/capability-availability-snapshot.schema.json"),
        Root<DevelopmentRoutingResult>(
            "development/development-routing-result.schema.json"),
        Root<DevelopmentReceipt>(
            "development/development-receipt.schema.json"),
        Root<TaskDefinition>("tasks/task-definition.schema.json"),
        Root<TaskRequest<string>>("tasks/task-request.schema.json"),
        Root<TaskInstance>("tasks/task-instance.schema.json"),
        Root<TaskAttempt>("tasks/task-attempt.schema.json"),
        Root<TaskActivationBinding>(
            "tasks/task-activation-binding.schema.json"),
        Root<TaskScheduleDefinition>(
            "tasks/task-schedule-definition.schema.json"),
        Root<TaskOccurrence>("tasks/task-occurrence.schema.json"),
    ];

    [TestMethod]
    public void DurableRootModelsMatchTheirCanonicalSchemaPropertyNames()
    {
        var schemaFiles = ConformanceInputs
            .Files("Schemas", "*.schema.json")
            .Where(file => !Normalize(file).Contains(
                "/dev-containers/",
                StringComparison.Ordinal))
            .ToArray();
        var schemasById = schemaFiles.ToDictionary(
            file => ReadStringAtPath(File.ReadAllBytes(file), ["$id"])
                ?? throw new AssertFailedException($"{file} has no $id."),
            StringComparer.Ordinal);

        foreach (var binding in Bindings)
        {
            var schemaFile = schemaFiles.Single(file =>
                Normalize(file).EndsWith(binding.SchemaSuffix, StringComparison.Ordinal));
            var location = ResolveLocation(
                schemaFile,
                binding.Pointer,
                schemasById);
            var bytes = File.ReadAllBytes(location.SchemaFile);
            var required = ReadStringArrayAtPath(
                bytes,
                [.. location.Pointer, "required"]);
            var properties = ReadObjectPropertyNamesAtPath(
                bytes,
                [.. location.Pointer, "properties"]);
            var modelParameters = GetWireConstructorParameters(binding.ModelType);

            Assert.IsTrue(
                required.SetEquals(modelParameters),
                $"{binding.ModelType.FullName}: schema required " +
                $"[{string.Join(", ", required)}], model [{string.Join(", ", modelParameters)}].");
            Assert.IsTrue(
                properties.SetEquals(modelParameters),
                $"{binding.ModelType.FullName}: schema properties " +
                $"[{string.Join(", ", properties)}], model [{string.Join(", ", modelParameters)}].");
        }
    }

    private static ModelSchemaBinding Root<T>(string schemaSuffix) =>
        new(typeof(T), schemaSuffix, []);

    private static ModelSchemaBinding Nested<T>(
        string schemaSuffix,
        params string[] pointer) =>
        new(typeof(T), schemaSuffix, pointer);

    private static SchemaLocation ResolveLocation(
        string schemaFile,
        string[] pointer,
        Dictionary<string, string> schemasById)
    {
        if (pointer.Length != 0)
        {
            return new SchemaLocation(schemaFile, pointer);
        }

        var bytes = File.ReadAllBytes(schemaFile);
        var reference = ReadStringAtPath(bytes, ["$ref"]);
        if (reference is null)
        {
            return new SchemaLocation(schemaFile, []);
        }

        var hashIndex = reference.IndexOf('#');
        var schemaId = hashIndex < 0 ? reference : reference[..hashIndex];
        Assert.IsTrue(schemasById.TryGetValue(schemaId, out var referencedFile), reference);
        var fragment = hashIndex < 0 ? string.Empty : reference[(hashIndex + 1)..];
        var segments = fragment
            .Split('/', StringSplitOptions.RemoveEmptyEntries)
            .Select(segment => segment
                .Replace("~1", "/", StringComparison.Ordinal)
                .Replace("~0", "~", StringComparison.Ordinal))
            .ToArray();
        return new SchemaLocation(referencedFile, segments);
    }

    private static HashSet<string> GetWireConstructorParameters(Type modelType)
    {
        var constructor = modelType
            .GetConstructors(BindingFlags.Public | BindingFlags.Instance)
            .OrderByDescending(candidate => candidate.GetParameters().Length)
            .FirstOrDefault()
            ?? throw new AssertFailedException($"{modelType.FullName} has no public constructor.");
        return constructor
            .GetParameters()
            .Select(parameter => parameter.Name
                ?? throw new AssertFailedException(
                    $"{modelType.FullName} has an unnamed constructor parameter."))
            .Select(ToCamelCase)
            .ToHashSet(StringComparer.Ordinal);
    }

    private static string ToCamelCase(string value) =>
        char.ToLowerInvariant(value[0]) + value[1..];

    private static string Normalize(string path) =>
        path.Replace('\\', '/');

    private static string? ReadStringAtPath(
        ReadOnlySpan<byte> json,
        IReadOnlyList<string> path)
    {
        var reader = new Utf8JsonReader(json);
        if (!reader.Read() || reader.TokenType != JsonTokenType.StartObject)
        {
            return null;
        }

        foreach (var segment in path)
        {
            if (!MoveToProperty(ref reader, segment))
            {
                return null;
            }
        }

        return reader.TokenType == JsonTokenType.String ? reader.GetString() : null;
    }

    private static HashSet<string> ReadStringArrayAtPath(
        ReadOnlySpan<byte> json,
        IReadOnlyList<string> path)
    {
        var reader = new Utf8JsonReader(json);
        MoveToPath(ref reader, path);
        Assert.AreEqual(JsonTokenType.StartArray, reader.TokenType);
        var values = new HashSet<string>(StringComparer.Ordinal);
        while (reader.Read() && reader.TokenType != JsonTokenType.EndArray)
        {
            Assert.AreEqual(JsonTokenType.String, reader.TokenType);
            Assert.IsTrue(values.Add(reader.GetString()!));
        }

        return values;
    }

    private static HashSet<string> ReadObjectPropertyNamesAtPath(
        ReadOnlySpan<byte> json,
        IReadOnlyList<string> path)
    {
        var reader = new Utf8JsonReader(json);
        MoveToPath(ref reader, path);
        Assert.AreEqual(JsonTokenType.StartObject, reader.TokenType);
        var names = new HashSet<string>(StringComparer.Ordinal);
        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            Assert.AreEqual(JsonTokenType.PropertyName, reader.TokenType);
            Assert.IsTrue(names.Add(reader.GetString()!));
            Assert.IsTrue(reader.Read());
            reader.Skip();
        }

        return names;
    }

    private static void MoveToPath(
        ref Utf8JsonReader reader,
        IReadOnlyList<string> path)
    {
        Assert.IsTrue(reader.Read());
        Assert.AreEqual(JsonTokenType.StartObject, reader.TokenType);
        foreach (var segment in path)
        {
            Assert.IsTrue(MoveToProperty(ref reader, segment), segment);
        }
    }

    private static bool MoveToProperty(
        ref Utf8JsonReader reader,
        string propertyName)
    {
        if (reader.TokenType != JsonTokenType.StartObject)
        {
            return false;
        }

        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            Assert.AreEqual(JsonTokenType.PropertyName, reader.TokenType);
            var currentName = reader.GetString();
            Assert.IsTrue(reader.Read());
            if (string.Equals(currentName, propertyName, StringComparison.Ordinal))
            {
                return true;
            }

            reader.Skip();
        }

        return false;
    }

}
