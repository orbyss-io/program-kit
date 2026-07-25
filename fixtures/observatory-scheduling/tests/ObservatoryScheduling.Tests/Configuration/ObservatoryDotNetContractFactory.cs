using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Documentation;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;
using Orbyss.ProgramKit.DotNet.Health;
using Orbyss.ProgramKit.DotNet.Operations;
using Orbyss.ProgramKit.DotNet.Packages;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Operations.Contracts;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using ObservatoryScheduling.Core.Configuration;

namespace ObservatoryScheduling.Tests.Configuration;

internal static class ObservatoryDotNetContractFactory
{
    internal static DotNetShellDocument CreateShell()
    {
        var shellIdentity = Id("shell", "observatory-scheduling");
        var schedulingFeature = Feature(
            shellIdentity,
            "first-available",
            "ObservatoryScheduling.Scheduling.FirstAvailable.Features.FirstAvailableFeature",
            "ObservatoryScheduling.Scheduling.FirstAvailable");
        var visibilityFeature = Feature(
            shellIdentity,
            "static-visibility",
            "ObservatoryScheduling.Visibility.Fixed.Features.StaticVisibilityFeature",
            "ObservatoryScheduling.Visibility.Static");
        var constraintFeature = Feature(
            shellIdentity,
            "darkness-window",
            "ObservatoryScheduling.Constraints.DarknessWindow.Features.DarknessWindowFeature",
            "ObservatoryScheduling.Constraints.DarknessWindow");
        var apiFeature = Feature(
            shellIdentity,
            "scheduling-api",
            "ObservatoryScheduling.Scheduling.Api.Features.SchedulingApiFeature",
            "ObservatoryScheduling.Scheduling.Api");
        var features = ImmutableArray.Create(
            schedulingFeature,
            visibilityFeature,
            constraintFeature,
            apiFeature);
        var operation = new DotNetOperationBinding(
            Operation(
                Ref("operation", "schedule-viewing"),
                [Ref("schema", "viewing-request-v2")],
                Ref("schema", "viewing-session-v2"),
                [Ref("schema", "scheduling-diagnostic-v2")]),
            Ref("projection", "schedule-viewing"));
        var healthOperation = new DotNetOperationBinding(
            Operation(
                Ref("operation", "health-readiness"),
                [],
                Ref("schema", "health-response"),
                []),
            Ref("projection", "health-readiness"));
        var taskRequirement = new DotNetTaskRuntimeRequirement(
            Ref("runtime", "tasks-in-process"),
            [Ref("schedule-provider", "cronos-0-13")]);

        return new DotNetShellDocument(
            "pkid:schema:program-kit:dotnet-shell@4.0.0",
            new SemanticVersion("4.0.0"),
            VersionMapInputRevision(),
            VersionSelectionInputRevision(),
            new DotNetShellComposition(
                "cshells",
                new SemanticVersion("0.0.28"),
                [new DotNetShellSelection(
                    shellIdentity,
                    ["first-available", "static-visibility", "darkness-window"])]),
            features,
            new DotNetJsonSerializationSelection(
                [
                    new JsonSerializationProfileRef(
                        Id("profile", "observatory-json-v2"),
                        new SemanticVersion("2.0.0"),
                        Ref("profile", "observatory-json-v2").Digest),
                ],
                [
                    JsonContribution("observatory-window-converter"),
                    JsonContribution("observatory-model-context"),
                ]),
            [
                Host(
                    "observatory-api",
                    DotNetHostKind.Api,
                    shellIdentity,
                    features,
                    [operation, healthOperation],
                    [taskRequirement],
                    CreateApiHealth()),
                Host(
                    "observatory-console",
                    DotNetHostKind.Console,
                    shellIdentity,
                    features.Remove(apiFeature),
                    [operation],
                    [taskRequirement],
                    CreateManagementHealth(43102)),
                Host(
                    "observatory-worker",
                    DotNetHostKind.Worker,
                    shellIdentity,
                    features.Remove(apiFeature),
                    [operation],
                    [taskRequirement],
                    CreateManagementHealth(43103)),
            ],
            Compatibility());
    }

