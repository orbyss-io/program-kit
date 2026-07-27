namespace Orbyss.ProgramKit.Serialization.Json.Canonicalization;

internal sealed record CanonicalJsonMember(
    string Name,
    byte[] EncodedName,
    byte[] EncodedValue);
