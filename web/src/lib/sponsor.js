import config from "../config.js";

// 'https://www.wausaupilotandreview.com' -> 'wausaupilotandreview' (mirrors
// extract/templates.py so the static pages and the widget report identically).
const host = new URL(config.identity.url).hostname.replace(/^www\./, "");
const SOURCE = host.includes(".") ? host.slice(0, host.lastIndexOf(".")) : host;

// UTM-tag a paid link so click-through reports per placement — the fleet's
// sponsorship convention. A malformed sponsor URL throws: it is a config error
// the Python render already refuses, so it never reaches a live build.
export function sponsorHref(url) {
  const u = new URL(url);
  u.searchParams.set("utm_source", SOURCE);
  u.searchParams.set("utm_medium", "widget");
  u.searchParams.set("utm_campaign", "obituaries");
  return u.toString();
}
