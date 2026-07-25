using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
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

namespace Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

internal static class DotNetTestContractFactory
{
    internal static DotNetShellDocument Shell()
    {
        var shellIdentity = Id("shell", "main");
        var featureIdentity = Id("feature", "sample");
        var activationIdentity = Id("activation", "sample");
        var operation = Ref("operation", "run", '1');
        var schema = Ref("schema", "run-result", '2');
        var feature = new DotNetFeatureSelection(
            featureIdentity,
            activationIdentity,
            shellIdentity,
            "Fixtures.SampleFeature",
            Package("Fixtures.SampleFeature", "1.0.0", '3'));
        var operationBinding = new DotNetOperationBinding(
            new OperationContractDescriptor(
                operation,
                [schema],
                [
                    new OperationResultContract(
                        schema,
                        OperationResultDisposition.Terminal),
                ],
                [schema],
                [],
                [
                    new RelatedOperationContract(
                        Id("relation", "additional-input"),
                        Ref("operation", "continue", '5'),
                        schema),
                ],
                null,
                null,
                OperationExpectedRevisionPolicy.Unsupported,
                OperationIdempotencyPolicy.Unsupported,
                OperationCancellationPolicy.Cooperative,
                OperationProgressPolicy.Unsupported,
                Compatibility(),
                new OperationDeprecation(false, null)),
            Ref("generator", "operation-projection", '4'));
        var healthListener = new DotNetHealthListener(
            Id("listener", "management"),
            "http",
            "127.0.0.1",
            18081,
            DotNetHealthExposure.Loopback,
            null,
            null,
            null);
        var livenessListener = new DotNetHealthListener(
            Id("listener", "liveness"),
            "http",
            "127.0.0.1",
            18082,
            DotNetHealthExposure.Loopback,
            null,
            null,
            null);
        var healthEndpoint = new DotNetHealthEndpoint(
            DotNetHealthEndpointKind.Readiness,
            "/health/ready",
            healthListener.Identity,
            ["ready"],
            [],
            new DotNetHealthStatusCodeMap(200, 200, 503),
            Ref("profile", "health-response", '6'),
            "no-store",
            Ref("policy", "health-authority", '7'),
            new DotNetHealthDocumentationSelection(
                DotNetHealthDocumentationDisposition.OwnedOperation,
                operation));
        var livenessEndpoint = new DotNetHealthEndpoint(
            DotNetHealthEndpointKind.Liveness,
            "/health/live",
            livenessListener.Identity,
            [],
            ["ready", "startup"],
            new DotNetHealthStatusCodeMap(200, 200, 503),
            Ref("profile", "health-response", '6'),
            "no-store",
            Ref("policy", "health-authority", '7'),
            new DotNetHealthDocumentationSelection(
                DotNetHealthDocumentationDisposition.Excluded,
                null));
        var api = Host(
            "api",
            DotNetHostKind.Api,
            shellIdentity,
            activationIdentity,
            operationBinding,
            [
                Package("CShells", "0.0.28", '8'),
                Package("CShells.AspNetCore", "0.0.28", '9'),
            ],
            new DotNetHealthConfiguration(
                [healthEndpoint, livenessEndpoint],
                [healthListener, livenessListener]));
        var console = Host(
            "console",
            DotNetHostKind.Console,
            shellIdentity,
            activationIdentity,
            operationBinding,
            [
                Package("CShells", "0.0.28", '8'),
                Package("Microsoft.Extensions.Hosting", "10.0.10", 'a'),
            ],
            null);
        var worker = Host(
            "worker",
            DotNetHostKind.Worker,
            shellIdentity,
            activationIdentity,
            operationBinding,
            [
                Package("CShells", "0.0.28", '8'),
                Package("Microsoft.Extensions.Hosting", "10.0.10", 'a'),
            ],
            null);

        return new DotNetShellDocument(
            "pkid:schema:program-kit:dotnet-shell@2.0.0",
            new SemanticVersion("2.0.0"),
            Ref("version-map", "inputs", 'a'),
            Ref("version-selection", "inputs", 'b'),
            new DotNetShellComposition(
                "cshells",
                new SemanticVersion("0.0.28"),
                [new DotNetShellSelection(shellIdentity, ["sample"])]),
            [feature],
            new DotNetJsonSerializationSelection(
                [
                    new JsonSerializationProfileRef(
                        Id("profile", "contracts"),
                        new SemanticVersion("1.0.0"),
                        Digest('c')),
                ],
                []),
            [api, console, worker],
            Compatibility());
    }

