namespace Orbyss.ProgramKit.Planning.Approvals;

/// <summary>Identifies a principal supplied by the human-session boundary.</summary>
public sealed record PrincipalReference(
    string Kind,
    string Provider,
    string Identifier,
    string Role);
