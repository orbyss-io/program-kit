using CShells.Features;
using Microsoft.Extensions.DependencyInjection;

namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class JTestRunRequest
{
    public JTestRunRequest(string suite, int maximumParallelism)
    {
        Suite = suite;
        MaximumParallelism = maximumParallelism;
    }

    public string Suite { get; }

    public int MaximumParallelism { get; }
}

public sealed class JTestValidateRequest
{
    public JTestValidateRequest(string path)
    {
        Path = path;
    }

    public string Path { get; }
}

public sealed class JTestDescribeRequest
{
    public JTestDescribeRequest(string suite)
    {
        Suite = suite;
    }

    public string Suite { get; }
}

public interface IJTestRunHandler
{
    ValueTask<int> HandleAsync(
        JTestRunRequest request,
        CancellationToken cancellationToken);
}

public interface IJTestValidateHandler
{
    ValueTask<int> HandleAsync(
        JTestValidateRequest request,
        CancellationToken cancellationToken);
}

public interface IJTestDescribeHandler
{
    ValueTask<int> HandleAsync(
        JTestDescribeRequest request,
        CancellationToken cancellationToken);
}

public sealed class JTestRunHandler : IJTestRunHandler
{
    public ValueTask<int> HandleAsync(
        JTestRunRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        return ValueTask.FromResult(request.MaximumParallelism + 10);
    }
}

public sealed class JTestValidateHandler : IJTestValidateHandler
{
    public ValueTask<int> HandleAsync(
        JTestValidateRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        return ValueTask.FromResult(23);
    }
}

public sealed class JTestDescribeHandler : IJTestDescribeHandler
{
    public ValueTask<int> HandleAsync(
        JTestDescribeRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        return ValueTask.FromResult(29);
    }
}

public sealed class MetadataFixtureValidationResult
{
    public MetadataFixtureValidationResult(
        bool isValid,
        IReadOnlyList<string> messages)
    {
        ArgumentNullException.ThrowIfNull(messages);
        IsValid = isValid;
        Messages = messages;
    }

    public bool IsValid { get; }

    public IReadOnlyList<string> Messages { get; }
}

public interface IJTestRunValidator
{
    ValueTask<MetadataFixtureValidationResult> ValidateAsync(
        JTestRunRequest request,
        CancellationToken cancellationToken);
}

public sealed class JTestRunValidator : IJTestRunValidator
{
    public ValueTask<MetadataFixtureValidationResult> ValidateAsync(
        JTestRunRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        var valid = request.Suite != "missing";
        MetadataFixtureValidationResult result = new(
            valid,
            valid
                ? []
                : ["suite 'missing' is unavailable"]);
        return ValueTask.FromResult(result);
    }
}

public sealed class JTestFixtureFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
        services.AddScoped<IJTestRunHandler, JTestRunHandler>();
        services.AddScoped<IJTestValidateHandler, JTestValidateHandler>();
        services.AddScoped<IJTestDescribeHandler, JTestDescribeHandler>();
        services.AddScoped<IJTestRunValidator, JTestRunValidator>();
    }
}
