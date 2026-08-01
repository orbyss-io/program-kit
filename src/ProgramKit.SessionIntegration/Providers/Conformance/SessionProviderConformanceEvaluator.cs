using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.Conformance;

public sealed class SessionProviderConformanceEvaluator
{
    private readonly SessionProviderConformanceProfile profile;

    public SessionProviderConformanceEvaluator(SessionProviderConformanceProfile? profile = null)
    {
        this.profile = profile ?? SessionProviderConformanceProfiles.RepositoryWorkspaceV1;
    }

    public SessionProviderConformanceReport Evaluate(ISessionProviderAdapter adapter, SessionProjectionContext context)
    {
        List<SessionProviderConformanceFailure> failures = new();
        SessionProviderManifest manifest = adapter.Manifest;
        Check(manifest.SupportClaim == SessionProviderSupport.Supported, "support", manifest.ProviderIdentity.StableKey, "supported", Kebab(manifest.SupportClaim), failures);
        Check(string.Equals(manifest.CanonicalProfile, CanonicalJson.Profile, StringComparison.Ordinal), "normalization", manifest.ProviderIdentity.StableKey, CanonicalJson.Profile, manifest.CanonicalProfile, failures);
        Check(manifest.BindingKind == SessionBindingKind.ShellCli, "binding", manifest.ProviderIdentity.StableKey, "shell-cli", Kebab(manifest.BindingKind), failures);
        Check(profile.RequiredScopes.All(scope => manifest.SupportedScopes.Contains(scope, StringComparer.Ordinal)), "scope", manifest.ProviderIdentity.StableKey, string.Join(',', profile.RequiredScopes), string.Join(',', manifest.SupportedScopes), failures);
        Check(profile.RequiredOperations.All(operation => manifest.RequiredCliOperations.Contains(operation, StringComparer.Ordinal)), "operation", manifest.ProviderIdentity.StableKey, string.Join(',', profile.RequiredOperations), string.Join(',', manifest.RequiredCliOperations), failures);
        Check(string.Equals(manifest.ConformanceProfile.Kind, "session-provider-conformance", StringComparison.Ordinal), "profile", manifest.ConformanceProfile.StableKey, "session-provider-conformance", manifest.ConformanceProfile.Kind, failures);
        Check(manifest.ConformanceProfile == profile.Identity, "profile-identity", manifest.ConformanceProfile.StableKey, profile.Identity.Digest, manifest.ConformanceProfile.Digest, failures);
        Check(manifest.ProviderSurface.TestedVersions.Count > 0, "tested-version", manifest.ProviderIdentity.StableKey, "at least one tested version", "none", failures);
        Check(string.Equals(manifest.ProviderSurface.StructuredResultTransport, "json-stdout", StringComparison.Ordinal), "structured-result", manifest.ProviderIdentity.StableKey, "json-stdout", manifest.ProviderSurface.StructuredResultTransport, failures);
        Check(string.Equals(manifest.ProviderSurface.ReloadBehavior, "automatic-or-fresh-session", StringComparison.Ordinal), "fresh-session", manifest.ProviderIdentity.StableKey, "automatic-or-fresh-session", manifest.ProviderSurface.ReloadBehavior, failures);
        Check(string.Equals(manifest.DiagnosticCatalog.Kind, "diagnostic-catalog", StringComparison.Ordinal), "diagnostic", manifest.DiagnosticCatalog.StableKey, "diagnostic-catalog", manifest.DiagnosticCatalog.Kind, failures);
        Check(!profile.RequireGeneratedOwnership || manifest.ProjectionDescriptors.All(static item => item.Ownership == ArtifactOwnership.GeneratedOwned && item.ClaimClass == ClaimClass.CanonicalByte && string.Equals(item.RemovalPolicy, "exact-admitted-digest-only", StringComparison.Ordinal)), "ownership", manifest.ProviderIdentity.StableKey, "generated-owned canonical-byte exact-admitted-digest-only", "weakened projection contract", failures);

        IReadOnlyList<ProjectedSessionArtifact> first;
        Check(manifest.DefinitionBinding == context.Definition.Identity, "definition-binding", manifest.DefinitionBinding.StableKey, context.Definition.Identity.Digest, manifest.DefinitionBinding.Digest, failures);
        IReadOnlyList<ProjectedSessionArtifact> second;
        try
        {
            first = adapter.Project(context).OrderBy(static item => item.LogicalPath, StringComparer.Ordinal).ToArray();
            second = adapter.Project(context).OrderBy(static item => item.LogicalPath, StringComparer.Ordinal).ToArray();
        }
        catch (Exception exception)
        {
            failures.Add(new("projection", manifest.ProviderIdentity.StableKey, "bounded deterministic projection", exception.GetType().Name));
            return Report(context, manifest, Array.Empty<ProjectedSessionArtifact>(), failures);
        }

        Check(first.Count == manifest.ProjectionDescriptors.Count, "projection-count", manifest.ProviderIdentity.StableKey, manifest.ProjectionDescriptors.Count.ToString(System.Globalization.CultureInfo.InvariantCulture), first.Count.ToString(System.Globalization.CultureInfo.InvariantCulture), failures);
        Check(first.Select(static item => item.LogicalPath).Distinct(StringComparer.Ordinal).Count() == first.Count, "projection-path", manifest.ProviderIdentity.StableKey, "unique logical paths", "duplicate logical path", failures);
        Check(Equivalent(first, second), "determinism", manifest.ProviderIdentity.StableKey, "equal repeated projection", "projection bytes differ", failures);
        for (int index = 0; index < Math.Min(first.Count, manifest.ProjectionDescriptors.Count); index++)
        {
            SessionProjectionDescriptor descriptor = manifest.ProjectionDescriptors.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal).ElementAt(index);
            ProjectedSessionArtifact artifact = first[index];
            Check(string.Equals(descriptor.LogicalPath, artifact.LogicalPath, StringComparison.Ordinal), "path", descriptor.LogicalPath, descriptor.LogicalPath, artifact.LogicalPath, failures);
            Check(string.Equals(descriptor.MediaType, artifact.MediaType, StringComparison.Ordinal), "media-type", descriptor.LogicalPath, descriptor.MediaType, artifact.MediaType, failures);
            Check(artifact.Content.Length > 0, "content", descriptor.LogicalPath, "non-empty", "empty", failures);
        }

