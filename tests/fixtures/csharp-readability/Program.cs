using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

// Test-only syntax oracle for editable F4 examples. Not a consumer analyzer or formatter.
internal static class Program
{
    private static int Main(string[] paths)
    {
        Controls();
        var failures = new List<string>();
        foreach (var path in paths)
        {
            var source = File.ReadAllText(path);
            var found = Inspect(source);
            foreach (var failure in found)
            {
                failures.Add($"{path}: {failure}");
            }
        }
        foreach (var failure in failures) Console.Error.WriteLine(failure);
        Console.WriteLine($"Readability syntax controls and {paths.Length} C# files checked; {failures.Count} violations.");
        return failures.Count == 0 ? 0 : 1;
    }

    private static List<string> Inspect(string source)
    {
        var tree = CSharpSyntaxTree.ParseText(source);
        var root = tree.GetRoot();
        var text = tree.GetText();
        var failures = new List<string>();
        var diagnostics = tree.GetDiagnostics();
        var errors = diagnostics.Where(d => d.Severity == DiagnosticSeverity.Error);
        foreach (var error in errors)
            failures.Add("syntax: " + error);

        int Line(SyntaxToken token) => text.Lines.GetLinePosition(token.SpanStart).Line;
        void Layout(
            SyntaxToken open,
            SyntaxToken close,
            IEnumerable<SyntaxNode> values
        )
        {
            var items = values.ToArray();
            if (items.Length == 0 || (items.Length <= 2 && Line(open) == Line(close))) return;
            var previous = Line(open);
            foreach (var item in items)
            {
                var first = item.GetFirstToken();
                var firstLine = Line(first);
                if (firstLine <= previous) failures.Add($"layout at line {firstLine + 1}: one value per following line");
                var last = item.GetLastToken();
                previous = Line(last);
            }
            var openLineIndex = Line(open);
            var openLine = text.Lines[openLineIndex].ToString();
            var indent = openLine
                .TakeWhile(char.IsWhiteSpace)
                .Count();
            var closeColumn = text.Lines.GetLinePosition(close.SpanStart).Character;
            var closeLine = Line(close);
            if (closeLine <= previous || closeColumn != indent)
                failures.Add($"layout at line {closeLine + 1}: closing parenthesis needs its own aligned line");
        }

        var nodes = root.DescendantNodes();
        var arguments = nodes.OfType<ArgumentListSyntax>();
        foreach (var list in arguments)
        {
            Layout(
                list.OpenParenToken,
                list.CloseParenToken,
                list.Arguments
            );
        }
        var parameters = nodes.OfType<ParameterListSyntax>();
        foreach (var list in parameters)
        {
            Layout(
                list.OpenParenToken,
                list.CloseParenToken,
                list.Parameters
            );
        }
        var argumentNodes = nodes.OfType<ArgumentSyntax>();
        foreach (var argument in argumentNodes)
        {
            var expressions = argument.Expression.DescendantNodesAndSelf();
            Func<SyntaxNode, bool> isInvocation = node =>
                node is InvocationExpressionSyntax or ObjectCreationExpressionSyntax or ImplicitObjectCreationExpressionSyntax;
            var nested = expressions.Any(isInvocation);
            var first = argument.GetFirstToken();
            var line = Line(first);
            if (nested) failures.Add($"argument at line {line + 1}: prepare the value or delegate first");
        }
        var seen = new HashSet<InvocationExpressionSyntax>();
        var calls = nodes.OfType<InvocationExpressionSyntax>();
        foreach (var call in calls)
        {
            if (call.Expression is not MemberAccessExpressionSyntax { Expression: InvocationExpressionSyntax }) continue;
            InvocationExpressionSyntax? current = call;
            while (current is not null && seen.Add(current))
            {
                if (current.Expression is not MemberAccessExpressionSyntax member)
                {
                    var first = current.GetFirstToken();
                    var line = Line(first);
                    failures.Add($"chain at line {line + 1}: prepare the receiver first");
                    break;
                }
                var operatorLine = Line(member.OperatorToken);
                var lastReceiverToken = member.Expression.GetLastToken();
                var receiverLine = Line(lastReceiverToken);
                if (operatorLine <= receiverLine)
                    failures.Add($"chain at line {operatorLine + 1}: each invocation, including the first, starts below its receiver");
                current = member.Expression as InvocationExpressionSyntax;
            }
        }
        return failures;
    }

    private static void Controls()
    {
        var valid = """
            class Good(
                int first,
                int second,
                int third
            )
            {
                void Work()
                {
                    var value = Prepare();
                    var item = new Item(value);
                    Use(item, "literal(Call(a, b, c))");
                    receiver
                        .First()
                        .Second();
                    Use(
                        first,
                        second,
                        third
                    );
                }
            }
            """;
        if (Inspect(valid).Count != 0) throw new Exception("Valid readability control rejected.");
        var invalid = new[]
        {
            ("class Bad { void M(int a, int b, int c) {} }", "layout"),
            ("class Bad(int a, int b, int c) {}", "layout"),
            ("Use(a, b, c);", "layout"),
            ("new Item(a, b, c);", "layout"),
            ("Use(\n a, b,\n c\n);", "layout"),
            ("Use(\n a,\n b,\n c);", "layout"),
            ("Use(\n a,\n b,\n c\n );", "layout"),
            ("Use(Prepare());", "argument"),
            ("new Item(await PrepareAsync());", "argument"),
            ("Use(new Item(value));", "argument"),
            ("Use(() => Prepare());", "argument"),
            ("receiver.First().Second();", "chain"),
            ("receiver.First()\n .Second();", "chain"),
            ("receiver\n .First().Second();", "chain")
        };
        foreach (var (source, rule) in invalid)
        {
            var failures = Inspect(source);
            Func<string, bool> matchesRule = failure => failure.StartsWith(rule);
            var detected = failures.Any(matchesRule);
            if (!detected)
                throw new Exception($"Invalid {rule} control accepted: {source}");
        }
        Console.WriteLine("Independent controls: valid prepared arguments/layout/chain; 14 invalid declaration, call, constructor, nested-value/delegate and chain cases rejected.");
    }
}
