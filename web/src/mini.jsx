// Miniature obituaries widget — the article/sidebar embed.
//
// A compact card that flips through ~10 of the most recent obituaries in a
// random order on each load, carries the sponsor logos, and links back to the
// full obituaries page. Built as a second entry of the same Vite app so it
// deploys with the main widget and reads the same index + sponsor data.
//
// The "view all" link target comes from the iframe's `?link=` query param so
// the newsroom can point it at the WordPress page hosting the full tool without
// a rebuild; until that page exists it falls back to this deployment's root.

import React from "react";
import { createRoot } from "react-dom/client";
import config from "./config.js";
import MiniWidget from "./components/MiniWidget.jsx";
import { reportHeightToParent } from "./lib/frame.js";
import "./index.css";
import "./mini.css";

const root = document.documentElement;
root.style.setProperty("--accent", config.branding.accent);
root.style.setProperty("--paper", config.branding.paper);

reportHeightToParent();

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <MiniWidget />
  </React.StrictMode>
);
