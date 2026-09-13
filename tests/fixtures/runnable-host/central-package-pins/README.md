# Runtime staging central-package regression

This synthetic RM-01 regression preserves the relevant imported/consumer central
package layout. The validator copies the current shipped ProgramKit.Packages.props
into a disposable repository; the three public feature pins belong to the consumer
section of Directory.Packages.props. Optional selected-package imports are exercised
separately. No PriceCalculator implementation, credentials, approval or runtime
evidence is included.

Run `python tests/validate_runnable_host_pins.py` from the Program Kit repository.
Packages and download responses are deterministic fixtures. Passing this test is
staging-contract evidence, not proof of a deployed consumer journey.
