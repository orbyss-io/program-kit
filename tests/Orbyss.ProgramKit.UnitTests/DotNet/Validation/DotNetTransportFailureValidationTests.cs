using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.Operations.Contracts.Validation;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Validation;

[TestClass]
public sealed class DotNetTransportFailureValidationTests
{
    [TestMethod]
    public void ExplicitReviewedTransportFailureProfileIsValid()
    {
        var shell = WithTransportFailures(DotNetTestContractFactory.TransportFailures());

        var result = Validator().Validate(shell);

        Assert.IsTrue(result.IsValid, string.Join(Environment.NewLine, result.Diagnostics));
    }

    [TestMethod]
    public void GenericAndCancellationExceptionMappingsFailClosed()
    {
        var configuration = DotNetTestContractFactory.TransportFailures();
        configuration = configuration with
        {
            ExceptionMappings =
            [
                configuration.ExceptionMappings[0] with
                {
                    ExceptionType = "System.OperationCanceledException",
                },
            ],
        };

        var result = Validator().Validate(WithTransportFailures(configuration));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(
            static diagnostic =>
                diagnostic.Id == DotNetDiagnosticIds.InvalidExceptionFailureMapping));
    }

    [TestMethod]
    public void RawAspNetCoreExceptionRecordingConflictsWithSanitizedHandling()
    {
        var shell = WithTransportFailures(DotNetTestContractFactory.TransportFailures());
        var host = shell.Hosts.Single(static item =>
            item.Kind == DotNetHostKind.Api);
        var telemetry = host.Telemetry!;
        var instrumentations = telemetry.Instrumentations
            .Select(static instrumentation =>
                instrumentation.Kind ==
                    Orbyss.ProgramKit.DotNet.Observability.DotNetTelemetryInstrumentationKind.AspNetCore
                    ? instrumentation with { RecordExceptions = true }
                    : instrumentation)
            .ToImmutableArray();
        var invalid = shell with
        {
            Hosts = shell.Hosts.Select(item =>
                    item.Identity == host.Identity
                        ? item with
                        {
                            Telemetry = telemetry with
                            {
                                Instrumentations = instrumentations,
                            },
                        }
                        : item)
                .ToImmutableArray(),
        };

        var result = Validator().Validate(invalid);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(
            static item => item.Id ==
                DotNetDiagnosticIds.UnsafeTransportFailureDisclosure));
    }

    private static DotNetShellDocument WithTransportFailures(
        Orbyss.ProgramKit.DotNet.Operations.TransportFailures.DotNetTransportFailureConfiguration configuration)
    {
        var shell = DotNetTestContractFactory.Shell();
        return shell with
        {
            Hosts = shell.Hosts.Select(host =>
                host.Kind == DotNetHostKind.Api
                    ? host with { TransportFailures = configuration }
                    : host).ToImmutableArray(),
        };
    }

    private static DotNetShellValidator Validator() =>
        new(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            DotNetTestContractFactory.ProviderCatalog());
}
