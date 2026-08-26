using System.Collections.Immutable;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Diagnostics;
using Microsoft.CodeAnalysis.Operations;

namespace ProgramKit.Analyzers;

[DiagnosticAnalyzer(LanguageNames.CSharp)]
public sealed class ProgramKitAnalyzer : DiagnosticAnalyzer
{
    public const string ShellHostedServiceRuleId = "PK1001";
    public const string NamedArgumentsRuleId = "PK1002";

    private static readonly DiagnosticDescriptor ShellHostedServiceRule = new(
        ShellHostedServiceRuleId,
        "Shell features cannot register hosted services",
        "Register '{0}' through ProgramKit.Tasks; the Generic Host does not start shell-scoped IHostedService instances",
        "Lifecycle",
        DiagnosticSeverity.Error,
        isEnabledByDefault: true,
        description: "CShells creates a provider per shell generation, while the Generic Host starts hosted services only from the root provider.");

    private static readonly DiagnosticDescriptor NamedArgumentsRule = new(
        NamedArgumentsRuleId,
        "Use named arguments for complex calls",
        "Name argument '{0}' because this call supplies four or more arguments",
        "Style",
        DiagnosticSeverity.Info,
        isEnabledByDefault: true,
        description: "Program Kit Policy B asks complex call sites to name arguments while preserving concise obvious calls.");

    public override ImmutableArray<DiagnosticDescriptor> SupportedDiagnostics =>
        ImmutableArray.Create(ShellHostedServiceRule, NamedArgumentsRule);

    public override void Initialize(AnalysisContext context)
    {
        context.ConfigureGeneratedCodeAnalysis(GeneratedCodeAnalysisFlags.None);
        context.EnableConcurrentExecution();
        context.RegisterOperationAction(AnalyzeInvocation, OperationKind.Invocation);
        context.RegisterOperationAction(AnalyzeObjectCreation, OperationKind.ObjectCreation);
    }

    private static void AnalyzeInvocation(OperationAnalysisContext context)
    {
        var invocation = (IInvocationOperation)context.Operation;
        if (invocation.TargetMethod.Name == "AddHostedService"
            && invocation.TargetMethod.ContainingType.ToDisplayString() ==
            "Microsoft.Extensions.DependencyInjection.ServiceCollectionHostedServiceExtensions"
            && ImplementsShellFeature(context.ContainingSymbol.ContainingType))
        {
            var serviceName = invocation.TargetMethod.TypeArguments.FirstOrDefault()?.Name ?? "hosted service";
            context.ReportDiagnostic(Diagnostic.Create(ShellHostedServiceRule, invocation.Syntax.GetLocation(), serviceName));
        }

        AnalyzeArguments(context, invocation.Arguments);
    }

    private static void AnalyzeObjectCreation(OperationAnalysisContext context)
    {
        var creation = (IObjectCreationOperation)context.Operation;
        AnalyzeArguments(context, creation.Arguments);
    }

    private static void AnalyzeArguments(OperationAnalysisContext context, ImmutableArray<IArgumentOperation> arguments)
    {
        if (arguments.Length < 4)
            return;

        foreach (var argument in arguments)
        {
            if (argument.ArgumentKind != ArgumentKind.Explicit || argument.Syntax is ArgumentSyntax { NameColon: not null })
                continue;

            context.ReportDiagnostic(Diagnostic.Create(
                NamedArgumentsRule,
                argument.Syntax.GetLocation(),
                argument.Parameter?.Name ?? "argument"));
        }
    }

    private static bool ImplementsShellFeature(INamedTypeSymbol? type) =>
        type is not null && type.AllInterfaces.Any(candidate =>
            candidate.ToDisplayString() == "CShells.Features.IShellFeature");
}
