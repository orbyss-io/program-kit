# Owner-backed normalized label validation

Keep the pure consumer Core rule authoritative. A consumer-owned build exporter serializes its
actual identities, versions, constants and character predicates; `eng/label_validation.py` generates
the browser validator from that descriptor. Core contains C# policy, not JSON artifacts or a browser
dependency. Program Kit supports this bounded label contract rather than inspecting arbitrary C#
methods or introducing a rules engine.

The v1 contract rejects C0/C1 controls **anywhere in the raw string before trimming**, trims exactly
the .NET whitespace character set, and validates normalized UTF-16 length. The descriptor declares
the owner, contract and rule identities/versions, ordered operations, exact trim code units, raw
control ranges, length unit and minimum/maximum. Unsupported fields, descriptor schema versions, ordering, sets or
units fail generation; there is no approximation fallback. Owner policy and compatibility baselines
still control any intentional rule change.

## Export and generation

Create an owner build tool referencing the actual pure Core project. Its `export` command writes one
JSON descriptor to stdout. Select the wire representation in that build tool, reading bounds and
identities from the Core rule and deriving the character sets from the predicates that Core uses.
Do not maintain an independent schema or copy constants into the browser. The executable
[Core/exporter fixture](https://github.com/orbyss-io/program-kit/blob/main/tests/fixtures/label-validation/Exporter/Program.cs) demonstrates
the shape; its labels and identities are synthetic test data, not a product feature to adopt.

Restore the build tool explicitly through the consumer's selected native dependency/lock workflow.
Then run:

```powershell
python eng/label_validation.py export --repository . --project tools/PolicyValidation.Export/PolicyValidation.Export.csproj --output contracts/validation/policy-labels.json
python eng/label_validation.py generate --descriptor contracts/validation/policy-labels.json --output web/src/api/policy-labels.generated.ts
```

Export builds the owner tool with `--no-restore` before running it, so a stale executable cannot
refresh source-backed metadata. The exporter is an ordinary explicitly selected native .NET build
tool; it does not invoke a coding agent. The descriptor schema ships at
`eng/label-validation.schema.json`. The Python validator additionally checks normalized bound
ordering and unique rule identity, which standard JSON Schema cannot establish here by itself.

Both commands support `--check`. Check source-backed export first, then generated TypeScript:

```powershell
python eng/label_validation.py export --repository . --project tools/PolicyValidation.Export/PolicyValidation.Export.csproj --output contracts/validation/policy-labels.json --check
python eng/label_validation.py generate --descriptor contracts/validation/policy-labels.json --output web/src/api/policy-labels.generated.ts --check
```

These fail on missing/stale bytes; neither updates files in check mode. `generate --check` alone
does not establish that the checked descriptor still matches the current Core source. The generated
module includes the descriptor SHA-256 and immutable metadata with identities, versions and bounds.

## Browser use and input preservation

Call `normalizeLabel(ruleName, rawValue)` before admission/digest binding. A successful result carries
the exact normalized value; a failure carries a stable code (`type`, `control_character`, or
`normalized_length`) and the owner minimum/maximum/UTF-16 unit. Use those bounds for accessible error
copy. Send and hash the same normalized value that server policy admits.
Undeclared runtime rule keys throw a bounded configuration error, without reflecting the key or raw
input. Inherited object properties do not select a rule; explicitly declared own rule names remain valid.

Keep the raw correction input visible until a successful operation warrants clearing it. The
generated function never changes the input control or truncates its value. Do not set HTML
`maxlength` to a normalized limit: paste can truncate a raw value that would have been valid after
trimming. A native single-line `input type=text` also strips CR/LF before `.value` validation. Use a
control that retains the raw invalid value, such as an accessible one-row textarea, or explicitly
capture/reject raw paste and before-input data before native sanitization. Validating `.value` alone
does not prove rejection of the original pasted controls. Keep server rejection authoritative for
direct API callers regardless of browser behavior.

Do not attach ordinary JSON Schema `minLength`/`maxLength` to raw transport data and claim that they
express normalized UTF-16 bounds: standard schema length counts Unicode code points and does not
perform this normalization. Export the explicit descriptor separately or through a documented
owner OpenAPI extension; generated TypeScript types alone are not runtime business validation.
Keep independent transport byte/depth limits in the selected Foundation JSON contract.

## Focused verification

`python tests/validate_label_validation.py --unit` is the bounded Development test. It rejects
unsupported descriptors and stale generated output and verifies template materialization.

`python tests/validate_label_validation.py --execute --engines=chromium,webkit` additionally builds
the actual disposable Core/exporter, compiles generated TypeScript, checks normalized values and
UTF-8 digest parity, changes Core to prove both metadata and browser staleness, sends invalid raw
JSON through a native HTTP endpoint and checks zero fixture effects, and exercises native browsers.
The Chromium leg uses real clipboard paste for valid, overlong and control-bearing raw input. It
observes one actual admission request for valid input and no admission requests for invalid input,
with a synthetic admission response that does not claim server validation. Other engines exercise native text insertion. The
fixture preserves raw controls in a textarea and separately demonstrates native text-input LF
stripping. `--node-modules <path>` can reuse already installed exact maintained TypeScript/Playwright
pins; otherwise the test prepares those existing pins in its disposable fixture. No Forms dependency
is introduced. CI keeps `chromium,firefox,webkit`; the documented Windows Firefox launch limitation
does not change its CI acceptance.

This proof uses synthetic values and a disposable native HTTP effect counter. It establishes the
generation/parity contract, not real consumer, database, deployed bundle or full-story acceptance.
Consumer adoption must add its own production-port, persistence, request and browser regressions,
retaining existing replay, concurrency, rollback, cancellation and uncertainty coverage.
