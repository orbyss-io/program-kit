using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Default fail-closed host generation coordinator.</summary>
public sealed class DotNetHostGenerationCoordinator : IDotNetHostGenerationCoordinator
{
    private readonly IDotNetDocumentWriter documentWriter;
    private readonly IDotNetIntegratorDocumentValidator documentValidator;
    private readonly IDotNetHostLockSelector lockSelector;
    private readonly IDotNetHostSourceRenderer sourceRenderer;
    private readonly IDotNetShellValidator shellValidator;

    /// <summary>Initializes the coordinator with injected validation and rendering behavior.</summary>
    public DotNetHostGenerationCoordinator(
        IDotNetShellValidator shellValidator,
        IDotNetHostLockSelector lockSelector,
        IDotNetHostSourceRenderer sourceRenderer,
        IDotNetDocumentWriter documentWriter,
        IDotNetIntegratorDocumentValidator documentValidator)
    {
        this.shellValidator = shellValidator ??
            throw new ArgumentNullException(nameof(shellValidator));
        this.lockSelector = lockSelector ??
            throw new ArgumentNullException(nameof(lockSelector));
        this.sourceRenderer = sourceRenderer ??
            throw new ArgumentNullException(nameof(sourceRenderer));
        this.documentWriter = documentWriter ??
            throw new ArgumentNullException(nameof(documentWriter));
        this.documentValidator = documentValidator ??
            throw new ArgumentNullException(nameof(documentValidator));
    }

