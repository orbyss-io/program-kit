using System.Security.Claims;
using System.Text.Json;
using Example.Application.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using Orbyss.Foundation.Authentication;
using Orbyss.Foundation.Authentication.Core;
using Orbyss.Foundation.Web.ProblemDetails;

// Provider-free presentation seam proof. The fixture authentication service intentionally supplies
// an independently valid/absent local cookie result; this does not prove Foundation/Keycloak login.
var output = args.Single(); Directory.CreateDirectory(output);
var serviceCollection = new ServiceCollection();
serviceCollection.AddLogging(); serviceCollection.AddFoundationProblemDetails();
serviceCollection.AddSingleton<IAuthenticationService, FixtureCookieAuthentication>();
serviceCollection.AddSingleton(new ApplicationAuthenticationPresentation("Example <Workspace>", "/workspace", ["/bff/login", "/bff/access-denied", "/signin-oidc"]));
serviceCollection.AddSingleton<IAuthenticationErrorWriter>(provider => provider.GetRequiredService<ApplicationAuthenticationPresentation>());
await using var services = serviceCollection.BuildServiceProvider();
var writer = services.GetRequiredService<IAuthenticationErrorWriter>();
var cases = 0;

DefaultHttpContext Context(string path, string accept, bool existing = false)
{
    var context = new DefaultHttpContext { RequestServices = services };
    context.Request.Path = path; context.Request.PathBase = "/tenant"; context.Request.Headers.Accept = accept;
    context.Response.Body = new MemoryStream(); context.Items["existing-session"] = existing;
    return context;
}
async Task<string> Body(DefaultHttpContext context)
{
    context.Response.Body.Position = 0; return await new StreamReader(context.Response.Body).ReadToEndAsync();
}
void Require(bool value, string message) { if (!value) throw new InvalidOperationException(message); }

