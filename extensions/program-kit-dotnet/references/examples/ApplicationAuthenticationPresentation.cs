using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Http;
using Orbyss.Foundation.Authentication;
using Orbyss.Foundation.Authentication.Core;
using Orbyss.Foundation.Web.ProblemDetails;
using Orbyss.Foundation.Web.ProblemDetails.Core;

namespace Example.Application.Web;

// Application-owned presentation, registered as IAuthenticationErrorWriter by its real web feature.
// Keep this in that owner's implementation project, with its branding and exact selected callback paths.
// The Foundation final web policy still owns security headers. Do not install a consumer Host.
/// <summary>Owns browser authentication recovery and public session presentation without changing machine contracts.</summary>
public sealed class ApplicationAuthenticationPresentation : IAuthenticationErrorWriter
{
    /// <summary>Application-owned branding, encoded before rendering.</summary>
    private readonly string brand;
    /// <summary>The approved local workspace destination; request query strings cannot replace it.</summary>
    private readonly PathString returnPath;
    /// <summary>Exact selected login/callback/error routes permitted to receive browser HTML.</summary>
    private readonly HashSet<PathString> interactiveFailures;
    /// <summary>The owner's actually served external recovery-focus module, relative to the shell.</summary>
    private readonly PathString recoveryModulePath;

    /// <summary>Admits the owner's branding, workspace destination and exact interactive error routes.</summary>
    /// <param name="brand">The application's display name.</param>
    /// <param name="returnPath">An unambiguous application-local workspace path, without a query or fragment.</param>
    /// <param name="interactiveFailurePaths">The selected callback/error paths and /bff/login when supported initial-login recovery is selected; API routes are excluded.</param>
    /// <param name="recoveryModulePath">The owner-local asset serving the maintained authentication-recovery-focus module.</param>
    public ApplicationAuthenticationPresentation(string brand, string returnPath, IEnumerable<string> interactiveFailurePaths, string recoveryModulePath)
    {
        this.brand = string.IsNullOrWhiteSpace(brand) ? throw new ArgumentException("Application branding is required.") : brand;
        this.returnPath = LocalPath(returnPath);
        interactiveFailures = interactiveFailurePaths.Select(LocalPath).ToHashSet();
        this.recoveryModulePath = LocalPath(recoveryModulePath);
        if (interactiveFailures.Any(path => path.StartsWithSegments("/api")))
            throw new ArgumentException("API paths cannot select browser error presentation.");
    }

    /// <inheritdoc />
    public async Task WriteAsync(HttpContext context, int statusCode, string code)
    {
        var explanation = code switch
        {
            AuthenticationErrorCodes.CallbackInvalid => "This sign-in attempt could not be completed. Start a fresh attempt to try again.",
            AuthenticationErrorCodes.IdentityProviderUnavailable => "The sign-in provider is unavailable. You can try signing in again.",
            AuthenticationErrorCodes.AuthorizationDenied => "You do not have access to this workspace.",
            AuthenticationErrorCodes.IdentityInvalid => "This application could not validate your session. Please sign in again.",
            AuthenticationErrorCodes.InvalidAntiforgeryToken => "This request could not be admitted. Please try again from this application.",
            _ => "Please sign in to open your workspace."
        };
        if (statusCode is < 400 or > 599) throw new ArgumentOutOfRangeException(nameof(statusCode));
        var original = context.Features.Get<IAuthenticationFeature>();
        var purposePath = original?.OriginalPath ?? context.Request.Path;
        if (!interactiveFailures.Contains(purposePath) || !AcceptsHtml(context))
        {
            await FoundationProblemResults.Problem(new ProblemDefinition(statusCode, code)).ExecuteAsync(context);
            return;
        }
        // A failed new login does not revoke an independently valid cookie. Ask the actual native
        // cookie authentication service; do not infer an existing session from the error or URL.
        var existing = await context.AuthenticateAsync(CookieAuthenticationDefaults.AuthenticationScheme);
        await WritePageAsync(context, statusCode, "Sign-in needs attention", explanation, existing.Succeeded);
    }

