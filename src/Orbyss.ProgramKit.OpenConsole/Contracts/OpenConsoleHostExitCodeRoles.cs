namespace Orbyss.ProgramKit.OpenConsole.Contracts;

/// <summary>Language-neutral exit codes owned by the generated host lifecycle.</summary>
public sealed record OpenConsoleHostExitCodeRoles(
    [property: JsonPropertyName("invalidInvocation")] int InvalidInvocation,
    [property: JsonPropertyName("cancellation")] int Cancellation,
    [property: JsonPropertyName("internalFailure")] int InternalFailure);
