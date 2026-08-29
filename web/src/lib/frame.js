// Iframe height reporting — the piece that makes the WordPress embed seamless.
//
// An iframe can't size itself to its content, so when the widget runs embedded
// it posts its rendered height to the parent page. The embed snippet
// (docs/embedding.md) listens and stretches the iframe, so the tool never shows
// an inner scrollbar. Standalone (not embedded), this is a no-op.
//
// We post on a ResizeObserver AND a short interval: the observer catches most
// layout changes, and the interval is the reliable safety net for async growth
// (fonts, lazy images, late renders) and environments where the observer is
// flaky. It only posts when the height actually changes, so it's near-free.

const TYPE = "wpr-obituaries:height";

export function reportHeightToParent() {
  if (window.parent === window) return; // not embedded

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
      window.parent.postMessage({ type: TYPE, height }, "*");
    }
  };

  if (window.ResizeObserver) {
    new ResizeObserver(post).observe(document.body);
  }
  window.addEventListener("load", post);
  setInterval(post, 300);
  post();
}
