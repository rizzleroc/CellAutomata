// Record a vertical 9:16 walkthrough of the web9 UI for the promo.
//
// 1. serve docs/web9:  python3 -m http.server 8798
// 2. run:  URL=http://localhost:8798/ DUR=30000 node capture.mjs
//
// Produces capture/<id>.webm at 1080x1920. Rename to web9.webm for build.sh.
// Run on a networked machine so the #origin clip loads in-page (or self-host
// protocell.mp4 into ../assets/video/ first).
import { chromium } from "playwright";

const URL = process.env.URL || "http://localhost:8798/";
const OUTDIR = process.env.OUTDIR || "capture";
const DUR = Number(process.env.DUR || 30000); // scroll duration, ms

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 540, height: 960 },
  deviceScaleFactor: 2, // -> 1080x1920 capture
  recordVideo: { dir: OUTDIR, size: { width: 1080, height: 1920 } },
});
const page = await context.newPage();
await page.goto(URL, { waitUntil: "networkidle" });
await page.waitForTimeout(2500); // let the hero + clip settle

// smooth ease-in-out scroll through the whole page over DUR ms
await page.evaluate(
  (dur) =>
    new Promise((done) => {
      const max = Math.max(0, document.body.scrollHeight - innerHeight);
      const t0 = performance.now();
      (function frame(now) {
        const t = Math.min(1, (now - t0) / dur);
        const e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
        scrollTo(0, max * e);
        t < 1 ? requestAnimationFrame(frame) : done();
      })(t0);
    }),
  DUR,
);

await page.waitForTimeout(1500);
await context.close(); // finalizes the .webm
await browser.close();
console.log(`captured -> ${OUTDIR}/*.webm  (rename to web9.webm for build.sh)`);
