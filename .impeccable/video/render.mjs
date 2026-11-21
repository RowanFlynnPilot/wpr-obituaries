// Render walkthrough.html: headless Edge over the DevTools protocol seeks the composition frame by frame
// (window.seek(t) sets every style from t alone) and pipes each frame to ffmpeg as H.264.
//   node render.mjs stills <outdir> 3,10.5,18     PNG stills at those times, to look at before rendering
//   node render.mjs video  <out.mp4>              all frames, 1080x1920 at 30 fps
import { spawn } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const [mode, out, times] = process.argv.slice(2);
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const PORT = 9335;
const W = 1080, H = 1920;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const edge = spawn(EDGE, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'edge-video-'))}`,
  `--window-size=${W},${H}`, 'about:blank'], { stdio: 'ignore' });

async function pageSocket() {
  for (let i = 0; i < 60; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      const page = list.find((t) => t.type === 'page');
      if (page) return page.webSocketDebuggerUrl;
    } catch { /* not up yet */ }
    await sleep(200);
  }
  throw new Error('Edge did not start');
}

const ws = new WebSocket(await pageSocket());
await new Promise((r) => ws.addEventListener('open', r, { once: true }));
let nextId = 0;
const pending = new Map();
const seen = new Set();
ws.addEventListener('message', (m) => {
  const msg = JSON.parse(m.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  else if (msg.method) seen.add(msg.method);
});
const send = (method, params = {}) => new Promise((r) => { const id = ++nextId; pending.set(id, r); ws.send(JSON.stringify({ id, method, params })); });
async function evaluate(expression) {
  const res = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (res.result?.exceptionDetails) throw new Error(JSON.stringify(res.result.exceptionDetails).slice(0, 600));
  return res.result?.result?.value;
}
async function shot(format) {
  const res = await send('Page.captureScreenshot', { format, quality: format === 'jpeg' ? 94 : undefined, clip: { x: 0, y: 0, width: W, height: H, scale: 1 } });
  return Buffer.from(res.result.data, 'base64');
}

await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url: pathToFileURL(join(HERE, 'walkthrough.html')).href });
for (let i = 0; i < 300 && !seen.has('Page.loadEventFired'); i++) await sleep(100);
const info = await evaluate('window.ready');
console.log('ready', JSON.stringify(info));

try {
  if (mode === 'stills') {
    mkdirSync(out, { recursive: true });
    for (const t of times.split(',').map(Number)) {
      await evaluate(`seek(${t})`);
      writeFileSync(join(out, `t${String(t).replace('.', '_')}.png`), await shot('png'));
      console.log('still', t);
    }
  } else {
    const frames = info.frames;
    // Lossless PNG frames in, standard video out: BT.709, limited range, 4:2:0, so every phone shows the brand teal right.
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(info.fps), '-c:v', 'png', '-i', '-',
      '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-profile:v', 'high', '-level', '4.2',
      '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
      '-movflags', '+faststart', resolve(out)], { stdio: ['pipe', 'inherit', 'inherit'] });
    const started = Date.now();
    for (let f = 0; f < frames; f++) {
      await evaluate(`seek(${(f / info.fps).toFixed(5)})`);
      const buf = await shot('png');
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
      if (f % 150 === 0) console.log(`frame ${f}/${frames}  ${((Date.now() - started) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end();
    const code = await new Promise((r) => ff.on('close', r));
    console.log('ffmpeg exit', code, 'in', ((Date.now() - started) / 1000).toFixed(0), 's');
  }
} finally {
  ws.close();
  edge.kill();
}
process.exit(0);
