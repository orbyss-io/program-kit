using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Authority;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Resolution;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Kernel.Authority;

public sealed class RepositoryAuthorityProvider
{
    public const string SchemaId = "https://schemas.program-kit.dev/v1/authority-grant.schema.json";

    private readonly StructuralSchemaValidator structural = new(new SchemaRegistry());
    private readonly TypedContractBinder binder = new();

    public AuthorityDecision Demand(string workspaceRoot, FactoryInput input, ResolutionLock resolutionLock)
    {
        FactoryRequest request = input.Request;
        if (request.RequestedEffect == RequestedEffect.None)
        {
            throw new InvalidOperationException("Authority must not be demanded for a no-effect operation.");
        }

        ArtifactReference reference = request.AuthorityGrant
            ?? throw new UnauthorizedAccessException("No exact repository authority artifact was supplied.");
        JsonObject document = LoadAuthorityArtifact(workspaceRoot, reference, "grant");
        if (structural.Validate(SchemaId, document).Count > 0)
        {
            throw new UnauthorizedAccessException("The repository authority artifact does not conform to its exact schema.");
        }

        AuthorityGrant grant = Bind(document);
        if (!string.Equals(grant.Identity.Digest, reference.Identity.Digest, StringComparison.Ordinal)
            || !string.Equals(grant.Identity.Digest, IntakePipeline.DocumentIdentityDigest(document), StringComparison.Ordinal))
        {
            throw new UnauthorizedAccessException("The authority identity is not bound to the exact grant document.");
        }

        if (!grant.Operations.Contains(request.Operation)
            || !grant.Effects.Contains(request.RequestedEffect)
            || !string.Equals(grant.RequestBinding, input.RequestDocument.AuthorityBindingDigest, StringComparison.Ordinal))
        {
            throw new UnauthorizedAccessException("The grant does not approve this exact request, operation, and effect.");
        }

        string lockDigest = CanonicalJson.Digest(resolutionLock.CanonicalDocument);
        if (grant.LockBinding is not null && !string.Equals(grant.LockBinding, lockDigest, StringComparison.Ordinal))
        {
            throw new UnauthorizedAccessException("The grant lock binding does not match the resolved operation closure.");
        }

        if (!grant.Subjects.Any(subject => subject == request.WorkspaceIdentity)
            || !grant.Subjects.Any(subject => subject == request.RootBundle.Identity))
        {
            throw new UnauthorizedAccessException("The grant does not cover the exact workspace and root-bundle subjects.");
        }

        if (request.EvaluationContext.Instant < grant.NotBefore
            || request.EvaluationContext.Instant > grant.NotAfter
            || grant.NotBefore > grant.NotAfter)
        {
            throw new UnauthorizedAccessException("The grant is not valid at the approved request-bound evaluation instant.");
        }

        string operationClosure = RequiredCondition(grant, "operation-closure");
        string reviewBinding = RequiredCondition(grant, "review-digest");
        string expectedLiveState = RequiredCondition(grant, "expected-live-state");
        string revocationHandle = RequiredCondition(grant, "revocation-handle");
        if (!string.Equals(operationClosure, resolutionLock.ClosureDigest, StringComparison.Ordinal)
            || request.ExpectedState is null
            || !string.Equals(request.ExpectedState.ClosureDigest, resolutionLock.ClosureDigest, StringComparison.Ordinal)
            || !string.Equals(expectedLiveState, request.ExpectedState.LiveStateDigest, StringComparison.Ordinal))
        {
            throw new UnauthorizedAccessException("Authority closure or expected-state freshness is not exact.");
        }

        JsonObject review = LoadAuthorityArtifact(workspaceRoot, grant.Provenance, "human review");
        ValidateReview(review, grant, input.RequestDocument.AuthorityBindingDigest, reviewBinding, request);
        JsonObject revocations = LoadAuthorityArtifact(workspaceRoot, grant.RevocationReference, "revocation state");
        ValidateRevocation(revocations, revocationHandle);

        return new AuthorityDecision(
            grant,
            input.RequestDocument.AuthorityBindingDigest,
            operationClosure,
            grant.Provenance.Digest,
            grant.RevocationReference.Digest);
    }

    private AuthorityGrant Bind(JsonObject document)
    {
        JsonObject issuer = RequiredObject(document, "issuerAssertion");
        JsonObject validity = RequiredObject(document, "validity");
        GovernedIdentity[] subjects = RequiredArray(document, "subjects")
            .Select((node, index) => binder.BindIdentity(RequiredObject(node as JsonObject ?? throw new InvalidDataException($"subjects[{index}] must be an object."), "identity")))
            .ToArray();
        FactoryOperation[] operations = RequiredArray(document, "operations").Select(static node => ParseEnum<FactoryOperation>(node!.GetValue<string>())).ToArray();
        RequestedEffect[] effects = RequiredArray(document, "effects").Select(static node => ParseEnum<RequestedEffect>(node!.GetValue<string>())).ToArray();
        AuthorityCondition[] conditions = RequiredArray(document, "conditions")
            .Select((node, index) =>
            {
                JsonObject item = node as JsonObject ?? throw new InvalidDataException($"conditions[{index}] must be an object.");
                return new AuthorityCondition(RequiredString(item, "kind"), RequiredObject(item, "value"));
            }).ToArray();
        return new AuthorityGrant(
            RequiredString(document, "schema"),
            RequiredString(document, "canonicalProfile"),
            binder.BindIdentity(RequiredObject(document, "identity")),
            binder.BindIdentity(RequiredObject(issuer, "provider")),
            RequiredString(issuer, "issuer"),
            RequiredString(issuer, "assurance"),
            subjects,
            operations,
            effects,
            RequiredString(document, "requestBinding"),
            document["lockBinding"]?.GetValue<string>(),
            conditions,
            ParseInstant(validity, "notBefore"),
            ParseInstant(validity, "notAfter"),
            binder.BindArtifact(RequiredObject(document, "revocationReference")),
            binder.BindArtifact(RequiredObject(document, "provenance")),
            (JsonObject)document.DeepClone());
    }

