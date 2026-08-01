using System;
using System.Collections.Generic;
using System.Linq;

namespace Orbyss.ProgramKit.Providers.DotNet.Composition.HttpEndpoints;

public sealed record EndpointContribution(
    string Identity,
    string Method,
    string Route,
    string FeatureClass,
    int? SemanticOrder);

public static class EndpointAssembler
{
    public static IReadOnlyList<EndpointContribution> Resolve(IEnumerable<EndpointContribution> contributions)
    {
        EndpointContribution[] items = contributions.ToArray();
        if (items.Length == 0)
        {
            throw new InvalidOperationException("At least one endpoint contribution is required.");
        }

        IGrouping<string, EndpointContribution>? duplicate = items
            .GroupBy(static item => $"{item.Method.ToUpperInvariant()} {NormalizeRoute(item.Route)}", StringComparer.Ordinal)
            .FirstOrDefault(static group => group.Count() > 1);
        if (duplicate is not null)
        {
            throw new InvalidOperationException($"Duplicate route identity: {duplicate.Key}");
        }

        bool hasSemanticOrder = items.Any(static item => item.SemanticOrder is not null);
        if (hasSemanticOrder && items.Any(static item => item.SemanticOrder is null))
        {
            throw new InvalidOperationException("Meaningful endpoint order is ambiguous.");
        }

        return hasSemanticOrder
            ? items.OrderBy(static item => item.SemanticOrder).ThenBy(static item => item.Identity, StringComparer.Ordinal).ToArray()
            : items.OrderBy(static item => item.Identity, StringComparer.Ordinal).ToArray();
    }

    public static string NormalizeRoute(string route)
    {
        string normalized = route.Trim();
        if (!normalized.StartsWith('/'))
        {
            normalized = $"/{normalized}";
        }

        if (normalized.Length > 1)
        {
            normalized = normalized.TrimEnd('/');
        }

        return normalized;
    }
}
