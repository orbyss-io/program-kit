using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Artifacts;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers;
using Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;
namespace Orbyss.ProgramKit.SessionIntegration.Publication;

public sealed record SessionIntegrationCandidate(
    SessionIntegrationRequest Request,
    JsonObject CanonicalRequest,
    string RequestCoreIdentity,
    string RequestIdentity,
    string ExpectedLiveState,
    ISessionProviderAdapter Provider,
    IReadOnlyList<ProjectedSessionArtifact> Artifacts,
    string? AuthorityGrantLogicalPath,
    string SetDigest,
    string InstallationIdentity);

public sealed class SessionIntegrationCandidateBuilder
{
    private readonly SessionIntegrationServices services;

    public SessionIntegrationCandidateBuilder(SessionIntegrationServices services)
    {
        this.services = services;
    }

    public SessionIntegrationCandidate Build(string workspaceRoot, string requestPath, SessionLifecycleOperation expectedOperation)
    {
        JsonObject document = CanonicalJson.Parse(File.ReadAllBytes(requestPath)) as JsonObject
            ?? throw new InvalidDataException("The session request must be a JSON object.");
        if (!string.Equals(document["schema"]?.GetValue<string>(), "program-kit.session-integration-request/v1", StringComparison.Ordinal))
            throw new InvalidDataException("The session request schema is not supported.");
        SessionLifecycleOperation operation = ParseOperation(document["operation"]?.GetValue<string>());
        if (operation != expectedOperation) throw new InvalidDataException("The request operation does not match the CLI lifecycle operation.");
        if (!string.Equals(document["canonicalProfile"]?.GetValue<string>(), CanonicalJson.Profile, StringComparison.Ordinal))
            throw new InvalidDataException("The request canonical profile is not supported.");

        string scope = document["scope"]?.GetValue<string>() ?? throw new InvalidDataException("scope is required.");
        if (!string.Equals(scope, "workspace", StringComparison.Ordinal)) throw new InvalidDataException("Only exact workspace scope is supported.");
        RequestedEffect effect = ParseEffect(document["requestedEffect"]?.GetValue<string>());
        if ((operation is SessionLifecycleOperation.Explain or SessionLifecycleOperation.Verify) != (effect == RequestedEffect.None))
            throw new InvalidDataException("The request effect conflicts with the lifecycle operation.");

        JsonObject workspace = document["workspace"] as JsonObject ?? throw new InvalidDataException("workspace is required.");
        GovernedIdentity workspaceIdentity = ParseIdentity(workspace["identity"] as JsonObject);
        SessionWorkspaceBinding workspaceBinding = new(workspaceIdentity, workspace["rootBinding"]!.GetValue<string>());
        string observedRootBinding = Digests.Sha256(Encoding.UTF8.GetBytes(Path.GetFullPath(workspaceRoot)));
        if (!string.Equals(workspaceBinding.RootBindingDigest, observedRootBinding, StringComparison.Ordinal))
            throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(4), OperationPhase.Validation, EffectState.None, "The selected workspace root binding does not match the current workspace.");
        JsonObject evaluation = document["evaluationContext"] as JsonObject ?? throw new InvalidDataException("evaluationContext is required.");
        EvaluationContext evaluationContext = new(
            DateTimeOffset.ParseExact(evaluation["instant"]!.GetValue<string>(), "yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal),
            ParseIdentity(evaluation["source"] as JsonObject), evaluation["assurance"]!.GetValue<string>());

        JsonObject providerSelection = document["providerSelection"] as JsonObject ?? throw new InvalidDataException("providerSelection is required.");
        GovernedIdentity providerIdentity = Selected(providerSelection["provider"] as JsonObject);
        if (string.Equals(providerIdentity.Authority, "ambient", StringComparison.OrdinalIgnoreCase) || string.Equals(providerIdentity.Name, "ambient", StringComparison.OrdinalIgnoreCase))
            throw new AmbiguousSessionSelectionException("Ambient provider selection is ambiguous; select one exact registered provider content identity.");
        GovernedIdentity adapterIdentity = Selected(providerSelection["adapter"] as JsonObject);
        GovernedIdentity definitionIdentity = Selected(providerSelection["definition"] as JsonObject);
        GovernedIdentity conformance = ParseIdentity(providerSelection["conformanceProfile"] as JsonObject);
        ISessionProviderAdapter provider = services.Providers.Resolve(providerIdentity);
        if (provider.Manifest.AdapterIdentity != adapterIdentity)
            throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(2), OperationPhase.Resolution, EffectState.None, "The selected adapter content identity is unavailable.");
        if (services.Definition.Identity != definitionIdentity || provider.Manifest.DefinitionBinding != definitionIdentity)
            throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(2), OperationPhase.Resolution, EffectState.None, "The selected canonical definition content identity is unavailable.");
        if (provider.Manifest.ConformanceProfile != conformance)
            throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(2), OperationPhase.Resolution, EffectState.None, "The selected conformance-profile content identity is unavailable.");

        CliReleaseIdentity cli = ParseCli(document["cliRelease"] as JsonObject ?? throw new InvalidDataException("cliRelease is required."));
        services.CliVerifier.DemandExact(workspaceRoot, cli);

        JsonObject requestCore = (JsonObject)document.DeepClone();
        requestCore.Remove("authorityGrant");
        string requestCoreIdentity = CanonicalJson.Digest(requestCore);
        string requestIdentity = CanonicalJson.Digest(document);
        string? authorityPath = (document["authorityGrant"] as JsonObject)?["logicalPath"]?.GetValue<string>();
        SessionProviderSelection selection = new(providerIdentity, adapterIdentity, definitionIdentity, conformance);
        SessionIntegrationRequest request = new(
            "program-kit.session-integration-request/v1", CanonicalJson.Profile, operation, evaluationContext, workspaceBinding, scope, selection, cli, effect,
            requestCoreIdentity, requestIdentity, document["expectedInstallationState"]?.GetValue<string>(), null);
        SessionProjectionContext projectionContext = new(services.Definition, request, false);
        ProjectedSessionArtifact[] artifacts = provider.Project(projectionContext).OrderBy(static artifact => artifact.LogicalPath, StringComparer.Ordinal).ToArray();
        ValidateProjection(provider.Manifest, artifacts);
        SessionProviderConformanceReport conformanceReport = new SessionProviderConformanceEvaluator().Evaluate(provider, projectionContext);
        if (!conformanceReport.Conforms)
        {
            string failuresText = string.Join(", ", conformanceReport.Failures.Select(static failure => failure.Code));
            throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(3), OperationPhase.Validation, EffectState.None, $"The selected provider failed its declared conformance profile: {failuresText}");
        }

        SessionInstallationStore store = new(workspaceRoot, ProviderName(providerIdentity));
        string liveState = store.CurrentStateDigest(artifacts.Select(static artifact => artifact.LogicalPath));
        string setDigest = Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', artifacts.Select(static artifact => $"{artifact.LogicalPath}:{Digests.Sha256(artifact.Content)}"))));
        string installationIdentity = Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', new[]
        {
            requestCoreIdentity,
            services.Definition.Fingerprint,
            provider.Manifest.ProviderIdentity.Digest,
            provider.Manifest.AdapterIdentity.Digest,
            provider.Manifest.ConformanceProfile.Digest,
            cli.PackageDigest,
            cli.ExecutableDigest,
            cli.RuntimeProfile.Digest,
            setDigest,
        })));
        if (effect != RequestedEffect.None && !string.Equals(request.ExpectedInstallationState, liveState, StringComparison.Ordinal))
        {
            bool exactIdempotentInstall = operation == SessionLifecycleOperation.Install &&
                string.Equals(store.Inspect().Record?.InstallationIdentity.Digest, installationIdentity, StringComparison.Ordinal);
            if (!exactIdempotentInstall)
                throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(4), OperationPhase.Validation, EffectState.None, "The expected installation state is stale or does not match the exact live workspace state.");
        }
        if (operation == SessionLifecycleOperation.Install) PreflightOwnership(workspaceRoot, store, artifacts);

        return new SessionIntegrationCandidate(request, document, requestCoreIdentity, requestIdentity, liveState, provider, artifacts, authorityPath, setDigest, installationIdentity);
    }

    private static void ValidateProjection(SessionProviderManifest manifest, IReadOnlyList<ProjectedSessionArtifact> artifacts)
    {
        if (artifacts.Count != manifest.ProjectionDescriptors.Count) throw new InvalidDataException("The provider projection does not match its exact ownership manifest.");
        for (int index = 0; index < artifacts.Count; index++)
        {
            ProjectedSessionArtifact artifact = artifacts[index];
            SessionProjectionDescriptor descriptor = manifest.ProjectionDescriptors[index];
            if (!string.Equals(artifact.LogicalPath, descriptor.LogicalPath, StringComparison.Ordinal) || !string.Equals(artifact.MediaType, descriptor.MediaType, StringComparison.Ordinal))
                throw new InvalidDataException("The provider projection path or media type conflicts with the exact manifest.");
            _ = LogicalPaths.Normalize(artifact.LogicalPath);
        }
    }

    private static void PreflightOwnership(string workspaceRoot, SessionInstallationStore store, IEnumerable<ProjectedSessionArtifact> artifacts)
    {
        SessionInstallationInspection inspection = store.Inspect();
        foreach (ProjectedSessionArtifact artifact in artifacts)
        {
            string path = LogicalPaths.ResolveInside(workspaceRoot, artifact.LogicalPath);
            if (!File.Exists(path)) continue;
            string observed = Digests.Sha256(File.ReadAllBytes(path));
            bool admitted = inspection.Record?.ProjectionSet.Any(item => string.Equals(item.LogicalPath, artifact.LogicalPath, StringComparison.Ordinal) && string.Equals(item.ContentDigest, observed, StringComparison.Ordinal)) == true;
            if (!admitted) throw new IOException($"Consumer-owned or unadmitted content collides at {artifact.LogicalPath}.");
        }
    }

    private static SessionLifecycleOperation ParseOperation(string? value) => value switch { "explain" => SessionLifecycleOperation.Explain, "install" => SessionLifecycleOperation.Install, "verify" => SessionLifecycleOperation.Verify, "remove" => SessionLifecycleOperation.Remove, _ => throw new InvalidDataException("operation is required and must be exact.") };
    private static RequestedEffect ParseEffect(string? value) => value switch { "none" => RequestedEffect.None, "committed" => RequestedEffect.Committed, _ => throw new InvalidDataException("requestedEffect is invalid.") };
    private static string ProviderName(GovernedIdentity value) => value.Name;
    private static GovernedIdentity Selected(JsonObject? value) => ParseIdentity(value?["selected"] as JsonObject);
    private static GovernedIdentity ParseIdentity(JsonObject? value) => value is null ? throw new InvalidDataException("A governed identity is required.") : new(value["authority"]!.GetValue<string>(), value["kind"]!.GetValue<string>(), value["name"]!.GetValue<string>(), value["revision"]!.GetValue<string>(), value["digest"]!.GetValue<string>());
    private static CliReleaseIdentity ParseCli(JsonObject value)
    {
        string[] properties = { "schema", "canonicalProfile", "packageId", "packageVersion", "packageSource", "packageDigest", "commandName", "workspaceRelativeExecutable", "executableDigest", "reportedVersion", "runtimeProfile", "claimClass" };
        if (!value.Select(static item => item.Key).OrderBy(static item => item, StringComparer.Ordinal).SequenceEqual(properties.OrderBy(static item => item, StringComparer.Ordinal), StringComparer.Ordinal))
            throw new InvalidDataException("The CLI release properties do not match the governed contract.");
        if (!string.Equals(value["claimClass"]?.GetValue<string>(), "verified-equivalent", StringComparison.Ordinal))
            throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(1), OperationPhase.Validation, EffectState.None, "The CLI release claim class is not verified-equivalent.");
        return new CliReleaseIdentity(
            value["schema"]!.GetValue<string>(),
            value["canonicalProfile"]!.GetValue<string>(),
            value["packageId"]!.GetValue<string>(),
            value["packageVersion"]!.GetValue<string>(),
            ParseIdentity(value["packageSource"] as JsonObject),
            value["packageDigest"]!.GetValue<string>(),
            value["commandName"]!.GetValue<string>(),
            value["workspaceRelativeExecutable"]!.GetValue<string>(),
            value["executableDigest"]!.GetValue<string>(),
            value["reportedVersion"]!.GetValue<string>(),
            ParseIdentity(value["runtimeProfile"] as JsonObject),
            ClaimClass.VerifiedEquivalent);
    }
}
