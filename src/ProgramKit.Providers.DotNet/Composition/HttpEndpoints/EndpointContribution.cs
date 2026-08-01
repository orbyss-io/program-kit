using System;
using System.Collections.Generic;
using System.Linq;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Providers.DotNet.Diagnostics;

namespace Orbyss.ProgramKit.Providers.DotNet.Composition.HttpEndpoints;

public sealed record EndpointContribution(
    string Identity,
    string Method,
    string Route,
    string FeatureClass,
    int? SemanticOrder,
    string? AssemblerIdentity = "orbyss.program-kit.dotnet:aspnet-core-endpoint-assembler@1.0.0");

public static class EndpointAssembler
{
    public static IReadOnlyList<EndpointContribution> Resolve(IEnumerable<EndpointContribution> contributions)
    {
        EndpointContribution[] items = contributions.ToArray();
        if (items.Length == 0 || items.Any(static item => string.IsNullOrWhiteSpace(item.AssemblerIdentity)))
        {
            throw new ProviderDiagnosticException(
                DiagnosticIds.MissingAssembler,
                PrimaryDisposition.ProvideInput,
                "Every endpoint contribution requires one exact owning assembler.");
        }

        if (items.Select(static item => item.AssemblerIdentity).Distinct(StringComparer.Ordinal).Count() != 1)
        {
            throw new ProviderDiagnosticException(
                DiagnosticIds.MissingAssembler,
                PrimaryDisposition.ProvideInput,
                "Endpoint contributions do not resolve to one exact owning assembler.");
        }

        IGrouping<string, EndpointContribution>? duplicate = items
            .GroupBy(static item => $"{item.Method.ToUpperInvariant()} {NormalizeRoute(item.Route)}", StringComparer.Ordinal)
            .FirstOrDefault(static group => group.Count() > 1);
        if (duplicate is not null)
        {
            throw new ProviderDiagnosticException(
                DiagnosticIds.DuplicateRoute,
                PrimaryDisposition.Revise,
                "Two endpoint contributions resolve to the same route identity.");
        }

        bool hasSemanticOrder = items.Any(static item => item.SemanticOrder is not null);
        if (hasSemanticOrder && items.Any(static item => item.SemanticOrder is null))
        {
            throw new ProviderDiagnosticException(
                DiagnosticIds.AmbiguousOrder,
                PrimaryDisposition.ProvideInput,
                "Meaningful endpoint order remains ambiguous.");
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