    private static void ValidateReview(JsonObject review, AuthorityGrant grant, string requestBinding, string reviewBinding, FactoryRequest request)
    {
        if (!string.Equals(reviewBinding, grant.Provenance.Digest, StringComparison.Ordinal)
            || !string.Equals(review["schema"]?.GetValue<string>(), "program-kit.human-review/v1", StringComparison.Ordinal)
            || !string.Equals(review["decision"]?.GetValue<string>(), "approved", StringComparison.Ordinal)
            || string.IsNullOrWhiteSpace(review["reviewerIdentity"]?.GetValue<string>())
            || !string.Equals(review["requestBinding"]?.GetValue<string>(), requestBinding, StringComparison.Ordinal)
            || !string.Equals(review["operation"]?.GetValue<string>(), Kebab(request.Operation), StringComparison.Ordinal)
            || !string.Equals(review["effect"]?.GetValue<string>(), Kebab(request.RequestedEffect), StringComparison.Ordinal)
            || !string.Equals(review["evaluationInstant"]?.GetValue<string>(), request.EvaluationContext.Instant.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture), StringComparison.Ordinal))
        {
            throw new UnauthorizedAccessException("The exact current human review does not approve this request closure.");
        }
    }

    private static void ValidateRevocation(JsonObject document, string revocationHandle)
    {
        if (!string.Equals(document["schema"]?.GetValue<string>(), "program-kit.authority-revocations/v1", StringComparison.Ordinal)
            || document["revokedGrantDigests"] is not JsonArray revoked)
        {
            throw new UnauthorizedAccessException("The exact revocation state is unavailable or invalid.");
        }

        if (revoked.Any(node => string.Equals(node?.GetValue<string>(), revocationHandle, StringComparison.Ordinal)))
        {
            throw new UnauthorizedAccessException("The exact authority grant has been revoked.");
        }
    }

    private static string RequiredCondition(AuthorityGrant grant, string kind)
    {
        AuthorityCondition[] matches = grant.Conditions.Where(condition => string.Equals(condition.Kind, kind, StringComparison.Ordinal)).ToArray();
        if (matches.Length != 1

            || !string.Equals(matches[0].Value["classification"]?.GetValue<string>(), "public", StringComparison.Ordinal)
            || !string.Equals(matches[0].Value["valueKind"]?.GetValue<string>(), "digest", StringComparison.Ordinal)
            || matches[0].Value["value"]?.GetValue<string>() is not { Length: > 0 } value)
        {
            throw new UnauthorizedAccessException($"The grant requires exactly one safe digest condition: {kind}.");
        }

        return value;
    }

    private static JsonObject LoadAuthorityArtifact(string workspaceRoot, ArtifactReference reference, string kind)
    {
        try
        {
            return IntakePipeline.LoadExactArtifact(workspaceRoot, reference);
        }
        catch (Exception exception) when (exception is IOException or InvalidDataException or System.Text.Json.JsonException or ProgramKitDiagnosticException)
        {
            throw new UnauthorizedAccessException($"The exact {kind} authority evidence is unavailable or changed.", exception);
        }
    }

    private static JsonObject RequiredObject(JsonObject parent, string name) =>
        parent[name] as JsonObject ?? throw new InvalidDataException($"{name} must be an object.");

    private static JsonArray RequiredArray(JsonObject parent, string name) =>
        parent[name] as JsonArray ?? throw new InvalidDataException($"{name} must be an array.");

    private static string RequiredString(JsonObject parent, string name) =>
        parent[name]?.GetValue<string>() is { Length: > 0 } value
            ? value
            : throw new InvalidDataException($"{name} must be a non-empty string.");

    private static DateTimeOffset ParseInstant(JsonObject parent, string name) =>
        DateTimeOffset.ParseExact(RequiredString(parent, name), "yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);

    private static T ParseEnum<T>(string value)
        where T : struct, Enum => Enum.TryParse(value.Replace("-", string.Empty, StringComparison.Ordinal), true, out T result)
            ? result
            : throw new InvalidDataException($"Unsupported {typeof(T).Name} value: {value}");

    private static string Kebab<T>(T value)
        where T : struct, Enum
    {
        string name = value.ToString();
        System.Text.StringBuilder builder = new();
        for (int index = 0; index < name.Length; index++)
        {
            if (index > 0 && char.IsUpper(name[index]))
            {
                builder.Append('-');
            }

            builder.Append(char.ToLowerInvariant(name[index]));
        }

        return builder.ToString();
    }
}
