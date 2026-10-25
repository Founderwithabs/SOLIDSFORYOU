#!/usr/bin/env node
// Render an HTML design (infographic, comparison chart, A+ module, size chart)
// to a PNG or JPEG at an exact pixel size.
//
// Usage:
//   node render_image.cjs PAGE.html OUT.png [--width 2000] [--height 2000]
//     [--quality 92]   (JPEG only; the format follows OUT's extension)
//     [--chromium PATH] (a Chromium to use instead of Playwright's own)
//
// Images and fonts the page uses must be local files or data URLs. The page
// can set window.READY = false while it loads and true when done; the
// renderer waits for it (up to 15 s), and for fonts and images to load.
const fs = require("fs");
const path = require("path");

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

async function main() {
  const args = process.argv.slice(2);
  const str = (name) => {
    const i = args.indexOf(`--${name}`);
    return i >= 0 ? args[i + 1] : undefined;
  };
  const opt = (name, dflt) => {
    const i = args.indexOf(`--${name}`);
    return i >= 0 ? Number(args[i + 1]) : dflt;
  };
  const pos = args.filter((a, i) => !a.startsWith("--") && !(args[i - 1] || "").startsWith("--"));
  if (pos.length !== 2) {
    console.error("usage: render_image.cjs PAGE.html OUT.png [--width 2000] [--height 2000] [--quality 92] [--chromium PATH]");
    process.exit(2);
  }
  const [page, out] = pos.map((p) => path.resolve(p));
  const width = opt("width", 2000), height = opt("height", 2000);
  const fail = (msg) => { console.error(msg); process.exit(2); };
  if (!fs.existsSync(page)) fail(`page not found: ${page}`);
  for (const [name, v] of [["width", width], ["height", height]]) {
    if (!Number.isInteger(v) || v <= 0) fail(`--${name} must be a whole number of pixels above 0`);
  }
  if (!/\.(png|jpe?g)$/i.test(out)) fail(`${out}: save as .png or .jpg`);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch(
    str("chromium") ? { executablePath: str("chromium") } : {});
  const tab = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  const errors = [];
  tab.on("pageerror", (e) => errors.push(e.message));
  tab.on("requestfailed", (r) => errors.push(`failed to load ${r.url()}`));
  await tab.goto("file://" + page, { waitUntil: "load" });
  await tab.evaluate(() => document.fonts.ready);
  await tab.waitForFunction(() => window.READY !== false, null, { timeout: 15000 }).catch(() => {
    errors.push("window.READY never became true");
  });
  await tab.waitForFunction(() => [...document.images].every((i) => i.complete), null, { timeout: 15000 })
    .catch(() => errors.push("some images did not finish loading"));
  const jpeg = /\.jpe?g$/i.test(out);
  await tab.screenshot({ path: out, type: jpeg ? "jpeg" : "png",
    ...(jpeg ? { quality: opt("quality", 92) } : {}), clip: { x: 0, y: 0, width, height } });
  await browser.close();
  for (const e of errors) console.error("warning:", e);
  console.log(`wrote ${out} (${width}x${height})`);
}

main().catch((e) => { console.error(e.message); process.exit(1); });
