"""Independent process attempting exactly one conditional commit; no retries."""
import json
from pathlib import Path
import sys
import time

from .contract import admit
from .providers import Store
from .transport import ApiError


def main():
    provider, head, work, execution, ready, go = sys.argv[1:]
    store = Store(provider)
    _, state = store.read(head)
    proposed = admit(state, work, {"providerId": "probe-actor", "accountableHumanId": "probe-owner", "executionId": execution},
                     {"businessRevision": "synthetic-v1"}, ["probe-exclusive-resource"])
    Path(ready).write_text("ready")
    deadline = time.monotonic() + 60
    while not Path(go).exists():
        if time.monotonic() > deadline:
            raise RuntimeError("Race barrier timed out")
        time.sleep(0.05)
    try:
        result = {"outcome": "committed", "head": store.commit(head, proposed), "execution": execution}
    except ApiError as error:
        result = {"outcome": "rejected", "status": error.status, "codes": error.codes,
                  "classifiedStale": store.is_stale(error), "execution": execution}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
