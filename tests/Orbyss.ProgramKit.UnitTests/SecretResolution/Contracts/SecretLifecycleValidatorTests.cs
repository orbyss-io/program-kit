using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.SecretResolution.Contracts.Diagnostics;
using Orbyss.ProgramKit.SecretResolution.Contracts.Validation;
using Orbyss.ProgramKit.UnitTests.TestSupport.SecretResolution;

namespace Orbyss.ProgramKit.UnitTests.SecretResolution.Contracts;

[TestClass]
public sealed class SecretLifecycleValidatorTests
{
    [TestMethod]
    public void DenialOutageExpiryRevocationAndFailureAreMaterialFreeValidStates()
    {
        var expiry = new DateTimeOffset(2026, 7, 25, 9, 59, 0, TimeSpan.Zero);
        var cases = new[]
        {
            SecretResolutionTestContractFactory.Signal(
                SecretChangeKind.Denied,
                SecretResolutionStatus.Denied),
            SecretResolutionTestContractFactory.Signal(
                SecretChangeKind.ProviderUnavailable,
                SecretResolutionStatus.ProviderUnavailable),
            SecretResolutionTestContractFactory.Signal(
                SecretChangeKind.Expired,
                SecretResolutionStatus.Expired,
                expiresAt: expiry),
            SecretResolutionTestContractFactory.Signal(
                SecretChangeKind.Revoked,
                SecretResolutionStatus.Revoked),
            SecretResolutionTestContractFactory.Signal(
                SecretChangeKind.Failed,
                SecretResolutionStatus.Failed),
        };
        SecretChangeSignalValidator validator = new();

        foreach (var signal in cases)
        {
            Assert.IsTrue(
                validator.Validate(signal).IsValid,
                signal.Kind.ToString());
        }
    }

    [TestMethod]
    public void LifecycleRejectsGenerationRollbackAndInconsistentStatus()
    {
        SecretChangeSignalValidator validator = new();
        var rollback = SecretResolutionTestContractFactory.Signal(
            previousGeneration: 3,
            generation: 2);
        var inconsistent = SecretResolutionTestContractFactory.Signal(
            SecretChangeKind.Revoked,
            SecretResolutionStatus.Available);

        Assert.IsTrue(validator.Validate(rollback).Diagnostics.Any(
            static diagnostic =>
                diagnostic.Id == SecretResolutionDiagnosticIds.InvalidLifecycle));
        Assert.IsTrue(validator.Validate(inconsistent).Diagnostics.Any(
            static diagnostic =>
                diagnostic.Id == SecretResolutionDiagnosticIds.InvalidLifecycle));
    }

    [TestMethod]
    public void ChangeSignalSurfaceContainsMetadataOnly()
    {
        var properties = typeof(SecretChangeSignal)
            .GetProperties()
            .Select(static property => property.PropertyType)
            .ToArray();

        Assert.DoesNotContain(typeof(string), properties);
        Assert.DoesNotContain(typeof(byte[]), properties);
        Assert.DoesNotContain(typeof(object), properties);
        Assert.IsEmpty(
            typeof(SecretLifecycleMetadata).GetProperties().Where(
                static property =>
                property.PropertyType == typeof(string) ||
                property.PropertyType == typeof(byte[]) ||
                property.PropertyType == typeof(object)).ToArray());
    }
}
