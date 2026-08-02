using System;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Diagnostics;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public static class AdapterResultWriter
{
    public static JsonObject Success(AdapterOperation operation, JsonObject payload, string effectState = "none", JsonObject? programKitResult = null)
    {
        JsonObject result = new()
        {
            ["schema"] = "program-kit.spec-kit-adapter-result/v1",
            ["canonicalProfile"] = "program-kit.canonical-json/v1",
            ["operation"] = Kebab(operation),
            ["adapterRelease"] = "orbyss-program-kit-adapter@0.1.0",
            ["compatibility"] = "compatible",
            ["outcome"] = "succeeded",
            ["furthestStage"] = "completion",
            ["effectState"] = effectState,
            ["primaryDisposition"] = "complete",
            ["artifacts"] = new JsonArray(),
            ["diagnostics"] = EmptyDiagnostics(),
            ["disclosure"] = new JsonArray(),
            ["payload"] = payload,
        };
        if (programKitResult is not null) result["programKitResult"] = programKitResult.DeepClone();
        return result;
    }

    public static JsonObject NotApplicable(AdapterOperation operation, JsonObject payload) => new()
    {
        ["schema"] = "program-kit.spec-kit-adapter-result/v1",
        ["canonicalProfile"] = "program-kit.canonical-json/v1",
        ["operation"] = Kebab(operation),
        ["adapterRelease"] = "orbyss-program-kit-adapter@0.1.0",
        ["compatibility"] = "compatible",
        ["outcome"] = "not-applicable",
        ["furthestStage"] = "applicability",
        ["effectState"] = "none",
        ["primaryDisposition"] = "complete",
        ["artifacts"] = new JsonArray(),
        ["diagnostics"] = EmptyDiagnostics(),
        ["disclosure"] = new JsonArray(),
        ["payload"] = payload,
    };

    public static JsonObject Preserve(AdapterOperation operation, JsonObject programKitResult, JsonObject payload)
    {
        string publicEffect = programKitResult["effectState"]?.GetValue<string>() ?? "indeterminate";
        string effect = publicEffect switch
        {
            "none" => "adapter-files-only",
            "candidate-only" => "program-kit-candidate",
            "committed" => "program-kit-committed",
            _ => "indeterminate",
        };
        return new JsonObject
        {
            ["schema"] = "program-kit.spec-kit-adapter-result/v1",
            ["canonicalProfile"] = "program-kit.canonical-json/v1",
            ["operation"] = Kebab(operation),
            ["adapterRelease"] = "orbyss-program-kit-adapter@0.1.0",
            ["compatibility"] = "compatible",
            ["outcome"] = programKitResult["outcome"]!.DeepClone(),
            ["furthestStage"] = "invocation",
            ["effectState"] = effect,
            ["primaryDisposition"] = programKitResult["primaryDisposition"]!.DeepClone(),
            ["artifacts"] = new JsonArray(),
            ["diagnostics"] = EmptyDiagnostics(),
            ["disclosure"] = new JsonArray(),
            ["programKitResult"] = programKitResult.DeepClone(),
            ["payload"] = payload,
        };
    }

    public static JsonObject Failure(AdapterOperation operation, AdapterFailureKind kind, string outcome = "blocked")
    {
        AdapterDiagnosticDefinition definition = AdapterDiagnosticCatalog.Get(kind);
        JsonObject result = new()
        {
            ["schema"] = "program-kit.spec-kit-adapter-result/v1",
            ["canonicalProfile"] = "program-kit.canonical-json/v1",
            ["operation"] = Kebab(operation),
            ["adapterRelease"] = "orbyss-program-kit-adapter@0.1.0",
            ["compatibility"] = kind == AdapterFailureKind.UnsupportedCompatibility ? "incompatible" : "not-evaluated",
            ["outcome"] = outcome,
            ["furthestStage"] = kind == AdapterFailureKind.InvalidConfiguration ? "request" : "compatibility",
            ["effectState"] = "none",
            ["primaryDisposition"] = Kebab(definition.Disposition),
            ["artifacts"] = new JsonArray(),
            ["diagnostics"] = new JsonObject
            {
                ["total"] = 1,
                ["returned"] = 1,
                ["omitted"] = 0,
                ["grouping"] = "identity-occurrence",
                ["fullCollectionDigest"] = CanonicalDocument.Digest(new JsonArray(definition.Id)),
                ["items"] = new JsonArray(new JsonObject
                {
                    ["id"] = definition.Id,
                    ["messageKey"] = definition.MessageKey,
                    ["disposition"] = Kebab(definition.Disposition),
                    ["expected"] = "exact-compatible-input",
                    ["observed"] = "withheld-boundary-refusal",
                }),
            },
            ["disclosure"] = new JsonArray(new JsonObject { ["field"] = "external-error", ["classification"] = "withheld", ["action"] = "omitted" }),
        };
        return result;
    }

    private static JsonObject EmptyDiagnostics() => new()
    {
        ["total"] = 0,
        ["returned"] = 0,
        ["omitted"] = 0,
        ["grouping"] = "identity-occurrence",
        ["fullCollectionDigest"] = CanonicalDocument.Digest(new JsonArray()),
        ["items"] = new JsonArray(),
    };

    private static string Kebab<T>(T value) where T : struct, Enum
    {
        string name = value.ToString();
        System.Text.StringBuilder result = new();
        for (int index = 0; index < name.Length; index++)
        {
            if (index > 0 && char.IsUpper(name[index])) result.Append('-');
            result.Append(char.ToLowerInvariant(name[index]));
        }

        return result.ToString();
    }
}
