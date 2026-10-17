using Microsoft.EntityFrameworkCore;
using Orbyss.Foundation.PostgreSql;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Uses native Foundation units; schema deployment is a separate process.</summary>
public sealed class FixtureContext(DbContextOptions<FixtureContext> options) : FoundationPostgreSqlDbContext(options);
