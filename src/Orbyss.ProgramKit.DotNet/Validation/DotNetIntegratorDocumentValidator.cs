using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.OpenConsole.Contracts.Validation;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;

namespace Orbyss.ProgramKit.DotNet.Validation;

/// <summary>Default deterministic validator for typed integrator documents.</summary>
public sealed class DotNetIntegratorDocumentValidator : IDotNetIntegratorDocumentValidator
{
    private readonly IProgramKitSemanticValidator<OpenConsoleDocument>
        openConsoleValidator;

    /// <summary>Initializes the .NET validators over neutral Open Console validation.</summary>
    public DotNetIntegratorDocumentValidator(
        IProgramKitSemanticValidator<OpenConsoleDocument> openConsoleValidator)
    {
        this.openConsoleValidator = openConsoleValidator ??
            throw new ArgumentNullException(nameof(openConsoleValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(OpenApiDocumentProjection document)
    {
        var diagnostics = Create();
        if (document is null)
        {
            Error(diagnostics, "An OpenAPI projection is required.", string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (string.IsNullOrWhiteSpace(document.Title) ||
            document.Servers.IsDefault ||
            document.Operations.IsDefault ||
            document.SecuritySchemes.IsDefault)
        {
            Error(diagnostics, "OpenAPI title, servers, and operations must be explicit.", string.Empty);
        }

        var securitySchemeNames = new HashSet<string>(StringComparer.Ordinal);
        foreach (var scheme in document.SecuritySchemes)
        {
            var valid = !string.IsNullOrWhiteSpace(scheme.Name) &&
                        securitySchemeNames.Add(scheme.Name) &&
                        Enum.IsDefined(scheme.Kind);
            valid &= scheme.Kind switch
            {
                OpenApiSecuritySchemeKind.OpenIdConnect =>
                    scheme.OpenIdConnectUrl is
                    {
                        IsAbsoluteUri: true,
                    } &&
                    string.Equals(
                        scheme.OpenIdConnectUrl.Scheme,
                        Uri.UriSchemeHttps,
                        StringComparison.Ordinal) &&
                    scheme.BearerFormat is null,
                OpenApiSecuritySchemeKind.HttpBearerJwt =>
                    scheme.OpenIdConnectUrl is null &&
                    string.Equals(
                        scheme.BearerFormat,
                        "JWT",
                        StringComparison.Ordinal),
                _ => false,
            };
            if (!valid)
            {
                Error(
                    diagnostics,
                    "OpenAPI security schemes require a unique name and exact OIDC discovery or HTTP Bearer JWT mechanics.",
                    "/securitySchemes");
            }
        }

        var keys = new HashSet<string>(StringComparer.Ordinal);
        foreach (var operation in document.Operations)
        {
            var method = operation.Method.ToUpperInvariant();
            if (!operation.Path.StartsWith('/') ||
                method is not ("GET" or "PUT" or "POST" or "DELETE" or "OPTIONS" or "HEAD" or "PATCH" or "TRACE" or "QUERY") ||
                !keys.Add(string.Concat(method, " ", operation.Path)) ||
                string.IsNullOrWhiteSpace(operation.OperationId))
            {
                Error(diagnostics, "OpenAPI operations require unique method/path pairs, absolute paths, and stable operation IDs.", "/operations");
            }

            if (operation.Security is { } security &&
                ((security.Anonymous &&
                  (security.PolicyIdentity is not null ||
                   !security.SchemeNames.IsDefaultOrEmpty)) ||
                 (!security.Anonymous &&
                  (security.PolicyIdentity is null ||
                   security.SchemeNames.IsDefaultOrEmpty ||
                   security.SchemeNames.Any(
                       scheme => !securitySchemeNames.Contains(scheme)) ||
                   security.SchemeNames.Distinct(StringComparer.Ordinal).Count() !=
                       security.SchemeNames.Length))))
            {
                Error(
                    diagnostics,
                    "Operation security must explicitly select anonymous access or one named host policy with declared schemes.",
                    "/operations/security");
            }

            if (operation.ProblemDetailsResponses.IsDefault ||
                operation.ProblemDetailsResponses.Any(static response =>
                    response.StatusCode is < 400 or > 599 ||
                    response.Type is null ||
                    !response.Type.IsAbsoluteUri ||
                    response.Type.Scheme != Uri.UriSchemeHttps ||
                    string.IsNullOrWhiteSpace(response.Title)) ||
                operation.ProblemDetailsResponses
                    .Select(static response => response.FailureIdentity.Value)
                    .Distinct(StringComparer.Ordinal)
                    .Count() != operation.ProblemDetailsResponses.Length)
            {
                Error(
                    diagnostics,
                    "Problem Details responses must be initialized, unique, explicit HTTP failures with absolute HTTPS types.",
                    "/operations/problemDetailsResponses");
            }
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(OpenConsoleDocument document)
        => openConsoleValidator.Validate(document);

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(OpenWorkerDocument document)
    {
        var diagnostics = Create();
        if (document is null)
        {
            Error(diagnostics, "An Open Worker document is required.", string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (document.Schema != "pkid:schema:program-kit:open-worker@1.0.0" ||
            document.DocumentVersion.Value != "1.0.0" ||
            document.Workers.IsDefault)
        {
            Error(diagnostics, "Open Worker must select the exact small 1.0.0 schema and initialized workers.", string.Empty);
            return ProgramKitValidationResult.From(diagnostics);
        }

        var operations = new HashSet<string>(StringComparer.Ordinal);
        foreach (var worker in document.Workers)
        {
            if (!operations.Add(DotNetContractKeys.Exact(worker.OperationRevision)) ||
                string.IsNullOrWhiteSpace(worker.TriggerKind) ||
                worker.InputSchemaRevisions.IsDefault ||
                worker.OutputSchemaRevisions.IsDefault ||
                worker.ErrorSchemaRevisions.IsDefault)
            {
                Error(diagnostics, "Workers require unique operations, a versioned trigger kind, and initialized contract sets.", "/workers");
            }
        }

        var provenance = document.Provenance.OperationRevisions.IsDefault
            ? []
            : document.Provenance.OperationRevisions
                .Select(DotNetContractKeys.Exact)
                .ToHashSet(StringComparer.Ordinal);
        if (!operations.SetEquals(provenance))
        {
            Error(diagnostics, "Worker provenance must bind exactly the projected operations.", "/provenance/operationRevisions");
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    private static ImmutableArray<ProgramKitDiagnostic>.Builder Create() =>
        ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();

    private static void Error(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        string message,
        string path) =>
        diagnostics.Add(
            new ProgramKitDiagnostic(
                DotNetDiagnosticIds.InvalidIntegratorDocument,
                ProgramKitDiagnosticSeverity.Error,
                message,
                path));
}
