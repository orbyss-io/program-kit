using Npgsql;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Deploys this fixed synthetic schema, with no ownership-transfer or general migration mode.</summary>
public static class FixtureDeployment
{
    /// <summary>Serializes first preparation only; product users remain concurrent.</summary>
    public static async Task<string> PrepareAsync(FixtureIdentity identity, bool cleanup = false)
    {
        await using var connection = await identity.OpenAsync(deployment: true);
        await using var transaction = await connection.BeginTransactionAsync();
        var schema = identity.Schema;
        await ExecuteAsync(connection, $"SELECT pg_advisory_xact_lock(hashtextextended('{schema}',0))");
        await using var existence = new NpgsqlCommand($"SELECT count(*) FROM pg_namespace WHERE nspname='{schema}'", connection);
        var exists = (long)(await existence.ExecuteScalarAsync())! != 0;
        if (!exists)
        {
            if (cleanup) throw new InvalidOperationException("Missing fixture schema; absence is not successful cleanup.");
            await ExecuteAsync(connection, $"""
                CREATE SCHEMA "{schema}";
                COMMENT ON SCHEMA "{schema}" IS 'program-kit-disposable:{identity.Id}';
                REVOKE ALL ON SCHEMA "{schema}" FROM PUBLIC;
                CREATE TABLE "{schema}".journal(revision integer PRIMARY KEY CHECK(revision=1));
                INSERT INTO "{schema}".journal VALUES(1);
                CREATE TABLE "{schema}".entries(id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, value text NOT NULL UNIQUE);
                GRANT USAGE ON SCHEMA "{schema}" TO "{identity.RuntimeRole}";
                GRANT SELECT ON "{schema}".journal TO "{identity.RuntimeRole}";
                GRANT SELECT,INSERT,UPDATE,DELETE ON "{schema}".entries TO "{identity.RuntimeRole}";
                GRANT USAGE,SELECT ON SEQUENCE "{schema}".entries_id_seq TO "{identity.RuntimeRole}";
                """);
        }
        await ValidateAsync(connection, identity);
        if (cleanup) await ExecuteAsync(connection, $"DROP SCHEMA \"{schema}\" CASCADE");
        await transaction.CommitAsync();
        return cleanup ? "removed" : exists ? "existing" : "created";
    }

    /// <summary>Rejects unexpected objects and foreign owners instead of repairing them.</summary>
    private static async Task ValidateAsync(NpgsqlConnection connection, FixtureIdentity identity)
    {
        var schema = identity.Schema;
        var expected = new[] { "entries:r", "entries_id_seq:S", "entries_pkey:i", "entries_value_key:i", "journal:r", "journal_pkey:i" };
        await using var command = new NpgsqlCommand($"""
            SELECT c.relname || ':' || c.relkind::text, pg_get_userbyid(c.relowner)
            FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='{schema}' ORDER BY c.relname
            """, connection);
        var actual = new List<string>();
        await using (var reader = await command.ExecuteReaderAsync())
            while (await reader.ReadAsync())
            {
                if (reader.GetString(1) != identity.DeploymentRole) throw new InvalidOperationException("Foreign fixture object owner.");
                actual.Add(reader.GetString(0));
            }
        if (!actual.SequenceEqual(expected)) throw new InvalidOperationException("Unexpected fixture object inventory.");
        await using var validation = new NpgsqlCommand($"""
            SELECT obj_description(n.oid,'pg_namespace')='program-kit-disposable:{identity.Id}'
              AND pg_get_userbyid(n.nspowner)='{identity.DeploymentRole}'
              AND NOT EXISTS(SELECT FROM pg_proc WHERE pronamespace=n.oid)
              AND NOT EXISTS(SELECT FROM pg_type t WHERE t.typnamespace=n.oid AND
                NOT (t.typname IN ('entries','journal') AND t.typtype='c' OR t.typname IN ('_entries','_journal') AND t.typelem<>0))
              AND (SELECT count(*)=1 AND min(revision)=1 FROM "{schema}".journal)
            FROM pg_namespace n WHERE n.nspname='{schema}'
            """, connection);
        if (!Equals(await validation.ExecuteScalarAsync(), true)) throw new InvalidOperationException("Unmarked, foreign or changed fixture schema.");
    }

    private static async Task ExecuteAsync(NpgsqlConnection connection, string sql)
    {
        await using var command = new NpgsqlCommand(sql, connection);
        await command.ExecuteNonQueryAsync();
    }
}
