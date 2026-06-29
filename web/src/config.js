/* The per-newsroom config, injected at build time from ../../newsroom.config.json
   (see vite.config.js). One source of truth for identity, branding, and copy,
   shared with the Python render side so the widget and the static pages stay in
   visual lockstep. */
/* global __NEWSROOM__ */
const config = __NEWSROOM__;

export default config;
