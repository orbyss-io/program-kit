using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.CommandLine.Operations.Schemas;

/// <summary>
/// Resolves transitive dependencies only from the verified finite catalog.
/// No assembly, directory, or network discovery is performed.
/// </summary>
public sealed class SchemaDependencyClosureProvider :
    ISchemaDependencyClosureProvider
{
    private readonly ISchemaCatalog catalog;
    private readonly ISchemaDependencyClosureModuleFactory moduleFactory;

    /// <summary>Initializes finite closure traversal and module materialization.</summary>
    public SchemaDependencyClosureProvider(
        ISchemaCatalog catalog,
        ISchemaDependencyClosureModuleFactory moduleFactory)
    {
        this.catalog = catalog ?? throw new ArgumentNullException(nameof(catalog));
        this.moduleFactory = moduleFactory ??
            throw new ArgumentNullException(nameof(moduleFactory));
    }

    /// <inheritdoc />
    public IProgramKitSchemaModule Create(ArtifactReference selectedRevision)
    {
        ArgumentNullException.ThrowIfNull(selectedRevision);
        var selectedId = string.Concat(
            selectedRevision.Identity.Value,
            "@",
            selectedRevision.Version.Value);
        _ = catalog.Resolve(selectedId);
        HashSet<string> visited = new(StringComparer.Ordinal);
        HashSet<string> active = new(StringComparer.Ordinal);
        Visit(selectedId);
        var closure = visited
            .Select(catalog.Resolve)
            .OrderBy(static entry => entry.CanonicalUri, StringComparer.Ordinal)
            .ToImmutableArray();
        return moduleFactory.Create(selectedRevision, closure);

        void Visit(string exactId)
        {
            if (visited.Contains(exactId))
            {
                return;
            }

            if (!active.Add(exactId))
            {
                throw new InvalidDataException(
                    string.Concat(
                        "Schema dependency cycle is malformed at '",
                        exactId,
                        "'."));
            }

            var entry = catalog.Resolve(exactId);
            foreach (var dependency in entry.Dependencies)
            {
                Visit(dependency);
            }

            _ = active.Remove(exactId);
            _ = visited.Add(exactId);
        }
    }
}