    internal static OpenConsoleDocument ConsoleDocument(
        DotNetShellDocument shell)
    {
        var host = shell.Hosts.Single(static item => item.Kind == DotNetHostKind.Console);
        var operation = host.OperationBindings[0].OperationContract.OperationRevision;
        var schema = host.OperationBindings[0].GetResultSchemaRevisions()[0];
        var command = new OpenConsoleCommand(
            operation,
            ["observe", "run"],
            [["execute"], ["run-observation"]],
            "Runs the typed operation.",
            [
                new OpenConsoleArgument(
                    0,
                    "target",
                    "string",
                    new ConsoleValueArity(1, 1),
                    new ConsoleOccurrence(1, 1),
                    true,
                    null,
                    schema,
                    "Target identity."),
            ],
            [
                new OpenConsoleOption(
                    "count",
                    "c",
                    ["--number"],
                    ConsoleOptionKind.Value,
                    "int32",
                    new ConsoleValueArity(1, 1),
                    new ConsoleOccurrence(0, 1),
                    false,
                    "1",
                    schema,
                    "Observe:Count",
                    ["force"],
                    ["confirm"],
                    "Number of runs."),
                new OpenConsoleOption(
                    "force",
                    "f",
                    [],
                    ConsoleOptionKind.Flag,
                    "boolean",
                    new ConsoleValueArity(0, 0),
                    new ConsoleOccurrence(0, 1),
                    false,
                    null,
                    null,
                    null,
                    ["count"],
                    [],
                    "Forces execution."),
                new OpenConsoleOption(
                    "confirm",
                    null,
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
                    "Confirms execution."),
            ],
            null,
            new OpenConsoleStreamContract("stdout", "application/json", schema, true),
            new OpenConsoleStreamContract("stderr", "application/json", schema, false),
            [
                new OpenConsoleExitCode(0, "Succeeded", []),
                new OpenConsoleExitCode(2, "Invalid invocation", [schema]),
            ],
            Ref("policy", "run-authority", 'd'),
            [new OpenConsoleExample(["observe", "run", "target-1", "--count=2"], "Runs twice.")],
            null);
        return new OpenConsoleDocument(
            "pkid:schema:program-kit:open-console@1.0.0",
            new SemanticVersion("1.0.0"),
            new IntegratorDocumentInfo("sample", "Sample console.", new SemanticVersion("1.0.0")),
            Ref("host", "console", 'e'),
            new OpenConsoleParsing(true, "--", true, true, "invariant", "bounded-by-occurrence"),
            [],
            [command],
            new OpenConsoleHelp("help", "h", 0),
            new OpenConsoleCompletion("complete", true, true),
            Compatibility(),
            Provenance(host, operation));
    }

    internal static OpenWorkerDocument WorkerDocument(
        DotNetShellDocument shell)
    {
        var host = shell.Hosts.Single(static item => item.Kind == DotNetHostKind.Worker);
        var operation = host.OperationBindings[0].OperationContract.OperationRevision;
        var feature = shell.Features[0];
        var schema = host.OperationBindings[0].GetResultSchemaRevisions()[0];
        var worker = new OpenWorkerEntry(
            operation,
            feature.FeatureIdentity,
            feature.ActivationIdentity,
            Ref("task-definition", "run", 'f'),
            "schedule",
            schema,
            [schema],
            [schema],
            [schema],
            Ref("policy", "worker-authority", '1'),
            Ref("policy", "worker-cancellation", '2'),
            null,
            Compatibility());
        return new OpenWorkerDocument(
            "pkid:schema:program-kit:open-worker@1.0.0",
            new SemanticVersion("1.0.0"),
            new IntegratorDocumentInfo("sample-worker", "Sample worker.", new SemanticVersion("1.0.0")),
            Ref("host", "worker", '3'),
            [worker],
            Compatibility(),
            Provenance(host, operation));
    }

    internal static OpenApiDocumentProjection ApiDocument(
        DotNetShellDocument shell)
    {
        var host = shell.Hosts.Single(static item => item.Kind == DotNetHostKind.Api);
        var binding = host.OperationBindings[0];
        return new OpenApiDocumentProjection(
            "Sample API",
            new SemanticVersion("1.0.0"),
            [new OpenApiServerProjection("https://localhost:8443", "Local API")],
            [
                new OpenApiOperationProjection(
                    "/runs",
                    "POST",
                    "run",
                    "Runs the operation.",
                    binding.OperationContract.OperationRevision,
                    binding.GetInputSchemaRevisions(),
                    binding.GetResultSchemaRevisions(),
                    binding.GetDiagnosticSchemaRevisions(),
                    binding.GetRelatedOperationRevisions()),
            ],
            Provenance(host, binding.OperationContract.OperationRevision));
    }

    internal static ArtifactReference Ref(
        string kind,
        string name,
        char digest) =>
        new(
            Id(kind, name),
            new SemanticVersion("1.0.0"),
            Digest(digest));

    internal static ProgramKitIdentifier Id(string kind, string name) =>
        new(string.Concat("pkid:", kind, ":test:", name));

    internal static Sha256Digest Digest(char value) =>
        new(string.Concat("sha256:", new string(value, 64)));

    private static DotNetHostDefinition Host(
        string name,
        DotNetHostKind kind,
        ProgramKitIdentifier shellIdentity,
        ProgramKitIdentifier activationIdentity,
        DotNetOperationBinding operation,
        ImmutableArray<DotNetPackageReference> packages,
        DotNetHealthConfiguration? health) =>
        new(
            Id("host", name),
            new SemanticVersion("1.0.0"),
            kind,
            Ref("profile", "dotnet-10", '4'),
            Ref("generator", string.Concat(name, "-host"), '5'),
            [shellIdentity],
            [activationIdentity],
            packages,
            [operation],
            [],
            [],
            health,
            Compatibility());

    private static DotNetPackageReference Package(
        string id,
        string version,
        char digest) =>
        new(id, new SemanticVersion(version), Digest(digest));

    private static IntegratorDocumentProvenance Provenance(
        DotNetHostDefinition host,
        ArtifactReference operation) =>
        new(
            Ref("shell", "reviewed", '6'),
            host.GeneratorProfileRevision,
            [operation]);

    private static ArtifactCompatibility Compatibility() =>
        new(
            Id("policy", "compatibility"),
            [
                new CompatibilityClaim(
                    CompatibilityDimension.WireRead,
                    CompatibilityClassification.Unknown,
                    []),
            ],
            new SemanticVersionRange("[1.0.0]"),
            new SemanticVersionRange("[1.0.0]"),
            []);
}
