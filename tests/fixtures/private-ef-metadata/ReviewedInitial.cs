using Microsoft.EntityFrameworkCore.Migrations;
using Microsoft.EntityFrameworkCore.Migrations.Operations;
using Microsoft.EntityFrameworkCore.Migrations.Operations.Builders;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;
using System.Linq.Expressions;

namespace ProgramKit.PrivateEfMetadata.Migrations;

/// <summary>Reviews the synthetic EF-generated operations into readable native migration calls.</summary>
public partial class Initial : Migration
{
    /// <inheritdoc />
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.EnsureSchema(name: "ef_example");
        Func<ColumnsBuilder, ReviewedEntryColumns> buildColumns = BuildColumns;
        Action<CreateTableBuilder<ReviewedEntryColumns>> configureConstraints = ConfigureConstraints;
        migrationBuilder.CreateTable(
            name: "ef_entries",
            schema: "ef_example",
            columns: buildColumns,
            constraints: configureConstraints
        );
        migrationBuilder.CreateIndex(
            name: "IX_ef_entries_Value",
            schema: "ef_example",
            table: "ef_entries",
            column: "Value",
            unique: true
        );
    }

    /// <inheritdoc />
    protected override void Down(MigrationBuilder migrationBuilder)
        => migrationBuilder.DropTable(name: "ef_entries", schema: "ef_example");

    /// <summary>Keeps the generated identity strategy and non-null column definitions.</summary>
    private static ReviewedEntryColumns BuildColumns(ColumnsBuilder table)
    {
        var identity = table.Column<long>(type: "bigint", nullable: false);
        identity.Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn);
        var value = table.Column<string>(type: "text", nullable: false);
        return new ReviewedEntryColumns { Id = identity, Value = value };
    }

    /// <summary>Retains the primary key selected by native EF model generation.</summary>
    private static void ConfigureConstraints(CreateTableBuilder<ReviewedEntryColumns> table)
    {
        Expression<Func<ReviewedEntryColumns, object>> key = columns => columns.Id;
        table.PrimaryKey("PK_ef_entries", key);
    }
}
