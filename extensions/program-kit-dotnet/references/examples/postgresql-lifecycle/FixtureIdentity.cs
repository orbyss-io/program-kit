using System.Text.RegularExpressions;
using Npgsql;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Restricts this example to its uniquely labelled local disposable fixture.</summary>
public sealed record FixtureIdentity(string Id)
{
    /// <summary>Gets the isolated schema identifier.</summary>
    public string Schema => "pk_fixture_" + Id;
    /// <summary>Gets the deployment-only login.</summary>
    public string DeploymentRole => "pk_deploy_" + Id;
    /// <summary>Gets the runtime-only login.</summary>
    public string RuntimeRole => "pk_runtime_" + Id;

    /// <summary>Opens a connection only to the matching local fixture authority.</summary>
    public async Task<NpgsqlConnection> OpenAsync(bool deployment)
    {
        if (!Regex.IsMatch(Id, "\\A[0-9a-f]{32}\\z")) throw new ArgumentException("Invalid fixture identity.");
        var key = deployment ? "PK_FIXTURE_DEPLOYMENT" : "PK_FIXTURE_RUNTIME";
        var builder = new NpgsqlConnectionStringBuilder(Environment.GetEnvironmentVariable(key)
            ?? throw new InvalidOperationException("Missing scoped fixture connection."));
        if (builder.Host != "127.0.0.1" || builder.Database != "pk_fixture_" + Id
            || builder.Username != (deployment ? DeploymentRole : RuntimeRole))
            throw new InvalidOperationException("Foreign fixture target refused.");
        builder.Timeout = 5;
        builder.CommandTimeout = 15;
        builder.IncludeErrorDetail = false;
        var connection = new NpgsqlConnection(builder.ConnectionString);
        try
        {
            await connection.OpenAsync();
            await using var command = new NpgsqlCommand("SELECT shobj_description(oid,'pg_database') FROM pg_database WHERE datname=current_database()", connection);
            if (!Equals(await command.ExecuteScalarAsync(), "program-kit-disposable:" + Id))
                throw new InvalidOperationException("Missing original fixture database marker.");
            return connection;
        }
        catch { await connection.DisposeAsync(); throw; }
    }
}
