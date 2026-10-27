using Microsoft.EntityFrameworkCore.Migrations.Operations;
using Microsoft.EntityFrameworkCore.Migrations.Operations.Builders;

namespace Application.PostgreSql.Migrations;

/// <summary>Names only the column operations emitted by the reviewed synthetic EF migration.</summary>
internal sealed class ReviewedOwnerColumns
{
    /// <summary>Gets the independent note identifier column.</summary>
    public required OperationBuilder<AddColumnOperation> Id { get; init; }
    /// <summary>Gets the exact issuer column.</summary>
    public required OperationBuilder<AddColumnOperation> OwnerIssuer { get; init; }
    /// <summary>Gets the exact subject column.</summary>
    public required OperationBuilder<AddColumnOperation> OwnerSubject { get; init; }
    /// <summary>Gets the synthetic product value column.</summary>
    public required OperationBuilder<AddColumnOperation> Value { get; init; }
    /// <summary>Gets the non-secret integrity digest column.</summary>
    public required OperationBuilder<AddColumnOperation> Digest { get; init; }
}
