using System.Security.Claims;
using System.Security.Cryptography;
using Microsoft.IdentityModel.JsonWebTokens;
using Microsoft.IdentityModel.Tokens;

namespace GeneratedHost.Composition;

/// <summary>Exercises exact RFC 9068-style JWT access-token validation vectors.</summary>
public static class JwtVectorHarness
{
    /// <summary>Creates and validates one named access-token vector.</summary>
    public static async Task<bool> ValidateAsync(string vector)
    {
        using RSA rsa = RSA.Create(2048);
        RsaSecurityKey key = new(rsa);
        var now = DateTime.UtcNow;
        SecurityTokenDescriptor descriptor = new()
        {
            Issuer = vector == "wrong-issuer"
                ? "https://other.example.test/"
                : "https://identity.example.test/",
            Audience = vector == "wrong-audience"
                ? "other-api"
                : "fixture-api",
            Expires = vector == "expired"
                ? now.AddMinutes(-5)
                : now.AddMinutes(5),
            IssuedAt = vector == "expired"
                ? now.AddMinutes(-10)
                : now,
            NotBefore = vector == "expired"
                ? now.AddMinutes(-10)
                : now,
            TokenType = vector == "id-token-type"
                ? "JWT"
                : "at+jwt",
            SigningCredentials = vector == "unsigned"
                ? null
                : new SigningCredentials(
                    key,
                    SecurityAlgorithms.RsaSha256),
            Subject = new ClaimsIdentity(
                [new Claim("sub", "fixture-user")]),
        };
        JsonWebTokenHandler handler = new();
        var token = handler.CreateToken(descriptor);
        TokenValidationParameters validation = new()
        {
            IssuerSigningKey = key,
            ValidateIssuerSigningKey = true,
            RequireSignedTokens = true,
            ValidateIssuer = true,
            ValidIssuer = "https://identity.example.test/",
            ValidateAudience = true,
            ValidAudience = "fixture-api",
            ValidateLifetime = true,
            RequireExpirationTime = true,
            ClockSkew = TimeSpan.Zero,
            ValidAlgorithms = [SecurityAlgorithms.RsaSha256],
            ValidTypes = ["at+jwt"],
        };

        var result = await handler.ValidateTokenAsync(token, validation);
        return result.IsValid;
    }
}
