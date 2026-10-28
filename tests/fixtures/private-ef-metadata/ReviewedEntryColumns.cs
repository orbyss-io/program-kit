using Microsoft.EntityFrameworkCore.Migrations.Operations;
using Microsoft.EntityFrameworkCore.Migrations.Operations.Builders;

namespace ProgramKit.PrivateEfMetadata.Migrations;

/// <summary>Names native column operations so deferred builder arguments can be prepared separately.</summary>
internal sealed class ReviewedEntryColumns
{
    /// <summary>Gets the generated identity column operation.</summary>
    public required OperationBuilder<AddColumnOperation> Id { get; init; }

    /// <summary>Gets the required value column operation.</summary>
    public required OperationBuilder<AddColumnOperation> Value { get; init; }
}