    /// <inheritdoc />
    public ValueTask<ImmutableArray<GeneratedOutput>> GenerateAsync(
        DotNetHostGenerationInput input,
        DotNetHostKind requiredKind,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(input);
        cancellationToken.ThrowIfCancellationRequested();
        var validation = shellValidator.Validate(input.Shell);
        if (!validation.IsValid)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidShell,
                "Host generation requires a valid shell document.",
                string.Empty);
        }

        var host = ResolveHost(input.Shell.Hosts, input.HostIdentity, requiredKind);
        var hostLock = lockSelector.Resolve(input.Lock, input.HostIdentity, requiredKind);
        ValidateLock(input, host, hostLock);
        ValidateDocument(input, requiredKind);
        ValidateDocumentSemantics(input, host, requiredKind);
        var selectedActivations = host.FeatureActivationIdentities.ToHashSet();
        var features = input.Shell.Features
            .Where(feature => selectedActivations.Contains(feature.ActivationIdentity))
            .OrderBy(static feature => feature.ActivationIdentity.Value, StringComparer.Ordinal)
            .ToImmutableArray();
        var outputs = sourceRenderer.Render(
            host,
            hostLock,
            features,
            input.OpenApi,
            input.OpenConsole).ToBuilder();
        outputs.Add(new GeneratedOutput("shell.lock.json", documentWriter.Write(input.Lock)));
        if (input.OpenApi is not null)
        {
            outputs.Add(new GeneratedOutput("docs/openapi.json", documentWriter.Write(input.OpenApi)));
        }

        if (input.OpenConsole is not null)
        {
            outputs.Add(new GeneratedOutput("docs/open-console.json", documentWriter.Write(input.OpenConsole)));
        }

        if (input.OpenWorker is not null)
        {
            outputs.Add(new GeneratedOutput("docs/open-worker.json", documentWriter.Write(input.OpenWorker)));
        }

        return ValueTask.FromResult(
            outputs
                .OrderBy(static output => output.RelativePath, StringComparer.Ordinal)
                .ToImmutableArray());
    }

    private static DotNetHostDefinition ResolveHost(
        ImmutableArray<DotNetHostDefinition> hosts,
        ProgramKitIdentifier identity,
        DotNetHostKind requiredKind)
    {
        var matches = hosts
            .Where(host => host.Identity == identity)
            .ToArray();
        if (matches.Length != 1 || matches[0].Kind != requiredKind)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidHostSelection,
                "The requested host must resolve exactly once with the required kind.",
                "/hosts");
        }

        return matches[0];
    }

    private static void ValidateLock(
        DotNetHostGenerationInput input,
        DotNetHostDefinition host,
        DotNetHostLock hostLock)
    {
        var target = hostLock.Target;
        var mismatch =
            input.Lock.InputVersionMapRevision != input.Shell.InputVersionMapRevision ||
            input.Lock.InputVersionSelectionRevision != input.Shell.InputVersionSelectionRevision ||
            hostLock.InputVersionMapRevision != input.Shell.InputVersionMapRevision ||
            hostLock.InputVersionSelectionRevision != input.Shell.InputVersionSelectionRevision ||
            target.ProfileRevision != host.DotNetTargetProfileRevision ||
            target.SdkVersion != "10.0.302" ||
            target.TargetFramework != "net10.0" ||
            target.LanguageVersion != "14.0" ||
            target.RollForward != "disable" ||
            target.AllowPrerelease;
        if (mismatch)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidHostLock,
                "The host lock does not materialize the exact shell inputs and .NET 10 target profile.",
                "/hostLocks");
        }
    }

    private static void ValidateDocument(
        DotNetHostGenerationInput input,
        DotNetHostKind requiredKind)
    {
        var valid = requiredKind switch
        {
            DotNetHostKind.Api =>
                input.OpenApi is not null &&
                input.OpenConsole is null &&
                input.OpenWorker is null,
            DotNetHostKind.Console =>
                input.OpenApi is null &&
                input.OpenConsole is not null &&
                input.OpenWorker is null,
            DotNetHostKind.Worker =>
                input.OpenApi is null &&
                input.OpenConsole is null &&
                input.OpenWorker is not null,
            _ => false,
        };
        if (!valid)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidIntegratorDocument,
                "Exactly the integrator document matching the selected host kind is required.",
                "/documentation");
        }
    }

    private void ValidateDocumentSemantics(
        DotNetHostGenerationInput input,
        DotNetHostDefinition host,
        DotNetHostKind requiredKind)
    {
        var validation = requiredKind switch
        {
            DotNetHostKind.Api => documentValidator.Validate(input.OpenApi!),
            DotNetHostKind.Console => documentValidator.Validate(input.OpenConsole!),
            DotNetHostKind.Worker => documentValidator.Validate(input.OpenWorker!),
            _ => ProgramKitValidationResult.From(
                [
                    new ProgramKitDiagnostic(
                        DotNetDiagnosticIds.InvalidIntegratorDocument,
                        ProgramKitDiagnosticSeverity.Error,
                        "The host kind is unsupported.",
                        "/documentation"),
                ]),
        };
        if (!validation.IsValid)
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidIntegratorDocument,
                "The integrator document violates its exact projection contract.",
                "/documentation");
        }

        if (!HasExactProjection(input, host, requiredKind))
        {
            throw DotNetKitException.Create(
                DotNetDiagnosticIds.InvalidIntegratorDocument,
                "The integrator document must bind the selected shell, host, generator, operations, and typed contract sets exactly.",
                "/documentation");
        }
    }

    private static bool HasExactProjection(
        DotNetHostGenerationInput input,
        DotNetHostDefinition host,
        DotNetHostKind requiredKind)
    {
        var provenance = requiredKind switch
        {
            DotNetHostKind.Api => input.OpenApi!.Provenance,
            DotNetHostKind.Console => input.OpenConsole!.Provenance,
            DotNetHostKind.Worker => input.OpenWorker!.Provenance,
            _ => null,
        };
        if (provenance is null ||
            provenance.ShellRevision != input.ShellRevision ||
            provenance.GeneratorRevision != host.GeneratorProfileRevision)
        {
            return false;
        }

        var bindingKeys = host.OperationBindings
            .Select(static binding => Exact(binding.OperationContract.OperationRevision))
            .ToHashSet(StringComparer.Ordinal);
        var provenanceKeys = provenance.OperationRevisions
            .Select(Exact)
            .ToHashSet(StringComparer.Ordinal);
        if (!bindingKeys.SetEquals(provenanceKeys))
        {
            return false;
        }

        return requiredKind switch
        {
            DotNetHostKind.Api => HasExactApiProjection(
                host,
                input.OpenApi!),
            DotNetHostKind.Console =>
                input.OpenConsole!.HostRevision.Identity == host.Identity &&
                input.OpenConsole.HostRevision.Version == host.Version &&
                HasExactConsoleProjection(
                    host.OperationBindings,
                    input.OpenConsole),
            DotNetHostKind.Worker =>
                input.OpenWorker!.HostRevision.Identity == host.Identity &&
                input.OpenWorker.HostRevision.Version == host.Version &&
                HasExactWorkerProjection(
                    host.OperationBindings,
                    input.OpenWorker),
            _ => false,
        };
    }

    private static bool HasExactApiProjection(
        DotNetHostDefinition host,
        Documentation.Api.OpenApiDocumentProjection document)
    {
        var bindings = host.OperationBindings;
        if (bindings.Length != document.Operations.Length)
        {
            return false;
        }

        foreach (var operation in document.Operations)
        {
            var matches = bindings.Where(binding =>
                binding.OperationContract.OperationRevision == operation.OperationRevision).ToArray();
            if (matches.Length != 1 ||
                !ExactSet(
                    matches[0].GetInputSchemaRevisions(),
                    operation.InputSchemaRevisions) ||
                !ExactSet(
                    matches[0].GetResultSchemaRevisions(),
                    operation.ResultSchemaRevisions) ||
                !ExactSet(
                    matches[0].GetDiagnosticSchemaRevisions(),
                    operation.DiagnosticSchemaRevisions) ||
                !ExactSet(
                    matches[0].GetRelatedOperationRevisions(),
                    operation.RelatedOperationRevisions) ||
                !HasExactProblemDetailsProjection(host, operation) ||
                !HasExactSecurityProjection(host, document, operation))
            {
                return false;
            }
        }

        return true;
    }

    private static bool HasExactSecurityProjection(
        DotNetHostDefinition host,
        Documentation.Api.OpenApiDocumentProjection document,
        Documentation.Api.OpenApiOperationProjection operation)
    {
        var security = host.Security;
        if (security is null)
        {
            return document.SecuritySchemes.IsDefaultOrEmpty &&
                   operation.Security is null;
        }

        if (document.SecuritySchemes.IsDefault)
        {
            return false;
        }

        var expectedSchemes = new HashSet<string>(StringComparer.Ordinal);
        if (security.OidcConfidentialInteractive is { } oidc)
        {
            expectedSchemes.Add(string.Concat(
                oidc.Scheme,
                "|OpenIdConnect|",
                oidc.MetadataAddress.AbsoluteUri,
                "|"));
        }

        if (security.JwtResourceServer is { } jwt)
        {
            expectedSchemes.Add(string.Concat(
                jwt.Scheme,
                "|HttpBearerJwt||JWT"));
        }

        var actualSchemes = document.SecuritySchemes
            .Select(static scheme => string.Concat(
                scheme.Name,
                "|",
                scheme.Kind,
                "|",
                scheme.OpenIdConnectUrl?.AbsoluteUri,
                "|",
                scheme.BearerFormat))
            .ToHashSet(StringComparer.Ordinal);
        if (!expectedSchemes.SetEquals(actualSchemes) ||
            expectedSchemes.Count != document.SecuritySchemes.Length)
        {
            return false;
        }

        var operationBinding = security.OperationBindings.SingleOrDefault(
            binding =>
                binding.OperationRevision == operation.OperationRevision &&
                string.Equals(binding.Method, operation.Method, StringComparison.Ordinal) &&
                string.Equals(binding.Path, operation.Path, StringComparison.Ordinal));
        if (operationBinding is null || operation.Security is null)
        {
            return false;
        }

        if (operationBinding.Disposition ==
            Operations.Security.DotNetOperationSecurityDisposition.Anonymous)
        {
            return operation.Security.Anonymous &&
                   operation.Security.PolicyIdentity is null &&
                   operation.Security.SchemeNames.IsDefaultOrEmpty;
        }

        if (operationBinding.PolicyIdentity is null ||
            operation.Security.Anonymous ||
            operation.Security.PolicyIdentity != operationBinding.PolicyIdentity)
        {
            return false;
        }

        var policy = security.Policies.SingleOrDefault(
            item => item.PolicyRevision.Identity == operationBinding.PolicyIdentity);
        return policy is not null &&
               ExactStringSet(
                   policy.AuthenticationSchemes,
                   operation.Security.SchemeNames);
    }

    private static bool ExactStringSet(
        ImmutableArray<string> expected,
        ImmutableArray<string> actual)
    {
        if (expected.IsDefault || actual.IsDefault ||
            expected.Length != actual.Length)
        {
            return false;
        }

        return expected.ToHashSet(StringComparer.Ordinal)
            .SetEquals(actual);
    }

    private static bool HasExactProblemDetailsProjection(
        DotNetHostDefinition host,
        Documentation.Api.OpenApiOperationProjection operation)
    {
        if (operation.ProblemDetailsResponses.IsDefault)
        {
            return false;
        }

        var expected = host.TransportFailures?.Profile.Failures
            .Select(static failure => string.Concat(
                failure.StatusCode,
                "|",
                failure.Identity.Value,
                "|",
                failure.Type.AbsoluteUri,
                "|",
                failure.Title,
                "|",
                Exact(failure.ProblemSchemaRevision)))
            .ToHashSet(StringComparer.Ordinal) ?? [];
        var actual = operation.ProblemDetailsResponses
            .Select(static response => string.Concat(
                response.StatusCode,
                "|",
                response.FailureIdentity.Value,
                "|",
                response.Type.AbsoluteUri,
                "|",
                response.Title,
                "|",
                Exact(response.ProblemSchemaRevision)))
            .ToHashSet(StringComparer.Ordinal);
        return expected.SetEquals(actual) &&
               expected.Count == operation.ProblemDetailsResponses.Length;
    }

    private static bool HasExactConsoleProjection(
        ImmutableArray<Operations.DotNetOperationBinding> bindings,
        Documentation.Console.OpenConsoleDocument document)
    {
        if (bindings.Length != document.Commands.Length)
        {
            return false;
        }

        foreach (var command in document.Commands)
        {
            var matches = bindings.Where(binding =>
                binding.OperationContract.OperationRevision == command.OperationRevision).ToArray();
            var inputSchemas = command.Arguments
                .Select(static argument => argument.ValueSchemaRevision)
                .Concat(
                    document.GlobalOptions
                        .Concat(command.Options)
                        .Where(static option => option.ValueSchemaRevision is not null)
                        .Select(static option => option.ValueSchemaRevision!))
                .Concat(command.StandardInput is null
                    ? []
                    : [command.StandardInput.SchemaRevision]);
            var diagnosticSchemas = command.ExitCodes
                .SelectMany(static exitCode =>
                    exitCode.DiagnosticSchemaRevisions)
                .Concat(command.StandardError is null
                    ? []
                    : [command.StandardError.SchemaRevision]);
            if (matches.Length != 1 ||
                !ExactDeclaredSet(
                    matches[0].GetInputSchemaRevisions(),
                    inputSchemas) ||
                !ContainsOrAbsent(
                    matches[0].GetResultSchemaRevisions(),
                    command.StandardOutput) ||
                !ExactDeclaredSet(
                    matches[0].GetDiagnosticSchemaRevisions(),
                    diagnosticSchemas))
            {
                return false;
            }
        }

        return true;
    }

    private static bool HasExactWorkerProjection(
        ImmutableArray<Operations.DotNetOperationBinding> bindings,
        Documentation.Worker.OpenWorkerDocument document)
    {
        if (bindings.Length != document.Workers.Length)
        {
            return false;
        }

        foreach (var worker in document.Workers)
        {
            var matches = bindings.Where(binding =>
                binding.OperationContract.OperationRevision == worker.OperationRevision).ToArray();
            if (matches.Length != 1 ||
                !ExactSet(
                    matches[0].GetInputSchemaRevisions(),
                    worker.InputSchemaRevisions) ||
                !ExactSet(
                    matches[0].GetResultSchemaRevisions(),
                    worker.OutputSchemaRevisions) ||
                !ExactSet(
                    matches[0].GetDiagnosticSchemaRevisions(),
                    worker.ErrorSchemaRevisions))
            {
                return false;
            }
        }

        return true;
    }

    private static bool ContainsOrAbsent(
        ImmutableArray<ArtifactReference> references,
        Documentation.Console.OpenConsoleStreamContract? stream) =>
        stream is null || references.Contains(stream.SchemaRevision);

    private static bool ExactSet(
        ImmutableArray<ArtifactReference> expected,
        ImmutableArray<ArtifactReference> actual) =>
        expected.Length == actual.Length &&
        expected.Select(Exact).ToHashSet(StringComparer.Ordinal)
            .SetEquals(actual.Select(Exact));

    private static bool ExactDeclaredSet(
        ImmutableArray<ArtifactReference> expected,
        IEnumerable<ArtifactReference> declared)
    {
        var expectedKeys = expected
            .Select(Exact)
            .ToHashSet(StringComparer.Ordinal);
        return expectedKeys.SetEquals(
            declared.Select(Exact));
    }

    private static string Exact(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}
