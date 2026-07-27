using System.Collections.Concurrent;
using System.Net;
using System.Net.Sockets;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Keycloak;

internal sealed class KeycloakLoopbackTransportBridge : IAsyncDisposable
{
    private readonly CancellationTokenSource cancellation = new();
    private readonly ConcurrentDictionary<long, Task> connections = new();
    private readonly TcpListener listener;
    private readonly string targetHost;
    private readonly int targetPort;
    private readonly Task acceptLoop;
    private long connectionIdentity;

    private KeycloakLoopbackTransportBridge(
        TcpListener listener,
        string targetHost,
        int targetPort)
    {
        this.listener = listener;
        this.targetHost = targetHost;
        this.targetPort = targetPort;
        acceptLoop = AcceptAsync();
    }

    internal static KeycloakLoopbackTransportBridge Start(
        string targetHost,
        int port)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(targetHost);
        ArgumentOutOfRangeException.ThrowIfLessThan(port, 1);
        ArgumentOutOfRangeException.ThrowIfGreaterThan(port, 65535);
        TcpListener listener = new(IPAddress.Loopback, port);
        listener.Start(16);
        return new KeycloakLoopbackTransportBridge(
            listener,
            targetHost,
            port);
    }

    public async ValueTask DisposeAsync()
    {
        await cancellation.CancelAsync();
        listener.Stop();
        try
        {
            await acceptLoop;
        }
        catch (OperationCanceledException)
        {
        }
        catch (SocketException)
        {
        }

        await Task.WhenAll(connections.Values);
        cancellation.Dispose();
    }

    private async Task AcceptAsync()
    {
        while (!cancellation.IsCancellationRequested)
        {
            TcpClient client = await listener.AcceptTcpClientAsync(
                cancellation.Token);
            var identity = Interlocked.Increment(ref connectionIdentity);
            var connection = ForwardAsync(client, cancellation.Token);
            connections.TryAdd(identity, connection);
            _ = ObserveAsync(identity, connection);
        }
    }

    private async Task ObserveAsync(long identity, Task connection)
    {
        try
        {
            await connection;
        }
        finally
        {
            connections.TryRemove(identity, out _);
        }
    }

    private async Task ForwardAsync(
        TcpClient inbound,
        CancellationToken cancellationToken)
    {
        using (inbound)
        using (TcpClient outbound = new())
        {
            try
            {
                await outbound.ConnectAsync(
                    targetHost,
                    targetPort,
                    cancellationToken);
                await using var inboundStream = inbound.GetStream();
                await using var outboundStream = outbound.GetStream();
                using var connectionCancellation =
                    CancellationTokenSource.CreateLinkedTokenSource(
                        cancellationToken);
                var request = inboundStream.CopyToAsync(
                    outboundStream,
                    connectionCancellation.Token);
                var response = outboundStream.CopyToAsync(
                    inboundStream,
                    connectionCancellation.Token);
                await Task.WhenAny(request, response);
                await connectionCancellation.CancelAsync();
                await IgnoreCancellationAsync(request);
                await IgnoreCancellationAsync(response);
            }
            catch (IOException)
            {
            }
            catch (SocketException)
            {
            }
            catch (OperationCanceledException)
                when (cancellationToken.IsCancellationRequested)
            {
            }
        }
    }

    private static async Task IgnoreCancellationAsync(Task operation)
    {
        try
        {
            await operation;
        }
        catch (IOException)
        {
        }
        catch (OperationCanceledException)
        {
        }
    }
}