foreach (var (path, accept) in new[] { ("/api/policies", "text/html"), ("/bff/access-denied", "*/*"), ("/unrelated", "text/html"), ("/bff/access-denied", "text/html;q=0") })
{
    var context = Context(path, accept);
    await writer.WriteAsync(context, 403, AuthenticationErrorCodes.AuthorizationDenied);
    using var json = JsonDocument.Parse(await Body(context));
    Require(context.Response.StatusCode == 403 && context.Response.ContentType!.StartsWith("application/problem+json"), "Machine representation changed.");
    Require(json.RootElement.GetProperty("code").GetString() == "authorization_denied", "Machine code changed."); cases++;
}
foreach (var (path, accept) in new[] { ("/api/policies", "text/html"), ("/bff/access-denied", "*/*") })
{
    var context = Context(path, accept);
    await writer.WriteAsync(context, 409, "custom_admission_denied");
    using var json = JsonDocument.Parse(await Body(context));
    Require(context.Response.StatusCode == 409 && context.Response.ContentType!.StartsWith("application/problem+json"), "Custom machine status/representation changed.");
    Require(json.RootElement.GetProperty("code").GetString() == "custom_admission_denied", "Safe custom machine code was replaced by browser copy admission."); cases++;
}
foreach (var (path, accept) in new[] { ("/api/policies", "text/html"), ("/bff/access-denied", "*/*") })
{
    var context = Context(path, accept);
    try { await writer.WriteAsync(context, 400, "<script>secret</script>"); throw new InvalidOperationException("Unsafe machine code bypassed native admission."); }
    catch (ArgumentException) { Require(context.Response.Body.Length == 0, "Unsafe machine code was written before rejection."); cases++; }
}
foreach (var existing in new[] { false, true })
{
    var context = Context("/signin-oidc", "text/html", existing);
    context.Request.QueryString = new QueryString("?returnUrl=https://attacker.invalid/&code=secret-provider-payload");
    await writer.WriteAsync(context, 400, AuthenticationErrorCodes.CallbackInvalid);
    var html = await Body(context);
    Require(context.Response.StatusCode == 400 && context.Response.ContentType == "text/html; charset=utf-8", "Browser status/representation changed.");
    Require(html.Contains("Example &lt;Workspace&gt;") && !html.Contains("secret-provider-payload") && !html.Contains("attacker.invalid"), "Unsafe browser reflection.");
    Require(html.Contains("Continue to your workspace") == existing && html.Contains("/tenant/bff/login?returnUrl=%2Ftenant%2Fworkspace"), "Session/restart decision changed.");
    Require(context.Response.Headers.CacheControl == "no-store" && context.Response.Headers["X-Robots-Tag"].ToString().Contains("noindex"), "Privacy headers lost.");
    await File.WriteAllTextAsync(Path.Combine(output, existing ? "error-existing.html" : "error-anonymous.html"), html); cases++;
}
foreach (var path in new[] { "/bff/login", "/bff/access-denied", "/api/policies", "/session-ended" })
{
    var context = Context("/tenant" + path, "text/html"); context.Request.PathBase = PathString.Empty;
    context.Features.Set<IAuthenticationFeature>(new AuthenticationFeature { OriginalPath = path, OriginalPathBase = "/tenant" });
    if (path == "/session-ended") await services.GetRequiredService<ApplicationAuthenticationPresentation>().WriteSessionPageAsync(context);
    else await writer.WriteAsync(context, 503, AuthenticationErrorCodes.IdentityProviderUnavailable);
    var body = await Body(context);
    if (path.StartsWith("/api"))
    {
        Require(context.Response.ContentType!.StartsWith("application/problem+json"), "Restored API received browser HTML.");
        using var json = JsonDocument.Parse(body); Require(json.RootElement.GetProperty("code").GetString() == "identity_provider_unavailable", "Restored API code changed.");
    }
    else
    {
        Require(context.Response.ContentType == "text/html; charset=utf-8" && body.Contains("/tenant/bff/login?returnUrl=%2Ftenant%2Fworkspace"), "Restored shell route lost purpose or native base.");
        await File.WriteAllTextAsync(Path.Combine(output, path == "/session-ended" ? "session-restored.html" : path == "/bff/login" ? "login-restored.html" : "denied-restored.html"), body);
    }
    cases++;
}
foreach (var (code, text) in new[] { (AuthenticationErrorCodes.IdentityProviderUnavailable, "provider is unavailable"), (AuthenticationErrorCodes.AuthorizationDenied, "do not have access"), ("<script>secret</script>", "Please sign in") })
{
    var context = Context("/bff/access-denied", "text/html"); await writer.WriteAsync(context, 503, code);
    var html = await Body(context); Require(html.Contains(text) && !html.Contains("<script>"), "Allowlisted browser copy changed."); cases++;
}
foreach (var existing in new[] { false, true })
{
    var context = Context("/session-ended", "text/html", existing);
    context.Request.QueryString = new QueryString("?remote=complete&signedOut=true");
    await services.GetRequiredService<ApplicationAuthenticationPresentation>().WriteSessionPageAsync(context);
    var html = await Body(context);
    Require(html.Contains("session is still active") == existing && html.Contains("Provider sign-out has not been confirmed") == !existing, "Landing trusted URL instead of session evidence.");
    await File.WriteAllTextAsync(Path.Combine(output, existing ? "session-existing.html" : "session-ended.html"), html); cases++;
}
foreach (var path in new[] { "//attacker.invalid", "/\\attacker.invalid", "/%2f%2fattacker.invalid", "/../outside", "/workspace?returnUrl=https://attacker.invalid" })
{
    try { _ = new ApplicationAuthenticationPresentation("Example", path, ["/signin-oidc"]); throw new InvalidOperationException("Unsafe target accepted."); }
    catch (ArgumentException) { cases++; }
}
var cancelled = Context("/signin-oidc", "text/html"); cancelled.RequestAborted = new CancellationToken(true);
try { await writer.WriteAsync(cancelled, 400, AuthenticationErrorCodes.CallbackInvalid); throw new InvalidOperationException("Cancellation lost."); }
catch (OperationCanceledException) { cases++; }
Console.WriteLine($"{cases} native presentation seam cases passed; no provider/consumer authentication acceptance claimed.");

sealed class FixtureCookieAuthentication : IAuthenticationService
{
    public Task<AuthenticateResult> AuthenticateAsync(HttpContext context, string? scheme) => Task.FromResult(
        context.Items["existing-session"] is true
            ? AuthenticateResult.Success(new AuthenticationTicket(new ClaimsPrincipal(new ClaimsIdentity([new Claim(ClaimTypes.NameIdentifier, "synthetic")], "fixture-cookie")), CookieAuthenticationDefaults.AuthenticationScheme))
            : AuthenticateResult.NoResult());
    public Task ChallengeAsync(HttpContext context, string? scheme, AuthenticationProperties? properties) => throw new NotSupportedException();
    public Task ForbidAsync(HttpContext context, string? scheme, AuthenticationProperties? properties) => throw new NotSupportedException();
    public Task SignInAsync(HttpContext context, string? scheme, ClaimsPrincipal principal, AuthenticationProperties? properties) => throw new NotSupportedException();
    public Task SignOutAsync(HttpContext context, string? scheme, AuthenticationProperties? properties) => throw new NotSupportedException();
}
