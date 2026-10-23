#!/usr/bin/env node
// Render an HTML motion-graphics page to MP4, frame by frame, so timing is
// exact no matter how slow the machine is.
//
// The page must define:
//   window.renderFrame(t)   draws the frame at time t (seconds); may be async
//   window.DURATION         length in seconds (or pass --duration)
//
// Usage:
//   NODE_PATH=$(npm root -g) node render_html_video.cjs PAGE.html OUT.mp4 \
//     [--fps 30] [--width 1920] [--height 1080] [--duration 10] \
//     [--audio mix.wav] [--from 0] [--to 10] [--png] [--transparent]
//
// --from/--to render only part of the video (for quick checks of one scene).
// Frames are captured as JPEG at quality 95 (about 10x faster than PNG and
// visually lossless before the H.264 encode). Pass --png for a lossless master.
// --transparent keeps the page background see-through (set the page's
// html/body background to transparent) and writes a ProRes 4444 .mov with
// alpha, for laying graphics over footage with ffmpeg's overlay filter.
const { spawn, execSync } = require("child_process");
const path = require("path");

function loadPlaywright() {
  try {
    return require("playwright");
  } catch {
    const root = execSync("npm root -g").toString().trim();
    return require(path.join(root, "playwright"));
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
  const { chromium } = loadPlaywright();
  const launch = {};
  if (process.env.CHROMIUM_PATH) launch.executablePath = process.env.CHROMIUM_PATH;
  const browser = await chromium.launch(launch);
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  page.on("pageerror", (e) => console.error("page error:", e.message));
  await page.goto("file://" + o.page);
  await page.evaluate(() => document.fonts.ready);
  const hasRender = await page.evaluate(() => typeof window.renderFrame === "function");
  if (!hasRender) throw new Error("page does not define window.renderFrame(t)");
  const duration = Number(o.duration || (await page.evaluate(() => window.DURATION)));
  if (!duration) throw new Error("no duration: set window.DURATION or pass --duration");

  const from = Number(o.from || 0);
  const to = Math.min(Number(o.to || duration), duration);
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
  const ffDone = new Promise((res, rej) =>
    ff.on("close", (code) => (code === 0 ? res() : rej(new Error("ffmpeg exit " + code)))));

  for (let f = first; f < last; f++) {
    await page.evaluate((t) => window.renderFrame(t), f / fps);
    const img = await page.screenshot(
      o.transparent ? { type: "png", omitBackground: true }
        : o.png ? { type: "png" } : { type: "jpeg", quality: 95 });
    if (!ff.stdin.write(img)) await new Promise((r) => ff.stdin.once("drain", r));
    if ((f - first) % (fps * 5) === 0) {
      process.stderr.write(`frame ${f - first}/${last - first}\n`);
    }
  }
  ff.stdin.end();
  await ffDone;
  await browser.close();
  console.log(`wrote ${o.out} (${((last - first) / fps).toFixed(2)} s at ${fps} fps)`);
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
