# ProgramKit.Authentication

Shared CShells authentication composition for Program Kit. The feature binds shell-scoped web
configuration, validates that exactly one authentication profile is active, maps provider roles and
scopes to canonical application permissions, and supplies a replaceable authentication error writer.

Applications activate a concrete profile feature rather than this package directly; the BFF-cookie
and SPA-PKCE features declare it as a dependency.
