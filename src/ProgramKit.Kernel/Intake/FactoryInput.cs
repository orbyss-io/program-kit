using System.Collections.Generic;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Kernel.Intake;

public sealed record FactoryRequestDocument(
    FactoryRequest Request,
    string RequestDigest,
    string AuthorityBindingDigest,
    JsonObject RootBundle,
    JsonObject CanonicalDocument);

public sealed record FactoryInput(
    FactoryRequestDocument RequestDocument,
    JsonObject Definition,
    IReadOnlyList<ArtifactReference> Inputs,
    IReadOnlyList<JsonObject> MappingEvidence)
{
    public FactoryRequest Request => RequestDocument.Request;

    public string RequestDigest => RequestDocument.RequestDigest;

    public JsonObject RootBundle => RequestDocument.RootBundle;
}
