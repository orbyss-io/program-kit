using System.Linq.Expressions;
using Microsoft.EntityFrameworkCore.Migrations;
using Microsoft.EntityFrameworkCore.Migrations.Operations.Builders;

namespace Application.PostgreSql.Migrations;

/// <summary>Preserves reviewed native EF operations while naming deferred column/constraint builders.</summary>
public partial class OwnerInitial : Migration
{
    /// <inheritdoc />
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.EnsureSchema(name: "owner_example");
        Func<ColumnsBuilder, ReviewedOwnerColumns> columns = BuildColumns;
        Action<CreateTableBuilder<ReviewedOwnerColumns>> constraints = ConfigureConstraints;
        migrationBuilder.CreateTable(
            name: "owner_notes",
            schema: "owner_example",
            columns: columns,
            constraints: constraints
        );
    }
    /// <inheritdoc />
    protected override void Down(MigrationBuilder migrationBuilder)
        => migrationBuilder.DropTable(name: "owner_notes", schema: "owner_example");
    /// <summary>Retains the native generated types, nullability and exact identity collations.</summary>
    private static ReviewedOwnerColumns BuildColumns(ColumnsBuilder table)
    {
        return new ReviewedOwnerColumns
        {
            Id = table.Column<Guid>(type: "uuid", nullable: false),
            OwnerIssuer = table.Column<string>(
                type: "text",
                nullable: false,
                collation: "C"
            ),
            OwnerSubject = table.Column<string>(
                type: "text",
                nullable: false,
                collation: "C"
            ),
            Value = table.Column<string>(type: "text", nullable: false),
            Digest = table.Column<byte[]>(type: "bytea", nullable: false)
        };
    }
    /// <summary>Retains the generated independent note primary key.</summary>
    private static void ConfigureConstraints(CreateTableBuilder<ReviewedOwnerColumns> table)
    {
        Expression<Func<ReviewedOwnerColumns, object>> key = columns => columns.Id;
        table.PrimaryKey("PK_owner_notes", key);
    }
}
