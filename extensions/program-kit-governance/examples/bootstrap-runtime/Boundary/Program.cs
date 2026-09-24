using System.Reflection;
var references = Assembly.LoadFile(Path.GetFullPath(args[0])).GetReferencedAssemblies();
var forbidden = references.Where(r => r.Name != "System.Runtime" && r.Name != "System.Private.CoreLib").Select(r => r.Name).ToArray();
if (forbidden.Length != 0) { Console.WriteLine("FORBIDDEN_CORE_REFERENCE: " + string.Join(",", forbidden)); return 42; }
Console.WriteLine("Core references only runtime contracts.");
return 0;
