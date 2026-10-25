#!/usr/bin/env node
// Render an HTML motion-graphics page to MP4, frame by frame, so timing is
// exact no matter how slow the machine is.
//
// The page must define:
//   window.renderFrame(t)   draws the frame at time t (seconds); may be async
//   window.DURATION         length in seconds (or pass --duration)
//
// Usage:
//   node render_html_video.cjs PAGE.html OUT.mp4 \
//     [--fps 30] [--width 1920] [--height 1080] [--duration 10] \
//     [--audio mix.wav] [--from 0] [--to 10] [--png] [--transparent]
//     [--chromium PATH]   (a Chromium to use instead of Playwright's own)
//
// --from/--to render only part of the video (for quick checks of one scene).
// Frames are captured as JPEG at quality 95 (about 10x faster than PNG and
// visually lossless before the H.264 encode). Pass --png for a lossless master.
// --transparent keeps the page background see-through (set the page's
// html/body background to transparent) and writes a ProRes 4444 .mov with
// alpha, for laying graphics over footage with ffmpeg's overlay filter.
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");

function loadPlaywright() {
  try {
    return require("playwright");
  } catch {
    // Not installed next to the script: try the global npm folder of this Node.js.
    const bin = path.dirname(process.execPath);
    for (const dir of [path.join(bin, "..", "lib", "node_modules"), path.join(bin, "node_modules")]) {
      try {
        return require(path.join(dir, "playwright"));
      } catch {}
    }
    throw new Error("Playwright isn't installed: run npm install -g playwright, then npx playwright install chromium");
  }
}

function parseArgs(argv) {
  const opts = { fps: 30, width: 1920, height: 1080 };
  const pos = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--png" || argv[i] === "--transparent") opts[argv[i].slice(2)] = true;
    else if (argv[i].startsWith("--")) opts[argv[i].slice(2)] = argv[++i];
    else pos.push(argv[i]);
  }
  if (pos.length !== 2) {
    console.error("usage: render_html_video.cjs PAGE.html OUT.mp4 [options]");
    process.exit(2);
  }
  return { page: path.resolve(pos[0]), out: path.resolve(pos[1]), ...opts };
}

async function main() {
  const o = parseArgs(process.argv.slice(2));
  const fps = Number(o.fps), width = Number(o.width), height = Number(o.height);
  if (!fs.existsSync(o.page)) fail(`page not found: ${o.page}`);
  for (const [name, v] of [["fps", fps], ["width", width], ["height", height]]) {
    if (!Number.isInteger(v) || v <= 0) fail(`--${name} must be a whole number above 0, not ${o[name]}`);
  }
  // H.264 in yuv420p only takes even sizes; say so instead of failing inside ffmpeg.
  if (!o.transparent && (width % 2 || height % 2)) {
    fail(`--width and --height must be even for MP4 (got ${width}x${height}); try ${width + (width % 2)}x${height + (height % 2)}`);
  }
  if (o.audio && !fs.existsSync(path.resolve(o.audio))) fail(`audio not found: ${o.audio}`);
  fs.mkdirSync(path.dirname(o.out), { recursive: true });
  const { chromium } = loadPlaywright();
  const launch = {};
  if (o.chromium) launch.executablePath = o.chromium;
  const browser = await chromium.launch(launch);
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  page.on("pageerror", (e) => console.error("page error:", e.message));
  await page.goto(pathToFileURL(o.page).href);  // "file://" + path breaks on Windows
  await page.evaluate(() => document.fonts.ready);
  const hasRender = await page.evaluate(() => typeof window.renderFrame === "function");
  if (!hasRender) throw new Error("page does not define window.renderFrame(t)");
  const duration = Number(o.duration || (await page.evaluate(() => window.DURATION)));
  if (!duration) throw new Error("no duration: set window.DURATION or pass --duration");

  const from = Number(o.from || 0);
  const to = Math.min(Number(o.to || duration), duration);
  if (!(from >= 0) || !(to > from)) fail(`--from must be at least 0 and before --to (got ${o.from || 0} to ${to})`);
  const first = Math.round(from * fps);
  const last = Math.round(to * fps);

  const args = ["-hide_banner", "-loglevel", "error", "-y",
    "-f", "image2pipe", "-framerate", String(fps), "-i", "-"];
  if (o.audio) args.push("-ss", String(from), "-t", String(to - from), "-i", path.resolve(o.audio));
  if (o.transparent) {
    args.push("-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
      "-r", String(fps));
    if (o.audio) args.push("-c:a", "pcm_s16le", "-shortest");
    args.push(o.out);
  } else {
    args.push("-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
      "-r", String(fps));
    if (o.audio) args.push("-c:a", "aac", "-b:a", "192k", "-shortest");
    args.push("-movflags", "+faststart", o.out);
  }
  const ff = spawn("ffmpeg", args, { stdio: ["pipe", "inherit", "inherit"] });
  const ffDone = new Promise((res, rej) => {
    ff.on("error", (e) => rej(e.code === "ENOENT"
      ? new Error("ffmpeg isn't installed: install it (Mac: brew install ffmpeg; Windows: winget install ffmpeg; Linux: apt install ffmpeg)")
      : e));
    ff.on("close", (code) => (code === 0 ? res() : rej(new Error("ffmpeg exit " + code))));
  });
  let ffExited = false;
  ffDone.catch(() => {}).finally(() => { ffExited = true; });  // reported where it is awaited
  ff.stdin.on("error", () => {});  // ffmpeg quitting early surfaces through ffDone

  for (let f = first; f < last; f++) {
    await page.evaluate((t) => window.renderFrame(t), f / fps);
    const img = await page.screenshot(
      o.transparent ? { type: "png", omitBackground: true }
        : o.png ? { type: "png" } : { type: "jpeg", quality: 95 });
    if (ffExited) break;  // ffmpeg stopped early: its error is reported below
    if (!ff.stdin.write(img)) {
      await Promise.race([new Promise((r) => ff.stdin.once("drain", r)), ffDone.catch(() => {})]);
    }
    if ((f - first) % (fps * 5) === 0) {
      process.stderr.write(`frame ${f - first}/${last - first}\n`);
    }
  }
  ff.stdin.end();
  await ffDone;
  await browser.close();
  console.log(`wrote ${o.out} (${((last - first) / fps).toFixed(2)} s at ${fps} fps)`);
}

function fail(msg) {
  console.error(msg);
  process.exit(2);
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
