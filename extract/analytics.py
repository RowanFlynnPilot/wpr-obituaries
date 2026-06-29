"""Privacy-first analytics snippets for the static pages.

Config-driven (`analytics` in newsroom.config.json) so each newsroom drops in its
own account. Pageviews give two things at once: proof-of-traffic for the
newsroom, and **sponsor impressions** (every page shows the sponsor, so an
impression *is* a pageview). Sponsor *clicks* are tracked as custom events via
`trackEvent`, which the sponsor links call.

Supported providers (all cookieless, no consent banner needed):
- "plausible"   — needs `domain`
- "goatcounter" — needs `site` (the <code> in <code>.goatcounter.com)
- "cloudflare"  — needs `site` (the beacon token); pageviews only, no events
- "custom"      — `headHtml` injected verbatim (any other provider)
- "" / absent   — disabled (renders nothing)

Event tracking (sponsor clicks) works with plausible and goatcounter; cloudflare
and most custom setups record pageviews only.
"""

from __future__ import annotations

import html


def _enabled(analytics: dict) -> bool:
    return bool((analytics or {}).get("provider"))


def head_snippet(analytics: dict) -> str:
    """The provider's loader script(s) for <head>. Empty when disabled."""
    if not _enabled(analytics):
        return ""
    provider = analytics["provider"]
    domain = html.escape(analytics.get("domain", ""), quote=True)
    site = html.escape(analytics.get("site", ""), quote=True)
    if provider == "plausible":
        return (
            f'<script defer data-domain="{domain}" src="https://plausible.io/js/script.js"></script>\n'
            "  <script>window.plausible=window.plausible||function(){"
            "(window.plausible.q=window.plausible.q||[]).push(arguments)}</script>"
        )
    if provider == "goatcounter":
        return (
            f'<script data-goatcounter="https://{site}.goatcounter.com/count" '
            'async src="//gc.zgo.at/count.js"></script>'
        )
    if provider == "cloudflare":
        return (
            '<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
            f"data-cf-beacon='{{\"token\": \"{site}\"}}'></script>"
        )
    if provider == "custom":
        return analytics.get("headHtml", "")
    return ""


def event_script(analytics: dict) -> str:
    """A <script> defining trackEvent + a delegated [data-track-event] listener.

    Empty when disabled. trackEvent dispatches to whichever provider global is
    present, so it is provider-agnostic and a no-op if none loaded.
    """
    if not _enabled(analytics):
        return ""
    return """<script>
    function trackEvent(name, props) {
      try {
        if (window.plausible) { window.plausible(name, { props: props || {} }); }
        else if (window.goatcounter && window.goatcounter.count) {
          window.goatcounter.count({ path: 'event-' + name, title: name, event: true });
        }
      } catch (e) {}
    }
    document.addEventListener('click', function (e) {
      var el = e.target.closest && e.target.closest('[data-track-event]');
      if (el) trackEvent(el.getAttribute('data-track-event'),
        { label: el.getAttribute('data-track-label') || '' });
    });
  </script>"""


def sponsor_track_attrs(analytics: dict, sponsor_name: str) -> str:
    """data-* attributes that mark a sponsor link for click tracking.

    Empty when disabled, so the rendered markup is unchanged for newsrooms
    without analytics.
    """
    if not _enabled(analytics):
        return ""
    return f' data-track-event="Sponsor click" data-track-label="{html.escape(sponsor_name, quote=True)}"'
