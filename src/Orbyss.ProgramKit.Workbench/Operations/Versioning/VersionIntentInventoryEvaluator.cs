namespace Orbyss.ProgramKit.Workbench.Operations.Versioning;

/// <summary>Default exact inventory-coverage evaluator.</summary>
public sealed class VersionIntentInventoryEvaluator :
    IVersionIntentInventoryEvaluator
{
    private readonly IProgramKitSemanticValidator<VersionIntentInventoryDocument>
        inventoryValidator;

    /// <summary>Initializes the evaluator with contract-owned validation.</summary>
    public VersionIntentInventoryEvaluator(
        IProgramKitSemanticValidator<VersionIntentInventoryDocument>
            inventoryValidator)
    {
        this.inventoryValidator = inventoryValidator ??
            throw new ArgumentNullException(nameof(inventoryValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Evaluate(
        VersionIntentInventoryValidationRequest request)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (request is null)
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.InvalidVersionIntentInventoryRequest,
                "A bounded version-intent inventory validation request is required.",
                string.Empty));
            return ProgramKitValidationResult.From(diagnostics);
        }

        diagnostics.AddRange(
            inventoryValidator.Validate(request.Inventory).Diagnostics);
        if (request.MaximumSources <= 0)
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.InvalidVersionIntentInventoryRequest,
                "The maximum source count must be positive.",
                "/maximumSources"));
        }

        if (request.ObservedSources.IsDefault)
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.InvalidVersionIntentInventoryRequest,
                "The observed-source collection must be initialized.",
                "/observedSources"));
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (request.ObservedSources.Length > request.MaximumSources ||
            request.Inventory is not null &&
            !request.Inventory.Entries.IsDefault &&
            request.Inventory.Entries.Length > request.MaximumSources)
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.OperationLimitExceeded,
                "Version-intent inventory validation exceeded the explicit source limit.",
                "/maximumSources"));
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (diagnostics.Count != 0)
        {
            return ProgramKitValidationResult.From(diagnostics);
        }

        ValidateCoverage(request, diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateCoverage(
        VersionIntentInventoryValidationRequest request,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var observations = new Dictionary<
            string,
            VersionBearingSourceObservation>(
            StringComparer.Ordinal);
        for (var index = 0; index < request.ObservedSources.Length; index++)
        {
            var observation = request.ObservedSources[index];
            var path = string.Concat("/observedSources/", index);
            if (observation is null ||
                string.IsNullOrWhiteSpace(observation.SourcePath) ||
                string.IsNullOrWhiteSpace(observation.SourceLocator) ||
                string.IsNullOrWhiteSpace(observation.CurrentValue))
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.InvalidVersionIntentInventoryRequest,
                    "Every observed source requires exact path, value, and digest.",
                    path));
                continue;
            }

            diagnostics.AddRange(Sha256Digest.Validate(
                observation.SourceDigest.Value,
                string.Concat(path, "/sourceDigest")).Diagnostics);
            if (!observations.TryAdd(
                    SourceKey(
                        observation.SourcePath,
                        observation.SourceLocator),
                    observation))
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.InvalidVersionIntentInventoryRequest,
                    "Observed source path and locator pairs must be unique.",
                    string.Concat(path, "/sourceLocator")));
            }
        }

        if (request.Inventory is null ||
            request.Inventory.Entries.IsDefault)
        {
            return;
        }

        var entries = request.Inventory.Entries
            .Where(static entry => entry is not null)
            .ToDictionary(
                static entry => SourceKey(
                    entry.SourcePath,
                    entry.SourceLocator),
                StringComparer.Ordinal);
        if (entries.Count != observations.Count ||
            entries.Keys.Except(
                observations.Keys,
                StringComparer.Ordinal).Any() ||
            observations.Keys.Except(
                entries.Keys,
                StringComparer.Ordinal).Any())
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.InvalidVersionIntentInventoryRequest,
                "Classified entries must exactly equal the bounded observed-source set.",
                "/observedSources"));
            return;
        }

        foreach (var entry in entries.Values)
        {
            var observation = observations[
                SourceKey(entry.SourcePath, entry.SourceLocator)];
            if (!string.Equals(
                    entry.CurrentValue,
                    observation.CurrentValue,
                    StringComparison.Ordinal) ||
                entry.SourceDigest != observation.SourceDigest)
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.InvalidVersionIntentInventoryRequest,
                    "Observed value and digest must exactly match the classified entry.",
                    string.Concat(
                        "/observedSources/",
                        entry.SourcePath,
                        entry.SourceLocator)));
            }
        }
    }

    private static string SourceKey(string path, string locator) =>
        string.Concat(path, "\n", locator);
}
