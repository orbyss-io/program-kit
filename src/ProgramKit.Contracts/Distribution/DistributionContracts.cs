using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Contracts.Distribution;

public sealed record DistributionBinding(
    string Schema,
    string CanonicalProfile,
    string PackageId,
    string PackageVersion,
    string CommandName,
    string InvocationKind,
    string ToolManifest,
    string ReportedVersion,
    string PackageDigest,
    string ExecutableDigest,
    GovernedIdentity RuntimeProfile,
    GovernedIdentity Distribution);

public sealed record DistributionCatalogEntry(
    GovernedIdentity Provider,
    IReadOnlyList<GovernedIdentity> Profiles,
    IReadOnlyList<string> Roles,
    IReadOnlyList<string> InputKinds,
    IReadOnlyList<string> OutputKinds,
    IReadOnlyList<string> Effects,
    IReadOnlyList<string> Processes,
    IReadOnlyList<GovernedIdentity> Contracts,
    string SupportStatus,
    IReadOnlyList<EvidenceReference> Evidence);

public sealed record DistributionCatalog(
    string Schema,
    string CanonicalProfile,
    DistributionBinding DistributionBinding,
    IReadOnlyList<DistributionCatalogEntry> Providers,
    IReadOnlyDictionary<string, string> Schemas,
    IReadOnlyDictionary<string, string> DiagnosticCatalogs,
    IReadOnlyDictionary<string, string> CanonicalProfiles,
    IReadOnlyList<EvidenceReference> Evidence,
    string Digest);
