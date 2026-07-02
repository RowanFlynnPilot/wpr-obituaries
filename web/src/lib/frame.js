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
    const height = document.documentElement.scrollHeight;
    if (height && height !== last) {
      last = height;
      window.parent.postMessage({ type: TYPE, height }, "*");
    }
  };

  if (window.ResizeObserver) {
    new ResizeObserver(post).observe(document.documentElement);
  }
  window.addEventListener("load", post);
  setInterval(post, 300);
  post();
}