    private static OperationContractDescriptor Operation(
        ArtifactReference revision,
        ImmutableArray<ArtifactReference> requests,
        ArtifactReference result,
        ImmutableArray<ArtifactReference> diagnostics) =>
        new(
            revision,
            requests,
            [
                new OperationResultContract(
                    result,
                    OperationResultDisposition.Terminal),
            ],
            diagnostics,
            [],
            [],
            null,
            null,
            OperationExpectedRevisionPolicy.Unsupported,
            OperationIdempotencyPolicy.Unsupported,
            OperationCancellationPolicy.Cooperative,
            OperationProgressPolicy.Unsupported,
            Compatibility(),
            new OperationDeprecation(false, null));

    internal static OpenApiDocumentProjection CreateApiDocument(
        DotNetShellDocument shell)
    {
        var host = SelectHost(shell, DotNetHostKind.Api);
        var schedule = host.OperationBindings.Single(static binding =>
            binding.OperationContract.OperationRevision.Identity.Value.EndsWith(
                ":schedule-viewing",
                StringComparison.Ordinal));
        var health = host.OperationBindings.Single(static binding =>
            binding.OperationContract.OperationRevision.Identity.Value.EndsWith(
                ":health-readiness",
                StringComparison.Ordinal));
        return new OpenApiDocumentProjection(
            "Observatory Scheduling API",
            new SemanticVersion("2.0.0"),
            [new OpenApiServerProjection(
                "http://127.0.0.1:43101",
                "Generated local fixture host")],
            [
                new OpenApiOperationProjection(
                    "/viewing-sessions",
                    "POST",
                    "scheduleViewing",
                    "Schedules the first valid viewing session.",
                    schedule.OperationContract.OperationRevision,
                    schedule.GetInputSchemaRevisions(),
                    schedule.GetResultSchemaRevisions(),
                    schedule.GetDiagnosticSchemaRevisions(),
                    schedule.GetRelatedOperationRevisions()),
                new OpenApiOperationProjection(
                    "/health/ready",
                    "GET",
                    "getReadiness",
                    "Reports whether the generated host is ready.",
                    health.OperationContract.OperationRevision,
                    health.GetInputSchemaRevisions(),
                    health.GetResultSchemaRevisions(),
                    health.GetDiagnosticSchemaRevisions(),
                    health.GetRelatedOperationRevisions()),
            ],
            Provenance(
                host,
                [
                    schedule.OperationContract.OperationRevision,
                    health.OperationContract.OperationRevision,
                ]));
    }

