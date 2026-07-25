namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>Finite OTLP transport selection.</summary>
public enum DotNetOtlpProtocol
{
    /// <summary>OTLP over gRPC.</summary>
    Grpc,
    /// <summary>OTLP protobuf over HTTP.</summary>
    HttpProtobuf,
}
