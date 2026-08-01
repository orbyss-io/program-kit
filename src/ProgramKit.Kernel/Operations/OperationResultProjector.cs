using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Operations;

public static class OperationResultProjector
{
    public static JsonObject ToJson(OperationResult result)
    {
        JsonObject document = new()
        {
            ["schema"] = result.Schema,
            ["canonicalProfile"] = result.CanonicalProfile,
            ["command"] = Kebab(result.Command),
            ["operationContract"] = ContractJson.Identity(result.OperationContract),
            ["outcome"] = Kebab(result.Outcome),
            ["furthestPhase"] = Kebab(result.FurthestPhase),
            ["effectState"] = Kebab(result.EffectState),
            ["primaryDisposition"] = Kebab(result.PrimaryDisposition),
            ["changes"] = new JsonArray(result.Changes.Select(Change).ToArray()),
            ["artifacts"] = new JsonArray(result.Artifacts.Select(ContractJson.Artifact).ToArray()),
            ["receipts"] = new JsonArray(result.Receipts.Select(ContractJson.Artifact).ToArray()),
            ["evidence"] = new JsonArray(result.Evidence.Select(ContractJson.Evidence).ToArray()),
            ["diagnostics"] = DiagnosticView(result.Diagnostics),
        };
        if (result.RequestIdentity is not null)
        {
            document["requestIdentity"] = result.RequestIdentity;
        }

        if (result.ConstructionIdentity is not null)
        {
            document["constructionIdentity"] = result.ConstructionIdentity;
        }

        if (result.Continuation is not null)
        {
            document["continuation"] = Continuation(result.Continuation);
        }

        if (result.Explanation is not null)
        {
            document["explanation"] = result.Explanation.DeepClone();
        }

        if (result.Utility is not null)
        {
            document["utility"] = result.Utility.DeepClone();
        }

        return document;
    }

    public static byte[] ToCanonicalBytes(OperationResult result) => CanonicalJson.Encode(ToJson(result));

    private static JsonObject Change(OperationChange value) => new()
    {
        ["kind"] = value.Kind,
        ["subject"] = Subject(value.Subject),
        ["effect"] = Kebab(value.Effect),
    };

    private static JsonObject DiagnosticView(DiagnosticView view)
    {
        JsonObject document = new()
        {
            ["total"] = view.Total,
            ["returned"] = view.Returned,
            ["omitted"] = view.Omitted,
            ["grouping"] = view.Grouping,
            ["fullCollectionDigest"] = view.FullCollectionDigest,
            ["items"] = new JsonArray(view.Items.Select(Diagnostic).ToArray()),
        };
        if (view.FullCollectionArtifact is not null)
        {
            document["fullCollectionArtifact"] = ContractJson.Artifact(view.FullCollectionArtifact);
        }

        if (view.Omitted > 0)
        {
            document["cursor"] = new JsonObject
            {
                ["collectionDigest"] = view.FullCollectionDigest,
                ["offset"] = view.Returned,
            };
        }

        return document;
    }

    private static JsonObject Diagnostic(Diagnostic diagnostic) => new()
    {
        ["id"] = diagnostic.Id,
        ["catalog"] = ContractJson.Identity(diagnostic.Catalog),
        ["severity"] = Kebab(diagnostic.Severity),
        ["category"] = Kebab(diagnostic.Category),
        ["phase"] = Kebab(diagnostic.Phase),
        ["occurrenceKey"] = diagnostic.OccurrenceKey,
        ["occurrenceCount"] = diagnostic.OccurrenceCount,
        ["subjects"] = new JsonArray(diagnostic.Subjects.Select(Subject).ToArray()),
        ["rule"] = ContractJson.Identity(diagnostic.Rule),
        ["messageKey"] = diagnostic.MessageKey,
        ["parameters"] = new JsonObject(diagnostic.Parameters.Select(static item => KeyValuePair.Create<string, JsonNode?>(item.Key, SafeValue(item.Value)))),
        ["cause"] = new JsonObject
        {
            ["kind"] = "bounded",
            ["details"] = new JsonArray(SafeValue(diagnostic.Cause)),
        },
        ["consequence"] = new JsonObject
        {
            ["kind"] = "bounded",
            ["affectedClaims"] = new JsonArray("operation-trust"),
        },
        ["remediations"] = new JsonArray(diagnostic.Remediations.Select(Remediation).ToArray()),
        ["evidence"] = new JsonArray(diagnostic.Evidence.Select(ContractJson.Evidence).ToArray()),
        ["documentation"] = new JsonArray(),
    };