    internal static OpenConsoleDocument CreateConsoleDocument(
        DotNetShellDocument shell)
    {
        var host = SelectHost(shell, DotNetHostKind.Console);
        var operation = host.OperationBindings[0].OperationContract.OperationRevision;
        var inputSchema = host.OperationBindings[0].GetInputSchemaRevisions()[0];
        var resultSchema = host.OperationBindings[0].GetResultSchemaRevisions()[0];
        var diagnosticSchema =
            host.OperationBindings[0].GetDiagnosticSchemaRevisions()[0];
        return new OpenConsoleDocument(
            "pkid:schema:program-kit:open-console@1.0.0",
            new SemanticVersion("1.0.0"),
            new IntegratorDocumentInfo(
                "observatory-scheduling",
                "Schedules immediate or background viewing work.",
                new SemanticVersion("2.0.0")),
            HostRevision(host),
            new OpenConsoleParsing(
                true,
                "--",
                true,
                true,
                "invariant",
                "bounded-by-occurrence"),
            [
                new OpenConsoleOption(
                    "format",
                    null,
                    [],
                    ConsoleOptionKind.Value,
                    "string",
                    new ConsoleValueArity(1, 1),
                    new ConsoleOccurrence(0, 1),
                    false,
                    "json",
                    inputSchema,
                    "Output:Format",
                    [],
                    [],
                    "Selects the typed output format."),
            ],
            [
                new OpenConsoleCommand(
                    operation,
                    ["schedule"],
                    [["viewing", "schedule"]],
                    "Schedules an observatory viewing session.",
                    [
                        new OpenConsoleArgument(
                            0,
                            "target",
                            "string",
                            new ConsoleValueArity(1, 1),
                            new ConsoleOccurrence(1, 1),
                            true,
                            null,
                            inputSchema,
                            "Target catalog identity."),
                    ],
                    [
                        ValueOption(
                            "earliest",
                            "e",
                            "date-time",
                            inputSchema,
                            true,
                            "Earliest UTC start."),
                        ValueOption(
                            "latest",
                            "l",
                            "date-time",
                            inputSchema,
                            true,
                            "Latest UTC finish."),
                        ValueOption(
                            "duration",
                            "d",
                            "string",
                            inputSchema,
                            true,
                            "Required viewing duration."),
                        new OpenConsoleOption(
                            "background",
                            "b",
                            [],
                            ConsoleOptionKind.Flag,
                            "boolean",
                            new ConsoleValueArity(0, 0),
                            new ConsoleOccurrence(0, 1),
                            false,
                            null,
                            null,
                            null,
                            [],
                            [],
                            "Dispatches the same request as background work."),
                    ],
                    null,
                    new OpenConsoleStreamContract(
                        "stdout",
                        "application/json",
                        resultSchema,
                        true),
                    new OpenConsoleStreamContract(
                        "stderr",
                        "application/json",
                        diagnosticSchema,
                        false),
                    [
                        new OpenConsoleExitCode(0, "Scheduled.", []),
                        new OpenConsoleExitCode(
                            2,
                            "Invalid invocation.",
                            [diagnosticSchema]),
                        new OpenConsoleExitCode(
                            3,
                            "Scheduling failed.",
                            [diagnosticSchema]),
                    ],
                    Ref("policy", "observatory-authority"),
                    [
                        new OpenConsoleExample(
                            [
                                "schedule",
                                "M42",
                                "--earliest=2026-01-01T20:00:00Z",
                                "--latest=2026-01-02T04:00:00Z",
                                "--duration=00:45:00",
                            ],
                            "Schedules an immediate 45-minute observation."),
                    ],
                    null),
            ],
            new OpenConsoleHelp("help", "h", 0),
            new OpenConsoleCompletion("complete", true, true),
            Compatibility(),
            Provenance(host, [operation]));
    }

    internal static OpenWorkerDocument CreateWorkerDocument(
        DotNetShellDocument shell)
    {
        var host = SelectHost(shell, DotNetHostKind.Worker);
        var operation = host.OperationBindings[0].OperationContract.OperationRevision;
        var binding = host.OperationBindings[0];
        var schedulingFeature = shell.Features.Single(static feature =>
            feature.FeatureIdentity.Name == "first-available");
        return new OpenWorkerDocument(
            "pkid:schema:program-kit:open-worker@1.0.0",
            new SemanticVersion("1.0.0"),
            new IntegratorDocumentInfo(
                "observatory-scheduling-worker",
                "Runs accepted viewing tasks and a bounded nightly schedule.",
                new SemanticVersion("2.0.0")),
            HostRevision(host),
            [
                new OpenWorkerEntry(
                    operation,
                    schedulingFeature.FeatureIdentity,
                    schedulingFeature.ActivationIdentity,
                    Ref("task-definition", "schedule-viewing-v2"),
                    "schedule",
                    Ref("schema", "cronos-schedule-descriptor"),
                    binding.GetInputSchemaRevisions(),
                    binding.GetResultSchemaRevisions(),
                    binding.GetDiagnosticSchemaRevisions(),
                    Ref("policy", "observatory-authority"),
                    Ref("policy", "observatory-cancellation"),
                    null,
                    Compatibility()),
            ],
            Compatibility(),
            Provenance(host, [operation]));
    }

