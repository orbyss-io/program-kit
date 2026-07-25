namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>Bounded OpenTelemetry resource identity for one generated host.</summary>
public sealed record DotNetTelemetryResource(
    [property: JsonPropertyName("serviceName")] string ServiceName,
    [property: JsonPropertyName("serviceNamespace")] string ServiceNamespace,
    [property: JsonPropertyName("serviceVersion")] SemanticVersion ServiceVersion,
    [property: JsonPropertyName("deploymentEnvironment")] string DeploymentEnvironment);
