using System.Collections.Immutable;
using System.Reflection;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Converters;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Metadata;
using Orbyss.ProgramKit.Serialization.Json.Profiles;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

/// <summary>Default validated factory for immutable Program Kit JSON registries.</summary>
public sealed class ProgramKitJsonRegistryFactory : IProgramKitJsonRegistryFactory
{
    /// <inheritdoc />
    public IProgramKitJsonRegistry Create(
        ImmutableArray<JsonSerializationProfile> profiles,
        ImmutableArray<JsonProfileOwnedMechanics> profileOwnedMechanics,
        ImmutableArray<JsonSerializationContributionSelection> contributionSelections)
    {
        if (profiles.IsDefault)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "JSON profile registrations must be initialized.",
                "/profiles");
        }

        if (contributionSelections.IsDefault)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "JSON contribution selections must be initialized.",
                "/selections");
        }

        var profilesByExactKey = ValidateProfiles(profiles);
        var ownedMetadataByProfile =
            ValidateProfileOwnedMechanics(profilesByExactKey, profileOwnedMechanics);
        foreach (var selection in contributionSelections)
        {
            ArgumentNullException.ThrowIfNull(selection);
            ValidateProfileReference(
                selection.Profile,
                "/selections/profile");
        }

        var selectedByProfile = contributionSelections
            .GroupBy(
                static selection => ExactKey(selection.Profile),
                StringComparer.Ordinal)
            .ToDictionary(
                static group => group.Key,
                static group => group.Select(
                    static selection => selection.Contribution).ToImmutableArray(),
                StringComparer.Ordinal);

        foreach (var selectionKey in selectedByProfile.Keys)
        {
            if (!profilesByExactKey.ContainsKey(selectionKey))
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.UnknownProfile,
                    $"A contribution selection references unknown profile '{selectionKey}'.",
                    "/selections");
            }
        }

        var orderedProfiles = profilesByExactKey
            .OrderBy(static pair => pair.Key, StringComparer.Ordinal)
            .Select(static pair => pair.Value)
            .ToImmutableArray();
        var frozenBuilder =
            ImmutableDictionary.CreateBuilder<string, FrozenJsonProfile>(
                StringComparer.Ordinal);
        var selectionsBuilder =
            ImmutableArray.CreateBuilder<JsonSerializationProfileSelection>();

        foreach (var profile in orderedProfiles)
        {
            var key = ExactKey(profile.Reference);
            var selected = selectedByProfile.GetValueOrDefault(
                key,
                ImmutableArray<JsonSerializationContribution>.Empty);
            var ownedMechanics = ownedMetadataByProfile.GetValueOrDefault(key);
            var orderedContributions =
                ValidateAndOrder(profile, ownedMechanics, selected);
            var options =
                BuildOptions(profile, ownedMechanics, orderedContributions);
            var rootMetadataTargetTypes =
                (ownedMechanics?.RuntimeTargetTypes ?? [])
                .AddRange(orderedContributions
                    .Where(static contribution =>
                        contribution.Descriptor.Kind ==
                        JsonSerializationContributionKind.TypeInfoResolver)
                    .SelectMany(static contribution =>
                        contribution.RuntimeTargetTypes))
                .Distinct()
                .ToImmutableArray();
            frozenBuilder.Add(
                key,
                new FrozenJsonProfile(
                    profile,
                    options,
                    rootMetadataTargetTypes));
            selectionsBuilder.Add(
                new JsonSerializationProfileSelection(
                    profile.Reference,
                    orderedContributions
                        .Select(static contribution => contribution.Descriptor.Reference)
                        .ToImmutableArray()));
        }

        return new ProgramKitJsonRegistry(
            orderedProfiles,
            selectionsBuilder.ToImmutable(),
            frozenBuilder.ToImmutable());
    }

    private static ImmutableDictionary<string, JsonProfileOwnedMechanics>
        ValidateProfileOwnedMechanics(
            Dictionary<string, JsonSerializationProfile> profilesByExactKey,
            ImmutableArray<JsonProfileOwnedMechanics> mechanics)
    {
        if (mechanics.IsDefault)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "Profile-owned metadata registrations must be initialized.",
                "/profileOwnedMetadata");
        }

        var result =
            ImmutableDictionary.CreateBuilder<string, JsonProfileOwnedMechanics>(
                StringComparer.Ordinal);
        var jsonMetaKey = ExactKey(ProgramKitJsonProfiles.JsonMeta.Reference);
        var jsonContractsKey = ExactKey(ProgramKitJsonProfiles.JsonContracts.Reference);
        foreach (var registration in mechanics)
        {
            ArgumentNullException.ThrowIfNull(registration);
            var key = ExactKey(registration.Profile);
            if (!profilesByExactKey.ContainsKey(key))
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.UnknownProfile,
                    $"Profile-owned metadata references unknown profile '{key}'.",
                    "/profileOwnedMetadata");
            }

            if (string.Equals(key, jsonContractsKey, StringComparison.Ordinal) ||
                string.Equals(key, jsonMetaKey, StringComparison.Ordinal) &&
                !registration.IsBuiltIn)
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.RevisionDigestConflict,
                    $"Built-in profile '{key}' cannot accept replacement profile-owned mechanics; publish a new profile revision.",
                    "/profileOwnedMetadata");
            }

            if (!result.TryAdd(key, registration))
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.InvalidProfile,
                    $"Profile '{key}' has more than one profile-owned metadata context.",
                    "/profileOwnedMetadata");
            }
        }

        if (profilesByExactKey.ContainsKey(jsonMetaKey) &&
            (!result.TryGetValue(jsonMetaKey, out var jsonMetaMechanics) ||
             !jsonMetaMechanics.IsBuiltIn))
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "The built-in json-meta profile requires its exact internal profile-owned mechanics.",
                "/profileOwnedMetadata");
        }

        return result.ToImmutable();
    }

    private static Dictionary<string, JsonSerializationProfile> ValidateProfiles(
        ImmutableArray<JsonSerializationProfile> profiles)
    {
        var profilesByRevision =
            new Dictionary<string, JsonSerializationProfile>(StringComparer.Ordinal);
        foreach (var profile in profiles)
        {
            ArgumentNullException.ThrowIfNull(profile);
            ValidateProfile(profile);
            var revisionKey = RevisionKey(profile.Reference);
            if (profilesByRevision.TryGetValue(revisionKey, out var observed))
            {
                if (!string.Equals(
                        observed.Reference.Digest.Value,
                        profile.Reference.Digest.Value,
                        StringComparison.Ordinal))
                {
                    throw ProgramKitJsonException.Create(
                        ProgramKitJsonDiagnosticIds.RevisionDigestConflict,
                        $"JSON profile revision '{revisionKey}' resolves to changed bytes.",
                        "/profiles");
                }

                if (observed != profile)
                {
                    throw ProgramKitJsonException.Create(
                        ProgramKitJsonDiagnosticIds.InvalidProfile,
                        $"JSON profile revision '{revisionKey}' has inconsistent descriptors under one digest.",
                        "/profiles");
                }

                continue;
            }

            profilesByRevision.Add(revisionKey, profile);
        }

        return profilesByRevision.Values.ToDictionary(
            static profile => ExactKey(profile.Reference),
            StringComparer.Ordinal);
    }

    private static void ValidateProfile(JsonSerializationProfile profile)
    {
        ValidateProfileReference(profile.Reference, "/profiles/reference");
        if (profile.CanonicalizationProfile is null)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "A JSON profile must declare its exact canonicalization profile.",
                "/profiles/canonicalizationProfile");
        }

        if (!string.Equals(
                ExactKey(profile.CanonicalizationProfile),
                ExactKey(ProgramKitJsonProfiles.CanonicalJsonRfc8785),
                StringComparison.Ordinal))
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "Every Serialization.JSON profile must select the exact canonical-json-rfc8785 profile.",
                "/profiles/canonicalizationProfile");
        }

        if (!Enum.IsDefined(profile.Extensibility) ||
            profile.Rules is null ||
            profile.MaximumLimits is null)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "A JSON profile must declare valid extensibility and strict rules.",
                "/profiles");
        }

        if (!profile.Rules.SourceGeneratedMetadataOnly ||
            !profile.Rules.SchemaDeclaredPropertyNames ||
            !profile.Rules.CaseSensitiveReads ||
            !profile.Rules.DisallowComments ||
            !profile.Rules.DisallowTrailingCommas ||
            !profile.Rules.DisallowUnmappedMembers ||
            !profile.Rules.WriteNullProperties ||
            !profile.Rules.StrictNumbers ||
            !profile.Rules.DisallowReferencePreservation ||
            !profile.Rules.RequireNfcStrings)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "Profiles must preserve source-generated metadata, exact case-sensitive names, explicit nulls, strict reading, strict numbers, and NFC canonical strings.",
                "/profiles/rules");
        }

        profile.MaximumLimits.EnsureValid("/profiles/maximumLimits");
    }

    private static ImmutableArray<JsonSerializationContribution> ValidateAndOrder(
        JsonSerializationProfile profile,
        JsonProfileOwnedMechanics? profileOwnedMechanics,
        ImmutableArray<JsonSerializationContribution> selected)
    {
        if (selected.IsDefaultOrEmpty)
        {
            return [];
        }

        if (profile.Extensibility == JsonProfileExtensibility.None)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.NonExtensibleProfile,
                $"Profile '{profile.Reference.Identity.Value}' accepts no contributions.",
                "/selections");
        }

        var byRevision =
            new Dictionary<string, JsonSerializationContribution>(StringComparer.Ordinal);
        var byIdentity =
            new Dictionary<string, JsonSerializationContribution>(StringComparer.Ordinal);
        foreach (var contribution in selected)
        {
            ArgumentNullException.ThrowIfNull(contribution);
            ValidateContribution(profile, contribution.Descriptor);
            ValidateContributionShape(contribution);
            var revisionKey = RevisionKey(contribution.Descriptor.Reference);
            if (byRevision.TryGetValue(revisionKey, out var observed))
            {
                if (!string.Equals(
                        observed.Descriptor.Reference.Digest.Value,
                        contribution.Descriptor.Reference.Digest.Value,
                        StringComparison.Ordinal))
                {
                    throw ProgramKitJsonException.Create(
                        ProgramKitJsonDiagnosticIds.RevisionDigestConflict,
                        $"JSON contribution revision '{revisionKey}' resolves to changed bytes.",
                        "/selections");
                }

                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.InvalidContribution,
                    $"JSON contribution revision '{revisionKey}' is selected more than once.",
                    "/selections");
            }

            var identity = contribution.Descriptor.Reference.Identity.Value;
            if (!byIdentity.TryAdd(identity, contribution))
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.InvalidContribution,
                    $"Only one contribution revision may be selected for identity '{identity}'.",
                    "/selections");
            }

            byRevision.Add(revisionKey, contribution);
        }

        var edges = byIdentity.Keys.ToDictionary(
            static identity => identity,
            static _ => new HashSet<string>(StringComparer.Ordinal),
            StringComparer.Ordinal);
        var indegrees = byIdentity.Keys.ToDictionary(
            static identity => identity,
            static _ => 0,
            StringComparer.Ordinal);

        foreach (var contribution in byIdentity.Values)
        {
            var identity = contribution.Descriptor.Reference.Identity.Value;
            AddConstraints(
                identity,
                contribution.Descriptor.Before,
                before: true,
                byIdentity,
                edges,
                indegrees);
            AddConstraints(
                identity,
                contribution.Descriptor.After,
                before: false,
                byIdentity,
                edges,
                indegrees);
        }

        ValidateReservedTargets(profile, profileOwnedMechanics, byIdentity.Values);
        ValidateTargetConflicts(byIdentity, edges);

        var available = new SortedSet<string>(
            indegrees
                .Where(static pair => pair.Value == 0)
                .Select(static pair => pair.Key),
            StringComparer.Ordinal);
        var ordered =
            ImmutableArray.CreateBuilder<JsonSerializationContribution>(
                byIdentity.Count);
        while (available.Count > 0)
        {
            var identity = available.Min
                ?? throw new InvalidOperationException("The sorted set contained a null identity.");
            available.Remove(identity);
            ordered.Add(byIdentity[identity]);
            foreach (var successor in edges[identity].Order(StringComparer.Ordinal))
            {
                indegrees[successor]--;
                if (indegrees[successor] == 0)
                {
                    available.Add(successor);
                }
            }
        }

        if (ordered.Count != byIdentity.Count)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.OrderingCycle,
                "Selected JSON contribution ordering contains a cycle.",
                "/selections");
        }

        return ordered.MoveToImmutable();
    }

    private static void ValidateContribution(
        JsonSerializationProfile profile,
        JsonSerializationContributionDescriptor descriptor)
    {
        if (descriptor is null)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "A JSON contribution descriptor is required.",
                "/selections/descriptor");
        }

        var reference = descriptor.Reference;
        if (reference is null ||
            !ProgramKitIdentifier.Validate(reference.Identity.Value).IsValid ||
            reference.Identity.Kind != "json-contribution" ||
            !SemanticVersion.Validate(reference.Version.Value).IsValid ||
            !Sha256Digest.Validate(reference.Digest.Value).IsValid ||
            !ProgramKitIdentifier.Validate(
                descriptor.OwningPackage.Value).IsValid ||
            descriptor.OwningPackage.Kind != "package" ||
            !ProgramKitIdentifier.Validate(
                descriptor.ApplicableProfileId.Value).IsValid ||
            descriptor.ApplicableProfileId.Kind != "profile" ||
            !SemanticVersionRange.Validate(
                descriptor.ApplicableProfileRange.Value).IsValid ||
            !string.Equals(
                descriptor.ApplicableProfileId.Value,
                profile.Reference.Identity.Value,
                StringComparison.Ordinal) ||
            !descriptor.ApplicableProfileRange.Contains(profile.Reference.Version) ||
            !Enum.IsDefined(descriptor.Kind) ||
            descriptor.TargetTypeFamilies.IsDefaultOrEmpty ||
            descriptor.TargetTypeFamilies.Any(string.IsNullOrWhiteSpace) ||
            descriptor.TargetTypeFamilies.Distinct(StringComparer.Ordinal).Count() !=
                descriptor.TargetTypeFamilies.Length)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "A JSON contribution must declare valid exact identity, owner, applicable profile, kind, and unique target claims.",
                "/selections/descriptor");
        }

        ValidateConstraintList(descriptor.Before, "/selections/descriptor/before");
        ValidateConstraintList(descriptor.After, "/selections/descriptor/after");
        if (descriptor.Before
            .Select(static item => item.Value)
            .Intersect(
                descriptor.After.Select(static item => item.Value),
                StringComparer.Ordinal)
            .Any())
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "The same contribution identity cannot appear in both before and after constraints.",
                "/selections/descriptor");
        }
    }

    private static void ValidateContributionShape(
        JsonSerializationContribution contribution)
    {
        if (contribution.RuntimeTargetTypes.IsDefaultOrEmpty)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "A JSON contribution must expose initialized runtime target types.",
                "/selections/descriptor/targetTypeFamilies");
        }

        JsonContributionTargetContract.EnsureDescriptorMatchesRuntimeTargets(
            contribution.Descriptor,
            contribution.RuntimeTargetTypes,
            allowOpenGenericDefinitions:
                contribution.Descriptor.Kind ==
                JsonSerializationContributionKind.ConverterFactory);
        var valid = contribution.Descriptor.Kind switch
        {
            JsonSerializationContributionKind.TypedConverter =>
                contribution.Converter is not null and not JsonConverterFactory &&
                contribution.TypeInfoResolver is null &&
                contribution.RuntimeTargetTypes.Length == 1 &&
                !contribution.RuntimeTargetTypes[0].ContainsGenericParameters &&
                ConverterAcceptsDeclaredTarget(contribution),
            JsonSerializationContributionKind.ConverterFactory =>
                contribution.Converter is JsonConverterFactory &&
                contribution.TypeInfoResolver is null,
            JsonSerializationContributionKind.TypeInfoResolver =>
                contribution.Converter is null &&
                contribution.TypeInfoResolver is JsonSerializerContext context &&
                JsonContributionTargetContract
                    .GetSourceGeneratedContextTargets(context)
                    .SequenceEqual(contribution.RuntimeTargetTypes),
            _ => false,
        };
        if (!valid)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "A JSON contribution runtime shape must exactly match its declared kind.",
                "/selections/descriptor/kind");
        }
    }

    private static bool ConverterAcceptsDeclaredTarget(
        JsonSerializationContribution contribution)
    {
        JsonContributionTargetContract.EnsureConverterAcceptsTarget(
            contribution.Descriptor.Reference.Identity.Value,
            contribution.Converter!,
            contribution.RuntimeTargetTypes[0],
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            "/selections/descriptor/targetTypeFamilies");
        return true;
    }

    private static void ValidateConstraintList(
        ImmutableArray<ProgramKitIdentifier> constraints,
        string path)
    {
        if (constraints.IsDefault ||
            constraints.Any(static item =>
                !ProgramKitIdentifier.Validate(item.Value).IsValid ||
                item.Kind != "json-contribution") ||
            constraints
                .Select(static item => item.Value)
                .Distinct(StringComparer.Ordinal)
                .Count() != constraints.Length)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "Ordering constraints must be an initialized set of unique JSON contribution identities.",
                path);
        }
    }

    private static void AddConstraints(
        string identity,
        ImmutableArray<ProgramKitIdentifier> constraints,
        bool before,
        Dictionary<string, JsonSerializationContribution> byIdentity,
        Dictionary<string, HashSet<string>> edges,
        Dictionary<string, int> indegrees)
    {
        foreach (var constraint in constraints)
        {
            var target = constraint.Value;
            if (!byIdentity.ContainsKey(target))
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.OrderingGap,
                    $"Ordering constraint '{target}' is not selected for this profile.",
                    "/selections");
            }

            var predecessor = before ? identity : target;
            var successor = before ? target : identity;
            if (edges[predecessor].Add(successor))
            {
                indegrees[successor]++;
            }
        }
    }

    private static void ValidateTargetConflicts(
        IReadOnlyDictionary<string, JsonSerializationContribution> byIdentity,
        IReadOnlyDictionary<string, HashSet<string>> edges)
    {
        var contributions = byIdentity.Values
            .OrderBy(
                static contribution => contribution.Descriptor.Reference.Identity.Value,
                StringComparer.Ordinal)
            .ToArray();
        for (var leftIndex = 0; leftIndex < contributions.Length; leftIndex++)
        {
            for (var rightIndex = leftIndex + 1;
                 rightIndex < contributions.Length;
                 rightIndex++)
            {
                var left = contributions[leftIndex];
                var right = contributions[rightIndex];
                if (!ClaimsCompete(left, right) ||
                    !JsonContributionTargetContract.ClaimsOverlap(
                        left.RuntimeTargetTypes,
                        right.RuntimeTargetTypes))
                {
                    continue;
                }

                var leftIdentity = left.Descriptor.Reference.Identity.Value;
                var rightIdentity = right.Descriptor.Reference.Identity.Value;
                if (!IsReachable(leftIdentity, rightIdentity, edges) &&
                    !IsReachable(rightIdentity, leftIdentity, edges))
                {
                    throw ProgramKitJsonException.Create(
                        ProgramKitJsonDiagnosticIds.ContributionConflict,
                        $"Contributions '{leftIdentity}' and '{rightIdentity}' have overlapping runtime targets without explicit precedence.",
                        "/selections");
                }
            }
        }
    }

    private static void ValidateReservedTargets(
        JsonSerializationProfile profile,
        JsonProfileOwnedMechanics? profileOwnedMechanics,
        IEnumerable<JsonSerializationContribution> contributions)
    {
        var builtInConverters =
            BuiltInPrimitiveConverterComposition.GetBuiltInConverterTargetTypes(profile);
        foreach (var contribution in contributions)
        {
            if (IsConverter(contribution) &&
                JsonContributionTargetContract.ClaimsOverlap(
                    contribution.RuntimeTargetTypes,
                    builtInConverters))
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.ContributionConflict,
                    $"Contribution '{contribution.Descriptor.Reference.Identity.Value}' claims a fixed built-in converter target.",
                    "/selections");
            }

            if (profileOwnedMechanics is not null &&
                IsConverter(contribution) &&
                JsonContributionTargetContract.ClaimsOverlap(
                    contribution.RuntimeTargetTypes,
                    profileOwnedMechanics.ConverterTargetTypes))
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.ContributionConflict,
                    $"Contribution '{contribution.Descriptor.Reference.Identity.Value}' claims a profile-owned converter target.",
                    "/selections");
            }

            if (profileOwnedMechanics is not null &&
                contribution.Descriptor.Kind ==
                JsonSerializationContributionKind.TypeInfoResolver &&
                JsonContributionTargetContract.ClaimsOverlap(
                    contribution.RuntimeTargetTypes,
                    profileOwnedMechanics.RuntimeTargetTypes))
            {
                throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.ContributionConflict,
                    $"Contribution '{contribution.Descriptor.Reference.Identity.Value}' overlaps profile-owned metadata.",
                    "/selections");
            }
        }
    }

    private static bool ClaimsCompete(
        JsonSerializationContribution left,
        JsonSerializationContribution right) =>
        IsConverter(left) && IsConverter(right) ||
        left.Descriptor.Kind == JsonSerializationContributionKind.TypeInfoResolver &&
        right.Descriptor.Kind == JsonSerializationContributionKind.TypeInfoResolver;

    private static bool IsConverter(JsonSerializationContribution contribution) =>
        contribution.Descriptor.Kind is
            JsonSerializationContributionKind.TypedConverter or
            JsonSerializationContributionKind.ConverterFactory;

    private static bool IsReachable(
        string source,
        string target,
        IReadOnlyDictionary<string, HashSet<string>> edges)
    {
        var pending = new Stack<string>();
        var visited = new HashSet<string>(StringComparer.Ordinal);
        pending.Push(source);
        while (pending.Count > 0)
        {
            var current = pending.Pop();
            if (!visited.Add(current))
            {
                continue;
            }

            foreach (var successor in edges[current])
            {
                if (string.Equals(successor, target, StringComparison.Ordinal))
                {
                    return true;
                }

                pending.Push(successor);
            }
        }

        return false;
    }

    private static void ValidateMetadataConventions(
        JsonSerializationProfile profile,
        JsonProfileOwnedMechanics? profileOwnedMechanics,
        ImmutableArray<JsonSerializationContribution> contributions,
        Dictionary<JsonConverterFactory, Dictionary<Type, bool>>
            factoryAcceptance)
    {
        var builtInConverterTargets =
            BuiltInPrimitiveConverterComposition.GetBuiltInConverterTargetTypes(
                profile);
        if (profileOwnedMechanics is not null)
        {
            ValidateSourceGeneratedContext(
                profile,
                profileOwnedMechanics.Context,
                profileOwnedMechanics.RuntimeTargetTypes,
                builtInConverterTargets,
                profileOwnedMechanics,
                contributions,
                factoryAcceptance,
                profileOwnedMechanics.Profile.Identity.Value,
                ProgramKitJsonDiagnosticIds.InvalidProfile);
        }

        foreach (var contribution in contributions.Where(static contribution =>
                     contribution.Descriptor.Kind ==
                     JsonSerializationContributionKind.TypeInfoResolver))
        {
            ValidateSourceGeneratedContext(
                profile,
                (JsonSerializerContext)contribution.TypeInfoResolver!,
                contribution.RuntimeTargetTypes,
                builtInConverterTargets,
                profileOwnedMechanics,
                contributions,
                factoryAcceptance,
                contribution.Descriptor.Reference.Identity.Value,
                ProgramKitJsonDiagnosticIds.InvalidContribution);
        }
    }

    private static void ValidateSourceGeneratedContext(
        JsonSerializationProfile profile,
        JsonSerializerContext context,
        ImmutableArray<Type> runtimeTargets,
        ImmutableArray<Type> builtInConverterTargets,
        JsonProfileOwnedMechanics? profileOwnedMechanics,
        ImmutableArray<JsonSerializationContribution> contributions,
        Dictionary<JsonConverterFactory, Dictionary<Type, bool>>
            factoryAcceptance,
        string ownerIdentity,
        string diagnosticId)
    {
        var declaredTargets = runtimeTargets.ToHashSet();
        var pending = new Stack<Type>(runtimeTargets.Reverse());
        var visited = new HashSet<Type>();
        while (pending.Count > 0)
        {
            var target = pending.Pop();
            if (!visited.Add(target))
            {
                continue;
            }

            EnsureModelFirstContract(
                target,
                ownerIdentity,
                diagnosticId);
            EnsureNoImplicitWireConvention(
                target,
                builtInConverterTargets,
                profileOwnedMechanics,
                contributions,
                factoryAcceptance,
                ownerIdentity,
                diagnosticId);
            ValidateContractConventionOverrides(
                target,
                ownerIdentity,
                diagnosticId);
            var targetCovered =
                HasSelectedConverterForRuntimeTarget(
                    target,
                    builtInConverterTargets,
                    profileOwnedMechanics,
                    contributions,
                    factoryAcceptance);
            JsonTypeInfo? typeInfo;
            try
            {
                typeInfo = context.GetTypeInfo(target);
            }
            catch (Exception exception)
                when (exception is not OutOfMemoryException and
                      not StackOverflowException and
                      not AccessViolationException)
            {
                throw new ProgramKitJsonException(
                    new ProgramKitDiagnostic(
                        diagnosticId,
                        ProgramKitDiagnosticSeverity.Error,
                        $"Source-generated metadata '{ownerIdentity}' failed to resolve declared target '{target.FullName}'.",
                        "/targetTypeFamilies"),
                    exception);
            }

            if (typeInfo is null)
            {
                if (declaredTargets.Contains(target))
                {
                    throw ProgramKitJsonException.Create(
                        diagnosticId,
                        $"Source-generated metadata '{ownerIdentity}' does not resolve declared target '{target.FullName}'.",
                        "/targetTypeFamilies");
                }

                continue;
            }

            if (typeInfo.Type != target)
            {
                throw ProgramKitJsonException.Create(
                    diagnosticId,
                    $"Source-generated metadata '{ownerIdentity}' returned mismatched metadata for reachable type '{target.FullName}'.",
                    "/targetTypeFamilies");
            }

            if (!ReferenceEquals(typeInfo.OriginatingResolver, context))
            {
                throw ProgramKitJsonException.Create(
                    diagnosticId,
                    $"Source-generated metadata '{ownerIdentity}' returned metadata for '{target.FullName}' that did not originate from the contributed context.",
                    "/targetTypeFamilies");
            }

            if (typeInfo.PolymorphismOptions is not null ||
                target.GetCustomAttribute<JsonPolymorphicAttribute>(
                    inherit: true) is not null ||
                target.GetCustomAttributes<JsonDerivedTypeAttribute>(
                    inherit: true).Any() ||
                typeInfo.NumberHandling is not null)
            {
                throw ProgramKitJsonException.Create(
                    diagnosticId,
                    $"Source-generated metadata '{ownerIdentity}' enables a forbidden polymorphism or number-handling override for '{target.FullName}'.",
                    "/targetTypeFamilies");
            }

            if (typeInfo.Kind == JsonTypeInfoKind.Object)
            {
                ValidateDeclaredMemberConventionOverrides(
                    target,
                    ownerIdentity,
                    diagnosticId);
            }

            foreach (var property in typeInfo.Properties)
            {
                ValidatePropertyConventionOverrides(
                    property,
                    ownerIdentity,
                    diagnosticId);
                EnsureModelFirstContract(
                    property.PropertyType,
                    ownerIdentity,
                    diagnosticId);
                if (targetCovered)
                {
                    continue;
                }

                var propertyCovered =
                    HasSelectedConverterForRuntimeTarget(
                        property.PropertyType,
                        builtInConverterTargets,
                        profileOwnedMechanics,
                        contributions,
                        factoryAcceptance);
                EnsureNoImplicitWireConvention(
                    property.PropertyType,
                    builtInConverterTargets,
                    profileOwnedMechanics,
                    contributions,
                    factoryAcceptance,
                    ownerIdentity,
                    diagnosticId);
                if (!propertyCovered)
                {
                    foreach (var reachableType in EnumerateWireTypes(
                                 property.PropertyType))
                    {
                        pending.Push(reachableType);
                    }
                }
            }
        }

        ValidateGeneratedContextOptions(
            profile,
            context,
            ownerIdentity,
            diagnosticId);
    }

    private static void ValidateGeneratedContextOptions(
        JsonSerializationProfile profile,
        JsonSerializerContext context,
        string ownerIdentity,
        string diagnosticId)
    {
        var options = context.Options;
        var generationMode = context
            .GetType()
            .GetCustomAttribute<JsonSourceGenerationOptionsAttribute>(
                inherit: false)
            ?.GenerationMode ?? JsonSourceGenerationMode.Default;
        var expectsCamelCase = string.Equals(
            ExactKey(profile.Reference),
            ExactKey(ProgramKitJsonProfiles.JsonMeta.Reference),
            StringComparison.Ordinal);
        var namingPolicyMatches = expectsCamelCase
            ? ReferenceEquals(
                options.PropertyNamingPolicy,
                JsonNamingPolicy.CamelCase)
            : options.PropertyNamingPolicy is null;
        if (!namingPolicyMatches ||
            options.DictionaryKeyPolicy is not null ||
            options.PropertyNameCaseInsensitive ||
            options.AllowTrailingCommas ||
            options.ReadCommentHandling != JsonCommentHandling.Disallow ||
            options.DefaultIgnoreCondition != JsonIgnoreCondition.Never ||
            options.NumberHandling != JsonNumberHandling.Strict ||
            options.UnmappedMemberHandling !=
            JsonUnmappedMemberHandling.Disallow ||
            options.ReferenceHandler is not null ||
            options.Converters.Count != 0 ||
            options.WriteIndented ||
            !ReferenceEquals(options.TypeInfoResolver, context) ||
            options.TypeInfoResolverChain.Count != 1 ||
            !ReferenceEquals(options.TypeInfoResolverChain[0], context) ||
            !options.RespectNullableAnnotations ||
            !options.RespectRequiredConstructorParameters ||
            options.IgnoreReadOnlyFields ||
            options.IgnoreReadOnlyProperties ||
            options.IncludeFields ||
            generationMode == JsonSourceGenerationMode.Serialization)
        {
            throw ProgramKitJsonException.Create(
                diagnosticId,
                $"Source-generated metadata '{ownerIdentity}' has options that differ from the selected strict profile.",
                "/targetTypeFamilies");
        }
    }

    private static void ValidateContractConventionOverrides(
        Type type,
        string ownerIdentity,
        string diagnosticId)
    {
        if (type.GetCustomAttribute<JsonConverterAttribute>(
                inherit: true) is not null ||
            type.GetCustomAttribute<JsonNumberHandlingAttribute>(
                inherit: true) is not null ||
            type.GetCustomAttribute<JsonUnmappedMemberHandlingAttribute>(
                inherit: true) is not null)
        {
            throw ProgramKitJsonException.Create(
                diagnosticId,
                $"Source-generated metadata '{ownerIdentity}' contains a contract-level JSON convention override for '{type.FullName}'; register exact profile mechanics instead.",
                "/targetTypeFamilies");
        }
    }

    private static void ValidateDeclaredMemberConventionOverrides(
        Type type,
        string ownerIdentity,
        string diagnosticId)
    {
        const BindingFlags memberFlags =
            BindingFlags.Instance |
            BindingFlags.Public |
            BindingFlags.NonPublic;
        foreach (var member in type
                     .GetMembers(memberFlags)
                     .Where(static member =>
                         member is PropertyInfo or FieldInfo))
        {
            var memberType = member switch
            {
                PropertyInfo property => property.PropertyType,
                FieldInfo field => field.FieldType,
                _ => throw new InvalidOperationException(
                    "Only properties and fields are inspected."),
            };
            if (member.GetCustomAttribute<JsonConverterAttribute>(
                    inherit: true) is not null ||
                member.GetCustomAttribute<JsonNumberHandlingAttribute>(
                    inherit: true) is not null ||
                member.GetCustomAttribute<JsonExtensionDataAttribute>(
                    inherit: true) is not null ||
                member.GetCustomAttribute<JsonIgnoreAttribute>(
                    inherit: true) is not null)
            {
                throw ProgramKitJsonException.Create(
                    diagnosticId,
                    $"Source-generated metadata '{ownerIdentity}' contains a member-level JSON convention override on '{type.FullName}.{member.Name}'; register exact profile mechanics instead.",
                    "/targetTypeFamilies");
            }
        }
    }

    private static void ValidatePropertyConventionOverrides(
        JsonPropertyInfo property,
        string ownerIdentity,
        string diagnosticId)
    {
        if (property.CustomConverter is not null ||
            property.NumberHandling is not null ||
            property.IsExtensionData ||
            property.ShouldSerialize is not null)
        {
            throw ProgramKitJsonException.Create(
                diagnosticId,
                $"Source-generated metadata '{ownerIdentity}' contains a property-level JSON convention override for '{property.Name}'; register exact profile mechanics instead.",
                "/targetTypeFamilies");
        }
    }

    private static void EnsureModelFirstContract(
        Type type,
        string ownerIdentity,
        string diagnosticId)
    {
        var jsonMechanicsAssembly = typeof(Utf8JsonReader).Assembly;
        foreach (var candidate in EnumerateWireTypes(type))
        {
            var candidateNamespace = candidate.Namespace;
            if (candidate != typeof(object) &&
                (candidate.Assembly != jsonMechanicsAssembly ||
                 candidateNamespace is null ||
                 !candidateNamespace.StartsWith(
                     "System.Text.Json",
                     StringComparison.Ordinal)))
            {
                continue;
            }

            throw ProgramKitJsonException.Create(
                diagnosticId,
                $"Source-generated metadata '{ownerIdentity}' declares untyped JSON mechanics type '{candidate.FullName}' instead of an owned model contract.",
                "/targetTypeFamilies");
        }
    }

    private static void EnsureNoImplicitWireConvention(
        Type type,
        ImmutableArray<Type> builtInConverterTargets,
        JsonProfileOwnedMechanics? profileOwnedMechanics,
        ImmutableArray<JsonSerializationContribution> contributions,
        Dictionary<JsonConverterFactory, Dictionary<Type, bool>>
            factoryAcceptance,
        string ownerIdentity,
        string diagnosticId)
    {
        foreach (var candidate in EnumerateWireTypes(type))
        {
            if (!RequiresExplicitWireConverter(candidate) ||
                HasSelectedConverterForRuntimeTarget(
                    candidate,
                    builtInConverterTargets,
                    profileOwnedMechanics,
                    contributions,
                    factoryAcceptance))
            {
                continue;
            }

            throw ProgramKitJsonException.Create(
                diagnosticId,
                $"Source-generated metadata '{ownerIdentity}' relies on implicit wire mechanics for '{candidate.FullName}'; enum, date/time, and decimal values require an exact versioned converter contribution, and high-precision decimals should normally use schema-constrained strings.",
                "/targetTypeFamilies");
        }
    }

    private static bool HasSelectedConverterForRuntimeTarget(
        Type runtimeType,
        ImmutableArray<Type> builtInConverterTargets,
        JsonProfileOwnedMechanics? profileOwnedMechanics,
        ImmutableArray<JsonSerializationContribution> contributions,
        Dictionary<JsonConverterFactory, Dictionary<Type, bool>>
            factoryAcceptance)
    {
        if (JsonContributionTargetContract.MatchesRuntimeTarget(
                runtimeType,
                builtInConverterTargets))
        {
            return true;
        }

        if (profileOwnedMechanics is not null)
        {
            foreach (var ownedConverter in profileOwnedMechanics.Converters)
            {
                if (ownedConverter.Converter is JsonConverterFactory factory)
                {
                    if (JsonContributionTargetContract.FactoryProvidesRuntimeTarget(
                            profileOwnedMechanics.Profile.Identity.Value,
                            factory,
                            ownedConverter.RuntimeTargetTypes,
                            runtimeType,
                            factoryAcceptance[factory],
                            ProgramKitJsonDiagnosticIds.InvalidProfile,
                            "/profileOwnedMechanics/converters/targetTypeFamilies"))
                    {
                        return true;
                    }
                }
                else if (JsonContributionTargetContract.MatchesRuntimeTarget(
                             runtimeType,
                             ownedConverter.RuntimeTargetTypes))
                {
                    return true;
                }
            }
        }

        foreach (var contribution in contributions.Where(IsConverter))
        {
            if (contribution.Converter is JsonConverterFactory factory)
            {
                if (JsonContributionTargetContract.FactoryProvidesRuntimeTarget(
                        contribution.Descriptor.Reference.Identity.Value,
                        factory,
                        contribution.RuntimeTargetTypes,
                        runtimeType,
                        factoryAcceptance[factory],
                        ProgramKitJsonDiagnosticIds.InvalidContribution,
                        "/targetTypeFamilies"))
                {
                    return true;
                }
            }
            else if (JsonContributionTargetContract.MatchesRuntimeTarget(
                         runtimeType,
                         contribution.RuntimeTargetTypes))
            {
                return true;
            }
        }

        return false;
    }

    private static Dictionary<JsonConverterFactory, Dictionary<Type, bool>>
        CreateFactoryAcceptance(
            JsonProfileOwnedMechanics? profileOwnedMechanics,
            ImmutableArray<JsonSerializationContribution> contributions)
    {
        var acceptance =
            new Dictionary<JsonConverterFactory, Dictionary<Type, bool>>(
                ReferenceEqualityComparer.Instance);
        if (profileOwnedMechanics is not null)
        {
            foreach (var ownedConverter in profileOwnedMechanics.Converters)
            {
                if (ownedConverter.Converter is not JsonConverterFactory factory)
                {
                    continue;
                }

                AddClosedFactoryClaims(
                    profileOwnedMechanics.Profile.Identity.Value,
                    factory,
                    ownedConverter.RuntimeTargetTypes,
                    acceptance,
                    ProgramKitJsonDiagnosticIds.InvalidProfile,
                    "/profileOwnedMechanics/converters/targetTypeFamilies");
            }
        }

        foreach (var contribution in contributions.Where(IsConverter))
        {
            if (contribution.Converter is not JsonConverterFactory factory)
            {
                continue;
            }

            AddClosedFactoryClaims(
                contribution.Descriptor.Reference.Identity.Value,
                factory,
                contribution.RuntimeTargetTypes,
                acceptance,
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "/targetTypeFamilies");
        }

        return acceptance;
    }

    private static void AddClosedFactoryClaims(
        string ownerIdentity,
        JsonConverterFactory factory,
        ImmutableArray<Type> runtimeTargets,
        Dictionary<JsonConverterFactory, Dictionary<Type, bool>> acceptance,
        string diagnosticId,
        string path)
    {
        if (!acceptance.TryGetValue(factory, out var acceptedTargets))
        {
            acceptedTargets = [];
            acceptance.Add(factory, acceptedTargets);
        }

        foreach (var target in runtimeTargets.Where(static target =>
                     !target.IsGenericTypeDefinition))
        {
            JsonContributionTargetContract.EnsureConverterAcceptsTarget(
                ownerIdentity,
                factory,
                target,
                diagnosticId,
                path);
            acceptedTargets[target] = true;
        }
    }

    private static ImmutableHashSet<Type> GetFrozenAcceptedTargets(
        JsonConverterFactory factory,
        ImmutableArray<Type> runtimeTargets,
        Dictionary<JsonConverterFactory, Dictionary<Type, bool>>
            acceptance) =>
        acceptance[factory]
            .Where(pair =>
                pair.Value &&
                JsonContributionTargetContract.MatchesRuntimeTarget(
                    pair.Key,
                    runtimeTargets))
            .Select(static pair => pair.Key)
            .ToImmutableHashSet();

    private static IEnumerable<Type> EnumerateWireTypes(Type type)
    {
        var pending = new Stack<Type>();
        var visited = new HashSet<Type>();
        pending.Push(type);
        while (pending.Count > 0)
        {
            var current = pending.Pop();
            if (!visited.Add(current))
            {
                continue;
            }

            yield return current;
            if (current.IsArray && current.GetElementType() is { } elementType)
            {
                pending.Push(elementType);
            }

            foreach (var argument in current.GetGenericArguments())
            {
                pending.Push(argument);
            }
        }
    }

    private static bool RequiresExplicitWireConverter(Type type) =>
        type.IsEnum ||
        type == typeof(decimal) ||
        type == typeof(DateTime) ||
        type == typeof(DateTimeOffset) ||
        type == typeof(DateOnly) ||
        type == typeof(TimeOnly);

    private static JsonSerializerOptions BuildOptions(
        JsonSerializationProfile profile,
        JsonProfileOwnedMechanics? profileOwnedMechanics,
        ImmutableArray<JsonSerializationContribution> contributions)
    {
        var factoryAcceptance = CreateFactoryAcceptance(
            profileOwnedMechanics,
            contributions);
        ValidateMetadataConventions(
            profile,
            profileOwnedMechanics,
            contributions,
            factoryAcceptance);
        var options = new JsonSerializerOptions
        {
            AllowTrailingCommas = false,
            DefaultIgnoreCondition = JsonIgnoreCondition.Never,
            DictionaryKeyPolicy = null,
            Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
            MaxDepth = profile.MaximumLimits.MaxDepth,
            NumberHandling = JsonNumberHandling.Strict,
            PropertyNameCaseInsensitive = false,
            PropertyNamingPolicy = null,
            ReadCommentHandling = JsonCommentHandling.Disallow,
            ReferenceHandler = null,
            RespectNullableAnnotations = true,
            RespectRequiredConstructorParameters = true,
            UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
            WriteIndented = false,
        };

        BuiltInPrimitiveConverterComposition.AddPrimitiveConverters(options);
        var resolverClaims = new List<(
            JsonSerializerContext Context,
            ImmutableArray<Type> RuntimeTargets,
            string OwnerIdentity)>();
        if (string.Equals(
                ExactKey(profile.Reference),
                ExactKey(ProgramKitJsonProfiles.JsonMeta.Reference),
                StringComparison.Ordinal))
        {
            // This fixed, non-extensible bootstrap profile binds its generated
            // camel-case metadata in the committed profile source. Consumer
            // profiles retain a null global naming policy.
            options.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
        }

        if (profileOwnedMechanics is not null)
        {
            foreach (var ownedConverter in profileOwnedMechanics.Converters)
            {
                options.Converters.Add(
                    ownedConverter.Converter is JsonConverterFactory ownedFactory
                        ? new DeclaredTargetJsonConverterFactory(
                            ownedFactory,
                            GetFrozenAcceptedTargets(
                                ownedFactory,
                                ownedConverter.RuntimeTargetTypes,
                                factoryAcceptance),
                            profileOwnedMechanics.Profile.Identity.Value)
                        : ExactDecimalStringConverterPolicy.Apply(
                            ownedConverter.RuntimeTargetTypes[0],
                            ownedConverter.Converter));
            }

            resolverClaims.Add((
                profileOwnedMechanics.Context,
                profileOwnedMechanics.RuntimeTargetTypes,
                profileOwnedMechanics.Profile.Identity.Value));
        }

        foreach (var contribution in contributions)
        {
            if (contribution.Converter is JsonConverterFactory factory)
            {
                options.Converters.Add(new DeclaredTargetJsonConverterFactory(
                    factory,
                    GetFrozenAcceptedTargets(
                        factory,
                        contribution.RuntimeTargetTypes,
                        factoryAcceptance),
                    contribution.Descriptor.Reference.Identity.Value));
            }
            else if (contribution.Converter is not null)
            {
                options.Converters.Add(ExactDecimalStringConverterPolicy.Apply(
                    contribution.RuntimeTargetTypes[0],
                    contribution.Converter));
            }

            if (contribution.TypeInfoResolver is JsonSerializerContext context)
            {
                resolverClaims.Add((
                    context,
                    contribution.RuntimeTargetTypes,
                    contribution.Descriptor.Reference.Identity.Value));
            }
        }

        var selectedResolverByRootType =
            ImmutableDictionary.CreateBuilder<Type, JsonSerializerContext>();
        foreach (var claim in resolverClaims)
        {
            foreach (var rootType in claim.RuntimeTargets)
            {
                selectedResolverByRootType.TryAdd(rootType, claim.Context);
            }
        }

        var frozenResolverOwnership = selectedResolverByRootType.ToImmutable();
        var resolvers = resolverClaims
            .Select(claim => new DeclaredTargetJsonTypeInfoResolver(
                claim.Context,
                claim.RuntimeTargets,
                claim.OwnerIdentity,
                frozenResolverOwnership))
            .Cast<IJsonTypeInfoResolver>()
            .ToArray();
        options.TypeInfoResolver = resolvers.Length == 0
            ? new NullJsonTypeInfoResolver()
            : JsonTypeInfoResolver.Combine(resolvers);
        options.MakeReadOnly(populateMissingResolver: false);
        return options;
    }

    private static void ValidateProfileReference(
        JsonSerializationProfileRef reference,
        string path)
    {
        if (reference is null ||
            !ProgramKitIdentifier.Validate(reference.Identity.Value).IsValid ||
            reference.Identity.Kind != "profile" ||
            !SemanticVersion.Validate(reference.Version.Value).IsValid ||
            !Sha256Digest.Validate(reference.Digest.Value).IsValid)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidProfile,
                "A JSON profile reference must contain an exact profile PKID, SemVer, and SHA-256 digest.",
                path);
        }
    }

    internal static string ExactKey(JsonSerializationProfileRef reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);

    private static string ExactKey(ProfileReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);

    private static string RevisionKey(JsonSerializationProfileRef reference) =>
        string.Concat(reference.Identity.Value, "@", reference.Version.Value);

    private static string RevisionKey(JsonSerializationContributionRef reference) =>
        string.Concat(reference.Identity.Value, "@", reference.Version.Value);
}
