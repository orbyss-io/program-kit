using Microsoft.Extensions.Logging.Abstractions;
using ProgramKit.Host.Health;
using Xunit;

namespace ProgramKit.Host.Tests;

/// <summary>Verifies redacted operational dependency degradation and recovery.</summary>
public sealed class PostgreSqlReadinessServiceTests
{
    /// <summary>A failed probe degrades readiness and the next successful probe recovers it.</summary>
    [Fact]
    public async Task ProbeOnceAsync_TransitionsFromDegradedToRecovered()
    {
        var state = new PostgreSqlReadinessState();
        var probe = new ScriptedProbe();
        var service = new PostgreSqlReadinessService(
            state,
            probe,
            NullLogger<PostgreSqlReadinessService>.Instance);

        await service.ProbeOnceAsync(CancellationToken.None);
        Assert.False(state.IsReady);
        Assert.Equal("not-ready", state.Status);

        await service.ProbeOnceAsync(CancellationToken.None);
        Assert.True(state.IsReady);
        Assert.Equal("ready", state.Status);
    }
}
