namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Explicit ASP.NET Core authentication scheme defaults.</summary>
public sealed record DotNetAuthenticationDefaults(
    [property: JsonPropertyName("authenticateScheme")] string AuthenticateScheme,
    [property: JsonPropertyName("challengeScheme")] string ChallengeScheme,
    [property: JsonPropertyName("forbidScheme")] string ForbidScheme,
    [property: JsonPropertyName("signInScheme")] string? SignInScheme,
    [property: JsonPropertyName("signOutScheme")] string? SignOutScheme);
