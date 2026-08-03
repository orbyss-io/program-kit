using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Kernel.Canonicalization;

public static class ContractJson
{
    public static JsonObject Identity(GovernedIdentity value) => new()
    {
        ["authority"] = value.Authority,
        ["kind"] = value.Kind,
        ["name"] = value.Name,
        ["revision"] = value.Revision,
        ["digest"] = value.Digest,
    };

    public static JsonObject Artifact(ArtifactReference value) => new()
    {
        ["identity"] = Identity(value.Identity),
        ["mediaType"] = value.MediaType,
        ["logicalPath"] = value.LogicalPath,
        ["digest"] = value.Digest,
        ["ownership"] = Kebab(value.Ownership),
    };

    public static JsonObject Trace(TraceReference value) => new()
    {
        ["source"] = Artifact(value.Source),
        ["pointer"] = value.DocumentPointer,
        ["claimKind"] = value.ClaimKind,
    };

    public static JsonObject Selection(ExactSelection value) => new()
    {
        ["role"] = value.Role,
        ["selected"] = Identity(value.Selected),
        ["selectionAuthority"] = Identity(value.SelectionAuthority),
        ["trace"] = value.Trace is null
            ? throw new InvalidOperationException("An exact selection requires trace.")
            : Trace(value.Trace),
    };

    public static JsonObject Subject(string kind, GovernedIdentity identity, string? logicalPath = null)
    {
        JsonObject subject = new()
        {
            ["kind"] = kind,
            ["identity"] = Identity(identity),
        };
        if (logicalPath is not null)
        {
            subject["logicalPath"] = logicalPath;
        }

        return subject;
    }

    public static JsonObject Evidence(EvidenceReference value) => new()
    {
        ["identity"] = Identity(value.Identity),
        ["subject"] = Identity(value.Subject),
        ["profile"] = Identity(value.Profile),
        ["artifact"] = Artifact(value.Artifact),
        ["freshness"] = value.Freshness,
    };

    public static JsonObject Gate(
        GovernedIdentity gate,
        string mode,
        string status,
        IEnumerable<JsonObject> subjects,
        IEnumerable<JsonObject>? evidence = null,
        IEnumerable<string>? diagnosticIds = null) => new()
        {
            ["gate"] = Identity(gate),
            ["mode"] = mode,
            ["status"] = status,
            ["subjects"] = new JsonArray(subjects.Select(static item => item.DeepClone()).ToArray()),
            ["evidence"] = new JsonArray((evidence ?? Array.Empty<JsonObject>()).Select(static item => item.DeepClone()).ToArray()),
            ["diagnosticIds"] = new JsonArray((diagnosticIds ?? Array.Empty<string>()).Select(static item => JsonValue.Create(item)).ToArray()),
        };

    public static GovernedIdentity StableIdentity(string authority, string kind, string name, string revision, string material) =>
        new(authority, kind, name, revision, Digests.Sha256(System.Text.Encoding.UTF8.GetBytes(material)));

    public static string Kebab<T>(T value)
        where T : struct, Enum
    {
        string name = value.ToString();
        System.Text.StringBuilder builder = new();
        for (int index = 0; index < name.Length; index++)
        {
            if (index > 0 && char.IsUpper(name[index]))
            {
                builder.Append('-');
            }

            builder.Append(char.ToLowerInvariant(name[index]));
        }

        return builder.ToString();
    }
}
