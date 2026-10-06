using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.WebUtilities;

namespace Notes.Oracle;

// Test-only external issuer and lost-response proxy. It never enters the application bundle.
internal static class FixtureIssuer
{
    internal static async Task RunAsync(string issuer, string target)
    {
        var builder = WebApplication.CreateBuilder();
        builder.Logging.ClearProviders();
        await using var app = builder.Build();
        app.Urls.Add(issuer);
        using var signing = RSA.Create(2048);
        var publicKey = signing.ExportParameters(false);
        var codes = new ConcurrentDictionary<string, Authorization>(StringComparer.Ordinal);
        var tokens = new ConcurrentDictionary<string, string>(StringComparer.Ordinal);
        app.MapGet("/.well-known/openid-configuration", () => Results.Json(new
        {
            issuer, authorization_endpoint = issuer + "/authorize", token_endpoint = issuer + "/token",
            userinfo_endpoint = issuer + "/userinfo", jwks_uri = issuer + "/keys",
            response_types_supported = new[] { "code" }, subject_types_supported = new[] { "public" },
            id_token_signing_alg_values_supported = new[] { "RS256" },
            code_challenge_methods_supported = new[] { "S256" }
        }));
        app.MapGet("/keys", () => Results.Json(new { keys = new[] { new
        { kty = "RSA", use = "sig", kid = "notes-fixture", alg = "RS256", n = Encode(publicKey.Modulus!), e = Encode(publicKey.Exponent!) } } }));
        app.MapGet("/authorize", (HttpContext http) =>
        {
            var query = http.Request.Query;
            var redirect = query["redirect_uri"].ToString();
            if (!redirect.StartsWith(target + "/signin-oidc", StringComparison.Ordinal)
                || query["code_challenge_method"] != "S256") return Results.BadRequest();
            var subject = query["fixture_subject"].ToString();
            if (subject is not ("alice" or "bob")) return Results.BadRequest();
            var code = Guid.NewGuid().ToString("N");
            codes[code] = new(subject, query["client_id"].ToString(), query["nonce"].ToString(), query["code_challenge"].ToString(), redirect);
            return Results.Redirect(QueryHelpers.AddQueryString(redirect, new Dictionary<string, string?>
                { ["code"] = code, ["state"] = query["state"].ToString() }));
        });
        app.MapPost("/token", async (HttpContext http) =>
        {
            var form = await http.Request.ReadFormAsync();
            if (!codes.TryRemove(form["code"].ToString(), out var admitted)
                || admitted.Redirect != form["redirect_uri"]
                || admitted.Challenge != Encode(SHA256.HashData(Encoding.ASCII.GetBytes(form["code_verifier"].ToString()))))
                return Results.BadRequest();
            var access = Guid.NewGuid().ToString("N");
            tokens[access] = admitted.Subject;
            var now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            var header = Encode(JsonSerializer.SerializeToUtf8Bytes(new { alg = "RS256", typ = "JWT", kid = "notes-fixture" }));
            var payload = Encode(JsonSerializer.SerializeToUtf8Bytes(new
                { iss = issuer, sub = admitted.Subject, aud = admitted.Client, nonce = admitted.Nonce, iat = now, exp = now + 300, name = admitted.Subject }));
            var signed = header + "." + payload;
            var token = signed + "." + Encode(signing.SignData(Encoding.ASCII.GetBytes(signed), HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1));
            return Results.Json(new { id_token = token, access_token = access, token_type = "Bearer", expires_in = 300 });
        });
        app.MapGet("/userinfo", (HttpContext http) =>
            tokens.TryGetValue(http.Request.Headers.Authorization.ToString().Replace("Bearer ", "", StringComparison.Ordinal), out var subject)
                ? Results.Json(new { sub = subject, name = subject, fixture_raw_issuer = "https://untrusted.example",
                    fixture_raw_subject = "foreign-alias" }) : Results.Unauthorized());
        app.MapPost("/drop-response/{**path}", async (HttpContext http, string path) =>
        {
            using var client = new HttpClient(new HttpClientHandler { AllowAutoRedirect = false, UseCookies = false });
            using var request = new HttpRequestMessage(HttpMethod.Post, target + "/" + path)
                { Content = new StreamContent(http.Request.Body) };
            request.Content.Headers.ContentType = new("application/json");
            foreach (var name in new[] { "Cookie", "X-CSRF-TOKEN", "Origin" })
                if (http.Request.Headers.TryGetValue(name, out var value)) request.Headers.TryAddWithoutValidation(name, value.ToArray());
            using var response = await client.SendAsync(request);
            _ = await response.Content.ReadAsByteArrayAsync();
            if ((int)response.StatusCode is < 200 or > 299) throw new InvalidOperationException("Lost-response injection requires an actual successful committed response.");
            // The host has completed its mutation before the client connection is deliberately lost.
            http.Abort();
        });
        app.MapGet("/ready", () => Results.Ok());
        await app.RunAsync();
    }

    private static string Encode(byte[] bytes) => Convert.ToBase64String(bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_');
    private sealed record Authorization(string Subject, string Client, string Nonce, string Challenge, string Redirect);
}
