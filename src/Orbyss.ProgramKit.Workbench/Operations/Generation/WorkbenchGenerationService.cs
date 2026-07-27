using System.Security.Cryptography;
using Orbyss.ProgramKit.Workbench.Operations.Diagnostics;

namespace Orbyss.ProgramKit.Workbench.Operations.Generation;

/// <summary>Default bounded transactional generation coordinator.</summary>
/// <typeparam name="T">The generator input type.</typeparam>
public sealed class WorkbenchGenerationService<T> :
    IWorkbenchGenerationService<T>
{
    private readonly IWorkbenchGenerator<T> generator;
    private readonly IWorkbenchOutputWorkspace workspace;

    /// <summary>Initializes generation with injected behavior and output authority.</summary>
    public WorkbenchGenerationService(
        IWorkbenchGenerator<T> generator,
        IWorkbenchOutputWorkspace workspace)
    {
        this.generator = generator ?? throw new ArgumentNullException(nameof(generator));
        this.workspace = workspace ?? throw new ArgumentNullException(nameof(workspace));
    }

    /// <inheritdoc />
    public async ValueTask<WorkbenchResult<GenerationReceipt>> GenerateAsync(
        GenerationRequest<T> request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        var requestValidation = ValidateRequest(request);
        if (!requestValidation.IsValid)
        {
            return new WorkbenchResult<GenerationReceipt>(default, requestValidation);
        }

        IWorkbenchOutputTransaction? transaction = null;
        try
        {
            var outputs = await generator.GenerateAsync(
                request.Input,
                cancellationToken).ConfigureAwait(false);
            var outputValidation = ValidateOutputs(outputs, request.Limits);
            if (!outputValidation.IsValid)
            {
                return new WorkbenchResult<GenerationReceipt>(default, outputValidation);
            }

            var ordered = outputs
                .OrderBy(static output => output.RelativePath, StringComparer.Ordinal)
                .ToImmutableArray();
            transaction = await workspace.BeginAsync(
                request.WriteRoot,
                request.CollisionPolicy,
                cancellationToken).ConfigureAwait(false);
            foreach (var output in ordered)
            {
                cancellationToken.ThrowIfCancellationRequested();
                await transaction.StageAsync(output, cancellationToken).ConfigureAwait(false);
            }

            cancellationToken.ThrowIfCancellationRequested();
            await transaction.CommitAsync(cancellationToken).ConfigureAwait(false);
            var receipts = ordered
                .Select(static output => new GeneratedOutputReceipt(
                    output.RelativePath,
                    CalculateDigest(output.Content.Span),
                    output.Content.Length))
                .ToImmutableArray();
            return new WorkbenchResult<GenerationReceipt>(
                new GenerationReceipt(receipts),
                ProgramKitValidationResult.Valid);
        }
        catch (OperationCanceledException exception)
        {
            return await FailureAfterRollbackAsync(
                transaction,
                WorkbenchDiagnosticIds.OperationCancelled,
                exception.Message).ConfigureAwait(false);
        }
        catch (IOException exception)
        {
            return await FailureAfterRollbackAsync(
                transaction,
                WorkbenchDiagnosticIds.OutputPublicationFailed,
                exception.Message).ConfigureAwait(false);
        }
        catch (UnauthorizedAccessException exception)
        {
            return await FailureAfterRollbackAsync(
                transaction,
                WorkbenchDiagnosticIds.OutputPublicationFailed,
                exception.Message).ConfigureAwait(false);
        }
    }

    private static async ValueTask<WorkbenchResult<GenerationReceipt>>
        FailureAfterRollbackAsync(
            IWorkbenchOutputTransaction? transaction,
            string diagnosticId,
            string message)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.Add(WorkbenchDiagnostics.Error(
            diagnosticId,
            message,
            "/writeRoot"));
        if (transaction is not null)
        {
            try
            {
                await transaction.RollbackAsync(CancellationToken.None).ConfigureAwait(false);
            }
            catch (IOException exception)
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.OutputRollbackFailed,
                    string.Concat(
                        "Private staging cleanup could not be confirmed: ",
                        exception.Message),
                    "/writeRoot"));
            }
            catch (UnauthorizedAccessException exception)
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.OutputRollbackFailed,
                    string.Concat(
                        "Private staging cleanup could not be confirmed: ",
                        exception.Message),
                    "/writeRoot"));
            }
        }

        return new WorkbenchResult<GenerationReceipt>(
            default,
            ProgramKitValidationResult.From(diagnostics));
    }

    private static ProgramKitValidationResult ValidateRequest(
        GenerationRequest<T> request)
    {
        if (request.Input is null ||
            string.IsNullOrWhiteSpace(request.WriteRoot) ||
            request.Limits is null ||
            request.Limits.MaxFiles <= 0 ||
            request.Limits.MaxFileBytes <= 0 ||
            request.Limits.MaxTotalBytes <= 0 ||
            !Enum.IsDefined(request.CollisionPolicy))
        {
            return ProgramKitValidationResult.From(
            [
                WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.OperationLimitExceeded,
                    "Generation requires input, a write root, a defined collision policy, and positive limits.",
                    string.Empty),
            ]);
        }

        return ProgramKitValidationResult.Valid;
    }

    private static ProgramKitValidationResult ValidateOutputs(
        ImmutableArray<GeneratedOutput> outputs,
        GenerationLimits limits)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (outputs.IsDefault || outputs.Length > limits.MaxFiles)
        {
            diagnostics.Add(WorkbenchDiagnostics.Error(
                WorkbenchDiagnosticIds.OperationLimitExceeded,
                "The generated output count is invalid or exceeds the declared limit.",
                "/outputs"));
            return ProgramKitValidationResult.From(diagnostics);
        }

        var paths = new HashSet<string>(StringComparer.Ordinal);
        long total = 0;
        for (var index = 0; index < outputs.Length; index++)
        {
            var output = outputs[index];
            var path = string.Concat("/outputs/", index);
            if (output is null ||
                !IsNormalizedRelativePath(output.RelativePath) ||
                !paths.Add(output.RelativePath))
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.OutputPublicationFailed,
                    "Output paths must be unique normalized forward-slash relative paths.",
                    string.Concat(path, "/relativePath")));
                continue;
            }

            total = checked(total + output.Content.Length);
            if (output.Content.Length > limits.MaxFileBytes ||
                total > limits.MaxTotalBytes)
            {
                diagnostics.Add(WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.OperationLimitExceeded,
                    "Generated output bytes exceed the declared limit.",
                    string.Concat(path, "/content")));
            }
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    private static bool IsNormalizedRelativePath(string path) =>
        !string.IsNullOrWhiteSpace(path) &&
        !Path.IsPathRooted(path) &&
        !path.Contains('\\') &&
        path.Split('/').All(static segment =>
            segment.Length > 0 &&
            segment != "." &&
            segment != "..");

    private static Sha256Digest CalculateDigest(ReadOnlySpan<byte> bytes)
    {
        var digest = SHA256.HashData(bytes);
        return new Sha256Digest(
            string.Concat("sha256:", Convert.ToHexString(digest).ToLowerInvariant()));
    }
}
