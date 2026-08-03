using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.Contracts.Schemas;

public static class ContractSchemaResources
{
    public const string OperationResultId = "https://schemas.program-kit.dev/v2/operation-result.schema.json";
    public const string DistributionBindingId = "https://schemas.program-kit.dev/v1/distribution-binding.schema.json";
    public const string WorkspaceInitializationRequestId = "https://schemas.program-kit.dev/v1/workspace-init-request.schema.json";
    public const string WorkspaceManifestId = "https://schemas.program-kit.dev/v1/workspace.schema.json";
    public const string CatalogRequestId = "https://schemas.program-kit.dev/v1/catalog-request.schema.json";
    public const string DistributionCatalogId = "https://schemas.program-kit.dev/v1/distribution-catalog.schema.json";
    public const string WorkspaceRestoreRequestId = "https://schemas.program-kit.dev/v1/workspace-restore-request.schema.json";
    public const string WorkspaceLockId = "https://schemas.program-kit.dev/v1/workspace-lock.schema.json";
    public const string PreparationRequestId = "https://schemas.program-kit.dev/v1/preparation-request.schema.json";
    public const string PreparationProposalId = "https://schemas.program-kit.dev/v1/preparation-proposal.schema.json";
    public const string AuthorityDecisionRecordId = "https://schemas.program-kit.dev/v1/authority-decision-record.schema.json";
    public const string AuthorityRecordRequestId = "https://schemas.program-kit.dev/v1/authority-record-request.schema.json";
    public const string SessionIntegrationDefinitionId = "https://schemas.program-kit.dev/v1/session-integration-definition.schema.json";
    public const string SessionProviderManifestId = "https://schemas.program-kit.dev/v1/session-provider-manifest.schema.json";
    public const string SessionIntegrationRequestId = "https://schemas.program-kit.dev/v1/session-integration-request.schema.json";
    public const string SessionInstallationRecordId = "https://schemas.program-kit.dev/v1/session-installation-record.schema.json";

    public static string ReadById(string id) => ReadAll().Values.Single(content => string.Equals(JsonNode.Parse(content)?["$id"]?.GetValue<string>(), id, StringComparison.Ordinal));

    public static IReadOnlyDictionary<string, string> ReadAll()
    {
        Assembly assembly = typeof(ContractSchemaResources).Assembly;
        return assembly.GetManifestResourceNames()
            .Where(static name => name.EndsWith(".schema.json", StringComparison.Ordinal))
            .OrderBy(static name => name, StringComparer.Ordinal)
            .ToDictionary(
                static name => name[(name.LastIndexOf('.', name.Length - ".schema.json".Length - 1) + 1)..],
                name =>
                {
                    using Stream stream = assembly.GetManifestResourceStream(name)
                        ?? throw new InvalidOperationException($"Missing schema resource: {name}");
                    using StreamReader reader = new(stream);
                    return reader.ReadToEnd();
                },
                StringComparer.Ordinal);
    }
}
