import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base must match where the site is served. For a GitHub Pages project site
// that is "/<repo>/". If you point a custom subdomain at Pages, change to "/".
export default defineConfig({
  plugins: [react()],
  base: "/wpr-obituaries/",
});
