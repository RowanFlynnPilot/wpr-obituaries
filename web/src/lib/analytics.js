import config from "../config.js";

const A = config.analytics || {};

// Provider-agnostic custom event (e.g. a sponsor click). Dispatches to whichever
// analytics global the configured provider loaded; a no-op if none is present.
// Mirrors trackEvent in extract/analytics.py so both surfaces report the same way.
export function trackEvent(name, props) {
  if (!A.provider) return;
  try {
    if (window.plausible) {
      window.plausible(name, { props: props || {} });
    } else if (window.goatcounter && window.goatcounter.count) {
      window.goatcounter.count({ path: "event-" + name, title: name, event: true });
    }
  } catch (e) {
    /* analytics must never break the page */
  }
}
