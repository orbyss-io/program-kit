#:project ../src/ProgramKit.Kernel/ProgramKit.Kernel.csproj
#:property PublishAot=false

using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Intake;

string repositoryRoot = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "..", "..", ".."));
if (!File.Exists(Path.Combine(repositoryRoot, "global.json")))
{
    repositoryRoot = Directory.GetCurrentDirectory();
}

string fixtureRoot = Path.Combine(repositoryRoot, "tests", "Fixtures", "Reference.Status", "Valid");
const string ZeroDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";
const string EmptyDigest = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

JsonObject Identity(string authority, string kind, string name, string revision, string digest) => new()
{
    ["authority"] = authority,
    ["kind"] = kind,
    ["name"] = name,
    ["revision"] = revision,
    ["digest"] = digest,
};

JsonObject Artifact(JsonObject identity, string mediaType, string logicalPath, string digest, string ownership = "consumer-owned") => new()
{
    ["identity"] = identity.DeepClone(),
    ["mediaType"] = mediaType,
    ["logicalPath"] = logicalPath,
    ["digest"] = digest,
    ["ownership"] = ownership,
};

string ByteDigest(ReadOnlySpan<byte> bytes) => $"sha256:{Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant()}";

void SetSelfDigest(JsonObject document)
{
    JsonObject identity = (JsonObject)document["identity"]!;
    identity["digest"] = ZeroDigest;
    identity["digest"] = CanonicalJson.Digest(document);
}

string WriteCanonical(string relativePath, JsonObject document)
{
    string path = Path.Combine(fixtureRoot, relativePath.Replace('/', Path.DirectorySeparatorChar));
    Directory.CreateDirectory(Path.GetDirectoryName(path)!);
    File.WriteAllBytes(path, CanonicalJson.Encode(document));
    return ByteDigest(File.ReadAllBytes(path));
}

JsonObject Trace(JsonObject rootArtifact, string pointer) => new()
{
    ["source"] = rootArtifact.DeepClone(),
    ["pointer"] = pointer,
    ["claimKind"] = "approved-selection",
};

JsonObject Selection(string role, JsonObject selected, JsonObject authority, JsonObject rootArtifact, string pointer) => new()
{
    ["role"] = role,
    ["selected"] = selected.DeepClone(),
    ["selectionAuthority"] = authority.DeepClone(),
    ["trace"] = Trace(rootArtifact, pointer),
};

string implementationPath = Path.Combine(fixtureRoot, "implementation", "StatusFeature.cs");
string implementationDigest = ByteDigest(File.ReadAllBytes(implementationPath));
JsonObject implementationIdentity = Identity("consumer.reference", "source-code", "Reference.Status.StatusFeature", "1.0.0", implementationDigest);
JsonObject implementationArtifact = Artifact(implementationIdentity, "text/x-csharp", "implementation/StatusFeature.cs", implementationDigest);

JsonObject component = new()
{
    ["name"] = "Reference.Status",
    ["namespace"] = "Reference.Status",
    ["packageId"] = "Reference.Status",
    ["version"] = "1.0.0",
    ["featureName"] = "Status",
    ["featureClass"] = "StatusFeature",
    ["contractName"] = "IStatusReader",
    ["implementationSource"] = "implementation/StatusFeature.cs",
};
JsonObject application = new()
{
    ["name"] = "Reference.Status.Api",
    ["namespace"] = "Reference.Status.Api",
    ["route"] = "/status",
    ["method"] = "GET",
    ["consumesPackage"] = "Reference.Status",
};
JsonObject definition = new()
{
    ["schema"] = "program-kit.provider.dotnet.component-api-definition/v1",
    ["dependencyMirror"] = "dependencies",
    ["component"] = component.DeepClone(),
    ["application"] = application.DeepClone(),
};
string definitionDigest = CanonicalJson.Digest(definition);
JsonObject definitionIdentity = Identity("consumer.reference", "semantic-record", "Reference.Status.ComponentApi", "1.0.0", definitionDigest);
JsonObject definitionArtifact = Artifact(definitionIdentity, "application/vnd.program-kit.provider.dotnet.component-api+json", "definitions/reference-status.json", definitionDigest);
WriteCanonical("definitions/reference-status.json", definition);

