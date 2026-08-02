using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Invocation;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public sealed class ConstructCommand
{
    private readonly IPublicProgramKitInvoker invoker;

    public ConstructCommand(IPublicProgramKitInvoker? invoker = null)
    {
        this.invoker = invoker ?? new PublicProgramKitInvoker();
    }

    public JsonObject Execute(string workspaceRoot, JsonObject request)
    {
        AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspaceRoot, request, requireReviewedHandoff: true);
        if (!context.Applicability.Active)
            return AdapterResultWriter.NotApplicable(AdapterOperation.Construct, new JsonObject { ["blocking"] = context.Applicability.BlocksWorkflow });
        if (request["grant"] is not JsonObject grant)
            return AdapterResultWriter.Failure(AdapterOperation.Construct, Diagnostics.AdapterFailureKind.InvalidAuthority, "needs-input");

        string requestedEffect = request["requestedEffect"]!.GetValue<string>();
        string maximumEffect = context.Handoff!.Document["maximumEffect"]!.GetValue<string>();
        if (requestedEffect is not ("candidate-only" or "committed") || requestedEffect != maximumEffect)
            return AdapterResultWriter.Failure(AdapterOperation.Construct, Diagnostics.AdapterFailureKind.InvalidAuthority);

        JsonObject prepareRequest = (JsonObject)request.DeepClone();
        prepareRequest["operation"] = "prepare";
        JsonObject prepared = new PrepareCommand(invoker).Execute(workspaceRoot, prepareRequest);
        if (prepared["outcome"]!.GetValue<string>() != "succeeded")
            return AdapterResultWriter.Failure(AdapterOperation.Construct, Diagnostics.AdapterFailureKind.ProcessFailure);

        string featureRoot = $"specs/{context.FeatureKey}/program-kit/generated";
        Dictionary<string, JsonObject> documents = new(AdapterFeatureClosure.Load(workspaceRoot, featureRoot), StringComparer.Ordinal);
        JsonObject preparationResult = documents[$"{featureRoot}/results/prepare.json"];
        JsonObject proposal = preparationResult["payload"]?["proposal"]?.AsObject()
            ?? throw new InvalidDataException("The current public preparation result has no proposal.");
        JsonObject construct = (JsonObject)proposal["ungrantedProjection"]!.DeepClone();
        if (construct["requestedEffect"]?.GetValue<string>() != requestedEffect)
            return AdapterResultWriter.Failure(AdapterOperation.Construct, Diagnostics.AdapterFailureKind.InvalidAuthority);
        construct["authorityGrant"] = grant.DeepClone();
        string constructPath = $"{featureRoot}/requests/construct.json";
        documents[constructPath] = construct;
        AdapterFeatureClosure.Publish(workspaceRoot, context, documents);

        JsonObject result = invoker.Invoke(workspaceRoot, "construct", constructPath);
        documents[$"{featureRoot}/results/construct.json"] = result;
        PublicationResult publication = AdapterFeatureClosure.Publish(workspaceRoot, context, documents);
        return AdapterResultWriter.Preserve(AdapterOperation.Construct, result, new JsonObject
        {
            ["grant"] = grant.DeepClone(),
            ["request"] = constructPath,
            ["changed"] = publication.Changed,
        });
    }
}
