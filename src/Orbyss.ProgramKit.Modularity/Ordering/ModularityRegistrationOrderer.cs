using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Modularity.Diagnostics;

namespace Orbyss.ProgramKit.Modularity.Ordering;

internal static class ModularityRegistrationOrderer
{
    internal static bool ValidateDescriptors<TRegistration>(
        IReadOnlyList<TRegistration> registrations,
        Func<TRegistration, ModularityRegistrationDescriptor?> descriptorSelector,
        IProgramKitSemanticValidator<ArtifactReference> artifactReferenceValidator,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
        where TRegistration : class
    {
        var valid = true;
        var identities = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < registrations.Count; index++)
        {
            var registration = registrations[index];
            var itemPath = string.Concat(path, "/", index);
            if (registration is null)
            {
                diagnostics.Add(ModularityDiagnostics.Error(
                    ModularityDiagnosticIds.InvalidRegistrationDescriptor,
                    "A registration is required.",
                    itemPath));
                valid = false;
                continue;
            }

            var descriptor = descriptorSelector(registration);
            if (!ValidateDescriptor(
                    descriptor,
                    artifactReferenceValidator,
                    itemPath,
                    diagnostics))
            {
                valid = false;
                continue;
            }

            var identity = descriptor!.Registration.Identity.Value;
            if (!identities.Add(identity))
            {
                diagnostics.Add(ModularityDiagnostics.Error(
                    ModularityDiagnosticIds.DuplicateRegistrationIdentity,
                    string.Concat(
                        "Registration identity '",
                        identity,
                        "' occurs more than once."),
                    string.Concat(itemPath, "/descriptor/registration/identity")));
                valid = false;
            }
        }

        return valid;
    }