    // Map only an application-owned PUBLIC route such as /session-ended, with AllowAnonymous and
    // WebResponseMetadata(Private: true). Keep /bff/signed-out and /bff/user JSON contracts untouched.
    /// <summary>Renders public recovery from actual local cookie authentication, preserving unknown provider completion.</summary>
    public async Task WriteSessionPageAsync(HttpContext context)
    {
        var session = await context.AuthenticateAsync(CookieAuthenticationDefaults.AuthenticationScheme);
        await WritePageAsync(context, StatusCodes.Status200OK,
            session.Succeeded ? "Your application session is still active" : "Your application session has ended",
            session.Succeeded
                ? "This application still has an active session. You can continue or try signing out again."
                : "This application has no active session. Provider sign-out has not been confirmed; its session may still be active.",
            session.Succeeded);
    }

    /// <summary>Renders encoded, focused recovery with safe shell-relative navigation and private-response headers.</summary>
    private async Task WritePageAsync(HttpContext context, int status, string title, string explanation, bool existingSession)
    {
        context.RequestAborted.ThrowIfCancellationRequested();
        // Shell endpoint delegates can restore the outer request path before invoking the writer.
        // Native authentication retains the admitted shell-relative path/base across that boundary.
        var basePath = context.Features.Get<IAuthenticationFeature>()?.OriginalPathBase ?? context.Request.PathBase;
        var home = basePath.Add(returnPath).Value!;
        var restart = basePath.Add(new PathString("/bff/login")).Value! + "?returnUrl=" + Uri.EscapeDataString(home);
        var focusModule = basePath.Add(recoveryModulePath).Value!;
        var continueLink = existingSession ? $"<p><a tabindex=\"0\" href=\"{Encode(home)}\">Continue to your workspace</a></p>" : "";
        context.Response.StatusCode = status;
        context.Response.ContentType = "text/html; charset=utf-8";
        context.Response.Headers.CacheControl = "no-store";
        context.Response.Headers["X-Robots-Tag"] = "noindex, nofollow";
        await context.Response.WriteAsync($"""
            <!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
            <title>{Encode(title)} — {Encode(brand)}</title></head><body><header><p>{Encode(brand)}</p></header>
            <main aria-labelledby="recovery-title"><h1 id="recovery-title" data-authentication-recovery-heading tabindex="-1" autofocus>{Encode(title)}</h1>
            <p role="status">{Encode(explanation)}</p>{continueLink}<p><a tabindex="0" href="{Encode(restart)}">Start a fresh sign-in</a></p>
            </main><script type="module" src="{Encode(focusModule)}"></script></body></html>
            """, context.RequestAborted);
    }

    /// <summary>Requires explicit acceptable HTML rather than treating a wildcard as browser admission.</summary>
    private static bool AcceptsHtml(HttpContext context)
    {
        // Explicit route purpose plus explicit HTML admission; */* alone remains a machine response.
        try { return context.Request.GetTypedHeaders().Accept?.Any(value =>
            string.Equals(value.MediaType.Value, "text/html", StringComparison.OrdinalIgnoreCase) && (value.Quality ?? 1) > 0) == true; }
        catch (FormatException) { return false; }
    }

    /// <summary>Rejects ambiguous, external and request-derived browser destinations before registration.</summary>
    private static PathString LocalPath(string value)
    {
        if (!value.StartsWith('/') || value.StartsWith("//") || value.IndexOfAny(['\\', '%', '?', '#']) >= 0
            || value.Any(char.IsControl) || value.Split('/').Any(segment => segment is "." or ".."))
            throw new ArgumentException("Browser destinations must be unambiguous application-local paths.");
        return new PathString(value);
    }

    /// <summary>Encodes all application text and navigation attributes for HTML.</summary>
    private static string Encode(string value) => HtmlEncoder.Default.Encode(value);
}
