import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import config from "./config.js";
import { reportHeightToParent } from "./lib/frame.js";
import "./index.css";

// Brand-distinct CSS variables come from the newsroom config. Set as inline
// styles on :root so they win over the defaults baked into index.css — no flash,
// no per-fork stylesheet edit.
const root = document.documentElement;
root.style.setProperty("--accent", config.branding.accent);
root.style.setProperty("--paper", config.branding.paper);

// When embedded on the newsroom's WordPress site, keep the iframe sized to the
// content (see docs/embedding.md for the matching snippet).
reportHeightToParent();

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
