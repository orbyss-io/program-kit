using System;
using System.Security.Cryptography;
using System.Text;

namespace Orbyss.ProgramKit.Contracts.Identity;

public sealed record GovernedIdentity(
    string Authority,
    string Kind,
    string Name,
    string Revision,
    string Digest)
{
    public string StableKey => $"{Authority}:{Kind}:{Name}@{Revision}";
}

public static class ProtocolIdentities
{
    public static GovernedIdentity Operation(string command) =>
        Exact("orbyss.program-kit", "operation-contract", command, "1.0.0");

    public static GovernedIdentity Rule(string name) =>
        Exact("orbyss.program-kit", "rule", name, "1.0.0");

    public static GovernedIdentity Catalog(string authority, string name) =>
        Exact(authority, "diagnostic-catalog", name, "1.0.0");

    private static GovernedIdentity Exact(string authority, string kind, string name, string revision)
    {
        string material = $"program-kit.governed-identity/v1\n{authority}\n{kind}\n{name}\n{revision}";
        string digest = $"sha256:{Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(material))).ToLowerInvariant()}";
        return new GovernedIdentity(authority, kind, name, revision, digest);
    }
}
