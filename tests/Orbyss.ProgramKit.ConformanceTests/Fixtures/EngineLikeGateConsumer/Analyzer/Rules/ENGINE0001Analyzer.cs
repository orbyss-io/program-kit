using System.Collections.Immutable;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Diagnostics;

namespace Engine.Semantics.Analyzers;

[DiagnosticAnalyzer(LanguageNames.CSharp)]
public sealed class ENGINE0001Analyzer : DiagnosticAnalyzer
{
    public const string DiagnosticId = "ENGINE0001";
    private const string ForbiddenSuffix = "Service";

    private static readonly DiagnosticDescriptor Rule = new(
        DiagnosticId,
        "Service suffix is forbidden",
        "Engine-owned type name must not end with Service",
        "ConsumerOwned",
        DiagnosticSeverity.Error,
        isEnabledByDefault: true);

    public override ImmutableArray<DiagnosticDescriptor> SupportedDiagnostics =>
        [Rule];

    public override void Initialize(AnalysisContext context)
    {
        context.ConfigureGeneratedCodeAnalysis(GeneratedCodeAnalysisFlags.None);
        context.EnableConcurrentExecution();
        context.RegisterSyntaxNodeAction(
            AnalyzeType,
            SyntaxKind.ClassDeclaration,
            SyntaxKind.StructDeclaration,
            SyntaxKind.InterfaceDeclaration,
            SyntaxKind.RecordDeclaration,
            SyntaxKind.RecordStructDeclaration,
            SyntaxKind.EnumDeclaration);
    }

    private static void AnalyzeType(SyntaxNodeAnalysisContext context)
    {
        var identifier = context.Node switch
        {
            BaseTypeDeclarationSyntax declaration => declaration.Identifier,
            _ => default,
        };
        if (identifier.ValueText.EndsWith(
                ForbiddenSuffix,
                StringComparison.Ordinal))
        {
            context.ReportDiagnostic(
                Diagnostic.Create(Rule, identifier.GetLocation()));
        }
    }
}
