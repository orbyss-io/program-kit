using System;
using System.Collections.Generic;
using System.Linq;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Providers.DotNet.Diagnostics;

namespace Orbyss.ProgramKit.Providers.DotNet.Evaluation;

public static class RuntimeDependencyValidator
{
    public static void EnsureAllowed(IEnumerable<string> libraryIdentities, IEnumerable<string> allowedPackageIds)
    {
        HashSet<string> allowed = new(allowedPackageIds, StringComparer.OrdinalIgnoreCase);
        string[] forbidden = libraryIdentities
            .Select(static identity => identity.Split('/', 2, StringSplitOptions.None)[0])
            .Where(name => !allowed.Contains(name))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(static name => name, StringComparer.Ordinal)
            .ToArray();
        if (forbidden.Length > 0)
        {
            throw new ProviderDiagnosticException(
                DiagnosticIds.ForbiddenRuntimeDependency,
                PrimaryDisposition.Stop,
                "Generated consumer dependency evidence contains an unapproved runtime dependency.");
        }
    }
}
