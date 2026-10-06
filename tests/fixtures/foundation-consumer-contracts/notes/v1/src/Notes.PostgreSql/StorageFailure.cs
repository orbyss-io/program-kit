using Microsoft.EntityFrameworkCore;
using Npgsql;

namespace Notes.PostgreSql;

internal static class StorageFailure
{
    internal static bool IsExpected(Exception exception) => exception is NpgsqlException
        || exception is DbUpdateException { InnerException: NpgsqlException };
}
