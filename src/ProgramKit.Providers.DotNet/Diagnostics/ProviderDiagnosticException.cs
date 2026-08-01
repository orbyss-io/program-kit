using System;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Providers.DotNet.Diagnostics;

public sealed class ProviderDiagnosticException : Exception
{
    public ProviderDiagnosticException(string diagnosticId, PrimaryDisposition disposition, string message)
        : base(message)
    {
        DiagnosticId = diagnosticId;
        Disposition = disposition;
    }

    public string DiagnosticId { get; }

    public PrimaryDisposition Disposition { get; }
}
