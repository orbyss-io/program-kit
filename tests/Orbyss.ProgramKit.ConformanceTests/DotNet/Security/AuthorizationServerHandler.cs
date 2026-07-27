using System.Net;
using System.Security.Cryptography;
using System.Text;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Security;

internal sealed class AuthorizationServerHandler : HttpMessageHandler
{
    private const string AccessTokenType =
        "urn:ietf:params:oauth:token-type:access_token";

    internal int RequestCount { get; private set; }
    internal bool SawClientCredentials { get; private set; }
    internal bool SawExactExchange { get; private set; }
    internal HttpStatusCode StatusCode { get; init; } = HttpStatusCode.OK;
    internal string IssuedTokenType { get; init; } = AccessTokenType;

    protected override async Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        RequestCount++;
        var form = await request.Content!.ReadAsStringAsync(cancellationToken);
        SawClientCredentials |= form.Contains(
            "grant_type=client_credentials",
            StringComparison.Ordinal);
        SawExactExchange |=
            form.Contains(
                "grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Atoken-exchange",
                StringComparison.Ordinal) &&
            form.Contains("subject_token_type=", StringComparison.Ordinal) &&
            form.Contains("actor_token_type=", StringComparison.Ordinal) &&
            request.Headers.Authorization?.Scheme == "Basic";
        var json = string.Concat(
            "{\"access_token\":\"",
            Convert.ToBase64String(RandomNumberGenerator.GetBytes(32)),
            "\",\"issued_token_type\":\"",
            IssuedTokenType,
            "\",\"token_type\":\"Bearer\",\"expires_in\":300,\"scope\":\"catalog.read\"}");
        return new HttpResponseMessage(StatusCode)
        {
            Content = new StringContent(json, Encoding.UTF8, "application/json"),
        };
    }
}