        string projectedGuidance = string.Join('\n', first.Select(static artifact => Encoding.UTF8.GetString(artifact.Content)));
        Check(!profile.RequireCleanStructuredResult || projectedGuidance.Contains(profile.ResultSchema, StringComparison.Ordinal), "structured-result-contract", manifest.ProviderIdentity.StableKey, profile.ResultSchema, "missing", failures);
        Check(!profile.RequireAuthorityPreservation || projectedGuidance.Contains("authority=request-bound", StringComparison.Ordinal), "authority", manifest.ProviderIdentity.StableKey, "authority=request-bound", "missing", failures);
        Check(!profile.RequireDisclosurePreservation || projectedGuidance.Contains("disclosure=classified", StringComparison.Ordinal), "disclosure", manifest.ProviderIdentity.StableKey, "disclosure=classified", "missing", failures);
        Check(projectedGuidance.Contains("normalization=canonical-json", StringComparison.Ordinal), "normalization-guidance", manifest.ProviderIdentity.StableKey, "normalization=canonical-json", "missing", failures);
        Check(!profile.RequireFreshSessionClassification || projectedGuidance.Contains("fresh-session=separately-classified", StringComparison.Ordinal), "fresh-session-guidance", manifest.ProviderIdentity.StableKey, "fresh-session=separately-classified", "missing", failures);

