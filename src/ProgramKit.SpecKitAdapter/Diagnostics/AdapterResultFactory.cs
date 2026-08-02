using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.SpecKitAdapter.Diagnostics;

public static class AdapterResultFactory
{
    public static JsonObject Failure(AdapterOperation operation, AdapterFailureKind kind, string outcome)
    {
        Diagnostic diagnostic = AdapterDiagnosticFactory.Create(
            kind,
            DisclosureFilter.PublicText("adapter-boundary"),
            DisclosureFilter.PublicText("exact-compatible-input"),
            DisclosureFilter.PublicText("withheld-boundary-refusal"));
        JsonObject projected = Project(diagnostic);
        return new JsonObject
        {
            ["schema"] = "program-kit.spec-kit-adapter-result/v1",
            ["canonicalProfile"] = "program-kit.canonical-json/v1",
            ["operation"] = Kebab(operation),
            ["adapterRelease"] = "orbyss-program-kit-adapter@0.1.0",
            ["compatibility"] = kind == AdapterFailureKind.UnsupportedCompatibility ? "incompatible" : "not-evaluated",
            ["outcome"] = outcome,
            ["furthestStage"] = Stage(kind),
            ["effectState"] = Effect(operation, kind),
            ["primaryDisposition"] = Kebab(diagnostic.Disposition),
            ["artifacts"] = new JsonArray(),
            ["diagnostics"] = new JsonObject
            {
                ["total"] = 1,
                ["returned"] = 1,
                ["omitted"] = 0,
                ["grouping"] = "identity-occurrence",
                ["fullCollectionDigest"] = CanonicalDocument.Digest(new JsonArray(projected.DeepClone())),
                ["items"] = new JsonArray(projected),
            },
            ["disclosure"] = new JsonArray(
                new JsonObject { ["field"] = "external-stdout", ["classification"] = "withheld", ["action"] = "omitted" },
                new JsonObject { ["field"] = "external-stderr", ["classification"] = "withheld", ["action"] = "omitted" },
                new JsonObject { ["field"] = "exception-detail", ["classification"] = "withheld", ["action"] = "omitted" }),
        };
    }

    private static JsonObject Project(Diagnostic diagnostic) => new()
    {
        ["id"] = diagnostic.Id,
        ["catalog"] = Identity(diagnostic.Catalog),
        ["severity"] = Kebab(diagnostic.Severity),
        ["category"] = Kebab(diagnostic.Category),
        ["phase"] = Kebab(diagnostic.Phase),
        ["disposition"] = Kebab(diagnostic.Disposition),
        ["occurrenceKey"] = diagnostic.OccurrenceKey,
        ["occurrenceCount"] = diagnostic.OccurrenceCount,
        ["subjects"] = new JsonArray(Safe(diagnostic.Parameters["subject"])),
        ["rule"] = Identity(diagnostic.Rule),
        ["messageKey"] = diagnostic.MessageKey,
        ["parameters"] = new JsonObject(diagnostic.Parameters.Select(static item => KeyValuePair.Create<string, JsonNode?>(item.Key, Safe(item.Value)))),
        ["cause"] = Safe(diagnostic.Cause),
        ["consequence"] = Safe(diagnostic.Consequence),
        ["expected"] = Safe(diagnostic.Expected),
        ["observed"] = Safe(diagnostic.Observed),
        ["remediations"] = new JsonArray(diagnostic.Remediations.Select(Remediation).ToArray()),
        ["evidence"] = new JsonArray(diagnostic.Evidence.Select(Evidence).ToArray()),
    };

    private static JsonObject Safe(SafeValue value)
    {
        SafeValue safe = DisclosureFilter.Enforce(value);
        JsonObject projected = new()
        {
            ["classification"] = Kebab(safe.Classification),
            ["valueKind"] = Kebab(safe.ValueKind),
        };
        if (safe.Value is not null) projected["value"] = safe.Value;
        if (safe.RedactionReason is not null) projected["reason"] = safe.RedactionReason;
        if (safe.PolicyReference is not null) projected["policy"] = Identity(safe.PolicyReference);
        return projected;
    }

    private static JsonObject Remediation(Remediation value) => new()
    {
        ["kind"] = value.Kind,
        ["effectClass"] = Kebab(value.EffectClass),
        ["authorityRequired"] = new JsonArray(value.AuthorityRequired.Select(static item => JsonValue.Create(item)).ToArray()),
        ["request"] = new JsonObject
        {
            ["kind"] = "argument-array",
            ["arguments"] = new JsonArray(value.RequestArguments!.Select(static item => JsonValue.Create(item)).ToArray()),
        },
        ["postconditions"] = new JsonArray(value.Postconditions.Select(static item => JsonValue.Create(item)).ToArray()),
        ["retryPhase"] = Kebab(value.RetryPhase),
    };

    private static JsonObject Evidence(EvidenceReference value) => new()
    {
        ["identity"] = Identity(value.Identity),
        ["subject"] = Identity(value.Subject),
        ["profile"] = Identity(value.Profile),
        ["artifact"] = new JsonObject
        {
            ["identity"] = Identity(value.Artifact.Identity),
            ["mediaType"] = value.Artifact.MediaType,
            ["logicalPath"] = value.Artifact.LogicalPath,
            ["digest"] = value.Artifact.Digest,
            ["ownership"] = Kebab(value.Artifact.Ownership),
        },
        ["freshness"] = value.Freshness,
    };

    private static JsonObject Identity(GovernedIdentity value) => new()
    {
        ["authority"] = value.Authority,
        ["kind"] = value.Kind,
        ["name"] = value.Name,
        ["revision"] = value.Revision,
        ["digest"] = value.Digest,
    };

    private static string Stage(AdapterFailureKind kind) => kind switch
    {
        AdapterFailureKind.InvalidConfiguration or AdapterFailureKind.UnsafePath or AdapterFailureKind.ForbiddenOperation => "request",
        AdapterFailureKind.UnsupportedCompatibility or AdapterFailureKind.InvalidSelection => "compatibility",
        AdapterFailureKind.UnresolvedApplicability => "applicability",
        AdapterFailureKind.InvalidHandoff or AdapterFailureKind.InvalidReview or AdapterFailureKind.StaleTrace => "handoff",
        AdapterFailureKind.ProcessFailure or AdapterFailureKind.InvalidAuthority => "invocation",
        AdapterFailureKind.PublicationDrift => "publication",
        _ => "request",
    };

    private static string Effect(AdapterOperation operation, AdapterFailureKind kind)
    {
        if (kind != AdapterFailureKind.ProcessFailure) return "none";
        return operation switch
        {
            AdapterOperation.Construct => "indeterminate",
            AdapterOperation.Prepare or AdapterOperation.Explain or AdapterOperation.Evaluate => "adapter-files-only",
            _ => "none",
        };
    }

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
