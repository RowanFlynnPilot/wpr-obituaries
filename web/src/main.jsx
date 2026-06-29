import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import config from "./config.js";
import "./index.css";

// Brand-distinct CSS variables come from the newsroom config. Set as inline
// styles on :root so they win over the defaults baked into index.css — no flash,
// no per-fork stylesheet edit.
const root = document.documentElement;
root.style.setProperty("--accent", config.branding.accent);
root.style.setProperty("--paper", config.branding.paper);

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
