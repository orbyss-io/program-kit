using System.Reflection;

var assemblyPath = Path.GetFullPath(args[0]);
var assembly = Assembly.LoadFile(assemblyPath);
var references = assembly.GetReferencedAssemblies();
Func<AssemblyName, bool> isForbidden = reference =>
    reference.Name != "System.Runtime" && reference.Name != "System.Private.CoreLib";
Func<AssemblyName, string> referenceName = reference => reference.Name;
var forbidden = references
    .Where(isForbidden)
    .Select(referenceName)
    .ToArray();
if (forbidden.Length != 0)
{
    var names = string.Join(",", forbidden);
    var diagnostic = "FORBIDDEN_CORE_REFERENCE: " + names;
    Console.WriteLine(diagnostic);
    return 42;
}
Console.WriteLine("Core references only runtime contracts.");
return 0;
