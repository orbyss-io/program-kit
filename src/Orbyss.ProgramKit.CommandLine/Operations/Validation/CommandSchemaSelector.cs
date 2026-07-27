using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CommandLine.Operations.Validation;

/// <summary>Exact schema selector over the finite Program Kit module set.</summary>
public sealed class CommandSchemaSelector : ICommandSchemaSelector
{
    private readonly IProgramKitSchemaModule artifacts;
    private readonly IProgramKitSchemaModule architecture;
    private readonly IProgramKitSchemaModule quality;
    private readonly IProgramKitSchemaModule planning;
    private readonly IProgramKitSchemaModule development;
    private readonly IProgramKitSchemaModule serialization;
    private readonly IProgramKitSchemaModule tasksCore;
    private readonly IProgramKitSchemaModule taskSchedules;
    private readonly IProgramKitSchemaModule dotNet;

    /// <summary>Initializes the selector from exact package-owned schema modules.</summary>
    public CommandSchemaSelector(
        IProgramKitSchemaModule artifacts,
        IProgramKitSchemaModule architecture,
        IProgramKitSchemaModule quality,
        IProgramKitSchemaModule planning,
        IProgramKitSchemaModule development,
        IProgramKitSchemaModule serialization,
        IProgramKitSchemaModule tasksCore,
        IProgramKitSchemaModule taskSchedules,
        IProgramKitSchemaModule dotNet)
    {
        this.artifacts = artifacts ?? throw new ArgumentNullException(nameof(artifacts));
        this.architecture = architecture ?? throw new ArgumentNullException(nameof(architecture));
        this.quality = quality ?? throw new ArgumentNullException(nameof(quality));
        this.planning = planning ?? throw new ArgumentNullException(nameof(planning));
        this.development = development ?? throw new ArgumentNullException(nameof(development));
        this.serialization = serialization ?? throw new ArgumentNullException(nameof(serialization));
        this.tasksCore = tasksCore ?? throw new ArgumentNullException(nameof(tasksCore));
        this.taskSchedules = taskSchedules ??
            throw new ArgumentNullException(nameof(taskSchedules));
        this.dotNet = dotNet ?? throw new ArgumentNullException(nameof(dotNet));
    }

    /// <inheritdoc />
    public IProgramKitSchemaModule Resolve(
        ReadOnlyMemory<byte> utf8Json,
        out ArtifactReference revision)
    {
        var schemaIdentity = SchemaIdentityReader.Read(utf8Json.Span);
        var matches = Modules()
            .SelectMany(module => module.Resources.Select(resource => (module, resource)))
            .Where(candidate =>
                string.Equals(
                    candidate.resource.CanonicalUri.AbsoluteUri,
                    schemaIdentity,
                    StringComparison.Ordinal) ||
                string.Equals(
                    string.Concat(
                        candidate.resource.SchemaReference.Identity.Value,
                        "@",
                        candidate.resource.SchemaReference.Version.Value),
                    schemaIdentity,
                    StringComparison.Ordinal))
            .ToArray();
        if (matches.Length != 1)
        {
            throw new InvalidDataException(
                "The declared schema URI must resolve exactly once in the explicit module set.");
        }

        revision = matches[0].resource.SchemaReference;
        return matches[0].module;
    }

    private IEnumerable<IProgramKitSchemaModule> Modules()
    {
        yield return artifacts;
        yield return architecture;
        yield return quality;
        yield return planning;
        yield return development;
        yield return serialization;
        yield return tasksCore;
        yield return taskSchedules;
        yield return dotNet;
    }
}
