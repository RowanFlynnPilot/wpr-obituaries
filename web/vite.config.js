import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "node:fs";

// The one per-newsroom config, shared with the Python render side. Read at build
// time so identity/branding reach both the bundled JS (via `define`) and the
// static index.html (via the transform below) with no runtime fetch or flash.
const newsroom = JSON.parse(
  readFileSync(new URL("../newsroom.config.json", import.meta.url), "utf-8")
);

const escapeHtml = (s) =>
  String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

// Privacy-first analytics loader for <head>, mirroring extract/analytics.py so the
// widget and the static pages report to the same account. Empty when disabled.
function analyticsHead(a) {
  if (!a || !a.provider) return "";
  if (a.provider === "plausible")
    return (
      `<script defer data-domain="${escapeHtml(a.domain || "")}" src="https://plausible.io/js/script.js"></script>\n` +
      `    <script>window.plausible=window.plausible||function(){(window.plausible.q=window.plausible.q||[]).push(arguments)}</script>`
    );
  if (a.provider === "goatcounter")
    return `<script data-goatcounter="https://${escapeHtml(a.site || "")}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>`;
  if (a.provider === "cloudflare")
    return `<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{"token": "${escapeHtml(a.site || "")}"}'></script>`;
  if (a.provider === "custom") return a.headHtml || "";
  return "";
}

// base must match where the site is served. For a GitHub Pages project site
// that is "/<repo>/". If you point a custom subdomain at Pages, change to "/".
export default defineConfig({
  plugins: [
    react(),
    {
      name: "newsroom-index-html",
      // `pre` so the placeholders (esp. %FONTS_URL% inside an href) are replaced
      // before Vite's HTML pass runs decodeURI on URL attributes — a raw
      // "%FO..." reads as a malformed percent-escape and fails the build.
      transformIndexHtml: {
        order: "pre",
        handler(html) {
          const { identity, branding } = newsroom;
          return html
            .replace(/%NEWSROOM_NAME%/g, escapeHtml(identity.name))
            .replace(/%NEWSROOM_SHORT%/g, escapeHtml(identity.shortName))
            .replace(/%FONTS_URL%/g, escapeHtml(branding.fontsUrl))
            .replace(/%PAPER%/g, escapeHtml(branding.paper))
            .replace(/%ANALYTICS_HEAD%/g, analyticsHead(newsroom.analytics));
        },
      },
    },
  ],
  define: {
    __NEWSROOM__: JSON.stringify(newsroom),
  },
  base: "/wpr-obituaries/",
});
