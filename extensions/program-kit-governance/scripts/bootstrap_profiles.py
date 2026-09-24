"""Profile dependencies from secure-web-profiles.md; never mutate intake authority."""
from __future__ import annotations

from copy import deepcopy


AUTHENTICATED_PROFILES = {
    "bff-cookie-v1": "authenticated-browser-bff",
    "spa-pkce-v1": "browser-spa-pkce",
}


def validate_profile_dependencies(decisions: dict) -> None:
    selected = decisions.get("selected_profiles", [])
    if not isinstance(selected, list) or any(not isinstance(item, str) for item in selected):
        raise ValueError("Bootstrap selected_profiles must be a list of strings")
    profiles = {item.casefold() for item in selected}
    web = decisions.get("web", {})
    if not isinstance(web, dict):
        return  # Full schema/governance validation owns malformed values.
    if web.get("browser_ui") is True and not profiles.intersection({"browser-web", "typescript-web"}):
        raise ValueError("web.browser_ui true requires browser-web or typescript-web in selected_profiles; ui-experience-v1 alone does not select the browser boundary")
    if web.get("secure_profile") in AUTHENTICATED_PROFILES and "dotnet" not in profiles:
        raise ValueError("Managed authenticated web profiles require dotnet in selected_profiles and its host/dependency disclosure before assessment approval; an undecided backend cannot adopt Foundation sign-in")
    if "dotnet" in profiles and not isinstance(decisions.get("dotnet"), dict):
        raise ValueError("A selected .NET profile requires a dotnet decision block before research")


def effective_stage_intake(intake: dict, decisions: dict) -> dict:
    """Route adopted profiles, not prose recommendations, without rewriting confirmed facts."""
    result = deepcopy(intake)
    routing = result["routing"]
    capabilities = set(routing["capabilities"])
    profiles = {item.casefold() for item in decisions.get("selected_profiles", [])}
    web = decisions.get("web", {})
    if isinstance(web, dict) and "secure_profile" in web:
        capabilities.difference_update(AUTHENTICATED_PROFILES.values())
        capability = AUTHENTICATED_PROFILES.get(web["secure_profile"])
        if capability:
            capabilities.add(capability)
    if "dotnet" in profiles:
        routing["languages"] = sorted(set(routing["languages"]) | {".NET"})
        host = decisions.get("dotnet", {})
        if host.get("program_kit_host_opt_out") is True:
            capabilities.discard("dotnet-host-runtime")
        elif host.get("host_runtime") == "Orbyss.Foundation.Host":
            capabilities.add("dotnet-host-runtime")
    routing["capabilities"] = sorted(capabilities)
    return result
