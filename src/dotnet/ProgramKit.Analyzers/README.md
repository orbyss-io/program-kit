# ProgramKit.Analyzers

- `PK1001` prevents `AddHostedService` inside a CShells feature because the root Generic Host will not start it.
- `PK1002` suggests named arguments for calls with four or more arguments. Consumers control its severity in `.editorconfig`.

The consumer scaffold references this package centrally with `PrivateAssets=all`; application projects do not
need individual analyzer references.