    internal static ImmutableArray<TRegistration> Order<TRegistration>(
        IReadOnlyList<TRegistration> registrations,
        Func<TRegistration, ModularityRegistrationDescriptor> descriptorSelector,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
        where TRegistration : class
    {
        var byIdentity = registrations.ToDictionary(
            registration => descriptorSelector(registration).Registration.Identity.Value,
            StringComparer.Ordinal);
        var outgoing = byIdentity.Keys.ToDictionary(
            identity => identity,
            static _ => new HashSet<string>(StringComparer.Ordinal),
            StringComparer.Ordinal);
        var incomingCount = byIdentity.Keys.ToDictionary(
            identity => identity,
            static _ => 0,
            StringComparer.Ordinal);
        var orderingValid = true;

        foreach (var registration in registrations)
        {
            var descriptor = descriptorSelector(registration);
            var identity = descriptor.Registration.Identity.Value;
            foreach (var later in descriptor.Order.Before)
            {
                orderingValid &= AddEdge(
                    identity,
                    later.Value,
                    byIdentity,
                    outgoing,
                    incomingCount,
                    path,
                    diagnostics);
            }

            foreach (var earlier in descriptor.Order.After)
            {
                orderingValid &= AddEdge(
                    earlier.Value,
                    identity,
                    byIdentity,
                    outgoing,
                    incomingCount,
                    path,
                    diagnostics);
            }
        }

        if (!orderingValid)
        {
            return [];
        }

        var available = registrations
            .Where(registration =>
                incomingCount[descriptorSelector(registration).Registration.Identity.Value] == 0)
            .ToList();
        var ordered = ImmutableArray.CreateBuilder<TRegistration>(registrations.Count);
        while (available.Count > 0)
        {
            available.Sort((left, right) =>
                Compare(descriptorSelector(left), descriptorSelector(right)));
            var next = available[0];
            available.RemoveAt(0);
            ordered.Add(next);

            var nextIdentity = descriptorSelector(next).Registration.Identity.Value;
            foreach (var dependent in outgoing[nextIdentity].Order(StringComparer.Ordinal))
            {
                incomingCount[dependent]--;
                if (incomingCount[dependent] == 0)
                {
                    available.Add(byIdentity[dependent]);
                }
            }
        }

        if (ordered.Count != registrations.Count)
        {
            var cyclicIdentities = incomingCount
                .Where(static pair => pair.Value > 0)
                .Select(static pair => pair.Key)
                .Order(StringComparer.Ordinal);
            diagnostics.Add(ModularityDiagnostics.Error(
                ModularityDiagnosticIds.OrderingCycle,
                string.Concat(
                    "Registration ordering contains a cycle among: ",
                    string.Join(", ", cyclicIdentities),
                    "."),
                path));
            return [];
        }

        return ordered.MoveToImmutable();
    }

    private static bool ValidateDescriptor(
        ModularityRegistrationDescriptor? descriptor,
        IProgramKitSemanticValidator<ArtifactReference> artifactReferenceValidator,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (descriptor is null)
        {
            diagnostics.Add(ModularityDiagnostics.Error(
                ModularityDiagnosticIds.InvalidRegistrationDescriptor,
                "A registration descriptor is required.",
                string.Concat(path, "/descriptor")));
            return false;
        }

        var valid = true;
        if (descriptor.Registration is null ||
            !artifactReferenceValidator.Validate(descriptor.Registration).IsValid)
        {
            diagnostics.Add(ModularityDiagnostics.Error(
                ModularityDiagnosticIds.InvalidRegistrationDescriptor,
                "An exact registration identity, version, and digest is required.",
                string.Concat(path, "/descriptor/registration")));
            valid = false;
        }

        if (!ProgramKitIdentifier.Validate(descriptor.OwnerId.Value).IsValid)
        {
            diagnostics.Add(ModularityDiagnostics.Error(
                ModularityDiagnosticIds.InvalidRegistrationDescriptor,
                "A valid registration owner identity is required.",
                string.Concat(path, "/descriptor/ownerId")));
            valid = false;
        }

        if (descriptor.Order is null)
        {
            diagnostics.Add(ModularityDiagnostics.Error(
                ModularityDiagnosticIds.InvalidOrderingDescriptor,
                "An ordering descriptor is required.",
                string.Concat(path, "/descriptor/order")));
            return false;
        }

        valid &= ValidateOrderIdentities(
            descriptor.Order.Before,
            descriptor.Registration?.Identity,
            string.Concat(path, "/descriptor/order/before"),
            diagnostics);
        valid &= ValidateOrderIdentities(
            descriptor.Order.After,
            descriptor.Registration?.Identity,
            string.Concat(path, "/descriptor/order/after"),
            diagnostics);
        if (!descriptor.Order.Before.IsDefault &&
            !descriptor.Order.After.IsDefault)
        {
            var before = descriptor.Order.Before
                .Select(static identity => identity.Value)
                .ToHashSet(StringComparer.Ordinal);
            if (descriptor.Order.After.Any(identity => before.Contains(identity.Value)))
            {
                diagnostics.Add(ModularityDiagnostics.Error(
                    ModularityDiagnosticIds.InvalidOrderingDescriptor,
                    "The same registration cannot appear in both before and after constraints.",
                    string.Concat(path, "/descriptor/order")));
                valid = false;
            }
        }

        return valid;
    }

    private static bool ValidateOrderIdentities(
        ImmutableArray<ProgramKitIdentifier> identities,
        ProgramKitIdentifier? registrationIdentity,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (identities.IsDefault)
        {
            diagnostics.Add(ModularityDiagnostics.Error(
                ModularityDiagnosticIds.InvalidOrderingDescriptor,
                "Ordering identities must be initialized.",
                path));
            return false;
        }

        var valid = true;
        var seen = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < identities.Length; index++)
        {
            var identity = identities[index];
            if (!ProgramKitIdentifier.Validate(identity.Value).IsValid)
            {
                diagnostics.Add(ModularityDiagnostics.Error(
                    ModularityDiagnosticIds.InvalidOrderingDescriptor,
                    "A valid ordering identity is required.",
                    string.Concat(path, "/", index)));
                valid = false;
            }
            else if (!seen.Add(identity.Value))
            {
                diagnostics.Add(ModularityDiagnostics.Error(
                    ModularityDiagnosticIds.InvalidOrderingDescriptor,
                    "Ordering identities must be unique.",
                    string.Concat(path, "/", index)));
                valid = false;
            }

            if (registrationIdentity is { } self &&
                string.Equals(identity.Value, self.Value, StringComparison.Ordinal))
            {
                diagnostics.Add(ModularityDiagnostics.Error(
                    ModularityDiagnosticIds.InvalidOrderingDescriptor,
                    "A registration cannot order itself.",
                    string.Concat(path, "/", index)));
                valid = false;
            }
        }

        return valid;
    }

    private static bool AddEdge<TRegistration>(
        string earlier,
        string later,
        Dictionary<string, TRegistration> byIdentity,
        Dictionary<string, HashSet<string>> outgoing,
        Dictionary<string, int> incomingCount,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!byIdentity.ContainsKey(earlier) || !byIdentity.ContainsKey(later))
        {
            var missing = !byIdentity.ContainsKey(earlier) ? earlier : later;
            diagnostics.Add(ModularityDiagnostics.Error(
                ModularityDiagnosticIds.MissingOrderingDependency,
                string.Concat(
                    "Ordering dependency '",
                    missing,
                    "' is not registered in the applicable registry."),
                path));
            return false;
        }

        if (outgoing[earlier].Add(later))
        {
            incomingCount[later]++;
        }

        return true;
    }

    private static int Compare(
        ModularityRegistrationDescriptor left,
        ModularityRegistrationDescriptor right)
    {
        var priority = left.Order.Priority.CompareTo(right.Order.Priority);
        if (priority != 0)
        {
            return priority;
        }

        var identity = string.CompareOrdinal(
            left.Registration.Identity.Value,
            right.Registration.Identity.Value);
        if (identity != 0)
        {
            return identity;
        }

        var version = string.CompareOrdinal(
            left.Registration.Version.Value,
            right.Registration.Version.Value);
        return version != 0
            ? version
            : string.CompareOrdinal(
                left.Registration.Digest.Value,
                right.Registration.Digest.Value);
    }
}
