using System.Collections.Immutable;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

/// <summary>
/// Collects explicitly selected profiles and contributions for one shell, then
/// atomically freezes them into immutable serializer options.
/// </summary>
public sealed class ProgramKitJsonBuilder : IProgramKitJsonBuilder
{
    private readonly List<JsonSerializationProfile> profiles = [];
    private readonly List<JsonProfileOwnedMechanics> profileOwnedMechanics = [];
    private readonly List<JsonSerializationContributionSelection> contributionSelections = [];
    private readonly Lock sync = new();
    private ProgramKitJsonBuilderState state;
    private TaskCompletionSource<IProgramKitJsonRegistry>? freezeCompletion;
    private int freezingThreadId;

    /// <summary>Initializes a builder with its registry factory collaborator.</summary>
    public ProgramKitJsonBuilder(IProgramKitJsonRegistryFactory registryFactory)
    {
        ArgumentNullException.ThrowIfNull(registryFactory);
        RegistryFactory = registryFactory;
        RegisterBuiltInOwnedProfile(
            ProgramKitJsonProfiles.JsonMeta,
            JsonMetaComposition.CreateOwnedMechanics());
        profiles.Add(ProgramKitJsonProfiles.JsonContracts);
    }

    internal IProgramKitJsonRegistryFactory RegistryFactory { get; }

    /// <inheritdoc />
    public IProgramKitJsonBuilder AddProfile(JsonSerializationProfile profile)
    {
        ArgumentNullException.ThrowIfNull(profile);
        lock (sync)
        {
            EnsureMutable();
            profiles.Add(profile);
        }

        return this;
    }

    /// <inheritdoc />
    public IProgramKitJsonBuilder AddOwnedProfile(
        JsonSerializationProfile profile,
        JsonProfileOwnedMechanics mechanics)
    {
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(mechanics);
        lock (sync)
        {
            EnsureMutable();
            EnsureExactOwnedProfilePair(profile, mechanics);
            var revision = ProgramKitJsonRegistryKey.Revision(profile.Reference);
            if (profiles.Any(candidate =>
                    string.Equals(
                        ProgramKitJsonRegistryKey.Revision(candidate.Reference),
                        revision,
                        StringComparison.Ordinal)))
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.RevisionDigestConflict,
                    $"Profile-owned mechanics require a new profile revision; '{revision}' already exists.",
                    "/profiles");
            }

            profiles.Add(profile);
            profileOwnedMechanics.Add(mechanics);
        }

        return this;
    }

    /// <inheritdoc />
    public IProgramKitJsonBuilder AddJsonSerializationContribution(
        JsonSerializationProfileRef profileReference,
        JsonSerializationContribution contribution)
    {
        ArgumentNullException.ThrowIfNull(profileReference);
        ArgumentNullException.ThrowIfNull(contribution);
        lock (sync)
        {
            EnsureMutable();
            contributionSelections.Add(
                new JsonSerializationContributionSelection(
                    profileReference,
                    contribution));
        }

        return this;
    }

    /// <inheritdoc />
    public IProgramKitJsonRegistry Freeze()
    {
        Task<IProgramKitJsonRegistry>? concurrentFreeze = null;
        TaskCompletionSource<IProgramKitJsonRegistry>? ownedCompletion = null;
        ImmutableArray<JsonSerializationProfile> profileSnapshot = default;
        ImmutableArray<JsonProfileOwnedMechanics> mechanicsSnapshot = default;
        ImmutableArray<JsonSerializationContributionSelection> selectionSnapshot = default;

        lock (sync)
        {
            if (state == ProgramKitJsonBuilderState.Frozen)
            {
                return freezeCompletion?.Task.GetAwaiter().GetResult()
                    ?? throw new InvalidOperationException(
                        "A frozen JSON builder has no registry.");
            }

            if (state == ProgramKitJsonBuilderState.Freezing)
            {
                if (freezingThreadId == Environment.CurrentManagedThreadId)
                {
                    throw ProgramKitJsonException.Create(
                        ProgramKitJsonDiagnosticIds.RegistryFrozen,
                        "Reentrant JSON registry freezing is forbidden.");
                }

                concurrentFreeze = freezeCompletion?.Task
                    ?? throw new InvalidOperationException(
                        "An active JSON freeze has no completion boundary.");
            }
            else
            {
                state = ProgramKitJsonBuilderState.Freezing;
                freezingThreadId = Environment.CurrentManagedThreadId;
                ownedCompletion = new TaskCompletionSource<IProgramKitJsonRegistry>(
                    TaskCreationOptions.RunContinuationsAsynchronously);
                freezeCompletion = ownedCompletion;
                profileSnapshot = profiles.ToImmutableArray();
                mechanicsSnapshot = profileOwnedMechanics.ToImmutableArray();
                selectionSnapshot = contributionSelections.ToImmutableArray();
            }
        }

        if (concurrentFreeze is not null)
        {
            return concurrentFreeze.GetAwaiter().GetResult();
        }

        try
        {
            var registry = RegistryFactory.Create(
                profileSnapshot,
                mechanicsSnapshot,
                selectionSnapshot);
            lock (sync)
            {
                state = ProgramKitJsonBuilderState.Frozen;
                freezingThreadId = 0;
            }

            ownedCompletion!.SetResult(registry);
            return registry;
        }
        catch (Exception exception)
        {
            lock (sync)
            {
                state = ProgramKitJsonBuilderState.Mutable;
                freezingThreadId = 0;
                freezeCompletion = null;
            }

            ownedCompletion!.SetException(exception);
            _ = ownedCompletion.Task.Exception;
            throw;
        }
    }

    private void RegisterBuiltInOwnedProfile(
        JsonSerializationProfile profile,
        JsonProfileOwnedMechanics mechanics)
    {
        EnsureExactOwnedProfilePair(profile, mechanics);
        profiles.Add(profile);
        profileOwnedMechanics.Add(mechanics);
    }

    private static void EnsureExactOwnedProfilePair(
        JsonSerializationProfile profile,
        JsonProfileOwnedMechanics mechanics)
    {
        if (!string.Equals(
                ProgramKitJsonRegistryKey.Exact(profile.Reference),
                ProgramKitJsonRegistryKey.Exact(mechanics.Profile),
                StringComparison.Ordinal))
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "Profile-owned mechanics must be registered atomically with their exact owning profile revision.",
                "/profileOwnedMechanics/profile");
        }
    }

    private void EnsureMutable()
    {
        if (state != ProgramKitJsonBuilderState.Mutable)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.RegistryFrozen,
                state == ProgramKitJsonBuilderState.Freezing
                    ? "The shell-scoped JSON builder is currently freezing."
                    : "The shell-scoped JSON builder is already frozen.");
        }
    }
}
