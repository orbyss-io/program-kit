using Orbyss.ProgramKit.SecretResolution.Contracts;
namespace Orbyss.ProgramKit.SecretResolutionConsumerFixture.Hosting;

/// <summary>Consumer-owned fixture reaction supplied to generated mechanics.</summary>
public sealed class FixtureReactionConsumer :
    IFixtureSecretSubscriptionReactionConsumer
{
    private readonly Func<
        SecretReactionRequest,
        CancellationToken,
        ValueTask<SecretReactionResult>> reaction;

    /// <summary>Initializes the fixture with explicit consumer behavior.</summary>
    public FixtureReactionConsumer(
        Func<
            SecretReactionRequest,
            CancellationToken,
            ValueTask<SecretReactionResult>> reaction)
    {
        ArgumentNullException.ThrowIfNull(reaction);
        this.reaction = reaction;
    }

    /// <inheritdoc />
    public ValueTask<SecretReactionResult> ApplyAsync(
        SecretReactionRequest request,
        CancellationToken cancellationToken) =>
        reaction(request, cancellationToken);
}