        return Report(context, manifest, first, failures);
    }

    public SessionProviderConformanceReport CompareSemanticObservations(IEnumerable<SessionSemanticObservation> observations)
    {
        SessionSemanticObservation[] ordered = observations.OrderBy(static item => item.Channel, StringComparer.Ordinal).ToArray();
        List<SessionProviderConformanceFailure> failures = new();
        if (ordered.Length < 2) failures.Add(new("semantic-corpus", "channels", "at least two observations", ordered.Length.ToString(System.Globalization.CultureInfo.InvariantCulture)));
        if (ordered.Length > 0)
        {
            SessionSemanticObservation expected = ordered[0];
            foreach (SessionSemanticObservation item in ordered.Skip(1))
            {
                Check(item.Command == expected.Command, "operation-identity", item.Channel, Kebab(expected.Command), Kebab(item.Command), failures);
                Check(item.Outcome == expected.Outcome, "outcome", item.Channel, Kebab(expected.Outcome), Kebab(item.Outcome), failures);
                Check(item.EffectState == expected.EffectState, "effect", item.Channel, Kebab(expected.EffectState), Kebab(item.EffectState), failures);
                Check(item.PrimaryDisposition == expected.PrimaryDisposition, "disposition", item.Channel, Kebab(expected.PrimaryDisposition), Kebab(item.PrimaryDisposition), failures);
                Check(string.Equals(item.ResultSchema, profile.ResultSchema, StringComparison.Ordinal), "result-schema", item.Channel, profile.ResultSchema, item.ResultSchema, failures);
                Check(item.AuthorityPreserved, "authority", item.Channel, "preserved", "not-preserved", failures);
                Check(item.DisclosurePreserved, "disclosure", item.Channel, "preserved", "not-preserved", failures);
                Check(item.WorkingScopePreserved, "working-scope", item.Channel, "preserved", "not-preserved", failures);
                Check(item.FreshSessionClassified, "fresh-session", item.Channel, "classified", "not-classified", failures);
            }
        }

        string normalized = string.Join('\n', ordered.Select(Normalize));
        string digest = Digests.Sha256(Encoding.UTF8.GetBytes(normalized));
        return new(failures.Count == 0, profile.Identity.StableKey, digest, digest, failures.OrderBy(static item => item.Code, StringComparer.Ordinal).ThenBy(static item => item.Subject, StringComparer.Ordinal).ToArray());
    }

    private SessionProviderConformanceReport Report(SessionProjectionContext context, SessionProviderManifest manifest, IReadOnlyList<ProjectedSessionArtifact> artifacts, List<SessionProviderConformanceFailure> failures)
    {
        string input = $"{context.Definition.Identity.StableKey}:{context.Definition.Identity.Digest}\n{context.Request.RequestCoreIdentity}\n{manifest.ProviderIdentity.StableKey}:{manifest.ProviderIdentity.Digest}\n{manifest.AdapterIdentity.StableKey}:{manifest.AdapterIdentity.Digest}\n{manifest.ConformanceProfile.StableKey}:{manifest.ConformanceProfile.Digest}";
        string observation = string.Join('\n', artifacts.OrderBy(static item => item.LogicalPath, StringComparer.Ordinal).Select(static item => $"{item.LogicalPath}:{item.MediaType}:{Digests.Sha256(item.Content)}"));
        return new(failures.Count == 0, profile.Identity.StableKey, Digests.Sha256(Encoding.UTF8.GetBytes(input)), Digests.Sha256(Encoding.UTF8.GetBytes(observation)), failures.OrderBy(static item => item.Code, StringComparer.Ordinal).ThenBy(static item => item.Subject, StringComparer.Ordinal).ToArray());
    }

    private static bool Equivalent(IReadOnlyList<ProjectedSessionArtifact> left, IReadOnlyList<ProjectedSessionArtifact> right) =>
        left.Count == right.Count && left.Zip(right).All(static pair => string.Equals(pair.First.LogicalPath, pair.Second.LogicalPath, StringComparison.Ordinal) && string.Equals(pair.First.MediaType, pair.Second.MediaType, StringComparison.Ordinal) && pair.First.Content.AsSpan().SequenceEqual(pair.Second.Content));

    private static void Check(bool condition, string code, string subject, string expected, string observed, ICollection<SessionProviderConformanceFailure> failures)
    {
        if (!condition) failures.Add(new(code, subject, expected, observed));
    }

    private static string Normalize(SessionSemanticObservation item) => $"{item.Channel}:{Kebab(item.Command)}:{Kebab(item.Outcome)}:{Kebab(item.EffectState)}:{Kebab(item.PrimaryDisposition)}:{item.ResultSchema}:{item.AuthorityPreserved}:{item.DisclosurePreserved}:{item.WorkingScopePreserved}:{item.FreshSessionClassified}";
    private static string Kebab<T>(T value) where T : struct, Enum => string.Concat(value.ToString().Select((character, index) => index > 0 && char.IsUpper(character) ? $"-{char.ToLowerInvariant(character)}" : char.ToLowerInvariant(character).ToString()));
}
