namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Exact secure cookie mechanics without application meaning.</summary>
public sealed record DotNetCookieSecurityProfile(
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("sameSite")] DotNetCookieSameSite SameSite,
    [property: JsonPropertyName("httpOnly")] bool HttpOnly,
    [property: JsonPropertyName("secureAlways")] bool SecureAlways,
    [property: JsonPropertyName("isEssential")] bool IsEssential,
    [property: JsonPropertyName("lifetimeMinutes")] int LifetimeMinutes);