    internal static ArtifactReference ShellRevision() =>
        new(
            Id("shell", "observatory-scheduling-v2"),
            new SemanticVersion("2.0.0"),
            new Sha256Digest(
                "sha256:87e700b361625e78730e77f0287cd31d4da8645bd071af50981773553b3b6893"));

    internal static ArtifactReference VersionMapInputRevision() =>
        new(
            Id("version-map", "observatory-v2-input"),
            new SemanticVersion("2.0.0"),
            new Sha256Digest(
                "sha256:d0c3e2caaf4322a861c4f3859435f60eef250286a5dc960ceafbd99b7ed3e40c"));

    internal static ArtifactReference VersionSelectionInputRevision() =>
        new(
            Id("version-selection", "observatory-v2-input"),
            new SemanticVersion("2.0.0"),
            new Sha256Digest(
                "sha256:f9df715f82efdfbbdfc692c1aefeff7b2a1a9c9292b522ea6dc9c34d9dbc2612"));

    internal static ArtifactReference Ref(string kind, string name) =>
        ObservatoryRevisions.Reference(
            string.Concat("pkid:", kind, ":fixture:", name),
            "2.0.0");

    private static DotNetFeatureSelection Feature(
        ProgramKitIdentifier shellIdentity,
        string name,
        string typeName,
        string packageId) =>
        new(
            Id("feature", name),
            Id("activation", name),
            shellIdentity,
            typeName,
            Package(packageId, "0.1.0-fixture.1"));

    private static DotNetHostDefinition Host(
        string name,
        DotNetHostKind kind,
        ProgramKitIdentifier shellIdentity,
        ImmutableArray<DotNetFeatureSelection> features,
        ImmutableArray<DotNetOperationBinding> operations,
        ImmutableArray<DotNetTaskRuntimeRequirement> taskRequirements,
        DotNetHealthConfiguration health) =>
        new(
            Id("host", name),
            new SemanticVersion("2.0.0"),
            kind,
            Ref("profile", "dotnet-10"),
            Ref("generator", string.Concat(name, "-host")),
            [shellIdentity],
            features.Select(static feature => feature.ActivationIdentity)
                .ToImmutableArray(),
            HostPackages(kind),
            operations,
            [],
            [],
            taskRequirements,
            health,
            Compatibility());

    private static ImmutableArray<DotNetPackageReference> HostPackages(
        DotNetHostKind kind)
    {
        var packages = ImmutableArray.CreateBuilder<DotNetPackageReference>();
        packages.Add(Package("CShells", "0.0.28"));
        packages.Add(Package("CShells.AspNetCore", "0.0.28"));
        packages.Add(Package(
            "Orbyss.ProgramKit.Modularity.InProcess",
            "0.1.0-alpha.1"));
        packages.Add(Package(
            "Orbyss.ProgramKit.Tasks.Hosting",
            "0.1.0-alpha.1"));
        packages.Add(Package(
            "Orbyss.ProgramKit.Tasks.InProcess",
            "0.1.0-alpha.1"));
        if (kind == DotNetHostKind.Worker)
        {
            packages.Add(Package(
                "Orbyss.ProgramKit.Tasks.Schedules.Cronos",
                "0.1.0-alpha.1"));
        }

        return packages.ToImmutable();
    }

    private static DotNetHealthConfiguration CreateApiHealth()
    {
        var management = Listener("api-management", 43101);
        return new DotNetHealthConfiguration(
            [
                Endpoint(
                    DotNetHealthEndpointKind.Readiness,
                    "/health/ready",
                    management.Identity,
                    ["ready"],
                    [],
                    true),
                Endpoint(
                    DotNetHealthEndpointKind.Liveness,
                    "/health/live",
                    management.Identity,
                    [],
                    ["ready"],
                    false),
            ],
            [management]);
    }