string providerDigest = ByteDigest(Encoding.UTF8.GetBytes("dotnet10-cshells-0.0.28@29fe542835696131278fcacc6cdb9a6186fc0447"));
JsonObject providerIdentity = Identity("orbyss.program-kit.dotnet", "factory-provider", "dotnet-cshells", "1.0.0", providerDigest);
JsonObject distributionIdentity = Identity("orbyss.program-kit.dotnet", "distribution", "dotnet10-cshells", "1.0.0", providerDigest);
JsonObject profileIdentity = Identity("orbyss.program-kit.dotnet", "target-profile", "dotnet10-cshells-0.0.28", "1.0.0", ByteDigest(Encoding.UTF8.GetBytes("dotnet10-cshells-0.0.28")));
JsonObject selectionAuthority = Identity("consumer.reference", "selection-authority", "reference-status-review", "1.0.0", ByteDigest(Encoding.UTF8.GetBytes("reference-status-selection-authority-v1")));
JsonObject workspaceIdentity = Identity("consumer.reference", "workspace", "reference.status.workspace", "1.0.0", ByteDigest(Encoding.UTF8.GetBytes("reference.status.workspace@1.0.0")));
JsonObject evaluationSource = Identity("consumer.reference", "evaluation-context-source", "fixture-review", "1.0.0", ByteDigest(Encoding.UTF8.GetBytes("reference-status-approved-evaluation-context")));

JsonObject bundle = new()
{
    ["schema"] = "program-kit.software-definition-bundle/v1",
    ["canonicalProfile"] = CanonicalJson.Profile,
    ["identity"] = Identity("consumer.reference", "application-bundle", "Reference.Status.Api", "1.0.0", ZeroDigest),
    ["semanticRecords"] = new JsonArray(definitionArtifact.DeepClone()),
    ["implementationRecords"] = new JsonArray(implementationArtifact.DeepClone()),
    ["relationships"] = new JsonArray(),
    ["profiles"] = new JsonArray(profileIdentity.DeepClone()),
    ["selections"] = new JsonArray(),
    ["dispositions"] = new JsonArray(),
};
SetSelfDigest(bundle);
string bundleArtifactDigest = ByteDigest(CanonicalJson.Encode(bundle));
JsonObject bundleArtifact = Artifact((JsonObject)bundle["identity"]!, "application/vnd.program-kit.software-definition+json", "definitions/software-bundle.json", bundleArtifactDigest);
WriteCanonical("definitions/software-bundle.json", bundle);

JsonArray selections = new(
    Selection("intake-mapping", providerIdentity, selectionAuthority, bundleArtifact, "/profiles/0"),
    Selection("construction", providerIdentity, selectionAuthority, bundleArtifact, "/profiles/0"),
    Selection("evaluation", providerIdentity, selectionAuthority, bundleArtifact, "/profiles/0"),
    Selection("target-profile", profileIdentity, selectionAuthority, bundleArtifact, "/profiles/0"));
JsonObject evaluationContext = new()
{
    ["instant"] = "2026-08-01T12:00:00Z",
    ["source"] = evaluationSource.DeepClone(),
    ["assurance"] = "approved-declared-instant",
};

JsonObject BaseRequest(string operation, string effect) => new()
{
    ["schema"] = "program-kit.factory-request/v1",
    ["canonicalProfile"] = CanonicalJson.Profile,
    ["operation"] = operation,
    ["rootBundle"] = bundleArtifact.DeepClone(),
    ["workspaceIdentity"] = workspaceIdentity.DeepClone(),
    ["evaluationContext"] = evaluationContext.DeepClone(),
    ["requestedEffect"] = effect,
    ["selections"] = selections.DeepClone(),
};

string Closure(JsonObject request)
{
    JsonObject contractIdentity = Identity("consumer.reference", "consumer-contract", "IStatusReader", "1.0.0", CanonicalJson.Digest(component));
    JsonObject relationshipIdentity = Identity("consumer.reference", "relationship", "Reference.Status.Api-consumes-Reference.Status", "1.0.0", CanonicalJson.Digest(application));
    JsonObject closure = new()
    {
        ["schema"] = "program-kit.operation-closure/v1",
        ["operation"] = request["operation"]!.GetValue<string>(),
        ["requestedEffect"] = request["requestedEffect"]!.GetValue<string>(),
        ["workspace"] = workspaceIdentity.DeepClone(),
        ["rootBundle"] = bundleArtifact.DeepClone(),
        ["resolvedItems"] = new JsonArray(definitionArtifact.DeepClone(), implementationArtifact.DeepClone()),
        ["relationship"] = new JsonObject
        {
            ["identity"] = relationshipIdentity,
            ["status"] = "direct",
            ["contract"] = contractIdentity,
        },
        ["providers"] = new JsonArray(providerIdentity.DeepClone(), providerIdentity.DeepClone()),
        ["distribution"] = distributionIdentity.DeepClone(),
        ["profile"] = profileIdentity.DeepClone(),
        ["package"] = new JsonObject { ["id"] = "Reference.Status", ["version"] = "1.0.0" },
        ["route"] = "/status",
        ["evaluationContext"] = evaluationContext.DeepClone(),
    };
    if (request["constructionMode"] is not null)
    {
        closure["constructionMode"] = request["constructionMode"]!.DeepClone();
    }
    return CanonicalJson.Digest(closure);
}

