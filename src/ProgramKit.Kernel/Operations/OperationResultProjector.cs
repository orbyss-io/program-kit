using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
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
            ["operationContract"] = Identity(result.OperationContract),
            ["outcome"] = Kebab(result.Outcome),
            ["furthestPhase"] = Kebab(result.FurthestPhase),
            ["effectState"] = Kebab(result.EffectState),
            ["primaryDisposition"] = Kebab(result.PrimaryDisposition),
            ["changes"] = new JsonArray(result.Changes.Select(Change).ToArray()),
            ["artifacts"] = new JsonArray(result.Artifacts.Select(Artifact).ToArray()),
            ["receipts"] = new JsonArray(result.Receipts.Select(Artifact).ToArray()),
            ["evidence"] = new JsonArray(),
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

    private static JsonObject Identity(GovernedIdentity value) => new()
    {
        ["authority"] = value.Authority,
        ["kind"] = value.Kind,
        ["name"] = value.Name,
        ["revision"] = value.Revision,
        ["digest"] = value.Digest,
    };

    private static JsonObject Artifact(ArtifactReference value) => new()
    {
        ["identity"] = Identity(value.Identity),
        ["mediaType"] = value.MediaType,
        ["logicalPath"] = value.LogicalPath,
        ["digest"] = value.Digest,
        ["ownership"] = Kebab(value.Ownership),
    };

    private static JsonObject Change(OperationChange value) => new()
    {
        ["kind"] = value.Kind,
        ["subject"] = value.Subject,
        ["effect"] = Kebab(value.Effect),
    };

    private static JsonObject DiagnosticView(DiagnosticView view) => new()
    {
        ["total"] = view.Total,
        ["returned"] = view.Returned,
        ["omitted"] = view.Omitted,
        ["grouping"] = view.Grouping,
        ["fullCollectionDigest"] = view.FullCollectionDigest,
        ["items"] = new JsonArray(view.Items.Select(Diagnostic).ToArray()),
    };

    private static JsonObject Diagnostic(Diagnostic diagnostic) => new()
    {
        ["id"] = diagnostic.Id,
        ["catalog"] = Identity(diagnostic.Catalog),
        ["severity"] = Kebab(diagnostic.Severity),
        ["category"] = Kebab(diagnostic.Category),
        ["phase"] = Kebab(diagnostic.Phase),
        ["occurrenceKey"] = diagnostic.OccurrenceKey,
        ["occurrenceCount"] = diagnostic.OccurrenceCount,
        ["subjects"] = new JsonArray(diagnostic.Subjects.Select(static subject => JsonValue.Create(subject)).ToArray()),
        ["rule"] = Identity(diagnostic.Rule),
        ["messageKey"] = diagnostic.MessageKey,
        ["parameters"] = new JsonObject(diagnostic.Parameters.Select(static item => KeyValuePair.Create<string, JsonNode?>(item.Key, JsonValue.Create(item.Value)))),
        ["cause"] = new JsonObject { ["kind"] = "bounded", ["details"] = new JsonArray(diagnostic.Cause) },
        ["consequence"] = new JsonObject { ["kind"] = "bounded", ["affectedClaims"] = new JsonArray(diagnostic.Consequence) },
        ["remediations"] = new JsonArray(diagnostic.Remediations.Select(Remediation).ToArray()),
        ["evidence"] = new JsonArray(),
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
            request["artifact"] = Artifact(remediation.RequestArtifact);
        }

        return new JsonObject
        {
            ["kind"] = remediation.Kind,
            ["targets"] = new JsonArray(remediation.Targets.Select(static value => JsonValue.Create(value)).ToArray()),
            ["preconditions"] = new JsonArray(remediation.Preconditions.Select(static value => JsonValue.Create(value)).ToArray()),
            ["effectClass"] = Kebab(remediation.EffectClass),
            ["authorityRequired"] = new JsonArray(remediation.AuthorityRequired.Select(static value => JsonValue.Create(value)).ToArray()),
            ["request"] = request,
            ["postconditions"] = new JsonArray(remediation.Postconditions.Select(static value => JsonValue.Create(value)).ToArray()),
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
            ["identity"] = item.Identity,
            ["valueKind"] = item.ValueKind,
            ["requiredAuthority"] = item.RequiredAuthority,
            ["rule"] = Identity(item.Rule),
        }).ToArray()),
        ["choices"] = new JsonArray(),
        ["authorityRequirements"] = new JsonArray(continuation.AuthorityRequirements.Select(static value => JsonValue.Create(value)).ToArray()),
        ["freshnessBindings"] = new JsonObject
        {
            ["workspaceDigest"] = continuation.WorkspaceDigest,
            ["evidenceDigest"] = continuation.EvidenceDigest,
        },
        ["digest"] = continuation.Digest,
    };

    private static string Kebab<T>(T value)
        where T : struct, Enum
    {
        string name = value.ToString();
        System.Text.StringBuilder builder = new();
        for (int index = 0; index < name.Length; index++)
        {
            char current = name[index];
            if (index > 0 && char.IsUpper(current))
            {
                builder.Append('-');
            }

            builder.Append(char.ToLowerInvariant(current));
        }

        return builder.ToString();
    }
}
