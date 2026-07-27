using Orbyss.ProgramKit.Tasks.Core.Bindings;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Explicit registration of one exact activation binding.</summary>
public sealed record TaskActivationBindingRegistration(
    TaskActivationBinding Binding);
