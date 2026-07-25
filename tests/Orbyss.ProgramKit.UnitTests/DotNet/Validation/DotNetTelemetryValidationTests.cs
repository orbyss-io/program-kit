using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Observability;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.Operations.Contracts.Validation;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Validation;

[TestClass]
public sealed class DotNetTelemetryValidationTests
{
    [TestMethod]
    public void ExactReviewedTelemetryProfileIsValid()
    {
        var result = Validator().Validate(DotNetTestContractFactory.Shell());

        Assert.IsTrue(
            result.IsValid,
            string.Join(Environment.NewLine, result.Diagnostics));
    }

    [TestMethod]
    public void SensitiveHttpAndProviderGraphReloadFailClosed()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        var unsafeTelemetry = host.Telemetry! with
        {
            ProviderGraphReloadable = true,
            HttpDiagnostics = host.Telemetry!.HttpDiagnostics with
            {
                IncludeRequestBody = true,
                RequestHeaders = ["Authorization"],
            },
        };
        var invalid = shell with
        {
            Hosts = shell.Hosts.SetItem(0, host with
            {
                Telemetry = unsafeTelemetry,
            }),
        };

        var result = Validator().Validate(invalid);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(
            static item => item.Id == DotNetDiagnosticIds.UnsafeTelemetryData));
        Assert.IsTrue(result.Diagnostics.Any(
            static item => item.Id == DotNetDiagnosticIds.InvalidTelemetryConfiguration));
    }

    [TestMethod]
    public void DisabledHttpDiagnosticsWithSelectedFieldsFailClosed()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        var invalid = shell with
        {
            Hosts = shell.Hosts.SetItem(0, host with
            {
                Telemetry = host.Telemetry! with
                {
                    HttpDiagnostics = host.Telemetry.HttpDiagnostics with
                    {
                        Enabled = false,
                    },
                },
            }),
        };

        var result = Validator().Validate(invalid);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(
            static item => item.Id == DotNetDiagnosticIds.UnsafeTelemetryData));
    }

    [TestMethod]
    public void CustomHttpSpanAndPackageDriftFailClosed()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        var activity = host.Telemetry!.Activities[0] with
        {
            Kind = DotNetActivityKind.Server,
        };
        var package = host.Telemetry.Packages[0] with
        {
            Version = new SemanticVersion("1.16.0"),
        };
        var invalid = shell with
        {
            Hosts = shell.Hosts.SetItem(0, host with
            {
                Telemetry = host.Telemetry with
                {
                    Activities = [activity],
                    Packages = host.Telemetry.Packages.SetItem(0, package),
                },
            }),
        };

        var result = Validator().Validate(invalid);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(
            static item => item.Id == DotNetDiagnosticIds.DuplicateTelemetryInstrumentation));
        Assert.IsTrue(result.Diagnostics.Any(
            static item => item.Id == DotNetDiagnosticIds.TelemetryPackageMismatch));
    }

    [TestMethod]
    public void UnboundedAttributeAndUnstructuredScopeFailClosed()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts[0];
        var metric = host.Telemetry!.Metrics[0] with
        {
            Attributes =
            [
                new DotNetTelemetryAttributeDefinition(
                    "operation.outcome",
                    10,
                    []),
            ],
        };
        var loggerEvent = host.Telemetry.LoggerEvents[0] with
        {
            MessageTemplate = "Operation started.",
        };
        var invalid = shell with
        {
            Hosts = shell.Hosts.SetItem(0, host with
            {
                Telemetry = host.Telemetry with
                {
                    LoggerEvents = [loggerEvent],
                    Metrics = [metric],
                },
            }),
        };

        var result = Validator().Validate(invalid);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(
            static item => item.Id == DotNetDiagnosticIds.UnsafeTelemetryData));
    }

    private static DotNetShellValidator Validator() =>
        new(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            DotNetTestContractFactory.ProviderCatalog());
}
