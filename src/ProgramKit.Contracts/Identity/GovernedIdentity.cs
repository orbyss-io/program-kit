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
    private const string EmptyDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";

    public static GovernedIdentity Operation(string command) =>
        new("orbyss.program-kit", "operation-contract", command, "1.0.0", EmptyDigest);

    public static GovernedIdentity Rule(string name) =>
        new("orbyss.program-kit", "rule", name, "1.0.0", EmptyDigest);

    public static GovernedIdentity Catalog(string authority, string name) =>
        new(authority, "diagnostic-catalog", name, "1.0.0", EmptyDigest);
}
