using System.Collections.Generic;
using Orbyss.ProgramKit.Contracts.Distribution;
using Orbyss.ProgramKit.Contracts.Identity;

namespace Orbyss.ProgramKit.Contracts.Workspace;

public sealed record WorkspaceInitializationRequest(
    string Schema,
    string CanonicalProfile,
    GovernedIdentity WorkspaceIdentity,
    DistributionBinding DistributionBinding,
    string RequestedBy,
    string RequestedEffect,
    string ManifestPath,
    string LockPath);

public sealed record NamedProfileSelection(
    string Alias,
    GovernedIdentity Provider,
    GovernedIdentity TargetProfile,
    GovernedIdentity SelectionAuthority);

public sealed record WorkspaceFactoryConfiguration(
    IReadOnlyList<NamedProfileSelection> Selections,
    string? DefaultSelection);

public sealed record WorkspaceManifest(
    string Schema,
    DistributionBinding Distribution,
    WorkspaceFactoryConfiguration Factory);

public sealed record WorkspaceRestoreRequest(
    string Schema,
    string CanonicalProfile,
    GovernedIdentity WorkspaceIdentity,
    DistributionBinding DistributionBinding,
    string Manifest,
    string LockPath,
    string Mode,
    IReadOnlyList<string> AllowedSources);

public sealed record WorkspaceResolutionLock(
    string Schema,
    string CanonicalProfile,
    GovernedIdentity WorkspaceIdentity,
    DistributionBinding DistributionBinding,
    string ManifestDigest,
    string Mode,
    IReadOnlyList<GovernedIdentity> ResolvedItems,
    IReadOnlyList<NamedProfileSelection> Selections,
    string? DefaultSelection,
    IReadOnlyList<GovernedIdentity> UnresolvedItems,
    string ClosureDigest,
    IReadOnlyList<string> Evidence,
    string Digest);
