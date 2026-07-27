using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.SecretResolution.Contracts.Diagnostics;
using Orbyss.ProgramKit.SecretResolution.Contracts.Validation;
using Orbyss.ProgramKit.UnitTests.TestSupport.SecretResolution;

namespace Orbyss.ProgramKit.UnitTests.SecretResolution.Contracts;

[TestClass]
public sealed class SecretResolutionContractValidatorTests
{
    [TestMethod]
    public void FiniteResultKindsHaveExplicitCompatibleReactions()
    {
        SecretResolutionContractValidator validator = new();
        var cases = new[]
        {
            (SecretResultKind.ConfigurationText, SecretConsumerReaction.HotReplacement),
            (SecretResultKind.ConfigurationBytes, SecretConsumerReaction.HotReplacement),
            (SecretResultKind.Certificate, SecretConsumerReaction.ClientRecreation),
            (SecretResultKind.MountedFileHandle, SecretConsumerReaction.ResourceRecycle),
            (SecretResultKind.CredentialHandle, SecretConsumerReaction.Reconnect),
            (SecretResultKind.AssertionService, SecretConsumerReaction.HotReplacement),
            (SecretResultKind.WorkloadIdentityCapability, SecretConsumerReaction.ClientRecreation),
        };

        foreach (var (kind, reaction) in cases)
        {
            var shape = kind is SecretResultKind.ConfigurationText or
                SecretResultKind.ConfigurationBytes
                ? SecretConsumptionShape.Configuration
                : SecretConsumptionShape.NativeCapability;

            Assert.IsTrue(
                validator.Validate(
                    SecretResolutionTestContractFactory.Contract(
                        kind,
                        reaction,
                        shape)).IsValid,
                string.Concat(kind, " -> ", reaction));
        }
    }

    [TestMethod]
    public void IncompatibleResultReactionMatrixFailsClosed()
    {
        SecretResolutionContractValidator validator = new();
        var cases = new[]
        {
            (SecretResultKind.ConfigurationText, SecretConsumerReaction.ClientRecreation),
            (SecretResultKind.MountedFileHandle, SecretConsumerReaction.HotReplacement),
            (SecretResultKind.WorkloadIdentityCapability, SecretConsumerReaction.HotReplacement),
        };

        foreach (var (kind, reaction) in cases)
        {
            var result = validator.Validate(
                SecretResolutionTestContractFactory.Contract(
                    kind,
                    reaction,
                    SecretConsumptionShape.NativeCapability));

            Assert.IsFalse(result.IsValid, string.Concat(kind, " -> ", reaction));
            Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
                diagnostic.Id == SecretResolutionDiagnosticIds.IncompatibleReaction));
        }
    }

    [TestMethod]
    public void ConfigurationIsOnlyATextOrBytesSpecialization()
    {
        SecretResolutionContractValidator validator = new();
        var result = validator.Validate(
            SecretResolutionTestContractFactory.Contract(
                SecretResultKind.Certificate,
                SecretConsumerReaction.HotReplacement,
                SecretConsumptionShape.Configuration));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id ==
            SecretResolutionDiagnosticIds.InvalidConfigurationProjection));
    }

    [TestMethod]
    public void RequiredRotationNeedsProviderSupportAndConsumerReaction()
    {
        SecretResolutionContractValidator validator = new();
        var unsupportedProvider = validator.Validate(
            SecretResolutionTestContractFactory.Contract(
                rotationCapability: SecretRotationCapability.Unsupported));
        var unsupportedConsumer = validator.Validate(
            SecretResolutionTestContractFactory.Contract(
                reaction: SecretConsumerReaction.Unsupported));

        Assert.IsTrue(unsupportedProvider.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == SecretResolutionDiagnosticIds.IncompatibleReaction));
        Assert.IsTrue(unsupportedConsumer.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == SecretResolutionDiagnosticIds.IncompatibleReaction));
    }

    [TestMethod]
    public void LocatorAndReferenceMustRemainExplicitlyClassified()
    {
        SecretResolutionContractValidator validator = new();
        var contract = SecretResolutionTestContractFactory.Contract();
        var unclassified = contract with
        {
            Reference = contract.Reference with
            {
                LocatorClassification = SecretReferenceClassification.Unspecified,
            },
        };

        var result = validator.Validate(unclassified);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == SecretResolutionDiagnosticIds.UnclassifiedReference));
    }

    [TestMethod]
    public void ReferenceMustSelectExactResolverRevision()
    {
        SecretResolutionContractValidator validator = new();
        var contract = SecretResolutionTestContractFactory.Contract();
        var mismatched = contract with
        {
            Resolver = contract.Resolver with
            {
                CapabilityRevision =
                    SecretResolutionTestContractFactory.Reference(
                        "pkid:capability:program-kit:different-resolver"),
            },
        };

        var result = validator.Validate(mismatched);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == SecretResolutionDiagnosticIds.InvalidReference));
    }
}
