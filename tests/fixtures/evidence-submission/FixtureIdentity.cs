using System.Security.Claims;
using System.Text.Encodings.Web;
using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Options;

namespace Evidence.Probe;

public sealed class FixtureIdentity(
    IOptionsMonitor<AuthenticationSchemeOptions> options,
    ILoggerFactory logger,
    UrlEncoder encoder
) : AuthenticationHandler<AuthenticationSchemeOptions>(
    options,
    logger,
    encoder
)
{
    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        var owner = Request.Headers["X-Fixture-Owner"].ToString();
        if (owner is not ("fictional-reviewer" or "other-reviewer"))
        {
            var absent = AuthenticateResult.NoResult();
            return Task.FromResult(absent);
        }
        Claim[] claims = [new Claim(ClaimTypes.Name, owner)];
        var identity = new ClaimsIdentity(claims, "fixture");
        var principal = new ClaimsPrincipal(identity);
        var ticket = new AuthenticationTicket(principal, "fixture");
        var result = AuthenticateResult.Success(ticket);
        return Task.FromResult(result);
    }
}
