---
description: Remove only unchanged regenerable adapter-owned candidate files.
---

Invoke the deterministic adapter `cleanup` operation only on explicit request.
It may remove bytes whose current digest and ownership match the adapter
manifest; it must preserve handoffs, reviews, Program Kit artifacts, products,
consumer source, and any drifted or unknown file.
