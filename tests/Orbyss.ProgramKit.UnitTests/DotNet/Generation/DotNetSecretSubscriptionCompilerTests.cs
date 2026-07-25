using System.Text;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.SecretResolution.Contracts.Validation;
using Orbyss.ProgramKit.UnitTests.TestSupport.SecretResolution;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
public sealed class DotNetSecretSubscriptionCompilerTests
{
    [TestMethod]
    public void CompilerEmitsBoundedDisposableConsumerOwnedReactionQueue()
    {
        DotNetSecretSubscriptionCompiler compiler =
            new(new SecretResolutionContractValidator());
        var definition = Definition(SecretConsumerReaction.Reconnect);

        var outputs = compiler.Compile(definition);
        var subscription = Encoding.UTF8.GetString(outputs[0].Content.ToArray());

        Assert.HasCount(2, outputs);
        Assert.Contains("Channel.CreateBounded<SecretReactionRequest>", subscription);
        Assert.Contains("BoundedChannelFullMode.Wait", subscription);
        Assert.Contains("TryWrite(request)", subscription);
        Assert.Contains("subscription?.Dispose()", subscription);
        Assert.Contains("consumer.ApplyAsync", subscription);
        Assert.Contains("SecretReactionResultValidator.ValidateResult", subscription);
        Assert.Contains("SecretChangeSignalValidator.ValidateSignal", subscription);
        Assert.Contains("SecretReactionStatus.Rejected", subscription);
        Assert.DoesNotContain(
            definition.Contract.Reference.LocatorRevision.Identity.Value,
            subscription);
        Assert.DoesNotContain("Value.ToString", subscription);
    }

    [TestMethod]
    public void EveryAutomaticReactionHasAnExactGeneratedBinding()
    {
        DotNetSecretSubscriptionCompiler compiler =
            new(new SecretResolutionContractValidator());
        var reactions = new[]
        {
            SecretConsumerReaction.HotReplacement,
            SecretConsumerReaction.ClientRecreation,
            SecretConsumerReaction.Reconnect,
            SecretConsumerReaction.ResourceRecycle,
            SecretConsumerReaction.HostRestartRequest,
            SecretConsumerReaction.Manual,
        };

        foreach (var reaction in reactions)
        {
            var outputs = compiler.Compile(Definition(reaction));
            var source = Encoding.UTF8.GetString(outputs[0].Content.ToArray());

            Assert.Contains(
                string.Concat("SecretConsumerReaction.", reaction),
                source);
        }
    }

    [TestMethod]
    public void NonRotatingUnsupportedBindingGeneratesNoRuntimeController()
    {
        DotNetSecretSubscriptionCompiler compiler =
            new(new SecretResolutionContractValidator());
        var definition = Definition(
            SecretConsumerReaction.Unsupported,
            rotationRequired: false);

        Assert.IsEmpty(compiler.Compile(definition));
        Assert.AreEqual(string.Empty, compiler.RenderRegistration(definition));
    }

    [TestMethod]
    public void QueueCapacityIsFiniteAndValidatedBeforeGeneration()
    {
        DotNetSecretSubscriptionCompiler compiler =
            new(new SecretResolutionContractValidator());

        Assert.ThrowsExactly<ArgumentOutOfRangeException>(() =>
            compiler.Compile(Definition(
                SecretConsumerReaction.Reconnect,
                queueCapacity: 0)));
        Assert.ThrowsExactly<ArgumentOutOfRangeException>(() =>
            compiler.Compile(Definition(
                SecretConsumerReaction.Reconnect,
                queueCapacity: 1025)));
    }

    private static DotNetSecretSubscriptionDefinition Definition(
        SecretConsumerReaction reaction,
        bool rotationRequired = true,
        int queueCapacity = 4)
    {
        var resultKind = reaction switch
        {
            SecretConsumerReaction.ResourceRecycle =>
                SecretResultKind.MountedFileHandle,
            SecretConsumerReaction.ClientRecreation or
                SecretConsumerReaction.Reconnect =>
                SecretResultKind.CredentialHandle,
            _ => SecretResultKind.ConfigurationText,
        };
        var shape = resultKind == SecretResultKind.ConfigurationText
            ? SecretConsumptionShape.Configuration
            : SecretConsumptionShape.NativeCapability;
        return new DotNetSecretSubscriptionDefinition(
            SecretResolutionTestContractFactory.Contract(
                resultKind,
                reaction,
                shape,
                rotationRequired),
            "Orbyss.ProgramKit.GeneratedFixture",
            string.Concat(reaction, "SecretSubscription"),
            queueCapacity);
    }
}
