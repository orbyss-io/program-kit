# Inventory Health

This prose records the natural-language consumer intent and is not itself a
Program Kit request.

<!-- program-kit:FR-001 -->
The Inventory Health feature exposes `GET /inventory/health` through
`Warehouse.Inventory.Api` and delegates to
`Warehouse.Inventory.IInventoryProbe`.
<!-- /program-kit:FR-001 -->

The endpoint reports the distinct degraded inventory state and backlog count
implemented by the consumer-owned feature source.
