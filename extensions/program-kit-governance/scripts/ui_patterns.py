"""Presentation patterns and identity state templates; never authentication or domain authority."""
from __future__ import annotations

from ui_content import esc

AUTH_STATES = {
    "login": ("Sign in", "Sign in to continue.", "provider-form"),
    "login-success": ("You’re signed in", "Continue to your application.", "continue-action"),
    "login-error": ("We couldn’t sign you in", "Review the sign-in message and follow the available recovery action.", "provider-error-and-form"),
    "session-expired": ("Your session has expired", "Sign in again to continue.", "sign-in-action"),
    "logout-confirmation": ("Sign out?", "Your application session will end. Review any unsaved work before continuing.", "logout-form-and-cancel"),
    "logout-progress": ("Signing out…", "Wait while your application ends the session.", "logout-status"),
    "logout-success": ("You’re signed out", "The sign-out steps required by this application have completed.", "sign-in-action"),
    "logout-error": ("Application session ended", "Sign-out from the sign-in service could not be confirmed. Your session in this application has ended.", "provider-recovery-action"),
}


def field(identity: str, label: str, hint: str = "", value: str = "") -> str:
    """A complete field; adapters own validation rules and error presentation timing."""
    description = f'{identity}-hint ' if hint else ''
    hint_html = f'<p id="{esc(identity)}-hint" class="pk-hint">{esc(hint)}</p>' if hint else ''
    return f'''<div class="pk-field"><label for="{esc(identity)}">{esc(label)}</label>
{hint_html}<input id="{esc(identity)}" name="{esc(identity)}" value="{esc(value)}" aria-describedby="{esc(description)}{esc(identity)}-error">
<p id="{esc(identity)}-error" class="pk-error" hidden></p></div>'''


def form_pattern(demo: bool = False) -> str:
    demo_attribute = ' data-pk-demo-form' if demo else ''
    return f'''<form class="pk-stack" data-pk-form{demo_attribute} novalidate>
<section data-pk-error-summary class="pk-error-summary" tabindex="-1" aria-label="Check your answers" hidden><h3>Check your answers</h3><ul></ul></section>
{field('example-name', 'Name', 'Enter the name people will use to identify this item.')}
{field('example-description', 'Description (optional)', 'Add context if it helps people distinguish this item.')}
<button type="submit">Save example</button>
<p data-pk-operation-status role="status" aria-live="polite" aria-atomic="true"></p>
</form>'''


def list_detail() -> str:
    return '''<div class="pk-list-detail"><section aria-labelledby="items-title"><h2 id="items-title">Items</h2>
<ul class="pk-item-list"><li><a href="#item-detail" aria-current="true">Example item</a></li></ul></section>
<section id="item-detail" class="pk-detail" aria-labelledby="detail-title"><h2 id="detail-title">Example item</h2>
<p>Review the selected item’s details and available actions.</p><!-- Consumer adapter owns selection, back navigation and retained state. --></section></div>'''


def feedback_patterns() -> str:
    return '''<div class="pk-stack">
<section class="pk-panel" aria-label="Loading example" aria-busy="true"><p role="status">Loading items…</p><div class="pk-skeleton" aria-hidden="true"></div></section>
<section class="pk-panel"><h3>No items yet</h3><p>Use the available create action to add the first item.</p></section>
<section class="pk-status pk-status-error"><h3>Could not load items</h3><p>We couldn’t load your items. Use the available recovery action to continue.</p></section>
<section class="pk-status pk-status-warning"><h3>Save result unknown</h3><p>We couldn’t confirm whether the change was saved. Check its status before trying again.</p></section>
<section class="pk-status pk-status-warning"><h3>This item changed</h3><p>Review the latest version before deciding what to do with your draft.</p></section>
</div>'''


def auth_document(profile: dict, state: str) -> str:
    title, message, slot = AUTH_STATES[state]
    brand = esc(profile['brand']['name'])
    logo = profile['brand'].get('logo')
    if logo:
        brand = f'<img class="pk-auth-logo" src="{esc(logo.get("url", "/assets/brand-logo.svg"))}" alt="{esc(logo["alt"])}">'
    # Slots are inert by design. No action URL, credential handling or completion is invented.
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{esc(title)} · {esc(profile['brand']['name'])}</title>
<link rel="stylesheet" href="/assets/tokens.css"><link rel="stylesheet" href="/assets/layout.css"></head>
<body data-presentation="{profile.get('presentation', 'classic-v1')}" class="pk-auth-page" data-auth-state="{state}">
<main class="pk-auth-shell"><div class="pk-auth-brand">{brand}</div><section class="pk-auth-card" aria-labelledby="auth-title">
<h1 id="auth-title">{esc(title)}</h1><p>{esc(message)}</p><div data-pk-slot="{slot}"><!-- Bind the verified identity state and provider/application-owned controls here. --></div>
</section></main></body></html>'''


def auth_contract() -> dict:
    return {'version': 'auth-presentation-v1', 'states': list(AUTH_STATES),
            'templatesAre': 'presentation only; consumer adapters bind verified state, localized copy and controls',
            'providerOwned': ['credentials', 'MFA', 'provider errors', 'provider logout confirmation', 'required actions'],
            'applicationOwned': ['validated callback success/error', 'session expired', 'local logout', 'post-logout result'],
            'logoutErrorPrecondition': 'local session ended; provider sign-out unconfirmed',
            'completion': 'logout-success only after the selected logout scope has been established',
            'security': ['existing validated redirect targets', 'antiforgery-protected logout where required',
                         'no credentials, tokens or personal data in templates/public exports',
                         'no local-session restoration after provider logout failure'],
            'providerAcceptance': 'required against the selected provider/version; templates and fixtures do not establish it'}
