#!/usr/bin/env node
// Open a public web page in a real browser and save what a researcher needs:
// the visible text, structured product data, key meta tags, a screenshot, and
// hints for common marketplace fields. It does not log in, solve captchas or
// get around blocks: if a page is blocked it says so.
//
// Usage:
//   node fetch_page.cjs URL OUT_DIR [--full] [--wait 2500]
//
// Writes OUT_DIR/text.txt, OUT_DIR/meta.json and OUT_DIR/screenshot.png
// (--full captures the whole page). Hints in meta.json are pointers only:
// confirm every value in text.txt or the screenshot before recording it.
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

function loadPlaywright() {
  try {
    return require("playwright");
  } catch {
    const root = execSync("npm root -g").toString().trim();
    return require(path.join(root, "playwright"));
  }
}

const BLOCK_SIGNS = [
  /enter the characters you see below/i, /are you a robot/i, /captcha/i,
  /unusual traffic/i, /access denied/i, /request blocked/i, /verify you are human/i,
  /sorry, we just need to make sure you're not a robot/i, /too many requests/i,
];

// Collected inside the page.
function collect() {
  const text = document.body ? document.body.innerText : "";
  const meta = {};
  for (const m of document.querySelectorAll("meta[property], meta[name]")) {
    const k = m.getAttribute("property") || m.getAttribute("name");
    if (/^(og:|product:|twitter:title|twitter:description|description)/.test(k)) {
      meta[k] = m.getAttribute("content");
    }
  }
  const jsonld = [];
  for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
    try { jsonld.push(JSON.parse(s.textContent)); } catch { /* skip broken blocks */ }
  }
  const pick = (sel) => {
    const el = document.querySelector(sel);
    return el ? el.textContent.replace(/\s+/g, " ").trim() : null;
  };
  // Amazon element ids that have been stable for years; null if absent.
  const amazon = {
    title: pick("#productTitle"),
    price: pick(".a-price .a-offscreen") || pick("#priceblock_ourprice") || pick("#priceblock_dealprice"),
    rating: pick("#acrPopover .a-icon-alt") || pick("#acrPopover"),
    ratings_count: pick("#acrCustomerReviewText"),
    bought_past_month: pick("#social-proofing-faceout-title-tk_bought"),
    image_thumbnails: document.querySelectorAll("#altImages li.imageThumbnail, #altImages li.item").length || null,
    has_video: !!document.querySelector("#altImages li.videoThumbnail, .videoBlockIngress"),
    has_a_plus: !!document.querySelector("#aplus, #aplus_feature_div .aplus-v2"),
    bullets: [...document.querySelectorAll("#feature-bullets li span.a-list-item")]
      .map((e) => e.textContent.replace(/\s+/g, " ").trim()).filter(Boolean),
  };
  return {
    title: document.title,
    canonical: (document.querySelector('link[rel="canonical"]') || {}).href || null,
    meta, jsonld, amazon, text,
    images: document.images.length,
  };
}

function findProducts(node, out = []) {
  if (Array.isArray(node)) node.forEach((n) => findProducts(n, out));
  else if (node && typeof node === "object") {
    const t = node["@type"];
    if (t === "Product" || (Array.isArray(t) && t.includes("Product"))) {
      const offers = [].concat(node.offers || []).flatMap((o) => o.offers || o);
      out.push({
        name: node.name || null,
        brand: (node.brand && (node.brand.name || node.brand)) || null,
        sku: node.sku || null,
        price: offers.map((o) => o.price || o.lowPrice).find((p) => p != null) ?? null,
        currency: offers.map((o) => o.priceCurrency).find(Boolean) || null,
        availability: offers.map((o) => o.availability).find(Boolean) || null,
        rating: node.aggregateRating ? node.aggregateRating.ratingValue : null,
        rating_count: node.aggregateRating
          ? node.aggregateRating.ratingCount || node.aggregateRating.reviewCount : null,
      });
    }
    Object.values(node).forEach((v) => findProducts(v, out));
  }
  return out;
}

function textHints(text) {
  const all = (re) => [...text.matchAll(re)].map((m) => m[0].trim()).slice(0, 8);
  return {
    prices: all(/(?:₹|Rs\.?|INR|\$|€|£)\s?[\d,]+(?:\.\d{1,2})?/g),
    mrp: all(/M\.?R\.?P\.?[^\n]{0,30}/gi),
    ratings: all(/\b[0-5](?:\.\d)?\s?(?:out of 5|★|stars?)\b/gi),
    counts: all(/[\d,]+\+?\s+(?:ratings|reviews|global ratings|Ratings & \d[\d,]* Reviews)/gi),
    bought: all(/[\d,.]+[KkMm]?\+?\s+bought in past month/gi),
    best_sellers_rank: all(/Best Sellers Rank[^\n]{0,120}/gi),
    discount: all(/\d{1,2}%\s?off/gi),
  };
}

async function main() {
  const args = process.argv.slice(2);
  const full = args.includes("--full");
  const waitIdx = args.indexOf("--wait");
  const wait = waitIdx >= 0 ? Number(args[waitIdx + 1]) : 2500;
  const pos = args.filter((a, i) => !a.startsWith("--") && args[i - 1] !== "--wait");
  if (pos.length !== 2) {
    console.error("usage: fetch_page.cjs URL OUT_DIR [--full] [--wait ms]");
    process.exit(2);
  }
  const [url, outDir] = pos;
  fs.mkdirSync(outDir, { recursive: true });

  const { chromium } = loadPlaywright();
  const launch = process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {};
  const browser = await chromium.launch(launch);
  const context = await browser.newContext({
    viewport: { width: 1366, height: 900 },
    locale: process.env.FETCH_LOCALE || "en-IN",
  });
  const page = await context.newPage();
  const result = { url, fetched_at: new Date().toISOString(), status: null, final_url: null };
  try {
    const resp = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    result.status = resp ? resp.status() : null;
    await page.waitForTimeout(wait);
    result.final_url = page.url();
    const data = await page.evaluate(collect);
    const blocked = BLOCK_SIGNS.some((re) => re.test(data.text.slice(0, 5000)))
      || [403, 429, 503].includes(result.status);
    Object.assign(result, {
      blocked,
      title: data.title,
      canonical: data.canonical,
      meta: data.meta,
      products: findProducts(data.jsonld),
      amazon: Object.values(data.amazon).some((v) => v && (v.length === undefined || v.length))
        ? data.amazon : null,
      hints: textHints(data.text),
      image_tags: data.images,
      text_chars: data.text.length,
    });
    fs.writeFileSync(path.join(outDir, "text.txt"), data.text);
    await page.screenshot({ path: path.join(outDir, "screenshot.png"), fullPage: full });
  } catch (e) {
    result.error = e.message.split("\n")[0];
    result.blocked = null;
  }
  fs.writeFileSync(path.join(outDir, "meta.json"), JSON.stringify(result, null, 2));
  await browser.close();
  console.log(JSON.stringify({
    url, status: result.status, blocked: result.blocked, error: result.error || null,
    title: result.title || null, products: (result.products || []).length,
    saved: outDir,
  }));
}

main().catch((e) => { console.error(e.message); process.exit(1); });
