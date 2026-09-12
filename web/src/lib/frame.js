// Iframe ↔ parent messaging — the pieces that make the WordPress embed seamless.
//
// 1. Height. An iframe can't size itself to its content, so when the widget
//    runs embedded it posts its rendered height to the parent page. The embed
//    snippet (docs/embedding.md) listens and stretches the iframe, so the tool
//    never shows an inner scrollbar.
// 2. State. The register mirrors its search/filter into its own URL
//    (lib/urlState.js), but the reader sees the *parent* page's URL. Posting the
//    same search string lets the snippet mirror it there too, so a shared or
//    bookmarked WordPress URL reopens the same list.
//
// Standalone (not embedded), both are no-ops.

const HEIGHT = "wpr-obituaries:height";
const STATE = "wpr-obituaries:state";

const embedded = () => window.parent !== window;

// We post on a ResizeObserver AND a short interval: the observer catches most
// layout changes, and the interval is the reliable safety net for async growth
// (fonts, lazy images, late renders) and environments where the observer is
// flaky. It only posts when the height actually changes, so it's near-free.
export function reportHeightToParent() {
  if (!embedded()) return;

  let last = 0;
  const post = () => {
    // Measure the body's laid-out height, NOT documentElement.scrollHeight:
    // scrollHeight is floored at the viewport, and the parent stretches the
    // iframe's viewport to whatever we last posted — so heights could only
    // ever ratchet up. body.offsetHeight shrinks back when a filter narrows
    // the register, letting the frame shrink with it.
    const height = Math.ceil(document.body.offsetHeight);
    if (height && height !== last) {
      last = height;
      window.parent.postMessage({ type: HEIGHT, height }, "*");
    }
  };

  if (window.ResizeObserver) {
    new ResizeObserver(post).observe(document.body);
  }
  window.addEventListener("load", post);
  setInterval(post, 300);
  post();
}

// `search` is the widget's own query string ("" for the default view).
export function reportStateToParent(search) {
  if (!embedded()) return;
  window.parent.postMessage({ type: STATE, search }, "*");
}
