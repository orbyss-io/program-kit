using Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>
/// One exact typed Console request plus the canonical bytes whose digest owns
/// the materialized closure.
/// </summary>
internal sealed record MaterializationRequestReadResult(
    DotNetConsoleInputMaterializationRequest LegacyRequest,
    DotNetConsoleInputMaterializationRequestAlpha2? Alpha2Request,
    byte[] CanonicalBytes);
