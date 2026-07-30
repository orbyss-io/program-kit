namespace Orbyss.ProgramKit.Serialization.Json.Serialization;

internal sealed record StrictJsonReadFailure(
    string Path,
    string MemberName,
    string ExpectedClrType,
    bool IsUndeclaredMember)
{
    internal string Message(string reason)
    {
        var displayPath = string.IsNullOrEmpty(Path)
            ? "<root>"
            : Path;
        return string.Concat(
            "Member '",
            MemberName,
            "' at '",
            displayPath,
            "' expected CLR type '",
            ExpectedClrType,
            "': ",
            IsUndeclaredMember
                ? "The member is undeclared for the containing CLR type."
                : reason);
    }
}
