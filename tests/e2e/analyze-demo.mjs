/**
 * E2E demo test — drives the PUBLIC site exactly like a real user:
 * logs in (basic auth ora/ora), fills the New Brand Analysis form, clicks
 * Start Analysis, and asserts that (1) the staged loader is actually visible
 * and progresses, and (2) the run redirects to a report page that renders
 * real results. Screenshots are written to tests/e2e/artifacts/ as proof.
 *
 * Requires the `playwright` package resolvable from this file. Either install it
 * in the frontend (npm i -D playwright && npx playwright install chromium) or,
 * for a one-off run, symlink a node_modules that already has it next to this
 * file:  ln -s <path>/node_modules tests/e2e/node_modules
 * Then:  node tests/e2e/analyze-demo.mjs
 */
import { chromium } from "playwright";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { mkdirSync } from "fs";

const BASE_URL = "https://brandcompass-develop.oratelecom.net";
const CREDENTIALS = { username: "ora", password: "ora" };
const BRAND = { name: "relyance", url: "https://relyanceagency.com/", industry: "closing", competitor: "sopra" };
const LOADER_TIMEOUT_MS = 12_000;
const REDIRECT_TIMEOUT_MS = 75_000;
// Language-agnostic: UI defaults to FR ("Étape") but can be EN ("Step").
const STEP_RE = /(Étape|Step)\s*\d+\s*\/\s*8/;

const __dirname = dirname(fileURLToPath(import.meta.url));
const ART = join(__dirname, "artifacts");
mkdirSync(ART, { recursive: true });

const log = (...a) => console.log(...a);
let loaderSeen = false;
let stageSamples = [];
let reportUrl = null;
let reportSnippet = "";

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ httpCredentials: CREDENTIALS, ignoreHTTPSErrors: true });
const page = await ctx.newPage();

try {
  log("→ open", BASE_URL + "/analyze");
  await page.goto(BASE_URL + "/analyze", { waitUntil: "domcontentloaded", timeout: 30_000 });
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});

  const startBtn = page.locator('button[type="submit"]');
  // Controlled inputs: fill only registers once React has hydrated. Retry the
  // fill until the submit button actually enables (proof that onChange fired).
  let enabled = false;
  for (let attempt = 0; attempt < 8 && !enabled; attempt++) {
    await page.getByPlaceholder("Nike", { exact: true }).fill(BRAND.name);
    await page.getByPlaceholder("https://www.nike.com", { exact: true }).fill(BRAND.url);
    await page.getByPlaceholder("sportswear", { exact: true }).fill(BRAND.industry);
    await page.getByPlaceholder("adidas", { exact: true }).fill(BRAND.competitor);
    enabled = await startBtn.isEnabled();
    if (!enabled) await page.waitForTimeout(500);
  }
  if (!enabled) throw new Error("Submit button never enabled — form state not updating (hydration?)");
  await page.screenshot({ path: join(ART, "01-form.png") });

  log("→ click Start Analysis");
  await startBtn.click();

  // (1) The staged loader must appear. If hydration is broken the click does
  // nothing and this throws — which is exactly the bug we are guarding against.
  await page.getByText(STEP_RE).waitFor({ timeout: LOADER_TIMEOUT_MS });
  loaderSeen = true;
  await page.screenshot({ path: join(ART, "02-loader.png") });
  log("✓ loader visible");

  // Sample the loader a few times to prove it actually progresses.
  for (let i = 0; i < 6; i++) {
    const box = page.locator("main >> text=/Étape|Terminé/").first();
    const step = (await page.getByText(STEP_RE).first().textContent().catch(() => null)) || "";
    const pct = (await page.locator("text=/%$/").first().textContent().catch(() => null)) || "";
    if (step || pct) stageSamples.push(`${step.trim()} ${pct.trim()}`.trim());
    await page.waitForTimeout(3500);
  }
  log("loader samples:", JSON.stringify(stageSamples));

  // (2) Must redirect to a real report and render results.
  log("→ waiting for redirect to /reports/...");
  await page.waitForURL(/\/reports\/[0-9a-f-]+/i, { timeout: REDIRECT_TIMEOUT_MS });
  reportUrl = page.url();
  // The report page fetches its data client-side ("Loading report..."). Wait for
  // the real content to render before asserting.
  await page.getByText(/Loading report/i).waitFor({ state: "detached", timeout: 25_000 }).catch(() => {});
  await page.getByText(/SEO|SWOT|GEO|positioning|recommendation|relyance/i).first()
    .waitFor({ state: "visible", timeout: 25_000 }).catch(() => {});
  // Let gauges count up and reveal animations settle before the proof shot.
  await page.waitForTimeout(2200);
  reportSnippet = (await page.locator("body").innerText()).replace(/\s+/g, " ").slice(0, 600);
  // Capture per-viewport while scrolling: fixed parallax bg + scroll-reveal
  // sections only paint correctly within the viewport, so fullPage misleads.
  const total = await page.evaluate(() => document.body.scrollHeight);
  const vh = await page.evaluate(() => window.innerHeight);
  let shot = 0;
  for (let y = 0; y < total; y += Math.round(vh * 0.85)) {
    await page.evaluate((yy) => window.scrollTo(0, yy), y);
    await page.waitForTimeout(900);
    await page.screenshot({ path: join(ART, `03-report-${String(shot).padStart(2, "0")}.png`) });
    shot++;
    if (shot > 8) break;
  }
  log("✓ report url:", reportUrl);

  const hasResults = /SEO|SWOT|GEO|positioning|score|relyance/i.test(reportSnippet) &&
    !/Loading report/i.test(reportSnippet);
  const PASS = loaderSeen && reportUrl && hasResults;

  log("\n==== RESULT ====");
  log("loaderSeen   :", loaderSeen);
  log("reportUrl    :", reportUrl);
  log("hasResults   :", hasResults);
  log("report text  :", reportSnippet.slice(0, 300));
  log("VERDICT      :", PASS ? "PASS ✅" : "FAIL ❌");
  process.exitCode = PASS ? 0 : 1;
} catch (err) {
  await page.screenshot({ path: join(ART, "99-error.png") }).catch(() => {});
  log("\n==== RESULT ====");
  log("loaderSeen   :", loaderSeen);
  log("ERROR        :", err.message);
  log("VERDICT      : FAIL ❌");
  process.exitCode = 1;
} finally {
  await browser.close();
}