JsonObject explainRequest = BaseRequest("explain", "none");
JsonObject evaluateRequest = BaseRequest("evaluate", "none");
WriteCanonical("requests/explain.json", explainRequest);
WriteCanonical("requests/evaluate.json", evaluateRequest);

JsonObject constructRequest = BaseRequest("construct", "committed");
constructRequest["constructionMode"] = "new";
string closureDigest = Closure(constructRequest);
constructRequest["expectedState"] = new JsonObject
{
    ["closureDigest"] = closureDigest,
    ["liveStateDigest"] = EmptyDigest,
};
string requestBinding = CanonicalJson.Digest(IntakePipeline.NormalizeRequest(constructRequest));

JsonObject review = new()
{
    ["schema"] = "program-kit.human-review/v1",
    ["decision"] = "approved",
    ["reviewerIdentity"] = "fixture-reviewer:reference-status-v1",
    ["requestBinding"] = requestBinding,
    ["operation"] = "construct",
    ["effect"] = "committed",
    ["evaluationInstant"] = "2026-08-01T12:00:00Z",
};
string reviewDigest = WriteCanonical("authority/review.json", review);
JsonObject reviewArtifact = Artifact(Identity("consumer.reference", "human-review", "reference-status-construction", "1.0.0", reviewDigest), "application/json", "authority/review.json", reviewDigest);

string revocationHandle = ByteDigest(Encoding.UTF8.GetBytes("consumer.reference:authority-grant:reference-status-construction@1.0.0:revocation-handle/v1"));
JsonObject revocations = new()
{
    ["schema"] = "program-kit.authority-revocations/v1",
    ["revokedGrantDigests"] = new JsonArray(),
};
string revocationsDigest = WriteCanonical("authority/revocations.json", revocations);
JsonObject revocationsArtifact = Artifact(Identity("consumer.reference", "revocation-state", "reference-status-authority", "1.0.0", revocationsDigest), "application/json", "authority/revocations.json", revocationsDigest);

JsonObject DigestCondition(string kind, string value) => new()
{
    ["kind"] = kind,
    ["value"] = new JsonObject { ["classification"] = "public", ["valueKind"] = "digest", ["value"] = value },
};

JsonObject grant = new()
{
    ["schema"] = "program-kit.authority-grant/v1",
    ["canonicalProfile"] = CanonicalJson.Profile,
    ["identity"] = Identity("consumer.reference", "authority-grant", "reference-status-construction", "1.0.0", ZeroDigest),
    ["issuerAssertion"] = new JsonObject
    {
        ["provider"] = Identity("orbyss.program-kit", "authority-provider", "repository-record", "1.0.0", ByteDigest(Encoding.UTF8.GetBytes("repository-record-presence/v1"))),
        ["issuer"] = "fixture-reviewer:reference-status-v1",
        ["assurance"] = "repository-record-presence",
    },
    ["subjects"] = new JsonArray(
        new JsonObject { ["kind"] = "workspace", ["identity"] = workspaceIdentity.DeepClone() },
        new JsonObject { ["kind"] = "root-bundle", ["identity"] = ((JsonObject)bundle["identity"]!).DeepClone() }),
    ["operations"] = new JsonArray("construct"),
    ["effects"] = new JsonArray("committed"),
    ["requestBinding"] = requestBinding,
    ["conditions"] = new JsonArray(
        DigestCondition("operation-closure", closureDigest),
        DigestCondition("review-digest", reviewDigest),
        DigestCondition("expected-live-state", EmptyDigest),
        DigestCondition("revocation-handle", revocationHandle)),
    ["validity"] = new JsonObject { ["notBefore"] = "2026-01-01T00:00:00Z", ["notAfter"] = "2027-01-01T00:00:00Z" },
    ["revocationReference"] = revocationsArtifact.DeepClone(),
    ["provenance"] = reviewArtifact.DeepClone(),
};
SetSelfDigest(grant);
string grantDigest = WriteCanonical("authority/construct-grant.json", grant);
constructRequest["authorityGrant"] = Artifact((JsonObject)grant["identity"]!, "application/vnd.program-kit.authority-grant+json", "authority/construct-grant.json", grantDigest);
WriteCanonical("requests/construct.json", constructRequest);

Console.WriteLine($"Reference fixture updated. closure={closureDigest} requestBinding={requestBinding}");
