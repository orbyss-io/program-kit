using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Authority;

public sealed class RepositoryAuthorityGrantStore
{
    public RequestBoundAuthorityGrant Load(string workspaceRoot, string logicalPath, AuthorityDemand demand)
    {
        string path = LogicalPaths.ResolveInside(workspaceRoot, logicalPath);
        if (!File.Exists(path)) throw new UnauthorizedAccessException("The exact request-bound authority grant artifact is unavailable.");
        JsonObject document = CanonicalJson.Parse(File.ReadAllBytes(path)).AsObject();
        if (!string.Equals(document["schema"]?.GetValue<string>(), "program-kit.authority-grant/v1", StringComparison.Ordinal)) throw new UnauthorizedAccessException("The authority grant schema is not supported.");
        GovernedIdentity identity = ParseIdentity(document["identity"]!.AsObject());
        GovernedIdentity subject = ParseIdentity(document["subjects"]!.AsArray().Select(static item => item!.AsObject()).Single()["identity"]!.AsObject());
        string subjectBinding = string.Equals(subject.Name, demand.WorkspaceIdentity, StringComparison.Ordinal) ? subject.Name : subject.StableKey;
        JsonObject validity = document["validity"]!.AsObject();
        return new RequestBoundAuthorityGrant(
            "program-kit.request-bound-authority-grant/v1", identity.StableKey, subjectBinding,
            document["operations"]!.AsArray().Select(static value => value!.GetValue<string>()).Single(),
            document["effects"]!.AsArray().Select(static value => value!.GetValue<string>()).Single(),
            document["requestBinding"]!.GetValue<string>(), Condition(document, "provider"), Condition(document, "scope"),
            ParseInstant(validity["notBefore"]!.GetValue<string>()), ParseInstant(validity["notAfter"]!.GetValue<string>()),
            false, IsConsumed(workspaceRoot, identity.StableKey));
    }

    public bool IsConsumed(string workspaceRoot, string grantIdentity) => File.Exists(ConsumptionPath(workspaceRoot, grantIdentity));

    public void MarkConsumed(string workspaceRoot, string grantIdentity, string requestIdentity)
    {
        string path = ConsumptionPath(workspaceRoot, grantIdentity);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        JsonObject marker = new() { ["schema"] = "program-kit.consumed-authority-grant/v1", ["grantIdentity"] = grantIdentity, ["requestIdentity"] = requestIdentity };
        byte[] bytes = CanonicalJson.Encode(marker);
        string temporary = $"{path}.{Guid.NewGuid():N}.tmp";
        using (FileStream stream = new(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
        {
            stream.Write(bytes);
            stream.Flush(flushToDisk: true);
        }

        File.Move(temporary, path, overwrite: false);
    }

    private static string ConsumptionPath(string workspaceRoot, string grantIdentity)
    {
        string digest = Digests.Sha256(Encoding.UTF8.GetBytes(grantIdentity))["sha256:".Length..];
        return Path.Combine(Path.GetFullPath(workspaceRoot), ".program-kit", "consumed-authority-grants", $"{digest}.json");
    }

    private static string Condition(JsonObject grant, string kind) => grant["conditions"]!.AsArray().Select(static value => value!.AsObject()).Single(item => string.Equals(item["kind"]!.GetValue<string>(), kind, StringComparison.Ordinal))["value"]!["value"]!.GetValue<string>();
    private static DateTimeOffset ParseInstant(string value) => DateTimeOffset.ParseExact(value, "yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);
    private static GovernedIdentity ParseIdentity(JsonObject value) => new(value["authority"]!.GetValue<string>(), value["kind"]!.GetValue<string>(), value["name"]!.GetValue<string>(), value["revision"]!.GetValue<string>(), value["digest"]!.GetValue<string>());
}
