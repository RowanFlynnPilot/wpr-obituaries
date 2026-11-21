# The walkthrough video

A 62-second, 1080x1920 walkthrough of the obituaries tool, made from the tool's
own screens. `walkthrough.src.html` is the composition: every frame is a pure
function of time (`seek(t)`), so a headless browser can step through it.

Rebuild, from the repo root, after `python extract/main.py --render-only` and
`npm --prefix web run build`:

```bash
python .impeccable/video/capture.py      # screens from web/dist -> shots/ + shots/layout.json
python .impeccable/video/build.py        # walkthrough.src.html + layout -> walkthrough.html
cd .impeccable/video
node render.mjs video WPR-Obituaries-walkthrough-silent.mp4   # about 3 minutes
ffmpeg -y -i WPR-Obituaries-walkthrough-silent.mp4 -vf "scale=720:1280:flags=lanczos,format=yuv420p" \
  -c:v libx264 -preset slow -crf 29 -movflags +faststart WPR-Obituaries-walkthrough-silent-for-text.mp4
python mix.py                            # adds audio/music.mp3 + page turns -> the scored copies
```

Needs Node 22+, Edge, ffmpeg and Python Playwright. `node render.mjs stills
_stills 8,26,40` renders single frames to check before a full render.

- `capture.py` pins the clock (`NOW`) and names the people the video features
  (`TYPED`, `QUERY`, `PERSON`). The screens show real published notices: move
  `NOW` forward and re-check who appears before re-rendering.
- `audio/music.mp3` and the page-turn takes were generated for this video; they
  are committed because regenerating them costs credits and would not match.
- `walkthrough-v1.src.html` is the first cut (silent, 60 s), kept for reference.
