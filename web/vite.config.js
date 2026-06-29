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
            .replace(/%PAPER%/g, escapeHtml(branding.paper));
        },
      },
    },
  ],
  define: {
    __NEWSROOM__: JSON.stringify(newsroom),
  },
  base: "/wpr-obituaries/",
});
