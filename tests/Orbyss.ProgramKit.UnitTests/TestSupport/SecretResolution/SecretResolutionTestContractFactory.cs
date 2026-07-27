using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.UnitTests.TestSupport.SecretResolution;

internal static class SecretResolutionTestContractFactory
{
    internal static SecretResolutionContract Contract(
        SecretResultKind resultKind = SecretResultKind.ConfigurationText,
        SecretConsumerReaction reaction = SecretConsumerReaction.HotReplacement,
        SecretConsumptionShape shape = SecretConsumptionShape.Configuration,
        bool rotationRequired = true,
        SecretRotationCapability rotationCapability =
            SecretRotationCapability.ChangeSignal,
        SecretResultLifetime lifetime = SecretResultLifetime.Consumer)
    {
        var capability = Reference(
            "pkid:capability:program-kit:test-secret-resolver");
        return new SecretResolutionContract(
            new SecretReferenceDescriptor(
                new ProgramKitIdentifier(
                    "pkid:secret-reference:fixture:service-credential"),
                SecretReferenceClassification.RestrictedMetadata,
                resultKind,
                capability,
                Reference("pkid:locator:fixture:provider-owned-locator"),
                SecretReferenceClassification.SensitiveMetadata),
            new SecretResolverCapabilityDescriptor(
                capability,
                [resultKind],
                [lifetime],
                [SecretReferenceClassification.RestrictedMetadata],
                [SecretReferenceClassification.SensitiveMetadata],
                rotationCapability),
            new SecretConsumptionBinding(
                lifetime,
                shape,
                rotationRequired,
                reaction));
    }

    internal static SecretChangeSignal Signal(
        SecretChangeKind kind = SecretChangeKind.GenerationChanged,
        SecretResolutionStatus status = SecretResolutionStatus.Available,
        long previousGeneration = 1,
        long generation = 2,
        DateTimeOffset? expiresAt = null) =>
        new(
            new ProgramKitIdentifier(
                "pkid:secret-reference:fixture:service-credential"),
            kind,
            previousGeneration,
            new SecretLifecycleMetadata(
                generation,
                status,
                new DateTimeOffset(2026, 7, 25, 10, 0, 0, TimeSpan.Zero),
                expiresAt));

    internal static ArtifactReference Reference(string identity) =>
        new(
            new ProgramKitIdentifier(identity),
            new SemanticVersion("1.0.0"),
            new Sha256Digest(
                "sha256:1111111111111111111111111111111111111111111111111111111111111111"));
}