    private static JsonObject Remediation(Remediation remediation)
    {
        JsonObject request = new() { ["kind"] = "factory-request" };
        if (remediation.RequestDocument is not null)
        {
            request["document"] = remediation.RequestDocument.DeepClone();
        }

        if (remediation.RequestArtifact is not null)
        {
            request["artifact"] = ContractJson.Artifact(remediation.RequestArtifact);
        }

        return new JsonObject
        {
            ["kind"] = remediation.Kind,
            ["targets"] = new JsonArray(remediation.Targets.Select(Subject).ToArray()),
            ["preconditions"] = new JsonArray(remediation.Preconditions.Select(static value => SafeValue(value, false)).ToArray()),
            ["effectClass"] = Kebab(remediation.EffectClass),
            ["authorityRequired"] = new JsonArray(remediation.AuthorityRequired.Select(static value => JsonValue.Create(Slug(value))).ToArray()),
            ["request"] = request,
            ["postconditions"] = new JsonArray(remediation.Postconditions.Select(static value => SafeValue(value, false)).ToArray()),
            ["retryPhase"] = Kebab(remediation.RetryPhase),
        };
    }

    private static JsonObject Continuation(Continuation continuation) => new()
    {
        ["schema"] = continuation.Schema,
        ["canonicalProfile"] = continuation.CanonicalProfile,
        ["requestDigest"] = continuation.RequestDigest,
        ["completedWork"] = new JsonArray(),
        ["missingInputs"] = new JsonArray(continuation.MissingInputs.Select(static item => new JsonObject
        {
            ["identity"] = Slug(item.Identity, allowDots: true),
            ["valueKind"] = Slug(item.ValueKind),
            ["requiredAuthority"] = Slug(item.RequiredAuthority),
            ["rule"] = ContractJson.Identity(item.Rule),
        }).ToArray()),
        ["choices"] = new JsonArray(continuation.Choices.OrderBy(static item => item.Key, StringComparer.Ordinal).SelectMany(static item => item.Value.Select(value => new JsonObject
        {
            ["inputIdentity"] = Slug(item.Key, allowDots: true),
            ["value"] = SafeValue(value, false),
            ["consequence"] = "Selecting this exact value will be fully revalidated.",
        })).ToArray()),
        ["authorityRequirements"] = new JsonArray(continuation.AuthorityRequirements.Select(static value => JsonValue.Create(Slug(value))).ToArray()),
        ["freshnessBindings"] = new JsonObject
        {
            ["workspaceDigest"] = continuation.WorkspaceDigest,
            ["evidenceDigest"] = continuation.EvidenceDigest,
        },
        ["digest"] = continuation.Digest,
    };

    private static JsonObject Subject(string value)
    {
        bool logical = false;
        string normalized = value;
        try
        {
            if (value.Contains('/', StringComparison.Ordinal) || value.Contains('\\', StringComparison.Ordinal))
            {
                normalized = LogicalPaths.Normalize(value);
                logical = true;
            }
        }
        catch (ArgumentException)
        {
            normalized = Slug(value);
        }

        if (!logical)
        {
            normalized = Slug(normalized, allowDots: true);
        }

        GovernedIdentity identity = ContractJson.StableIdentity("orbyss.program-kit", "diagnostic-subject", normalized, "1", value);
        JsonObject subject = ContractJson.Subject(logical ? "logical-path" : "governed-subject", identity);
        if (logical)
        {
            subject["logicalPath"] = normalized;
        }

        return subject;
    }

    private static JsonObject SafeValue(SafeValue value)
    {
        JsonObject document = new()
        {
            ["classification"] = Kebab(value.Classification),
            ["valueKind"] = ProjectSafeValueKind(value.ValueKind),
        };
        if (value.Classification == SafeValueClassification.Withheld)
        {
            document["redactionReason"] = value.RedactionReason;
            document["policyReference"] = ContractJson.Artifact(value.PolicyReference!);
        }
        else
        {
            document["value"] = value.Value;
        }

        return document;
    }

    private static string ProjectSafeValueKind(SafeValueKind value) => value switch
    {
        SafeValueKind.Text => "string",
        SafeValueKind.WholeNumber => "integer",
        SafeValueKind.Flag => "boolean",
        _ => Kebab(value),
    };

    private static JsonObject SafeValue(string value, bool logicalPath) => SafeValue(new SafeValue(
        logicalPath ? SafeValueClassification.RepositoryRelative : SafeValueClassification.Public,
        logicalPath ? SafeValueKind.LogicalPath : SafeValueKind.Text,
        value));

    private static string Slug(string value, bool allowDots = false)
    {
        System.Text.StringBuilder builder = new();
        foreach (char current in value)
        {
            char lower = char.ToLowerInvariant(current);
            if (char.IsLetterOrDigit(lower) || lower == '-' || allowDots && lower == '.')
            {
                builder.Append(lower);
            }
            else if (builder.Length > 0 && builder[^1] != '-')
            {
                builder.Append('-');
            }
        }

        string result = builder.ToString().Trim('-');
        if (result.Length == 0 || !char.IsLetter(result[0]))
        {
            result = $"value-{result}";
        }

        return result.Length <= 200 ? result : result[..200];
    }

    private static string Kebab<T>(T value)
        where T : struct, Enum => ContractJson.Kebab(value);
}
