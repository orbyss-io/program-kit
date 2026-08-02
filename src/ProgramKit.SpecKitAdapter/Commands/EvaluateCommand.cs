using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Invocation;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public sealed class EvaluateCommand
{
    private readonly IPublicProgramKitInvoker invoker;

    public EvaluateCommand(IPublicProgramKitInvoker? invoker = null)
    {
        this.invoker = invoker ?? new PublicProgramKitInvoker();
    }

    public JsonObject Execute(string workspaceRoot, JsonObject request)
    {
        AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspaceRoot, request, requireReviewedHandoff: true);
        if (!context.Applicability.Active)
            return AdapterResultWriter.Inactive(AdapterOperation.Evaluate, context.Applicability);
        string featureRoot = $"specs/{context.FeatureKey}/program-kit/generated";
        Dictionary<string, JsonObject> documents = new(AdapterFeatureClosure.Load(workspaceRoot, featureRoot), StringComparer.Ordinal);
        JsonObject construct = documents.TryGetValue($"{featureRoot}/requests/construct.json", out JsonObject? found)
            ? (JsonObject)found.DeepClone()
            : throw new InvalidDataException("Evaluation requires one prior explicit adapter construct request.");
        construct["operation"] = "evaluate";
        construct["requestedEffect"] = "none";
        construct.Remove("constructionMode");
        construct.Remove("authorityGrant");
        construct.Remove("expectedState");
        string evaluatePath = $"{featureRoot}/requests/evaluate.json";
        documents[evaluatePath] = construct;
        AdapterFeatureClosure.Publish(workspaceRoot, context, documents);
        JsonObject result = invoker.Invoke(workspaceRoot, "evaluate", evaluatePath);
        documents[$"{featureRoot}/results/evaluate.json"] = result;
        PublicationResult publication = AdapterFeatureClosure.Publish(workspaceRoot, context, documents);
        return AdapterResultWriter.Preserve(AdapterOperation.Evaluate, result, new JsonObject { ["request"] = evaluatePath, ["changed"] = publication.Changed });
    }
}
