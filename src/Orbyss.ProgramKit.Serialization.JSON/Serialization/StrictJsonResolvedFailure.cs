namespace Orbyss.ProgramKit.Serialization.Json.Serialization;

internal sealed record StrictJsonResolvedFailure(
    Type ExpectedType,
    string MemberName,
    bool IsUndeclaredMember);
