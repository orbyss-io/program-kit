using System.Collections.Generic;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;

namespace Orbyss.ProgramKit.SpecKitAdapter.Contracts;

public enum AdapterOperation
{
    Doctor,
    Activate,
    Disable,
    Handoff,
    Validate,
    Prepare,
    Explain,
    Construct,
    Evaluate,
    Cleanup,
}

public enum ActivationMode { Off, Assist, Required }
public enum Applicability { Applicable, Disabled, NotApplicable, Unresolved }
public enum AdapterOutcome { Succeeded, NotApplicable, NeedsInput, Blocked, Cancelled, Faulted }
public enum AdapterStage { Request, Compatibility, Applicability, Handoff, Translation, Invocation, Publication, Completion }
public enum AdapterEffectState { None, AdapterFilesOnly, ProgramKitCandidate, ProgramKitCommitted, Indeterminate }

public sealed record FeatureOverride(
    ActivationMode Mode,
    Applicability Applicability,
    string? Selection,
    JsonObject DecisionSource);

public sealed record AdapterProjectConfig(
    string Schema,
    string Invocation,
    string Manifest,
    string Lock,
    ActivationMode DefaultMode,
    IReadOnlyDictionary<string, FeatureOverride> Features,
    RequestedEffect DefaultRequestedEffect);

public sealed record AdapterRequest(
    string Schema,
    AdapterOperation Operation,
    GovernedIdentity Workspace,
    ArtifactReference Config,
    RequestedEffect RequestedEffect,
    string OutputRoot,
    GovernedIdentity? Feature = null,
    ArtifactReference? Handoff = null,
    ArtifactReference? Review = null,
    ArtifactReference? Grant = null);

public sealed record AdapterCompatibilityManifest(
    string Schema,
    string Adapter,
    IReadOnlyList<string> SpecKitVersions,
    IReadOnlyList<string> ProgramKitVersions,
    IReadOnlyList<string> RuntimeProfiles,
    IReadOnlyList<string> ProviderProfiles,
    IReadOnlyDictionary<string, string> ContractBindings,
    IReadOnlyDictionary<string, string> CommandBindings,
    AdapterTranslationProfile TranslationProfile,
    IReadOnlyList<string> Platforms,
    IReadOnlyList<string> ReleaseArtifacts,
    string Digest);

public sealed record AdapterGeneratedManifest(
    string Schema,
    GovernedIdentity AdapterRelease,
    ArtifactReference Compatibility,
    GovernedIdentity Feature,
    IReadOnlyList<ArtifactReference> Inputs,
    IReadOnlyList<ArtifactReference> Outputs,
    IReadOnlyDictionary<string, IReadOnlyList<string>> InvalidationSets,
    string Digest);

public sealed record AdapterResult(
    string Schema,
    string CanonicalProfile,
    AdapterOperation Operation,
    GovernedIdentity AdapterRelease,
    string Compatibility,
    AdapterOutcome Outcome,
    AdapterStage FurthestStage,
    AdapterEffectState EffectState,
    PrimaryDisposition PrimaryDisposition,
    IReadOnlyList<ArtifactReference> Artifacts,
    DiagnosticView Diagnostics,
    IReadOnlyList<DisclosureEntry> Disclosure,
    JsonObject? ProgramKitResult = null,
    JsonObject? Payload = null);
