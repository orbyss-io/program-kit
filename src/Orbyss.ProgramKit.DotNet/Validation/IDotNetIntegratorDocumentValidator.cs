using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;

namespace Orbyss.ProgramKit.DotNet.Validation;

/// <summary>Validates typed API, Console, and Worker projection inputs.</summary>
public interface IDotNetIntegratorDocumentValidator
{
    /// <summary>Validates an OpenAPI projection.</summary>
    ProgramKitValidationResult Validate(OpenApiDocumentProjection document);

    /// <summary>Validates an Open Console document.</summary>
    ProgramKitValidationResult Validate(OpenConsoleDocument document);

    /// <summary>Validates an Open Worker document.</summary>
    ProgramKitValidationResult Validate(OpenWorkerDocument document);
}
