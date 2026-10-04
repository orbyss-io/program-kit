# Generic dependency profile native lock

`packages.lock.json` belongs to `tests/validate_default_dependency_profile.py`.
It binds the generic probe's Foundation 0.2.4, Forms 0.2.1, Localization 0.1.2,
private Build 0.1.0 and transitive restore inputs. Qualification uses locked restore
in an isolated cache. It never copies a consumer's project or native lock.

A dependency change needs a new profile and qualification. Regenerate this lock
from the generic project for that candidate, inspect the dependency changes, and
run the integration checks before registering the profile. A passing restore
alone grants no consumer review, compatibility, or publication authority.
