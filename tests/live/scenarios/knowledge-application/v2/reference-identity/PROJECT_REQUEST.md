# Equipment lending desk

This is a fictional acceptance product, independent of PriceCalculator. Bootstrap a
new .NET and React repository, then deliver one vertical slice: an operator reserves
one of two cameras, explicitly confirms the reservation, and can cancel it. A later
reporting feature remains planned and must not be scaffolded by setup or upgrade.

RM01 owns reservation policy, lifecycle, durable admission and its public V1 contract.
An available camera moves Draft → Reserved → Confirmed or Reserved → Cancelled.
Confirmation requires the operator's explicit acknowledgement. Cancelled reservations
cannot be confirmed. Denied policy and illegal transitions must cause no stock or
notification effects. Retrying an identical operation returns its original operation
and reservation identity; reusing the key with different content is a conflict.
Accepted reservations survive process restart. A transient notification failure must
retain durable retry ownership; recovery sends the notification once without reserving
another camera. Injected test time and effect ports allow deterministic failure cases.

Use proportional policies and transition code with typed outcomes, no speculative
framework. Keep domain contracts and Core logic free of HTTP, serializers, persistence
and DI. Put the persistence adapter behind an explicit capability; prove real shell
registration/resolution and replacement compatibility. A deliberate forbidden feature
reference must fail the maintained evaluated/compiled architecture checks. One operation
folder owns each request/handler/response and its tests; the IWebShellFeature stays thin.

Publish the reservation form through Forms 0.2's public release producer during the
build. Admit its immutable artifacts before using the supported React renderer. No
deployed Forms management service is required. Use explicit Foundation JSON request
and response profiles, named response policies and one header writer. When hosted-page
delivery is selected, use its admitted asset and typed public bootstrap mechanism.
Never put secrets or private reservation records into public bootstrap data.

The independent fixture contract fixes observable HTTP and browser behavior, not
internal filenames or class names. The feature owner chooses names, placement and
extension points, records them in the normal artifacts and follows installed commands.
Bootstrap may run bounded scratch compatibility tests; it must not implement RM01.
Every feature starts with grilling and confirmation of its exact brief.

Upgrade uses an independently admitted reference consumer built from real released
Program Kit inputs. Keep its consumer source/configuration edits, canonical identity,
V1 JSON names, status semantics and durable records. Apply scoped remediation for
new obligations and restore through the same coordinator. A fabricated historical
bootstrap or feature checkpoint is never a valid baseline.

Each paid phase remains separately authorized. No automatic rerun. Evaluate quality,
tokens and preventable work together; retain failures, cache accounting and unknown
measurements. A cheaper run that omits required work fails acceptance.
