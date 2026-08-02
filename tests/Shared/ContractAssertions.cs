using System;
using System.IO;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Tests;

internal static class ContractAssertions
{
    public const string AuthorityGrant = "https://schemas.program-kit.dev/v1/authority-grant.schema.json";
    public const string FactoryRequest = "https://schemas.program-kit.dev/v1/factory-request.schema.json";
    public const string OperationResult = "https://schemas.program-kit.dev/v1/operation-result.schema.json";
    public const string Resolution = "https://schemas.program-kit.dev/v1/resolution.schema.json";
    public const string ConstructionReceipt = "https://schemas.program-kit.dev/v1/construction-receipt.schema.json";
    public const string WorkspaceSnapshot = "https://schemas.program-kit.dev/v1/workspace-snapshot.schema.json";

    public static JsonObject ParseAndValidate(string schemaId, string json)
    {
        JsonObject document = JsonNode.Parse(json) as JsonObject
            ?? throw new AssertFailedException("Expected one public JSON object.");
        AssertValid(schemaId, document);
        return document;
    }

    public static JsonObject ReadAndValidate(string schemaId, string path)
    {
        Assert.IsTrue(File.Exists(path), $"Expected public artifact: {path}");
        return ParseAndValidate(schemaId, File.ReadAllText(path));
    }

    public static void AssertValid(string schemaId, JsonObject document)
    {
        var failures = new StructuralSchemaValidator(new SchemaRegistry()).Validate(schemaId, document);
        Assert.AreEqual(0, failures.Count, string.Join(Environment.NewLine, failures));
    }
}
