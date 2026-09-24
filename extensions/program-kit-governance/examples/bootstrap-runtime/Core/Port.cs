namespace ProgramKit.Compatibility;
public interface IProbePort { string Read(); }
#if FORBIDDEN
public sealed record ForbiddenDependency(Microsoft.AspNetCore.Http.HttpContext Context);
#endif
