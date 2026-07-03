# Embedding the obituaries tool on wausaupilotandreview.com

Two embeds ship from the same deploy:

1. **The full tool** — the searchable register, for a dedicated page (like the
   Brewers page). Auto-sizes to its content, so no inner scrollbar.
2. **The mini widget** — a compact card that flips through ~10 recent
   obituaries in a random order on each load, with the sponsor logos and a
   "View all obituaries" link. For article bodies or the sidebar.

Both go into a WordPress **Custom HTML** block (the block editor's `/html`
block — script tags are allowed for admin/editor users, same as the existing
gas-prices widget). A live preview of both, exactly as embedded, is at
`<tool-url>/embed-test.html`.

> The tool is served from `https://obituaries.wausaupilotandreview.com/` (the
> brand subdomain). The snippets below point there.

## 1 — Full tool (dedicated page)

```html
<!-- Wausau Pilot & Review — Obituaries -->
<iframe id="wpr-obits-embed"
        src="https://obituaries.wausaupilotandreview.com/"
        title="Wausau area obituaries"
        style="display:block;width:100%;border:0;min-height:800px"
        loading="lazy"></iframe>
<script>
  (function () {
    var frame = document.getElementById("wpr-obits-embed");
    window.addEventListener("message", function (e) {
      if (
        frame && e.source === frame.contentWindow &&
        e.data && e.data.type === "wpr-obituaries:height"
      ) {
        frame.style.height = e.data.height + "px";
        frame.style.minHeight = "0";
      }
    });
  })();
</script>
```

How it works: the widget posts its rendered height to the page whenever its
layout changes (`web/src/lib/frame.js`), and this script stretches the iframe to
match — so the tool reads as part of the page, never a scrollbox. The
`e.source` check ties the listener to this exact iframe, so it keeps working
unchanged when the tool moves to the custom subdomain.

## 2 — Mini widget (articles / sidebar)

```html
<!-- Wausau Pilot & Review — Recent obituaries (mini) -->
<iframe id="wpr-obits-mini"
        src="https://obituaries.wausaupilotandreview.com/mini.html?link=https%3A%2F%2Fwausaupilotandreview.com%2Fobituaries%2F"
        title="Recent obituaries"
        style="display:block;width:100%;max-width:380px;margin:0 auto;border:0;min-height:340px"
        loading="lazy"></iframe>
<script>
  (function () {
    var frame = document.getElementById("wpr-obits-mini");
    window.addEventListener("message", function (e) {
      if (
        frame && e.source === frame.contentWindow &&
        e.data && e.data.type === "wpr-obituaries:height"
      ) {
        frame.style.height = e.data.height + "px";
        frame.style.minHeight = "0";
      }
    });
  })();
</script>
```

The `?link=` value is the URL-encoded address of the full-tool page —
`https://wausaupilotandreview.com/obituaries/` encodes to
`https%3A%2F%2Fwausaupilotandreview.com%2Fobituaries%2F` (already filled in
above). That's where the widget's "View all obituaries →" link sends readers.
To point it somewhere else, re-encode the new URL and swap it in; drop the
`?link=…` entirely and the link falls back to the tool's own register.

Details: shows 10 of the 20 most recent obituaries, shuffled per page load;
auto-advances every 6 s (pauses on hover); each person links to their full
obituary page (`target="_top"`, so it opens as a normal navigation, not inside
the frame); sponsor logos and click tracking match the main tool.

## Notes

- Both snippets are per-iframe (the listener is bound to its own frame by id +
  `e.source`), so the mini widget can appear on many pages, and both embeds can
  even share one page.
- If a page's CSP or a security plugin strips scripts, the iframes still render
  at their `min-height` fallback — functional, just not perfectly sized.
- The mini widget's `max-width: 380px` matches its internal card width; drop the
  `max-width`/`margin` styles to let a sidebar theme control width instead.
