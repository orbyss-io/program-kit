# Program Kit 0.9.5 compatibility report

0.9.5 supersedes 0.9.4 without changing its application or packaged-feature APIs. The only consumer
baseline change is stricter SDK selection: .NET SDK `10.0.202` must be installed and is selected
exactly. A machine with only another 10.0 patch now fails actionably instead of passing SDK resolution
and failing Program Kit's exact toolchain prerequisite later.

Consumers should upgrade directly to 0.9.5 and use runtime packages `0.9.5-preview.1`. The effective
shell-composition and explicit feature-disablement behavior documented for 0.9.4 is unchanged.