    private static DotNetHealthConfiguration CreateManagementHealth(int port)
    {
        var listener = Listener(string.Concat("management-", port), port);
        return new DotNetHealthConfiguration(
            [
                Endpoint(
                    DotNetHealthEndpointKind.Readiness,
                    "/health/ready",
                    listener.Identity,
                    ["ready"],
                    [],
                    false),
            ],
            [listener]);
    }

    private static DotNetHealthListener Listener(string name, int port) =>
        new(
            Id("listener", name),
            "http",
            "127.0.0.1",
            port,
            DotNetHealthExposure.Loopback,
            null,
            null,
            null);

    private static DotNetHealthEndpoint Endpoint(
        DotNetHealthEndpointKind kind,
        string path,
        ProgramKitIdentifier listener,
        ImmutableArray<string> include,
        ImmutableArray<string> exclude,
        bool documentAsOwnedOperation) =>
        new(
            kind,
            path,
            listener,
            include,
            exclude,
            new DotNetHealthStatusCodeMap(200, 200, 503),
            Ref("profile", "health-response"),
            "no-store",
            Ref("policy", "health-authority"),
            new DotNetHealthDocumentationSelection(
                documentAsOwnedOperation
                    ? DotNetHealthDocumentationDisposition.OwnedOperation
                    : DotNetHealthDocumentationDisposition.Excluded,
                documentAsOwnedOperation
                    ? Ref("operation", "health-readiness")
                    : null));

    private static OpenConsoleOption ValueOption(
        string longName,
        string shortName,
        string valueType,
        ArtifactReference schema,
        bool required,
        string summary) =>
        new(
            longName,
            shortName,
            [],
            ConsoleOptionKind.Value,
            valueType,
            new ConsoleValueArity(1, 1),
            new ConsoleOccurrence(required ? 1 : 0, 1),
            required,
            null,
            schema,
            null,
            [],
            [],
            summary);

    private static DotNetHostDefinition SelectHost(
        DotNetShellDocument shell,
        DotNetHostKind kind) =>
        shell.Hosts.Single(candidate => candidate.Kind == kind);

    private static ArtifactReference HostRevision(DotNetHostDefinition host) =>
        ObservatoryRevisions.Reference(
            host.Identity.Value,
            host.Version.Value);

    private static IntegratorDocumentProvenance Provenance(
        DotNetHostDefinition host,
        ImmutableArray<ArtifactReference> operations) =>
        new(
            ShellRevision(),
            host.GeneratorProfileRevision,
            operations);

    private static DotNetPackageReference Package(
        string id,
        string version) =>
        new(
            id,
            new SemanticVersion(version),
            ObservatoryRevisions.Reference(
                string.Concat(
                    id.StartsWith(
                        "Orbyss.ProgramKit.",
                        StringComparison.Ordinal)
                        ? "pkid:package:program-kit:"
                        : id.StartsWith(
                            "ObservatoryScheduling.",
                            StringComparison.Ordinal)
                            ? "pkid:package:fixture:"
                            : "pkid:package:external:",
                    id.Replace('.', '-').ToLowerInvariant()),
                version).Digest);

    private static JsonSerializationContributionRef JsonContribution(
        string name)
    {
        var revision = Ref("json-contribution", name);
        return new JsonSerializationContributionRef(
            revision.Identity,
            revision.Version,
            revision.Digest);
    }

    private static ProgramKitIdentifier Id(string kind, string name) =>
        new(string.Concat("pkid:", kind, ":fixture:", name));

    private static ArtifactCompatibility Compatibility() =>
        new(
            Id("policy", "compatibility"),
            [
                new CompatibilityClaim(
                    CompatibilityDimension.WireRead,
                    CompatibilityClassification.CompatibleAdditive,
                    []),
            ],
            new SemanticVersionRange("[1.0.0,3.0.0)"),
            new SemanticVersionRange("[1.0.0,3.0.0)"),
            []);
}
