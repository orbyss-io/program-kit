using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Operations.Security;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.Operations.Contracts.Validation;
using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Validation;

[TestClass]
public sealed class DotNetSecurityValidationTests
{
    [TestMethod]
    public void ExactOidcJwtAndOperationPolicyCompositionIsValid()
    {
        var result = Validator().Validate(DotNetTestContractFactory.Shell());

        Assert.IsTrue(
            result.IsValid,
            string.Join(Environment.NewLine, result.Diagnostics));
    }

    [TestMethod]
    public void IdTokenShapedJwtAndMissingOperationCoverageFailClosed()
    {
        var shell = DotNetTestContractFactory.Shell();
        var api = shell.Hosts.Single(static host =>
            host.Kind == DotNetHostKind.Api);
        var security = api.Security!;
        var invalid = security with
        {
            JwtResourceServer = security.JwtResourceServer! with
            {
                AccessTokenProfile = (DotNetJwtAccessTokenProfile)999,
            },
            OperationBindings = [],
        };

        var result = Validator().Validate(ReplaceSecurity(shell, api, invalid));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == DotNetDiagnosticIds.InvalidSecurityConfiguration));
    }

    [TestMethod]
    public void SecretValueShapeCannotReplaceClassifiedReference()
    {
        var shell = DotNetTestContractFactory.Shell();
        var api = shell.Hosts.Single(static host =>
            host.Kind == DotNetHostKind.Api);
        var security = api.Security!;
        var oidc = security.OidcConfidentialInteractive!;
        var authentication = oidc.ClientAuthentication;
        var invalidReference = authentication.Reference with
        {
            Classification = SecretReferenceClassification.Unspecified,
            ExpectedResultKind = SecretResultKind.Certificate,
        };
        var invalid = security with
        {
            OidcConfidentialInteractive = oidc with
            {
                ClientAuthentication = authentication with
                {
                    Reference = invalidReference,
                    ConfigurationKey = null,
                },
            },
        };

        var result = Validator().Validate(ReplaceSecurity(shell, api, invalid));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == DotNetDiagnosticIds.UnsafeSecurityMaterial));
    }

    private static DotNetShellDocument ReplaceSecurity(
        DotNetShellDocument shell,
        DotNetHostDefinition api,
        DotNetSecurityConfiguration security) =>
        shell with
        {
            Hosts = shell.Hosts.Select(host =>
                    host.Identity == api.Identity
                        ? host with { Security = security }
                        : host)
                .ToImmutableArray(),
        };

    private static DotNetShellValidator Validator() =>
        new(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            DotNetTestContractFactory.ProviderCatalog());
}
