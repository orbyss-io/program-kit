using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.SecretResolution.Contracts.Diagnostics;
using Orbyss.ProgramKit.SecretResolution.Contracts.Validation;

namespace Orbyss.ProgramKit.UnitTests.SecretResolution.Contracts;

[TestClass]
public sealed class SecretReactionResultValidatorTests
{
    [TestMethod]
    public void ManualAndUnsupportedReactionsCannotClaimSuccess()
    {
        foreach (var reaction in new[]
                 {
                     SecretConsumerReaction.Manual,
                     SecretConsumerReaction.Unsupported,
                 })
        {
            var result = SecretReactionResultValidator.ValidateResult(
                new SecretReactionResult(
                    new ProgramKitIdentifier(
                        "pkid:secret-reference:fixture:service-credential"),
                    2,
                    reaction,
                    SecretReactionStatus.Succeeded,
                    null));

            Assert.IsFalse(result.IsValid);
            Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
                diagnostic.Id == SecretResolutionDiagnosticIds.FalseSuccess));
        }
    }

    [TestMethod]
    public void FailedAndRejectedReactionsRequireSafeCodeNotMessage()
    {
        var result = SecretReactionResultValidator.ValidateResult(
            new SecretReactionResult(
                new ProgramKitIdentifier(
                    "pkid:secret-reference:fixture:service-credential"),
                2,
                SecretConsumerReaction.Reconnect,
                SecretReactionStatus.Failed,
                null));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == SecretResolutionDiagnosticIds.MissingRequiredValue));
        Assert.IsEmpty(
            typeof(SecretReactionResult).GetProperties().Where(
                static property => property.Name.Contains(
                    "Message",
                    StringComparison.Ordinal)).ToArray());
    }
}
