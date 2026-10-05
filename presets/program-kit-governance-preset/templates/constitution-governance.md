## Application engineering principles

### Test-first behavior

New or changed application behavior MUST have automated tests traced to its user stories,
requirements and acceptance scenarios. Write the relevant tests first, observe failure for the
intended missing behavior, implement, and refactor with the tests passing. A scoped exception
requires a concrete rationale and an alternative verification method in the plan or an ADR.
Reuse qualified component coverage; test the application's own policies, boundaries and integration
rather than duplicating a publisher's internal suite. Test output is ordinary execution output,
not a separate approval or proof dossier.

### Architecture and implementation quality

Preserve accepted domain ownership and dependency directions. Apply coding guidance only when
its conditions hold; use native analyzers, architecture checks, contract/security tests and code
review to verify the resulting implementation. Keep detailed conditional examples in referenced
guidance, not repeated constitutional inventories.

### Independent engineering

Restore, build, test, contract generation, packaging and deployment MUST remain runnable by humans
from documented engineering commands without AI, toolkit extensions or governance history.
